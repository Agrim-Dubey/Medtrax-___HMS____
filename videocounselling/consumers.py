from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
import json

from chat_room.models import ChatRoom 


class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group = f"video_{self.room_id}"
        self.user = self.scope.get("user") or AnonymousUser()

        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        room_data = await self._get_room_data(self.room_id, self.user.id)
        if not room_data:
            await self.close(code=4004)
            return
        if not room_data["is_participant"]:
            await self.close(code=4003)  
            return
        if not room_data["is_active"] or room_data["room_type"] != "patient_doctor":
            await self.close(code=4005)
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({
            "type": "connected",
            "user_id": self.user.id,
            "role": self.user.role,
            "room_id": int(self.room_id),
        })

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except:
            return

        kind = data.get("type")
        if kind in ("offer", "answer", "ice-candidate", "end"):
            await self.channel_layer.group_send(self.group, {
                "type": "signal.forward",
                "from_user_id": self.user.id,
                "payload": data,
            })

    async def signal_forward(self, event):
        if event.get("from_user_id") == self.user.id:
            return
        await self.send_json(event["payload"])

    async def send_json(self, payload):
        await self.send(text_data=json.dumps(payload))
    @database_sync_to_async
    def _get_room_data(self, room_id, user_id):
        try:
            room = ChatRoom.objects.prefetch_related("participants").get(id=room_id)
            return {
                "is_participant": room.participants.filter(id=user_id).exists(),
                "is_active": room.is_active,
                "room_type": room.room_type
            }
        except ChatRoom.DoesNotExist:
            return None
