from django.urls import re_path
from .consumers import VideoCallConsumer

websocket_urlpatterns = [
    re_path(r"ws/video/(?P<room_id>\d+)/$", VideoCallConsumer.as_asgi()),
]
