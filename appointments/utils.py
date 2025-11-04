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
    """
    Generate available time slots for a doctor on a specific date.
    Returns slots in HH:MM format (without seconds).
    """
    start_hour = 9
    end_hour = 17
    slot_duration = 30  # minutes
    
    # Generate all possible slots
    all_slots = []
    current_time = datetime.strptime(f"{start_hour}:00", "%H:%M")
    end_time = datetime.strptime(f"{end_hour}:00", "%H:%M")
    
    while current_time < end_time:
        all_slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=slot_duration)
    
    # Get booked appointments for this doctor on this date
    booked_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=date,
        status__in=['pending', 'confirmed']
    ).values_list('appointment_time', flat=True)
    
    # Convert booked times to HH:MM format (strip seconds)
    booked_slots = set()
    for time_obj in booked_appointments:
        if time_obj:
            # Convert time object to string in HH:MM format
            time_str = time_obj.strftime("%H:%M")
            booked_slots.add(time_str)
    
    # Filter out booked slots
    available_slots = [slot for slot in all_slots if slot not in booked_slots]
    
    # If it's today, also filter out past slots
    today = timezone.now().date()
    if date == today:
        current_time = timezone.now().time()
        current_time_str = current_time.strftime("%H:%M")
        available_slots = [
            slot for slot in available_slots 
            if slot > current_time_str
        ]
    
    return available_slots