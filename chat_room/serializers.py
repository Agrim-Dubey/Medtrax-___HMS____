from rest_framework import serializers
from Authapi.models import CustomUser
from .models import Message, UserOnlineStatus


class UserSerializer(serializers.ModelSerializer):
    is_online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'role', 'is_online', 'last_seen', 'full_name', 'unread_count']
    
    def get_is_online(self, obj):
        try:
            return obj.online_status.is_online
        except:
            return False
    
    def get_last_seen(self, obj):
        try:
            return obj.online_status.last_seen
        except:
            return None
    
    def get_full_name(self, obj):
        if obj.role == 'doctor' and hasattr(obj, 'doctor_profile'):
            return obj.doctor_profile.get_full_name()
        elif obj.role == 'patient' and hasattr(obj, 'patient_profile'):
            return obj.patient_profile.get_full_name()
        return obj.username
    
    def get_unread_count(self, obj):
        request_user = self.context.get('request_user')
        if request_user:
            return Message.objects.filter(sender=obj, receiver=request_user, is_read=False).count()
        return 0


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'sender_username', 'receiver_username', 'content', 'timestamp', 'is_read']
        read_only_fields = ['timestamp']