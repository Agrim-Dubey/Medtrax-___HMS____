from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.utils import timezone
from datetime import datetime, timedelta

from .models import ChatRoom, Message, DoctorConnection, GroupMembership
from .serializers import (
    ChatRoomListSerializer, ChatRoomDetailSerializer,
    MessageSerializer, MessageCreateSerializer,
    DoctorConnectionSerializer, DoctorConnectionListSerializer,
    GroupRoomSerializer, GroupMembershipSerializer,
    DoctorMinimalSerializer
)
from Authapi.models import Doctor, Patient

class PatientChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list_doctor_chats(self, request):
        if request.user.role != 'patient':
            return Response(
                {"error": "Only patients can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        now = timezone.now()
        today = now.date()
        chat_rooms = ChatRoom.objects.filter(
            room_type='patient_doctor',
            participants=request.user,
            is_active=True,
            appointment__status='confirmed',
            appointment__appointment_date__gte=today 
        ).select_related('appointment').prefetch_related('participants')
    
        valid_rooms = []
        for room in chat_rooms:
            appt = room.appointment

            if appt.appointment_date == today:
                appt_datetime = datetime.combine(
                    appt.appointment_date, 
                    appt.appointment_time
                )
                appt_datetime = timezone.make_aware(appt_datetime)
                if appt_datetime > now:
                    valid_rooms.append(room)
            else:
                valid_rooms.append(room)
        
        serializer = ChatRoomListSerializer(
            valid_rooms, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    def list_groups(self, request):
        if request.user.role != 'patient':
            return Response(
                {"error": "Only patients can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            patient = request.user.patient_profile
            patient_diseases = getattr(patient, 'diseases', [])
        except:
            patient_diseases = []

        groups = ChatRoom.objects.filter(
            room_type='group',
            is_active=True
        ).prefetch_related('participants')
        
        serializer = GroupRoomSerializer(
            groups, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    def join_group(self, request):
        if request.user.role != 'patient':
            return Response(
                {"error": "Only patients can join groups"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        group_id = request.data.get('group_id')
        disease_name = request.data.get('disease_name')
        
        if not group_id:
            return Response(
                {"error": "group_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        group = get_object_or_404(ChatRoom, id=group_id, room_type='group')

        patient = request.user.patient_profile

        if group.participants.filter(id=request.user.id).exists():
            return Response(
                {"message": "Already a member of this group"},
                status=status.HTTP_200_OK
            )

        group.participants.add(request.user)

        GroupMembership.objects.get_or_create(
            patient=patient,
            group_room=group,
            defaults={'is_diagnosed': True}
        )
        
        return Response(
            {"message": "Successfully joined the group"},
            status=status.HTTP_201_CREATED
        )
class DoctorChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list_patient_chats(self, request):
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        now = timezone.now()
        today = now.date()
        chat_rooms = ChatRoom.objects.filter(
            room_type='patient_doctor',
            participants=request.user,
            is_active=True,
            appointment__status='confirmed',
            appointment__appointment_date__gte=today
        ).select_related('appointment').prefetch_related('participants')
        
        serializer = ChatRoomListSerializer(
            chat_rooms, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    def list_doctor_chats(self, request):
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        chat_rooms = ChatRoom.objects.filter(
            room_type='doctor_doctor',
            participants=request.user,
            is_active=True
        ).prefetch_related('participants')
        
        serializer = ChatRoomListSerializer(
            chat_rooms, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    def send_connection_request(self, request):
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can send connection requests"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DoctorConnectionSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def list_pending_requests(self, request):
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        doctor = request.user.doctor_profile
        requests = DoctorConnection.objects.filter(
            to_doctor=doctor,
            status='pending'
        ).select_related('from_doctor', 'to_doctor')
        
        serializer = DoctorConnectionListSerializer(requests, many=True)
        return Response(serializer.data)
    
    def accept_connection(self, request, pk):
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can accept connections"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        doctor = request.user.doctor_profile
        connection = get_object_or_404(
            DoctorConnection, 
            pk=pk, 
            to_doctor=doctor,
            status='pending'
        )
        connection.status = 'accepted'
        chat_room = ChatRoom.objects.create(
            room_type='doctor_doctor',
            is_active=True
        )
        chat_room.participants.add(
            connection.from_doctor.user,
            connection.to_doctor.user
        )
        
        connection.chat_room = chat_room
        connection.save()
        
        serializer = DoctorConnectionSerializer(connection)
        return Response(serializer.data)
    
    def reject_connection(self, request, pk):
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can reject connections"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        doctor = request.user.doctor_profile
        connection = get_object_or_404(
            DoctorConnection,
            pk=pk,
            to_doctor=doctor,
            status='pending'
        )
        
        connection.status = 'rejected'
        connection.save()
        
        return Response({"message": "Connection request rejected"})
    
    def search_doctors(self, request):
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can search for other doctors"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {"error": "Search query 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        doctors = Doctor.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(specialization__icontains=query)
        ).exclude(user=request.user)[:20] 
        
        serializer = DoctorMinimalSerializer(doctors, many=True)
        return Response(serializer.data)

class ChatRoomViewSet(viewsets.ViewSet):

    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, pk):
        chat_room = get_object_or_404(ChatRoom, pk=pk)
        if not chat_room.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not a participant in this chat"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ChatRoomDetailSerializer(
            chat_room,
            context={'request': request}
        )
        return Response(serializer.data)
    
    def send_message(self, request, pk):
        chat_room = get_object_or_404(ChatRoom, pk=pk)
        if not chat_room.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not a participant in this chat"},
                status=status.HTTP_403_FORBIDDEN
            )
        if not chat_room.is_active:
            return Response(
                {"error": "This chat is no longer active"},
                status=status.HTTP_403_FORBIDDEN
            )
        message = Message.objects.create(
            room=chat_room,
            sender=request.user,
            content=request.data.get('content', '')
        )
        chat_room.save()
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def mark_as_read(self, request, pk):
        chat_room = get_object_or_404(ChatRoom, pk=pk)

        if not chat_room.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not a participant in this chat"},
                status=status.HTTP_403_FORBIDDEN
            )

        Message.objects.filter(
            room=chat_room,
            is_read=False
        ).exclude(
            sender=request.user
        ).update(is_read=True)
        
        return Response({"message": "Messages marked as read"})