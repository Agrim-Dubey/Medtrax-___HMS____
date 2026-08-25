from django.db.models import QuerySet
from django.utils import timezone
from authentication.models import Doctor, Patient
from .models import Appointment

def get_patient_appointments(*, patient: Patient) -> QuerySet[Appointment]:
    return Appointment.objects.filter(
        patient=patient
    ).select_related('doctor', 'doctor__user').order_by('-appointment_date')

def get_doctor_pending_requests(*, doctor: Doctor, date: timezone.datetime.date) -> QuerySet[Appointment]:
    return Appointment.objects.filter(
        doctor=doctor,
        status='pending',
        appointment_date__gte=date
    ).select_related('patient', 'patient__user').order_by('appointment_date', 'appointment_time')

def get_available_doctors() -> QuerySet[Doctor]:
    return Doctor.objects.filter(
        user__is_active=True
    ).select_related('user')

def get_doctor_dashboard_stats(*, doctor: Doctor, date: timezone.datetime.date) -> dict:
    return {
        'total_appointments': Appointment.objects.filter(doctor=doctor).count(),
        'today_appointments': Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            status__in=['confirmed', 'completed']
        ).count(),
        'total_patients': Appointment.objects.filter(doctor=doctor).values('patient').distinct().count(),
        'pending_requests': Appointment.objects.filter(
            doctor=doctor,
            status='pending'
        ).count()
    }

def get_patient_dashboard_stats(*, patient: Patient, date: timezone.datetime.date) -> dict:
    return {
        'total_appointments': Appointment.objects.filter(patient=patient).count(),
        'upcoming': Appointment.objects.filter(
            patient=patient,
            appointment_date__gte=date,
            status='confirmed'
        ).count(),
        'completed': Appointment.objects.filter(patient=patient, status='completed').count(),
        'pending': Appointment.objects.filter(patient=patient, status='pending').count()
    }

def get_patient_upcoming_appointments(*, patient: Patient, date: timezone.datetime.date, limit: int = 5) -> QuerySet[Appointment]:
    return Appointment.objects.filter(
        patient=patient,
        appointment_date__gte=date,
        status='confirmed'
    ).select_related('doctor', 'doctor__user')[:limit]

def get_patient_recent_appointments(*, patient: Patient, limit: int = 5) -> QuerySet[Appointment]:
    return Appointment.objects.filter(
        patient=patient,
        status='completed'
    ).select_related('doctor', 'doctor__user').order_by('-appointment_date')[:limit]

def get_doctor_all_appointments(*, doctor: Doctor) -> QuerySet[Appointment]:
    return Appointment.objects.filter(
        doctor=doctor
    ).select_related('patient', 'patient__user').order_by('-appointment_date', '-appointment_time')
