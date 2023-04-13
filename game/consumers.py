import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.serializers import serialize

from game import models
from game import utility
from game.utility import *

#PREPARE FOR REWRITE

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

        syncjson = sp_resync(self.table, self.user)
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
        resp = None
        game_over = None

        if 'betamt' in rec_data:
            sp_place_bet(self.table, self.user, int(rec_data['betamt']))
            sp_dealer_hit(self.table)
            sp_dealer_hit(self.table)  # Initial 2x hit
        elif 'action' in rec_data:
            if rec_data['action'] == 'reset':
                self.table = sp_reset_table(self.user)
                print("resetting")
            elif rec_data['action'] == 'Start':
                game_over = sp_check(self.table, self.user)
                sp_player_hit(self.table)
                sp_player_hit(self.table)  # Initial 2x hit
                self.table.status = 2
                self.table.save()
            elif rec_data['action'] == 'Hit':
                sp_player_hit(self.table)
                game_over = sp_check(self.table, self.user)
            elif rec_data['action'] == 'Stay':
                print("Staying")
                game_over = sp_check(self.table, self.user, dealer=True)
                sp_game_over(self.table, self.user, game_over)
            elif rec_data['action'] == 'Again':
                self.table = sp_reset_table(self.user)
            elif rec_data['action'] == 'Split':
                split(self.user)

        if game_over is not None:
            sp_game_over(self.table, self.user, game_over)
            resp = sp_resync(self.table, self.user, dealer_flip=True)
        else:
            resp = sp_resync(self.table, self.user)

        if resp is not None:
            self.send(text_data=resp)
