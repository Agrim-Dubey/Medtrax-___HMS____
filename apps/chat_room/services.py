from django.db import transaction
from django.shortcuts import get_object_or_404
from Authapi.models import CustomUser, Doctor
from .models import ChatRoom, DoctorConnection, Message

@transaction.atomic
def accept_doctor_connection(*, connection_id: int, to_doctor: Doctor) -> DoctorConnection:
    connection = get_object_or_404(
        DoctorConnection,
        pk=connection_id,
        to_doctor=to_doctor,
        status="pending"
    )

    connection.status = "accepted"

    chat_room = ChatRoom.objects.create(
        room_type="doctor_doctor",
        is_active=True
    )
    chat_room.participants.add(
        connection.from_doctor.user,
        connection.to_doctor.user
    )

    connection.chat_room = chat_room
    connection.save()
    return connection

@transaction.atomic
def reject_doctor_connection(*, connection_id: int, to_doctor: Doctor) -> DoctorConnection:
    connection = get_object_or_404(
        DoctorConnection,
        pk=connection_id,
        to_doctor=to_doctor,
        status="pending"
    )

    connection.status = "rejected"
    connection.save()
    return connection

@transaction.atomic
def send_chat_message(*, room_id: int, sender: CustomUser, content: str) -> Message:
    from django.core.exceptions import PermissionDenied
    chat_room = get_object_or_404(ChatRoom, pk=room_id)

    if not chat_room.participants.filter(id=sender.id).exists():
        raise PermissionDenied("Not a participant")

    if not chat_room.is_active:
        raise PermissionDenied("Chat inactive")

    message = Message.objects.create(
        room=chat_room,
        sender=sender,
        content=content.strip()
    )
    return message

@transaction.atomic
def mark_chat_messages_as_read(*, room_id: int, user: CustomUser):
    from django.core.exceptions import PermissionDenied
    chat_room = get_object_or_404(ChatRoom, pk=room_id)

    if not chat_room.participants.filter(id=user.id).exists():
        raise PermissionDenied("Not a participant")

    Message.objects.filter(
        room=chat_room,
        is_read=False
    ).exclude(sender=user).update(is_read=True)
