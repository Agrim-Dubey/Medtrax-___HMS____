from django.db.models import QuerySet
from Authapi.models import Patient, Doctor
from appointments.models import Appointment
from .models import Prescription

def get_doctor_patients(*, doctor: Doctor) -> list[Patient]:
    patient_ids = Appointment.objects.filter(
        doctor=doctor,
        status__in=['confirmed', 'completed']
    ).values_list('patient_id', flat=True).distinct()
    
    patients = Patient.objects.filter(
        id__in=patient_ids
    ).prefetch_related('appointments')
    
    patients_with_last_apt = []
    for patient in patients:
        last_apt = Appointment.objects.filter(
            doctor=doctor,
            patient=patient,
            status__in=['confirmed', 'completed']
        ).order_by('-appointment_date', '-appointment_time').first()
        
        if last_apt:
            patients_with_last_apt.append((patient, last_apt.appointment_date, last_apt.appointment_time))
            
    # Sort patients by their last appointment date/time descending
    patients_with_last_apt.sort(key=lambda x: (x[1], x[2]), reverse=True)
    return [item[0] for item in patients_with_last_apt]

def get_doctor_prescriptions(*, doctor: Doctor, patient_id: int = None) -> QuerySet[Prescription]:
    prescriptions = Prescription.objects.filter(
        doctor=doctor
    ).select_related('patient', 'doctor').prefetch_related('medications', 'lab_tests')
    
    if patient_id:
        prescriptions = prescriptions.filter(patient_id=patient_id)
        
    return prescriptions.order_by('-created_at')

def get_patient_prescriptions(*, patient: Patient, doctor_id: int = None) -> QuerySet[Prescription]:
    prescriptions = Prescription.objects.filter(
        patient=patient
    ).select_related('doctor', 'patient').prefetch_related('medications', 'lab_tests')
    
    if doctor_id:
        prescriptions = prescriptions.filter(doctor_id=doctor_id)
        
    return prescriptions.order_by('-created_at')
