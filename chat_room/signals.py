from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from chat_room.models import ChatRoom


@receiver(post_save, sender=Appointment)
def manage_patient_doctor_chat(sender, instance, created, **kwargs):
    if instance.status == 'confirmed':

        room, is_created = ChatRoom.objects.get_or_create(
            appointment=instance,
            defaults={
                'room_type': 'patient_doctor',
                'is_active': True,
            }
        )

        if is_created:
            room.participants.add(instance.patient.user, instance.doctor.user)

        else:

            if not room.is_active:
                room.is_active = True
                room.save()

        return
    if instance.status == 'cancelled':
        try:
            room = ChatRoom.objects.get(appointment=instance)
            room.is_active = False
            room.save()
        except ChatRoom.DoesNotExist:
            pass
