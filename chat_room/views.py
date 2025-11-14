from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.utils import timezone
from datetime import datetime
from .throttles import (
    ChatListThrottle, ChatMessageThrottle, ChatGroupThrottle,
    ChatConnectionThrottle, ChatSearchThrottle, ChatReadThrottle
)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ChatRoom, Message, DoctorConnection
from .serializers import (
    ChatRoomListSerializer, ChatRoomDetailSerializer,
    MessageSerializer, DoctorConnectionSerializer,
    DoctorConnectionListSerializer,
    DoctorMinimalSerializer
)
from Authapi.models import Doctor
from django.shortcuts import render


class PatientChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatListThrottle]
    
    @swagger_auto_schema(
        operation_summary="List patient's doctor chats",
        operation_description="Returns all active doctor chat rooms for confirmed appointments.",
        responses={200: ChatRoomListSerializer},
        tags=["Chat"]
    )
    def list(self, request): 
            if request.user.role != 'patient':
                return Response(
                    {"error": "Only patients can access this endpoint"}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            print(f"🔍 Fetching chats for patient: {request.user.id}")
            
            chat_rooms = ChatRoom.objects.filter(
                room_type='patient_doctor',
                participants=request.user,
                is_active=True,
                appointment__status='confirmed',
            ).select_related(
                'appointment__doctor__user',
                'appointment__patient__user'
            ).prefetch_related('participants')
            
            print(f"📊 Found {chat_rooms.count()} chat rooms")
            for room in chat_rooms:
                print(f"  - Room {room.id}: Appointment {room.appointment_id if room.appointment else 'None'}")
            
            serializer = ChatRoomListSerializer(
                chat_rooms, 
                many=True, 
                context={'request': request}
            )
            return Response(serializer.data)
    

class DoctorChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatListThrottle]
    
    @swagger_auto_schema(
        operation_summary="List doctor's patient chats",
        operation_description="Fetch all active patient chats for confirmed appointments.",
        responses={200: ChatRoomListSerializer},
        tags=["Chat"]
    )
    def list_patients(self, request): 
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can access this"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        chat_rooms = ChatRoom.objects.filter(
            room_type='patient_doctor',
            participants=request.user,
            is_active=True,
            appointment__status='confirmed',
        ).select_related(
            'appointment__doctor__user',
            'appointment__patient__user'
        ).prefetch_related('participants')
        
        serializer = ChatRoomListSerializer(
            chat_rooms, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="List doctor's doctor chats",
        operation_description="List all active doctor-to-doctor chat rooms.",
        responses={200: ChatRoomListSerializer},
        tags=["Chat"]
    )
    def list_doctors(self, request):
        if request.user.role != 'doctor':
            return Response(
                {"error": "Only doctors can access this"}, 
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
    @swagger_auto_schema(
        operation_summary="Send connection request",
        operation_description="Send a connection request to another doctor.",
        request_body=DoctorConnectionSerializer,
        responses={201: DoctorConnectionSerializer, 400: "Validation error"},
        tags=["Chat"]
    )

    @action(detail=False, methods=['post'], throttle_classes=[ChatConnectionThrottle])
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
    @action(detail=False, methods=['get'], throttle_classes=[ChatSearchThrottle])
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
        responses={200: ChatRoomDetailSerializer},
        tags=["Chat"]
    )
    def retrieve(self, request, pk):
        chat_room = get_object_or_404(
            ChatRoom.objects.prefetch_related('participants')
            .select_related('appointment'),
            pk=pk
        )
        
        if not chat_room.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "Not a participant"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ChatRoomDetailSerializer(
            chat_room, 
            context={'request': request}
        )
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Send a message",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content'],
            properties={
                'content': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="Message text"
                )
            }
        ),
        responses={201: MessageSerializer},
        tags=["Chat"]
    )
    @action(detail=True, methods=['post'], throttle_classes=[ChatMessageThrottle])
    def send_message(self, request, pk):
        chat_room = get_object_or_404(ChatRoom, pk=pk)
        
        if not chat_room.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "You are not a participant"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not chat_room.is_active:
            return Response(
                {"error": "Chat is inactive"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        content = request.data.get('content', '').strip()
        if not content:
            return Response(
                {"error": "Message content is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        message = Message.objects.create(
            room=chat_room, 
            sender=request.user, 
            content=content
        )
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Mark messages as read",
        responses={200: "Messages marked as read"},
        tags=["Chat"]
    )
    @action(detail=True, methods=['post'], throttle_classes=[ChatReadThrottle])
    def mark_as_read(self, request, pk):
        chat_room = get_object_or_404(ChatRoom, pk=pk)
        
        if not chat_room.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "Not a participant"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        Message.objects.filter(
            room=chat_room, 
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        return Response({"message": "Messages marked as read"})

def test_chat_doctor(request, room_id):
    return render(request, 'chat_room/chat_doctor.html', {'room_id': room_id})

def test_chat_patient(request, room_id):
    return render(request, 'chat_room/chat_patient.html', {'room_id': room_id})

