from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, DoctorConnection, GroupMembership
from Authapi.models import Doctor, Patient

User = get_user_model()
class UserBasicSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'full_name']
    
    def get_full_name(self, obj):
        try:
            if obj.role == 'doctor':
                return f"Dr. {obj.doctor_profile.get_full_name()}"
            elif obj.role == 'patient':
                return obj.patient_profile.get_full_name()
        except:
            return obj.username
        return obj.username


class DoctorMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id')
    
    class Meta:
        model = Doctor
        fields = ['id', 'user_id', 'full_name', 'specialization']
    
    def get_full_name(self, obj):
        return f"Dr. {obj.get_full_name()}"


class PatientMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id')
    
    class Meta:
        model = Patient
        fields = ['id', 'user_id', 'full_name', 'city']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
class MessageSerializer(serializers.ModelSerializer):
    sender = UserBasicSerializer(read_only=True)
    sender_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'room', 'sender', 'sender_id', 
            'content', 'timestamp', 'is_read'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def create(self, validated_data):
        sender_id = validated_data.pop('sender_id')
        sender = User.objects.get(id=sender_id)
        validated_data['sender'] = sender
        return super().create(validated_data)


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['room', 'content']

class ChatRoomListSerializer(serializers.ModelSerializer):
    participants = UserBasicSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_type', 'name', 'is_active',
            'participants', 'last_message', 'unread_count',
            'other_participant', 'created_at', 'updated_at'
        ]
    
    def get_last_message(self, obj):
        try:
            messages = getattr(obj, 'messages', None)
            if messages is not None:
                if hasattr(messages, 'all'):
                    last_msg = messages.all()[:1]
                    if last_msg:
                        last_msg = last_msg[0]
                    else:
                        return None
                else:
                    return None
            else:
                last_msg = obj.messages.order_by('-timestamp').first()
            
            if last_msg:
                return {
                    'content': last_msg.content[:100], 
                    'sender': last_msg.sender.username,
                    'timestamp': last_msg.timestamp
                }
        except Exception as e:
            print(f"Error fetching last message: {e}")
            return None
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(
                is_read=False
            ).exclude(
                sender=request.user
            ).count()
        return 0
    
    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user and obj.room_type in ['patient_doctor', 'doctor_doctor']:
            other = obj.participants.exclude(id=request.user.id).first()
            if other:
                return UserBasicSerializer(other).data
        return None


class ChatRoomDetailSerializer(serializers.ModelSerializer):
    participants = UserBasicSerializer(many=True, read_only=True)
    messages = serializers.SerializerMethodField()
    appointment_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'room_type', 'name', 'is_active',
            'participants', 'messages', 'appointment_info',
            'disease_name', 'created_at', 'updated_at'
        ]
    
    def get_messages(self, obj):
        messages = obj.messages.order_by('-timestamp')[:50]
        return MessageSerializer(messages, many=True).data
    
    def get_appointment_info(self, obj):
        if obj.appointment:
            return {
                'id': obj.appointment.id,
                'date': obj.appointment.appointment_date,
                'time': obj.appointment.appointment_time,
                'status': obj.appointment.status
            }
        return None
    
class DoctorConnectionSerializer(serializers.ModelSerializer):
    from_doctor = DoctorMinimalSerializer(read_only=True)
    to_doctor = DoctorMinimalSerializer(read_only=True)
    to_doctor_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = DoctorConnection
        fields = [
            'id', 'from_doctor', 'to_doctor', 'to_doctor_id',
            'status', 'chat_room', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'chat_room', 'created_at', 'updated_at']
    
    def create(self, validated_data):

        to_doctor_id = validated_data.pop('to_doctor_id')
        to_doctor = Doctor.objects.get(id=to_doctor_id)
        from_doctor = self.context['request'].user.doctor_profile

        existing = DoctorConnection.objects.filter(
            from_doctor=from_doctor,
            to_doctor=to_doctor
        ).first()
        
        if existing:
            raise serializers.ValidationError("Connection request already exists")
        
        return DoctorConnection.objects.create(
            from_doctor=from_doctor,
            to_doctor=to_doctor,
            status='pending'
        )


class DoctorConnectionListSerializer(serializers.ModelSerializer):

    from_doctor = DoctorMinimalSerializer(read_only=True)
    to_doctor = DoctorMinimalSerializer(read_only=True)
    
    class Meta:
        model = DoctorConnection
        fields = ['id', 'from_doctor', 'to_doctor', 'status', 'created_at']
