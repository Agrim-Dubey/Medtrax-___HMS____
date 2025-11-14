from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from chat_room.models import ChatRoom


@receiver(post_save, sender=Appointment)
def create_chat_room_for_appointment(sender, instance, created, **kwargs):
    if instance.status != 'confirmed':
        return

    try:
        instance.chat_room 
        return 
    except ChatRoom.DoesNotExist:
        pass  

    chat_room = ChatRoom.objects.create(
        room_type='patient_doctor',
        is_active=True,
        appointment=instance
    )

    chat_room.participants.add(
        instance.patient.user,
        instance.doctor.user
    )

    print(f"Chat room {chat_room.id} created for appointment {instance.id}")
