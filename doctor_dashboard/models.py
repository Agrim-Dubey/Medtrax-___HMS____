from django.db import models

from django.db import models
from Authapi.models import CustomUser, Doctor, Patient

class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20) 
    created_at = models.DateTimeField(auto_now_add=True)


class DoctorReview(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    rating = models.IntegerField()  
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class PatientVisit(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    visit_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
