from rest_framework import serializers
from .models import Message, UserOnlineStatus, Conversation
from Authapi.models import CustomUser, Doctor, Patient


class UserBasicSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()
    user_type = serializers.CharField(source='role', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'user_type', 'is_online', 'last_seen']
    
    def get_full_name(self, obj):
        try:
            if obj.role == 'doctor':
                return f"Dr. {obj.doctor_profile.get_full_name()}"
            elif obj.role == 'patient':
                return obj.patient_profile.get_full_name()
        except:
            return obj.username
    
    def get_is_online(self, obj):
        try:
            return obj.online_status.is_online
        except UserOnlineStatus.DoesNotExist:
            return False
    
    def get_last_seen(self, obj):
        try:
            return obj.online_status.last_seen
        except UserOnlineStatus.DoesNotExist:
            return None


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    receiver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'receiver',
            'sender_name',
            'receiver_name',
            'content',
            'timestamp',
            'is_read',
            'read_at',
            'attachment'
        ]
        read_only_fields = ['sender', 'timestamp', 'is_read', 'read_at']
    
    def get_sender_name(self, obj):
        try:
            if obj.sender.role == 'doctor':
                return f"Dr. {obj.sender.doctor_profile.get_full_name()}"
            elif obj.sender.role == 'patient':
                return obj.sender.patient_profile.get_full_name()
        except:
            return obj.sender.username
    
    def get_receiver_name(self, obj):
        try:
            if obj.receiver.role == 'doctor':
                return f"Dr. {obj.receiver.doctor_profile.get_full_name()}"
            elif obj.receiver.role == 'patient':
                return obj.receiver.patient_profile.get_full_name()
        except:
            return obj.receiver.username


class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message_content = serializers.CharField(source='last_message.content', read_only=True)
    last_message_timestamp = serializers.DateTimeField(source='last_message.timestamp', read_only=True)
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id',
            'other_user',
            'last_message_content',
            'last_message_timestamp',
            'unread_count',
            'updated_at'
        ]
    
    def get_other_user(self, obj):
        request_user = self.context.get('request').user
        other_user = obj.participant2 if obj.participant1 == request_user else obj.participant1
        return UserBasicSerializer(other_user).data
    
    def get_unread_count(self, obj):
        request_user = self.context.get('request').user
        return Message.objects.filter(
            sender=obj.participant2 if obj.participant1 == request_user else obj.participant1,
            receiver=request_user,
            is_read=False
        ).count()