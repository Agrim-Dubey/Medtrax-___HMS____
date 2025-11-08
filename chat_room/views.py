from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.utils import timezone
from datetime import datetime

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ChatRoom, Message, DoctorConnection, GroupMembership
from .serializers import (
    ChatRoomListSerializer, ChatRoomDetailSerializer,
    MessageSerializer, DoctorConnectionSerializer,
    DoctorConnectionListSerializer, GroupRoomSerializer,
    DoctorMinimalSerializer
)
from Authapi.models import Doctor

class PatientChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List patient's doctor chats",
        operation_description="Returns all active doctor chat rooms for the patient's confirmed and upcoming appointments.",
        responses={
            200: openapi.Response(
                description="List of doctor chat rooms",
                schema=ChatRoomListSerializer
            ),
            403: openapi.Response(description="Not allowed for non-patient users"),
        },
        tags=["Chat"]
    )
    def list_doctor_chats(self, request):
        if request.user.role != 'patient':
            return Response({"error": "Only patients can access this endpoint"}, status=status.HTTP_403_FORBIDDEN)

        now = timezone.now()
        today = now.date()
        
        chat_rooms = ChatRoom.objects.filter(
            room_type='patient_doctor',
            participants=request.user,
            is_active=True,
            appointment__status='confirmed',
            appointment__appointment_date__gte=today
        ).select_related(
            'appointment',
            'appointment__doctor',
            'appointment__doctor__user',
            'appointment__patient',
            'appointment__patient__user'
        ).prefetch_related(
            'participants'
        )

        valid_rooms = []
        for room in chat_rooms:
            appt = room.appointment
            if appt.appointment_date == today:
                appt_datetime = timezone.make_aware(datetime.combine(appt.appointment_date, appt.appointment_time))
                if appt_datetime > now:
                    valid_rooms.append(room)
            else:
                valid_rooms.append(room)

        serializer = ChatRoomListSerializer(valid_rooms, many=True, context={'request': request})
        return Response(serializer.data)
    @swagger_auto_schema(
        operation_summary="List support groups",
        operation_description="Fetch all active disease support group chat rooms available for patients.",
        responses={
            200: openapi.Response(
                description="List of available support groups",
                schema=GroupRoomSerializer
            ),
        },
        tags=["Chat"]
    )
    def list_groups(self, request):
        if request.user.role != 'patient':
            return Response({"error": "Only patients can access this endpoint"}, status=status.HTTP_403_FORBIDDEN)

        groups = ChatRoom.objects.filter(
            room_type='group', 
            is_active=True
        ).prefetch_related('participants')
        
        serializer = GroupRoomSerializer(groups, many=True, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Join a support group",
        operation_description="Join a specific disease support group using its ID.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['group_id'],
            properties={
                'group_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the group to join", example=1),
                'disease_name': openapi.Schema(type=openapi.TYPE_STRING, description="Optional disease name", example="Diabetes Type 2")
            }
        ),
        responses={
            201: openapi.Response(description="Joined group successfully"),
            200: openapi.Response(description="Already a member of this group"),
            400: openapi.Response(description="Invalid input"),
            403: openapi.Response(description="Forbidden (non-patient user)")
        },
        tags=["Chat"]
    )
    def join_group(self, request):
        if request.user.role != 'patient':
            return Response({"error": "Only patients can join groups"}, status=status.HTTP_403_FORBIDDEN)

        group_id = request.data.get('group_id')
        if not group_id:
            return Response({"error": "group_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        group = get_object_or_404(ChatRoom, id=group_id, room_type='group')

        if group.participants.filter(id=request.user.id).exists():
            return Response({"message": "Already a member of this group"}, status=status.HTTP_200_OK)

        group.participants.add(request.user)
        GroupMembership.objects.get_or_create(
            patient=request.user.patient_profile,
            group_room=group,
            defaults={'is_diagnosed': True}
        )
        return Response({"message": "Successfully joined the group"}, status=status.HTTP_201_CREATED)

class DoctorChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List doctor's patient chats",
        operation_description="Fetch all active chat rooms between the doctor and patients for confirmed appointments.",
        responses={200: ChatRoomListSerializer},
        tags=["Chat"]
    )
    def list_patient_chats(self, request):
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can access this"}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.now().date()
        
        chat_rooms = ChatRoom.objects.filter(
            room_type='patient_doctor',
            participants=request.user,
            is_active=True,
            appointment__status='confirmed',
            appointment__appointment_date__gte=today
        ).select_related(
            'appointment',
            'appointment__doctor',
            'appointment__doctor__user',
            'appointment__patient',
            'appointment__patient__user'
        ).prefetch_related(
            'participants'
        )
        
        serializer = ChatRoomListSerializer(chat_rooms, many=True, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="List doctor's doctor chats",
        operation_description="List all active doctor-to-doctor chat rooms.",
        responses={200: ChatRoomListSerializer},
        tags=["Chat"]
    )
    def list_doctor_chats(self, request):
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can access this"}, status=status.HTTP_403_FORBIDDEN)
        
        chat_rooms = ChatRoom.objects.filter(
            room_type='doctor_doctor',
            participants=request.user,
            is_active=True
        ).prefetch_related(
            'participants'
        )
        
        serializer = ChatRoomListSerializer(chat_rooms, many=True, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Send connection request",
        operation_description="Send a connection request to another doctor.",
        request_body=DoctorConnectionSerializer,
        responses={201: DoctorConnectionSerializer, 400: "Validation error"},
        tags=["Chat"]
    )
    def send_connection_request(self, request):
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can send connection requests"}, status=status.HTTP_403_FORBIDDEN)

        serializer = DoctorConnectionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="List pending requests",
        operation_description="Fetch all pending doctor-to-doctor connection requests.",
        responses={200: DoctorConnectionListSerializer},
        tags=["Chat"]
    )
    def list_pending_requests(self, request):
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can access this"}, status=status.HTTP_403_FORBIDDEN)

        requests_qs = DoctorConnection.objects.filter(
            to_doctor=request.user.doctor_profile,
            status='pending'
        ).select_related(
            'from_doctor',
            'from_doctor__user',
            'to_doctor',
            'to_doctor__user'
        )
        
        serializer = DoctorConnectionListSerializer(requests_qs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Accept connection request",
        operation_description="Accept a pending doctor connection request and start a chat.",
        responses={200: DoctorConnectionSerializer, 404: "Not found"},
        tags=["Chat"]
    )
    def accept_connection(self, request, pk):
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can accept connections"}, status=status.HTTP_403_FORBIDDEN)

        connection = get_object_or_404(
            DoctorConnection, 
            pk=pk,
            to_doctor=request.user.doctor_profile, 
            status='pending'
        )
        
        connection.status = 'accepted'
        chat_room = ChatRoom.objects.create(room_type='doctor_doctor', is_active=True)
        chat_room.participants.add(connection.from_doctor.user, connection.to_doctor.user)
        connection.chat_room = chat_room
        connection.save()
        
        return Response(DoctorConnectionSerializer(connection).data)

    @swagger_auto_schema(
        operation_summary="Reject connection request",
        operation_description="Reject a pending connection request from another doctor.",
        responses={200: "Request rejected"},
        tags=["Chat"]
    )
    def reject_connection(self, request, pk):
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can reject connections"}, status=status.HTTP_403_FORBIDDEN)

        connection = get_object_or_404(
            DoctorConnection,
            pk=pk, 
            to_doctor=request.user.doctor_profile, 
            status='pending'
        )
        
        connection.status = 'rejected'
        connection.save()
        
        return Response({"message": "Connection request rejected"})

    @swagger_auto_schema(
        operation_summary="Search for doctors",
        operation_description="Search for other doctors by name or specialization.",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Search term (name/specialization)", type=openapi.TYPE_STRING)
        ],
        responses={200: DoctorMinimalSerializer},
        tags=["Chat"]
    )
    def search_doctors(self, request):
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can search"}, status=status.HTTP_403_FORBIDDEN)

        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Query parameter 'q' is required"}, status=status.HTTP_400_BAD_REQUEST)

        doctors = Doctor.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(specialization__icontains=query)
        ).exclude(user=request.user).select_related('user')[:20]
        
        serializer = DoctorMinimalSerializer(doctors, many=True)
        return Response(serializer.data)
    
class ChatRoomViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get chat room details",
        operation_description="Fetch chat room details with recent messages.",
        responses={200: ChatRoomDetailSerializer, 404: "Not found"},
        tags=["Chat"]
    )
    def retrieve(self, request, pk):
        chat_room = get_object_or_404(
            ChatRoom.objects.prefetch_related(
                'participants',
                Prefetch('messages', queryset=Message.objects.order_by('-timestamp')[:50])
            ).select_related('appointment'),
            pk=pk
        )
        
        if not chat_room.participants.filter(id=request.user.id).exists():
            return Response({"error": "Not a participant"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ChatRoomDetailSerializer(chat_room, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Send a message",
        operation_description="Send a new message in a chat room.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content'],
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Message text", example="Hello, Doctor!")
            }
        ),
        responses={201: MessageSerializer, 403: "Forbidden"},
        tags=["Chat"]
    )
    def send_message(self, request, pk):
        chat_room = get_object_or_404(ChatRoom, pk=pk)
        
        if not chat_room.participants.filter(id=request.user.id).exists():
            return Response({"error": "You are not a participant"}, status=status.HTTP_403_FORBIDDEN)
        
        if not chat_room.is_active:
            return Response({"error": "Chat inactive"}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({"error": "Message content is required"}, status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(
            room=chat_room, 
            sender=request.user, 
            content=content
        )
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Mark messages as read",
        operation_description="Marks all unread messages in a chat room as read.",
        responses={200: "Messages marked as read"},
        tags=["Chat"]
    )
    def mark_as_read(self, request, pk):
        chat_room = get_object_or_404(ChatRoom, pk=pk)
        
        if not chat_room.participants.filter(id=request.user.id).exists():
            return Response({"error": "Not a participant"}, status=status.HTTP_403_FORBIDDEN)
        
        Message.objects.filter(
            room=chat_room, 
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        return Response({"message": "Messages marked as read"})