from django.test import TestCase
from unittest.mock import AsyncMock, patch
from appointments.consumers import QueueConsumer

class QueueConsumerTests(TestCase):
    def setUp(self):
        self.consumer = QueueConsumer()
        self.consumer.scope = {
            "url_route": {"kwargs": {"doctor_id": "42"}},
            "user": AsyncMock(is_authenticated=True)
        }
        self.consumer.channel_layer = AsyncMock()
        self.consumer.channel_name = "test_queue_channel"
        self.consumer.accept = AsyncMock()
        self.consumer.send = AsyncMock()

    async def test_queue_consumer_connect(self):
        await self.consumer.connect()
        self.assertEqual(self.consumer.group_name, "doctor_42_queue")
        self.consumer.accept.assert_awaited_once()

    async def test_send_queue_update(self):
        event = {"data": {"current_queue_count": 3, "estimated_wait_time": 90}}
        await self.consumer.send_queue_update(event)
        self.consumer.send.assert_awaited_once()
