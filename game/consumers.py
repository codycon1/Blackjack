import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.serializers import serialize

from game import models
from game import utility
from game.utility import *


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

        syncjson = sp_resync(self.table)
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
        # text_data_json = json.loads(text_data) <- This is JSON conversion, maybe refactor for it
        resp = None
        if text_data == "reset":
            self.table = sp_reset_table(self.user)
            print("Resetting")
        elif text_data == "hit":
            resp = sp_player_draw(self.table)
        elif text_data == "dhit":
            resp = sp_dealer_draw(self.table)

        if resp is not None:
            self.send(text_data=resp)


