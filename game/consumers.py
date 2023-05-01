import json

from asgiref.sync import async_to_sync
from django.db.models import Count
from channels.generic.websocket import WebsocketConsumer
from django.core.serializers import serialize

from game import models
from game import utility
from game.utility import *
import game.utility_mp as mp


# PREPARE FOR REWRITE

class SingleplayerConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None
        self.room_name = None
        self.room_group_name = None
        self.table = None

    def connect(self):
        # self.user is a proper model instance
        self.user = self.scope["user"]
        self.room_name = self.user.pk
        self.room_group_name = self.user.pk
        async_to_sync(self.channel_layer.group_add)(
            str(self.room_group_name), str(self.channel_name)
        )
        self.accept()
        print("Client connected", self.room_group_name)
        self.table = sp_prep_table(self.user)

        syncjson = sp_sync(self.table, self.user)
        if syncjson is not None:
            self.send(syncjson)

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            str(self.room_group_name), self.channel_name
        )
        print("Client disconnected", self.room_group_name)

    def send_resp(self, event):
        message = event["message"]
        self.send(text_data=json.dumps(message))

    def receive(self, text_data):
        print("Receiving", text_data)
        rec_data = json.loads(text_data)

        resp = sp_process_input_json(rec_data, self.user)

        if resp is not None:
            self.send(text_data=resp)


class MultiplayerConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None
        self.players = []
        self.room_name = None
        self.room_group_name = None
        self.table = None

    def connect(self):
        # self.user is a proper model instance
        self.user = self.scope["user"]
        self.table = mp.mp_prep_table(self.user)
        self.room_name = str(self.table.pk)
        self.room_group_name = str(self.table.pk)
        self.accept()
        async_to_sync(self.channel_layer.group_add)(
            str(self.room_group_name), str(self.channel_name)
        )
        print("Client connected", self.room_group_name)

        group_sync_json = mp.mp_group_sync(self.table)
        if group_sync_json is not None:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {"type": "send_resp", "message": group_sync_json}
            )

        personal_sync_json = mp.mp_sync(self.table, self.user)
        if personal_sync_json is not None:
            self.send(text_data=json.dumps(personal_sync_json))

    def disconnect(self, close_code):
        group_sync_json = mp.mp_player_disconnect(self.table, self.user)
        if group_sync_json is not None:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {"type": "send_resp", "message": group_sync_json}
            )
        async_to_sync(self.channel_layer.group_discard)(
            str(self.room_group_name), self.channel_name
        )
        print("Client disconnected", self.room_group_name)

    def send_resp(self, event):
        message = event["message"]
        player = event.get("player")
        if player is None or player == self.user.pk:
            self.send(text_data=json.dumps(message))

    def receive(self, text_data):
        print("Receiving", text_data)
        rec_data = json.loads(text_data)

        self.table.refresh_from_db()

        if rec_data.get("ready_action"):
            self.table.mp_status += 1
            self.table.save()

        table_status = self.table.mp_status
        player_count = self.table.players.all().count()

        if table_status >= player_count:
            resp = mp.mp_process_input_json(rec_data, self.user, self.table)
            if table_status == player_count:
                self.table.mp_status = table_status * 2
                self.table.save()

                for player in self.table.players.all().exclude(pk=self.user.pk):
                    ind_init_resp = mp.mp_sync(self.table, self.user)
                    if ind_init_resp is not None:
                        async_to_sync(self.channel_layer.group_send)(
                            self.room_group_name, {"type": "send_resp", "message": ind_init_resp, "player": player.pk}
                        )
            if resp is not None:
                self.send(text_data=json.dumps(resp))
            group_sync_json = mp.mp_group_sync(self.table)
            if group_sync_json is not None:
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, {"type": "send_resp", "message": group_sync_json}
                )


class HomeConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = 0
        self.room_name = 0
        self.room_group_name = 0

    def connect(self):
        self.user = self.scope["user"]
        self.room_name = self.user.pk
        self.room_group_name = self.user.pk
        async_to_sync(self.channel_layer.group_add)(
            str(self.room_group_name), str(self.channel_name)
        )
        self.accept()
        print("Homepage util connected")

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            str(self.room_group_name), self.channel_name
        )
        print("Homepage util disconnected", self.room_group_name)

    def receive(self, text_data):
        print("Receiving", text_data)

        if text_data == 'nuke':
            print("NUKING DB")
            tables = models.Table.objects.all()
            trackers = models.PlayerTracker.objects.all()
            bets = models.Bet.objects.all()
            cards = models.Card.objects.all()

            tables.delete()
            trackers.delete()
            bets.delete()
            cards.delete()
