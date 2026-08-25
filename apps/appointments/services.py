"""
Services for appointment management.
Handles business logic for booking, accepting, and rejecting appointments.
"""
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from authentication.models import Doctor, Patient
from .models import Appointment
from .tasks import send_immediate_appointment_notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils import get_doctor_queue_info

def broadcast_queue_update(doctor: Doctor):
    channel_layer = get_channel_layer()
    data = get_doctor_queue_info(doctor)
    async_to_sync(channel_layer.group_send)(
        f"doctor_{doctor.id}_queue",
        {"type": "send_queue_update", "data": data}
    )

@transaction.atomic
def create_appointment_request(*, patient: Patient, data: dict) -> Appointment:
    # Normally we'd extract the serializer.save() logic here if it was complex.
    # We assume data is already validated by the serializer.
    from .serializers import AppointmentRequestSerializer
    serializer = AppointmentRequestSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    
    appointment = serializer.save(patient=patient, status='pending')
    send_immediate_appointment_notification.delay(appointment.id, 'created')
    return appointment

@transaction.atomic
def accept_appointment_request(*, appointment_id: int, doctor: Doctor) -> Appointment:
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=doctor,
        status='pending'
    )
    
    appointment.status = 'confirmed'
    appointment.save()
    
    broadcast_queue_update(doctor)
    send_immediate_appointment_notification.delay(appointment.id, 'confirmed')
    return appointment

@transaction.atomic
def reject_appointment_request(*, appointment_id: int, doctor: Doctor) -> Appointment:
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=doctor,
        status='pending'
    )
    
    appointment.status = 'cancelled'
    appointment.save()
    
    broadcast_queue_update(doctor)
    send_immediate_appointment_notification.delay(appointment.id, 'cancelled')
    return appointment
