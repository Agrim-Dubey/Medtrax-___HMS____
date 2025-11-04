from django.utils import timezone
from .models import Appointment
from datetime import datetime, timedelta

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



def get_available_slots(doctor, date):
    start_hour = 9
    end_hour = 17
    all_slots = []
    current_time = datetime.strptime(f"{start_hour}:00", "%H:%M")
    end_time = datetime.strptime(f"{end_hour}:00", "%H:%M")
    
    while current_time < end_time:
        all_slots.append(current_time.strftime("%H:%M")) 
        current_time += timedelta(minutes=30)

    booked_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=date,
        status__in=['pending', 'confirmed']
    ).values_list('appointment_time', flat=True)
    
    booked_slots = [time.strftime("%H:%M") for time in booked_appointments]  # Changed from %H:%M:%S
    available_slots = [slot for slot in all_slots if slot not in booked_slots]
    
    return available_slots