from django.db import models
from Authapi.models import Doctor, Patient, CustomUser
from django.core.exceptions import ValidationError
from django.utils import timezone

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        Doctor, 
        on_delete=models.CASCADE, 
        related_name='doctor_appointments'
    )

    appointment_date = models.DateField(help_text="Date of appointment")
    appointment_time = models.TimeField(help_text="Time slot for appointment")

    duration = models.IntegerField(default=30, help_text="Duration in minutes")

    reason_for_visit = models.TextField(help_text="Chief complaint/reason for visit")
    symptoms = models.TextField(blank=True, null=True, help_text="Current symptoms")

    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )

    doctor_notes = models.TextField(
        blank=True, 
        null=True, 
        help_text="Doctor's notes after appointment"
    )
    rejection_reason = models.TextField(
        blank=True, 
        null=True, 
        help_text="Reason if rejected"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['patient', 'appointment_date']),
            models.Index(fields=['doctor', 'appointment_date']),
            models.Index(fields=['status']),
            models.Index(fields=['appointment_date']),
        ]

        unique_together = [['doctor', 'appointment_date', 'appointment_time']]
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'

    def __str__(self):
        return f"{self.patient.get_full_name()} → Dr. {self.doctor.get_full_name()} | {self.appointment_date} {self.appointment_time}"

    def clean(self):
        if self.appointment_date < timezone.now().date():
            raise ValidationError("Cannot book appointment in the past")
 
        if not self.doctor.is_approved:
            raise ValidationError("Doctor is not approved yet")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)