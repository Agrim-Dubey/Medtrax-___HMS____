from django.test import TestCase
from unittest.mock import AsyncMock, patch
from chat_room.middleware import WebSocketRateLimitMiddleware

class WebSocketRateLimitMiddlewareTests(TestCase):
    def setUp(self):
        self.inner_app = AsyncMock()
        self.middleware = WebSocketRateLimitMiddleware(self.inner_app)

    @patch("chat_room.middleware.cache")
    async def test_middleware_allows_normal_rate(self, mock_cache):
        mock_cache.get.return_value = 2
        mock_user = AsyncMock(id=99, is_authenticated=True)
        scope = {"type": "websocket", "user": mock_user}
        send = AsyncMock()
        receive = AsyncMock()

        await self.middleware(scope, receive, send)
        self.inner_app.assert_awaited_once_with(scope, receive, send)

    @patch("chat_room.middleware.cache")
    async def test_middleware_blocks_excessive_attempts(self, mock_cache):
        mock_cache.get.return_value = 15
        mock_user = AsyncMock(id=99, is_authenticated=True)
        scope = {"type": "websocket", "user": mock_user}
        send = AsyncMock()
        receive = AsyncMock()

        await self.middleware(scope, receive, send)
        send.assert_awaited_once()
        sent_data = send.await_args[0][0]
        self.assertEqual(sent_data["type"], "websocket.close")
        self.assertEqual(sent_data["code"], 4029)
