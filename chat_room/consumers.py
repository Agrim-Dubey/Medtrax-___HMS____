import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from Authapi.models import CustomUser
from .models import Message, UserOnlineStatus
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.user_id = str(self.user.id)
        self.user_group_name = f'user_{self.user_id}'
        
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.set_user_online(True)
        
        await self.accept()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        if hasattr(self, 'user') and not self.user.is_anonymous:
            await self.set_user_online(False)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            receiver_id = data.get('receiver_id')
            content = data.get('content')
            
            message = await self.save_message(self.user.id, receiver_id, content)
            
            await self.channel_layer.group_send(
                f'user_{receiver_id}',
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'sender_id': self.user.id,
                        'sender_username': self.user.username,
                        'receiver_id': receiver_id,
                        'content': content,
                        'timestamp': message.timestamp.isoformat(),
                        'is_read': False
                    }
                }
            )
            
            await self.send(text_data=json.dumps({
                'type': 'message_sent',
                'message': {
                    'id': message.id,
                    'sender_id': self.user.id,
                    'sender_username': self.user.username,
                    'receiver_id': receiver_id,
                    'content': content,
                    'timestamp': message.timestamp.isoformat(),
                    'is_read': False
                }
            }))
        
        elif message_type == 'mark_as_read':
            sender_id = data.get('sender_id')
            await self.mark_messages_as_read(sender_id, self.user.id)
            
            await self.send(text_data=json.dumps({
                'type': 'messages_marked_read',
                'sender_id': sender_id
            }))
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))
    
    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        sender = CustomUser.objects.get(id=sender_id)
        receiver = CustomUser.objects.get(id=receiver_id)
        message = Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=content
        )
        return message
    
    @database_sync_to_async
    def mark_messages_as_read(self, sender_id, receiver_id):
        Message.objects.filter(
            sender_id=sender_id,
            receiver_id=receiver_id,
            is_read=False
        ).update(is_read=True)
    
    @database_sync_to_async
    def set_user_online(self, is_online):
        status, created = UserOnlineStatus.objects.get_or_create(user=self.user)
        status.is_online = is_online
        status.last_seen = timezone.now()
        status.save()