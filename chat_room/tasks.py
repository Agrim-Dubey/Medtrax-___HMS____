from django.utils import timezone
from datetime import datetime, timedelta  
from .models import ChatRoom
from celery import shared_task  

@shared_task 
def disable_expired_chats():
    now = timezone.now()
    
    expired_rooms = ChatRoom.objects.filter(
        room_type='patient_doctor',
        is_active=True,
        appointment__isnull=False
    )
    
    disabled_count = 0
    for room in expired_rooms:
        appt = room.appointment
        appt_datetime = timezone.make_aware(
            datetime.combine(appt.appointment_date, appt.appointment_time) 
        )
        
        if appt_datetime < now:
            room.is_active = False
            room.save()
            disabled_count += 1
    
    return f"Disabled {disabled_count} expired chats"

@shared_task
def delete_old_chats():
    now = timezone.now()
    cutoff = now - timedelta(days=1)
    
    old_rooms = ChatRoom.objects.filter(
        room_type='patient_doctor',
        is_active=False,
        appointment__isnull=False
    )
    
    deleted_count = 0
    for room in old_rooms:
        appt = room.appointment
        appt_datetime = timezone.make_aware(
            datetime.combine(appt.appointment_date, appt.appointment_time) 
        )
        
        if appt_datetime < cutoff:
            room.delete()
            deleted_count += 1
    
    return f"Deleted {deleted_count} old chats"