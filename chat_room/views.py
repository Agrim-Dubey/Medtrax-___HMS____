from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

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
    """
    ViewSet for patient chat operations including doctor chats and support groups
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="List patient's doctor chats",
        description="Get all active chat rooms between the patient and their doctors for confirmed future appointments",
        responses={
            200: ChatRoomListSerializer(many=True),
            403: inline_serializer(
                name='PatientChatError',
                fields={'error': serializers.CharField()}
            )
        },
        tags=['Patient Chat']
    )
    def list_doctor_chats(self, request):
        """Get list of chat rooms with doctors for confirmed appointments"""
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
    
    @extend_schema(
        summary="List available support groups",
        description="Get all active disease support groups that patients can join",
        responses={
            200: GroupRoomSerializer(many=True),
            403: inline_serializer(
                name='PatientGroupError',
                fields={'error': serializers.CharField()}
            )
        },
        tags=['Patient Chat']
    )
    def list_groups(self, request):
        """Get list of available disease support groups"""
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
    
    @extend_schema(
        summary="Join a support group",
        description="Join a disease support group by providing the group ID",
        request=inline_serializer(
            name='JoinGroupRequest',
            fields={
                'group_id': serializers.IntegerField(help_text='ID of the group to join'),
                'disease_name': serializers.CharField(required=False, help_text='Optional disease name')
            }
        ),
        examples=[
            OpenApiExample(
                'Join Diabetes Group',
                value={'group_id': 1, 'disease_name': 'Diabetes Type 2'},
                request_only=True
            )
        ],
        responses={
            201: inline_serializer(
                name='JoinGroupSuccess',
                fields={'message': serializers.CharField()}
            ),
            200: inline_serializer(
                name='AlreadyMember',
                fields={'message': serializers.CharField()}
            ),
            400: inline_serializer(
                name='JoinGroupBadRequest',
                fields={'error': serializers.CharField()}
            ),
            403: inline_serializer(
                name='JoinGroupForbidden',
                fields={'error': serializers.CharField()}
            ),
        },
        tags=['Patient Chat']
    )
    def join_group(self, request):
        """Join a disease support group"""
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
    """
    ViewSet for doctor chat operations including patient chats, doctor connections, and search
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="List doctor's patient chats",
        description="Get all active chat rooms between the doctor and their patients for confirmed appointments",
        responses={
            200: ChatRoomListSerializer(many=True),
            403: inline_serializer(
                name='DoctorAccessError',
                fields={'error': serializers.CharField()}
            )
        },
        tags=['Doctor Chat']
    )
    def list_patient_chats(self, request):
        """Get list of chat rooms with patients"""
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
    
    @extend_schema(
        summary="List doctor's doctor chats",
        description="Get all active chat rooms between the doctor and other connected doctors",
        responses={
            200: ChatRoomListSerializer(many=True),
            403: inline_serializer(
                name='DoctorDoctorAccessError',
                fields={'error': serializers.CharField()}
            )
        },
        tags=['Doctor Chat']
    )
    def list_doctor_chats(self, request):
        """Get list of chat rooms with other doctors"""
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
    
    @extend_schema(
        summary="Send connection request to another doctor",
        description="Send a connection request to another doctor to initiate doctor-to-doctor chat",
        request=DoctorConnectionSerializer,
        examples=[
            OpenApiExample(
                'Connection Request',
                value={'to_doctor_id': 5},
                request_only=True
            )
        ],
        responses={
            201: DoctorConnectionSerializer,
            400: inline_serializer(
                name='ConnectionRequestError',
                fields={'error': serializers.CharField()}
            ),
            403: inline_serializer(
                name='ConnectionForbidden',
                fields={'error': serializers.CharField()}
            )
        },
        tags=['Doctor Connections']
    )
    def send_connection_request(self, request):
        """Send connection request to another doctor"""
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
    
    @extend_schema(
        summary="List pending connection requests",
        description="Get all pending connection requests received by the doctor",
        responses={
            200: DoctorConnectionListSerializer(many=True),
            403: inline_serializer(
                name='PendingRequestsError',
                fields={'error': serializers.CharField()}
            )
        },
        tags=['Doctor Connections']
    )
    def list_pending_requests(self, request):
        """Get pending connection requests"""
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
    
    @extend_schema(
        summary="Accept connection request",
        description="Accept a pending connection request and create a chat room between the two doctors",
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Connection request ID'
            )
        ],
        responses={
            200: DoctorConnectionSerializer,
            403: inline_serializer(
                name='AcceptConnectionError',
                fields={'error': serializers.CharField()}
            ),
            404: inline_serializer(
                name='ConnectionNotFound',
                fields={'detail': serializers.CharField()}
            )
        },
        tags=['Doctor Connections']
    )
    def accept_connection(self, request, pk):
        """Accept a connection request"""
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
    
    @extend_schema(
        summary="Reject connection request",
        description="Reject a pending connection request from another doctor",
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Connection request ID'
            )
        ],
        responses={
            200: inline_serializer(
                name='RejectConnectionSuccess',
                fields={'message': serializers.CharField()}
            ),
            403: inline_serializer(
                name='RejectConnectionError',
                fields={'error': serializers.CharField()}
            ),
            404: inline_serializer(
                name='ConnectionNotFound',
                fields={'detail': serializers.CharField()}
            )
        },
        tags=['Doctor Connections']
    )
    def reject_connection(self, request, pk):
        """Reject a connection request"""
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
    
    @extend_schema(
        summary="Search for doctors",
        description="Search for other doctors by name or specialization to send connection requests",
        parameters=[
            OpenApiParameter(
                name='q',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search query (searches in first name, last name, and specialization)',
                required=True
            )
        ],
        examples=[
            OpenApiExample(
                'Search by name',
                value='John',
            ),
            OpenApiExample(
                'Search by specialization',
                value='Cardiology',
            )
        ],
        responses={
            200: DoctorMinimalSerializer(many=True),
            400: inline_serializer(
                name='SearchError',
                fields={'error': serializers.CharField()}
            ),
            403: inline_serializer(
                name='SearchForbidden',
                fields={'error': serializers.CharField()}
            )
        },
        tags=['Doctor Connections']
    )
    def search_doctors(self, request):
        """Search for doctors by name or specialization"""
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
    """
    ViewSet for chat room operations including retrieving room details, sending messages, and marking as read
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get chat room details",
        description="Retrieve detailed information about a specific chat room including recent messages",
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Chat room ID'
            )
        ],
        responses={
            200: ChatRoomDetailSerializer,
            403: inline_serializer(
                name='ChatRoomAccessError',
                fields={'error': serializers.CharField()}
            ),
            404: inline_serializer(
                name='ChatRoomNotFound',
                fields={'detail': serializers.CharField()}
            )
        },
        tags=['Chat Room']
    )
    def retrieve(self, request, pk):
        """Get chat room details with messages"""
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
    
    @extend_schema(
        summary="Send a message",
        description="Send a message in a chat room",
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Chat room ID'
            )
        ],
        request=inline_serializer(
            name='SendMessageRequest',
            fields={
                'content': serializers.CharField(help_text='Message content')
            }
        ),
        examples=[
            OpenApiExample(
                'Send Message',
                value={'content': 'Hello, how are you feeling today?'},
                request_only=True
            )
        ],
        responses={
            201: MessageSerializer,
            403: inline_serializer(
                name='SendMessageError',
                fields={'error': serializers.CharField()}
            ),
            404: inline_serializer(
                name='RoomNotFound',
                fields={'detail': serializers.CharField()}
            )
        },
        tags=['Chat Room']
    )
    def send_message(self, request, pk):
        """Send a message in the chat room"""
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
    
    @extend_schema(
        summary="Mark messages as read",
        description="Mark all unread messages in a chat room as read (excludes messages sent by the current user)",
        parameters=[
            OpenApiParameter(
                name='pk',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Chat room ID'
            )
        ],
        responses={
            200: inline_serializer(
                name='MarkReadSuccess',
                fields={'message': serializers.CharField()}
            ),
            403: inline_serializer(
                name='MarkReadError',
                fields={'error': serializers.CharField()}
            ),
            404: inline_serializer(
                name='RoomNotFound',
                fields={'detail': serializers.CharField()}
            )
        },
        tags=['Chat Room']
    )
    def mark_as_read(self, request, pk):
        """Mark all messages in room as read"""
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