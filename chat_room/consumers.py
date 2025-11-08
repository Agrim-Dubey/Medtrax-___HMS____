from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
from django.utils import timezone

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        print("=" * 50)
        print("🔵 WebSocket connection attempt started")

        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        print(f"📍 Room ID: {self.room_id}")
        print(f"👤 User: {self.user} (Authenticated: {self.user.is_authenticated})")

        if not self.user.is_authenticated:
            print("❌ User not authenticated - closing connection")
            await self.close(code=4001)
            return

        print("✅ User is authenticated")
        print("🔍 Fetching room data...")

        room_data = await self.get_room_data()

        if not room_data:
            print("❌ Room not found - closing connection")
            await self.close(code=4004)
            return

        print(f"✅ Room data: {room_data}")

        if not room_data['is_participant']:
            print("❌ User is not a participant - closing connection")
            await self.close(code=4003)
            return

        print("✅ User is a participant")

        if not room_data['is_active']:
            print("❌ Room is not active - closing connection")
            await self.close(code=4005)
            return

        print("✅ Room is active")

        self.room_type = room_data['room_type']

        print(f"📝 Adding to channel group: {self.room_group_name}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        print("✅ Added to channel group")
        print("🤝 Accepting WebSocket connection...")

        await self.accept()

        print("✅ WebSocket accepted")
        print("📜 Fetching message history...")

        try:
            messages = await self.get_message_history()
            print(f"✅ Message history fetched: {len(messages)} messages")
        except Exception as e:
            print(f"❌ Error fetching message history: {e}")
            messages = []

        print("📤 Sending connection_established message...")

        try:
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to chat',
                'room_id': self.room_id,
                'user_id': self.user.id,
                'messages': messages
            }))
            print("✅ Connection established message sent successfully!")
            print("🎉 WebSocket connection complete and stable!")
        except Exception as e:
            print(f"❌ Error sending message: {e}")

        print("=" * 50)

    async def disconnect(self, close_code):
        print("=" * 50)
        print(f"🔴 WebSocket disconnecting - Close code: {close_code}")
        print(f"👤 User: {self.user if hasattr(self, 'user') else 'Unknown'}")
        print(f"📍 Room: {self.room_id if hasattr(self, 'room_id') else 'Unknown'}")

        if hasattr(self, 'room_group_name'):
            print(f"🚪 Removing from group: {self.room_group_name}")
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print("✅ Removed from channel group")

        print("=" * 50)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages from frontend."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
            return

        message = data.get('message', '').strip()
        if not message:
            return

        saved_message = await self.save_message(message)
        if not saved_message:
            await self.send(text_data=json.dumps({"error": "Unable to save message"}))
            return

        full_name = await self.get_user_full_name()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': saved_message.content,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'sender_full_name': full_name,
                'sender_role': self.user.role,
                'message_id': saved_message.id,
                'timestamp': saved_message.timestamp.isoformat(),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'sender_full_name': event['sender_full_name'],
            'sender_role': event['sender_role'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))

    async def typing_indicator(self, event):
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    # ---------- Database Utilities ---------- #

    @database_sync_to_async
    def get_message_history(self):
        try:
            messages = Message.objects.filter(
                room_id=self.room_id
            ).select_related('sender').order_by('-timestamp')[:50]

            message_list = []
            for msg in reversed(messages):
                sender_name = msg.sender.username
                try:
                    if msg.sender.role == 'doctor':
                        sender_name = f"Dr. {msg.sender.doctor_profile.get_full_name()}"
                    elif msg.sender.role == 'patient':
                        sender_name = msg.sender.patient_profile.get_full_name()
                except Exception as e:
                    print(f"⚠️ Error getting full name for user {msg.sender.id}: {e}")

                message_list.append({
                    'id': msg.id,
                    'sender_id': msg.sender.id,
                    'sender_username': msg.sender.username,
                    'sender_full_name': sender_name,
                    'sender_role': msg.sender.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'is_read': msg.is_read
                })
            return message_list

        except Exception as e:
            print(f"❌ Error fetching message history: {type(e).__name__}: {e}")
            import traceback
            print(traceback.format_exc())
            return []

    @database_sync_to_async
    def get_room_data(self):
        try:
            room = ChatRoom.objects.prefetch_related('participants').get(id=self.room_id)
            return {
                'is_participant': room.participants.filter(id=self.user.id).exists(),
                'is_active': room.is_active,
                'room_type': room.room_type
            }
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, content):
        try:
            room = ChatRoom.objects.get(id=self.room_id, is_active=True)

            if not room.participants.filter(id=self.user.id).exists():
                return None

            message = Message.objects.create(
                room=room,
                sender=self.user,
                content=content
            )
            room.updated_at = timezone.now()
            room.save()
            return message
        except Exception as e:
            print(f"❌ Error saving message: {e}")
            return None

    @database_sync_to_async
    def get_user_full_name(self):
        try:
            if self.user.role == 'doctor':
                return f"Dr. {self.user.doctor_profile.get_full_name()}"
            elif self.user.role == 'patient':
                return self.user.patient_profile.get_full_name()
        except Exception:
            return self.user.username
        return self.user.username
