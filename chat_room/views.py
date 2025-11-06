from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Message 
from Authapi.models import CustomUser, Doctor, Patient
from .serializers import (
    UserBasicSerializer,
    MessageSerializer,
    ConversationSerializer
)
from django.utils import timezone
from .pagination import ChatMessagePagination


class DoctorListView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        doctors = CustomUser.objects.filter(role='doctor', is_active=True)
        serializer = UserBasicSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientListView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        patients = CustomUser.objects.filter(role='patient', is_active=True)
        serializer = UserBasicSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConversationListView(generics.ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        ).select_related('participant1', 'participant2', 'last_message')
    
    def get_serializer_context(self):
        return {'request': self.request}


class ChatHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    pagination_class = ChatMessagePagination
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        current_user = self.request.user
        
        try:
            other_user = CustomUser.objects.get(id=user_id)

            Message.objects.filter(
                sender=other_user,
                receiver=current_user,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())

            return Message.objects.filter(
                Q(sender=current_user, receiver=other_user) |
                Q(sender=other_user, receiver=current_user)
            ).select_related('sender', 'receiver').order_by('-timestamp')  # Latest first for pagination
            
        except CustomUser.DoesNotExist:
            return Message.objects.none()


class UnreadMessagesCountView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)


class UnreadMessagesPerConversationView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from django.db.models import Count
        
        unread_by_sender = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).values('sender').annotate(count=Count('id'))
        
        return Response({
            str(item['sender']): item['count'] 
            for item in unread_by_sender
        }, status=status.HTTP_200_OK)


class DeleteMessageView(APIView):

    permission_classes = [IsAuthenticated]
    
    def delete(self, request, message_id):
        try:
            message = Message.objects.get(id=message_id, sender=request.user)
            message.delete()
            return Response(
                {"message": "Message deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
        except Message.DoesNotExist:
            return Response(
                {"error": "Message not found or you don't have permission to delete it"},
                status=status.HTTP_404_NOT_FOUND
            )


class SearchMessagesView(generics.ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    pagination_class = ChatMessagePagination
    
    def get_queryset(self):
        user = self.request.user
        query = self.request.query_params.get('q', '')
        
        if not query:
            return Message.objects.none()
        
        return Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).filter(
            content__icontains=query
        ).select_related('sender', 'receiver').order_by('-timestamp')