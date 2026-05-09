from django.db.models import QuerySet
from datetime import date
from Authapi.models import Patient
from appointments.models import Appointment

def get_patient_upcoming_appointments(*, patient: Patient, limit: int = 4) -> QuerySet[Appointment]:
    return patient.appointments.filter(
        appointment_date__gte=date.today(),
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')[:limit]

def get_patient_recent_appointments(*, patient: Patient, limit: int = 4) -> QuerySet[Appointment]:
    return patient.appointments.filter(
        appointment_date__lt=date.today(),
        status='completed'
    ).order_by('-appointment_date', '-appointment_time')[:limit]

def get_patient_dashboard_stats(*, patient: Patient) -> dict:
    total_appointments = patient.appointments.count()
    upcoming = patient.appointments.filter(
        appointment_date__gte=date.today(),
        status__in=['pending', 'confirmed']
    ).count()
    completed = patient.appointments.filter(
        status='completed'
    ).count()
    pending = patient.appointments.filter(
        status='pending'
    ).count()
    
    return {
        "total_appointments": total_appointments,
        "upcoming": upcoming,
        "completed": completed,
        "pending": pending
    }
