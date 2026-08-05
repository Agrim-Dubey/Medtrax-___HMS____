from django.test import TestCase
from unittest.mock import AsyncMock, patch
from videocounselling.consumers import VideoCallConsumer

class VideoCallConsumerConnectionTests(TestCase):
    def setUp(self):
        self.consumer = VideoCallConsumer()
        self.consumer.scope = {
            "url_route": {"kwargs": {"appointment_id": "88"}},
            "user": AsyncMock(is_authenticated=True, id=101)
        }
        self.consumer.channel_layer = AsyncMock()
        self.consumer.channel_name = "test_video_ch"
        self.consumer.accept = AsyncMock()
        self.consumer.close = AsyncMock()

    @patch.object(VideoCallConsumer, "check_participant")
    async def test_consumer_connects_when_authorized(self, mock_check):
        mock_check.return_value = True
        await self.consumer.connect()
        self.consumer.accept.assert_awaited_once()
        self.assertEqual(self.consumer.room_group_name, "video_88")

    @patch.object(VideoCallConsumer, "check_participant")
    async def test_consumer_rejects_unauthorized_user(self, mock_check):
        mock_check.return_value = False
        await self.consumer.connect()
        self.consumer.close.assert_awaited_once()
