from django.test import TestCase
from unittest.mock import AsyncMock
import json
from videocounselling.consumers import VideoCallConsumer

class VideoCallSignalingEventsTests(TestCase):
    def setUp(self):
        self.consumer = VideoCallConsumer()
        self.consumer.room_group_name = "video_99"
        self.consumer.user = AsyncMock(id=55)
        self.consumer.channel_layer = AsyncMock()

    async def test_relays_offer_signal(self):
        payload = json.dumps({"type": "offer", "offer": {"sdp": "v=0..."}})
        await self.consumer.receive(payload)
        self.consumer.channel_layer.group_send.assert_awaited_once()
        sent_event = self.consumer.channel_layer.group_send.await_args[0][1]
        self.assertEqual(sent_event["type"], "signal_offer")
        self.assertEqual(sent_event["sender_id"], 55)

    async def test_relays_ice_candidate_signal(self):
        payload = json.dumps({"type": "ice_candidate", "candidate": {"candidate": "cand..."}})
        await self.consumer.receive(payload)
        self.consumer.channel_layer.group_send.assert_awaited_once()
        sent_event = self.consumer.channel_layer.group_send.await_args[0][1]
        self.assertEqual(sent_event["type"], "signal_ice")
