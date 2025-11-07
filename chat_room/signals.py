from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from appointments.models import Appointment
from .models import ChatRoom


@receiver(post_save, sender=Appointment)
def manage_patient_doctor_chat(sender, instance, created, **kwargs):
    if instance.status == 'confirmed':
        chat_room, created = ChatRoom.objects.get_or_create(
            appointment=instance,
            defaults={
                'room_type': 'patient_doctor',
                'is_active': True,
            }
        )
        if created:
            chat_room.participants.add(instance.patient.user, instance.doctor.user)
            print(f"Chat room created for appointment #{instance.id}")
        else:
            if not chat_room.is_active:
                chat_room.is_active = True
                chat_room.save()
                print(f"🔄 Chat room reactivated for appointment #{instance.id}")

    elif instance.status == 'cancelled':
        try:
            chat_room = ChatRoom.objects.get(appointment=instance)
            chat_room.is_active = False
            chat_room.save()
            print(f" Chat room deactivated for cancelled appointment #{instance.id}")
        except ChatRoom.DoesNotExist:
            pass