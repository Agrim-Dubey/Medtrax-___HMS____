from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
from django.utils import timezone

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        room_data = await self.get_room_data()
        
        if not room_data:
            await self.close(code=4004)
            return
        
        if not room_data['is_participant']:
            await self.close(code=4003)
            return
        
        if not room_data['is_active']:
            await self.close(code=4005)
            return
        
        self.room_type = room_data['room_type']
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to chat',
            'room_id': self.room_id,
            'user_id': self.user.id
        }))
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                message_content = data.get('message', '').strip()
                
                if not message_content:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Message cannot be empty'
                    }))
                    return
                
                if len(message_content) > 5000:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Message too long'
                    }))
                    return
                
                message_obj = await self.save_message(message_content)
                
                if not message_obj:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Failed to save message'
                    }))
                    return
                
                user_full_name = await self.get_user_full_name()
                
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_content,
                        'sender_id': self.user.id,
                        'sender_username': self.user.username,
                        'sender_full_name': user_full_name,
                        'sender_role': self.user.role,
                        'message_id': message_obj.id,
                        'timestamp': message_obj.timestamp.isoformat(),
                    }
                )
            
            elif message_type == 'typing':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'is_typing': data.get('is_typing', False)
                    }
                )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Server error'
            }))
    
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
        except Exception:
            return None
    
    @database_sync_to_async
    def get_user_full_name(self):
        try:
            if self.user.role == 'doctor':
                return f"Dr. {self.user.doctor_profile.get_full_name()}"
            elif self.user.role == 'patient':
                return self.user.patient_profile.get_full_name()
        except:
            return self.user.username
        return self.user.username