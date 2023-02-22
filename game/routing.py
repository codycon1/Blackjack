from django.template.defaulttags import url
from django.urls import re_path, path

from . import consumers

websocket_urlpatterns = [
    path(r"singleplayer", consumers.SingleplayerConsumer.as_asgi()),
]