from django.db.models import Avg, QuerySet
from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment
from .models import DoctorReview
from Authapi.models import Doctor

def get_doctor_dashboard_stats(*, doctor: Doctor) -> dict:
    today = timezone.now().date()
    
    total_appointments_today = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today
    ).count()
    
    pending_appointments = Appointment.objects.filter(
        doctor=doctor,
        status='pending'
    ).count()
    
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__gte=today,
        status__in=['pending', 'confirmed']
    ).count()
    
    completed_appointments = Appointment.objects.filter(
        doctor=doctor,
        status='completed'
    ).count()
    
    reviews = DoctorReview.objects.filter(doctor=doctor)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    return {
        'total_appointments_today': total_appointments_today,
        'pending_appointments': pending_appointments,
        'upcoming_appointments': upcoming_appointments,
        'completed_appointments': completed_appointments,
        'average_rating': round(avg_rating, 1),
        'total_reviews': reviews.count()
    }

def get_doctor_today_appointments(*, doctor: Doctor, limit: int = 10) -> QuerySet[Appointment]:
    today = timezone.now().date()
    return Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today,
        status__in=['pending', 'confirmed']
    ).select_related('patient', 'patient__user').order_by('appointment_time')[:limit]

def get_doctor_upcoming_appointments(*, doctor: Doctor, limit: int = 10) -> QuerySet[Appointment]:
    today = timezone.now().date()
    week_later = today + timedelta(days=7)
    return Appointment.objects.filter(
        doctor=doctor,
        appointment_date__range=[today, week_later],
        status__in=['pending', 'confirmed']
    ).select_related('patient', 'patient__user').order_by('appointment_date', 'appointment_time')[:limit]

def get_doctor_recent_reviews(*, doctor: Doctor, limit: int = 5) -> QuerySet[DoctorReview]:
    return DoctorReview.objects.filter(
        doctor=doctor
    ).select_related('patient').order_by('-created_at')[:limit]

def get_doctor_weekly_stats(*, doctor: Doctor) -> list:
    today = timezone.now().date()
    weekly_stats = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            status='completed'
        ).count()
        
        weekly_stats.append({
            "date": date.strftime('%Y-%m-%d'),
            "day_name": date.strftime('%a'),
            "day_short": date.strftime('%d %b'),
            "patient_count": count
        })
    return weekly_stats
