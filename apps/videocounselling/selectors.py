from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from appointments.models import Appointment
from Authapi.models import CustomUser
from .models import VideoCall

def get_video_call_by_appointment(*, appointment_id: int, user: CustomUser) -> VideoCall:
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    is_doctor = hasattr(user, 'doctor_profile') and appointment.doctor == user.doctor_profile
    is_patient = hasattr(user, 'patient_profile') and appointment.patient == user.patient_profile

    if not is_doctor and not is_patient:
        raise PermissionDenied("You are not a participant of this appointment")

    try:
        return VideoCall.objects.get(appointment=appointment)
    except VideoCall.DoesNotExist:
        return None
