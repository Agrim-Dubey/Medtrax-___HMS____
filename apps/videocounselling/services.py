"""
Services for video counselling sessions.
Manages the lifecycle of video calls (initiate, join, end).
"""
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied, ValidationError
from appointments.models import Appointment
from Authapi.models import CustomUser
from .models import VideoCall

@transaction.atomic
def initiate_video_call(*, appointment_id: int, user: CustomUser) -> VideoCall:
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if not hasattr(user, 'doctor_profile') or appointment.doctor != user.doctor_profile:
        raise PermissionDenied("Only the doctor can initiate a call")

    if appointment.status != 'confirmed':
        raise ValidationError("Appointment must be confirmed to start a call")

    video_call, created = VideoCall.objects.get_or_create(
        appointment=appointment,
        defaults={'initiated_by': user, 'status': 'waiting'}
    )

    if not created and video_call.status == 'ended':
        video_call.status = 'waiting'
        video_call.started_at = None
        video_call.ended_at = None
        video_call.save()
        
    return video_call

@transaction.atomic
def join_video_call(*, appointment_id: int, user: CustomUser) -> VideoCall:
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
    is_patient = hasattr(user, 'patient_profile') and appointment.patient == user.patient_profile

    if not is_doctor and not is_patient:
        raise PermissionDenied("You are not a participant of this appointment")

    try:
        video_call = VideoCall.objects.get(appointment=appointment)
    except VideoCall.DoesNotExist:
        raise ValidationError("No active call for this appointment")

    if video_call.status == 'ended':
        raise ValidationError("This call has already ended")

    if video_call.status == 'waiting':
        video_call.status = 'active'
        video_call.started_at = timezone.now()
        video_call.save()
        
    return video_call

@transaction.atomic
def end_video_call(*, appointment_id: int, user: CustomUser) -> VideoCall:
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
    is_patient = hasattr(user, 'patient_profile') and appointment.patient == user.patient_profile

    if not is_doctor and not is_patient:
        raise PermissionDenied("You are not a participant of this appointment")

    try:
        video_call = VideoCall.objects.get(appointment=appointment)
    except VideoCall.DoesNotExist:
        raise ValidationError("No call found")

    video_call.status = 'ended'
    video_call.ended_at = timezone.now()
    video_call.save()
    
    return video_call
