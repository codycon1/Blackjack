from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.serializers import serialize

from game import models

class SingleplayerConsumer(WebsocketConsumer):

    def connect(self):
        self.room_name = "room"
        self.room_group_name = "group"
        print(self.scope['user'])
        async_to_sync(self.channel_layer.group_add)(
            str(self.room_group_name), self.channel_name
        )
        self.accept()
        print("Client connected", self.room_group_name)

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            str(self.room_group_name), self.channel_name
        )
        print("Client disconnected", self.room_group_name)
