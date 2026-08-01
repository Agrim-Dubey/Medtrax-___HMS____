from django.test import TestCase
from unittest.mock import AsyncMock, patch
from chat_room.consumers import ChatConsumer

class ChatConsumerTests(TestCase):
    def setUp(self):
        self.consumer = ChatConsumer()
        self.consumer.scope = {
            "url_route": {"kwargs": {"room_id": "101"}},
            "user": AsyncMock(is_authenticated=True, id=10),
            "query_string": b""
        }
        self.consumer.channel_layer = AsyncMock()
        self.consumer.channel_name = "test_chat_channel"
        self.consumer.accept = AsyncMock()
        self.consumer.close = AsyncMock()
        self.consumer.send = AsyncMock()

    @patch.object(ChatConsumer, "get_room_data")
    @patch.object(ChatConsumer, "get_message_history")
    async def test_chat_consumer_successful_connect(self, mock_hist, mock_room):
        mock_room.return_value = {
            "is_participant": True,
            "is_active": True,
            "appointment_status": "confirmed",
            "room_type": "patient_doctor"
        }
        mock_hist.return_value = []
        await self.consumer.connect()
        self.consumer.accept.assert_awaited_once()
        self.assertEqual(self.consumer.room_group_name, "chat_101")
