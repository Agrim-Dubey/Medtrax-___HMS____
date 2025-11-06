import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Message
from Authapi.models import CustomUser
from django.db.models import Q


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
        
        await self.accept()
        

        await self.set_user_online(True)
        

        await self.channel_layer.group_send(
            'online_users',
            {
                'type': 'user_status',
                'user_id': self.user_id,
                'is_online': True
            }
        )
    
    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        if not self.user.is_anonymous:

            await self.set_user_online(False)
 
            await self.channel_layer.group_send(
                'online_users',
                {
                    'type': 'user_status',
                    'user_id': self.user_id,
                    'is_online': False
                }
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            receiver_id = data.get('receiver_id')
            content = data.get('content')

            message = await self.save_message(
                sender_id=self.user.id,
                receiver_id=receiver_id,
                content=content
            )

            await self.update_conversation(
                sender_id=self.user.id,
                receiver_id=receiver_id,
                message_id=message.id
            )

            await self.channel_layer.group_send(
                f'user_{receiver_id}',
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'sender_id': self.user.id,
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
                    'receiver_id': receiver_id,
                    'content': content,
                    'timestamp': message.timestamp.isoformat(),
                    'is_read': False
                }
            }))
        
        elif message_type == 'mark_read':
            message_ids = data.get('message_ids', [])
            await self.mark_messages_read(message_ids)
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))
    
    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'is_online': event['is_online']
        }))
    
    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        sender = CustomUser.objects.get(id=sender_id)
        receiver = CustomUser.objects.get(id=receiver_id)
        return Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=content
        )
    
    @database_sync_to_async
    def update_conversation(self, sender_id, receiver_id, message_id):
        sender = CustomUser.objects.get(id=sender_id)
        receiver = CustomUser.objects.get(id=receiver_id)
        message = Message.objects.get(id=message_id)

        conversation = Conversation.objects.filter(
            (Q(participant1=sender) & Q(participant2=receiver)) |
            (Q(participant1=receiver) & Q(participant2=sender))
        ).first()
        
        if conversation:
            conversation.last_message = message
            conversation.save()
        else:
            Conversation.objects.create(
                participant1=sender,
                participant2=receiver,
                last_message=message
            )
    
    @database_sync_to_async
    def set_user_online(self, is_online):
        UserOnlineStatus.objects.update_or_create(
            user=self.user,
            defaults={'is_online': is_online}
        )
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        Message.objects.filter(
            id__in=message_ids,
            receiver=self.user
        ).update(is_read=True, read_at=timezone.now())