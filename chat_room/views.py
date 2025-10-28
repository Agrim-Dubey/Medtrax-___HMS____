
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q, Count, Max, Subquery, OuterRef
from Authapi.models import CustomUser
from .models import Message, UserOnlineStatus
from .serializers import UserSerializer, MessageSerializer


class UserListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        role = request.query_params.get('role')
        online_only = request.query_params.get('online_only', 'false').lower() == 'true'
        
        users = CustomUser.objects.exclude(id=request.user.id)
        
        if role:
            users = users.filter(role=role)
        
        if online_only:
            online_user_ids = UserOnlineStatus.objects.filter(is_online=True).values_list('user_id', flat=True)
            users = users.filter(id__in=online_user_ids)
        
        serializer = UserSerializer(users, many=True, context={'request_user': request.user})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        messages = Message.objects.filter(
            Q(sender=request.user, receiver_id=user_id) |
            Q(sender_id=user_id, receiver=request.user)
        ).order_by('timestamp')
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': unread_count}, status=status.HTTP_200_OK)


class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        sender_id = request.data.get('sender_id')
        
        Message.objects.filter(
            sender_id=sender_id,
            receiver=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({'status': 'messages marked as read'}, status=status.HTTP_200_OK)