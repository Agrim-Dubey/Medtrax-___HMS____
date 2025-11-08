from channels.generic.websocket import AsyncWebsocketConsumer
import json

class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.doctor_id = self.scope["url_route"]["kwargs"]["doctor_id"]
        self.group_name = f"doctor_{self.doctor_id}_queue"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_queue_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))

