from django.utils import timezone
from datetime import timedelta
from .models import ChatRoom

def disable_expired_chats():
    now = timezone.now()
    
    expired_rooms = ChatRoom.objects.filter(
        room_type='patient_doctor',
        is_active=True,
        appointment__isnull=False
    )
    
    for room in expired_rooms:
        appt = room.appointment
        appt_datetime = timezone.make_aware(
            timezone.datetime.combine(appt.appointment_date, appt.appointment_time)
        )
        
        if appt_datetime < now:
            room.is_active = False
            room.save()

def delete_old_chats():
    now = timezone.now()
    cutoff = now - timedelta(days=1)
    
    old_rooms = ChatRoom.objects.filter(
        room_type='patient_doctor',
        is_active=False,
        appointment__isnull=False
    )
    
    for room in old_rooms:
        appt = room.appointment
        appt_datetime = timezone.make_aware(
            timezone.datetime.combine(appt.appointment_date, appt.appointment_time)
        )
        
        if appt_datetime < cutoff:
            room.delete()