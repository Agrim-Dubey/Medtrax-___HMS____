from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from chat_room.models import ChatRoom
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Appointment)
def manage_patient_doctor_chat(sender, instance, created, **kwargs):
    logger.info(f"🔔 Signal fired: Appointment {instance.id}, Status: '{instance.status}', Created: {created}")
    
    if instance.status == 'confirmed':
        logger.info(f"✅ Status is 'confirmed', creating/checking chat room...")
        
        room, is_created = ChatRoom.objects.get_or_create(
            appointment=instance,
            defaults={
                'room_type': 'patient_doctor',
                'is_active': True,
            }
        )

        if is_created:
            room.participants.add(instance.patient.user, instance.doctor.user)
            logger.info(f" NEW chat room created: ID={room.id}, Participants added")
        else:
            if not room.is_active:
                room.is_active = True
                room.save()
                logger.info(f" Existing chat room reactivated: ID={room.id}")
            else:
                logger.info(f" Chat room already exists and is active: ID={room.id}")

        return
        
    elif instance.status == 'cancelled':
        logger.info(f" Status is 'cancelled', deactivating chat room...")
        try:
            room = ChatRoom.objects.get(appointment=instance)
            room.is_active = False
            room.save()
            logger.info(f" Chat room deactivated: ID={room.id}")
        except ChatRoom.DoesNotExist:
            logger.warning(f" No chat room found for cancelled appointment {instance.id}")
    else:
        logger.info(f"Status is '{instance.status}', no action taken")