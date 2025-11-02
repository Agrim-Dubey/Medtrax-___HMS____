from django.utils import timezone
from .models import Appointment


def get_doctor_queue_info(doctor):
    today = timezone.now().date()
    confirmed_count = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today,
        status='confirmed'
    ).count()
    estimated_wait = confirmed_count * 30
    return {
        'current_queue_count': confirmed_count,
        'estimated_wait_time': estimated_wait
    }