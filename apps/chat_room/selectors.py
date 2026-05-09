from django.db.models import QuerySet, Q
from Authapi.models import CustomUser, Doctor
from .models import ChatRoom, DoctorConnection, Message

def get_user_chat_rooms(*, user: CustomUser, room_type: str) -> QuerySet[ChatRoom]:
    """
    Fetches active chat rooms for a user based on room type.
    For 'patient_doctor', it also ensures a confirmed appointment exists.
    """
    qs = ChatRoom.objects.filter(
        room_type=room_type,
        participants=user,
        is_active=True
    ).prefetch_related("participants")
    
    if room_type == "patient_doctor":
        qs = qs.filter(
            appointment__isnull=False,
            appointment__status="confirmed"
        ).select_related('appointment')
        
    return qs

def get_pending_doctor_connections(*, doctor: Doctor) -> QuerySet[DoctorConnection]:
    return DoctorConnection.objects.filter(
        to_doctor=doctor,
        status="pending"
    ).select_related("from_doctor__user", "to_doctor__user")

def search_doctors_for_chat(*, query: str, current_user: CustomUser, limit: int = 20) -> QuerySet[Doctor]:
    return Doctor.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(specialization__icontains=query)
    ).exclude(user=current_user).select_related("user")[:limit]

def get_chat_room_detail(*, room_id: int, user: CustomUser) -> ChatRoom:
    from django.core.exceptions import PermissionDenied
    try:
        chat_room = ChatRoom.objects.prefetch_related(
            "participants"
        ).select_related("appointment").get(pk=room_id)
    except ChatRoom.DoesNotExist:
        return None
        
    if not chat_room.participants.filter(id=user.id).exists():
        raise PermissionDenied("Not a participant")
        
    if not chat_room.is_active:
        raise PermissionDenied("Chat inactive")
        
    return chat_room
