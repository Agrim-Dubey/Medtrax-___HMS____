import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from appointments.models import Appointment
from .models import VideoCall
from django.utils import timezone


class VideoCallConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.appointment_id = self.scope['url_route']['kwargs']['appointment_id']
        self.room_group_name = f'video_{self.appointment_id}'

        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if token:
            self.user = await self.get_user_from_token(token)
        else:
            self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        is_participant = await self.check_participant()
        if not is_participant:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'user_joined',
            'user_id': self.user.id,
        })

    async def disconnect(self, close_code):
        user_id = getattr(self.user, 'id', None)
        if hasattr(self, 'room_group_name') and user_id:
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'user_left',
                'user_id': user_id,
            })
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        # Note: Do NOT mark call as ended on simple socket drop or page refresh.
        # Explicit end_call signal handles permanent termination.

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        msg_type = data.get('type')

        if msg_type == 'offer':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'signal_offer',
                'offer': data['offer'],
                'sender_id': self.user.id,
            })

        elif msg_type == 'answer':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'signal_answer',
                'answer': data['answer'],
                'sender_id': self.user.id,
            })

        elif msg_type == 'ice_candidate':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'signal_ice',
                'candidate': data['candidate'],
                'sender_id': self.user.id,
            })

        elif msg_type == 'peer_ready':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'signal_peer_ready',
                'sender_id': self.user.id,
            })

        elif msg_type == 'end_call':
            await self.end_call_if_active()
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'call_ended',
                'sender_id': self.user.id,
            })

    async def user_joined(self, event):
        # Don't echo self join back to self
        if event['user_id'] != getattr(self.user, 'id', None):
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
            }))

    async def user_left(self, event):
        # Don't echo self leave back to self
        if event['user_id'] != getattr(self.user, 'id', None):
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
            }))

    async def signal_offer(self, event):
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'offer',
                'offer': event['offer'],
            }))

    async def signal_answer(self, event):
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'answer': event['answer'],
            }))

    async def signal_ice(self, event):
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate'],
            }))

    async def signal_peer_ready(self, event):
        if event['sender_id'] != getattr(self.user, 'id', None):
            await self.send(text_data=json.dumps({
                'type': 'peer_ready',
                'user_id': event['sender_id'],
            }))

    async def call_ended(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_ended',
        }))

    @database_sync_to_async
    def check_participant(self):
        try:
            appointment = Appointment.objects.get(id=self.appointment_id)
            user = self.user
            is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
            is_patient = hasattr(user, 'patient_profile') and appointment.patient == user.patient_profile
            return is_doctor or is_patient
        except Appointment.DoesNotExist:
            return False

    @database_sync_to_async
    def get_user_from_token(self, token):
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return UserModel.objects.get(id=user_id)
        except Exception:
            return None

    @database_sync_to_async
    def end_call_if_active(self):
        try:
            video_call = VideoCall.objects.get(appointment_id=self.appointment_id)
            if video_call.status in ['active', 'waiting']:
                video_call.status = 'ended'
                video_call.ended_at = timezone.now()
                video_call.save()
        except VideoCall.DoesNotExist:
            pass