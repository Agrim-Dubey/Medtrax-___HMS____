from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Message, UserOnlineStatus, Conversation
from Authapi.models import CustomUser, Doctor, Patient
from .serializers import (
    UserBasicSerializer,
    MessageSerializer,
    ConversationSerializer
)
from django.utils import timezone


class DoctorListView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        doctors = CustomUser.objects.filter(role='doctor')
        serializer = UserBasicSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientListView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        patients = CustomUser.objects.filter(role='patient')
        serializer = UserBasicSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConversationListView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        conversations = Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        )
        serializer = ConversationSerializer(conversations, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatHistoryView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            other_user = CustomUser.objects.get(id=user_id)
            current_user = request.user

            messages = Message.objects.filter(
                Q(sender=current_user, receiver=other_user) |
                Q(sender=other_user, receiver=current_user)
            ).order_by('timestamp')
            
            Message.objects.filter(
                sender=other_user,
                receiver=current_user,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
            
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class UnreadMessagesCountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)