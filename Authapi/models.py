from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=True, blank=True)
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    is_profile_complete = models.BooleanField(default=False)

    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.IntegerField(default=0)
    otp_locked_until = models.DateTimeField(null=True, blank=True)
    otp_type = models.CharField(max_length=15, null=True, blank=True)

    login_attempts = models.IntegerField(default=0)
    login_locked_until = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_profile_complete']),
        ]

    def __str__(self):
        return f"{self.username if self.username else self.email} ({self.role if self.role else 'unassigned'})"

    def is_otp_locked(self):
        if self.otp_locked_until and timezone.now() < self.otp_locked_until:
            return True
        if self.otp_locked_until and timezone.now() >= self.otp_locked_until:
            self.otp_locked_until = None
            self.otp_attempts = 0
            self.save(update_fields=['otp_locked_until', 'otp_attempts'])
        return False

    def is_login_locked(self):
        if self.login_locked_until and timezone.now() < self.login_locked_until:
            return True
        if self.login_locked_until and timezone.now() >= self.login_locked_until:
            self.login_locked_until = None
            self.login_attempts = 0
            self.save(update_fields=['login_locked_until', 'login_attempts'])
        return False

    def is_otp_expired(self):
        if not self.otp_created_at:
            return True
        return timezone.now() - self.otp_created_at > timedelta(minutes=3)

    def reset_otp_attempts(self):
        self.otp_attempts = 0
        self.otp_locked_until = None
        self.save(update_fields=['otp_attempts', 'otp_locked_until'])

    def reset_login_attempts(self):
        self.login_attempts = 0
        self.login_locked_until = None
        self.save(update_fields=['login_attempts', 'login_locked_until'])

    def clear_otp(self):
        self.otp = None
        self.otp_created_at = None
        self.otp_attempts = 0
        self.otp_locked_until = None
        self.otp_type = None
        self.save(update_fields=['otp', 'otp_created_at', 'otp_attempts', 'otp_locked_until', 'otp_type'])


class Doctor(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='doctor_profile')
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    specialization = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    experience = models.IntegerField()
    clinicaladdress = models.TextField()
    phone_number = models.CharField(max_length=15, unique=True)
    license_number = models.CharField(max_length=50, unique=True)
    medical_degree = models.FileField(upload_to='medical_documents/degrees/')
    license_certificate = models.FileField(upload_to='medical_documents/licenses/')
    university = models.CharField(max_length=100)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['license_number']),
            models.Index(fields=['user']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['specialization']),
        ]

    def __str__(self):
        return f"Dr. {self.user.username} - {self.specialization}"


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient_profile')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=5)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    city = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    emergency_email = models.EmailField(blank=True, null=True)
    is_insurance = models.BooleanField(default=False)
    ins_company_name = models.CharField(max_length=100, blank=True, null=True)
    ins_policy_number = models.CharField(max_length=50, blank=True, null=True)
    known_allergies = models.TextField(blank=True, null=True)
    chronic_diseases = models.TextField(blank=True, null=True)
    previous_surgeries = models.TextField(blank=True, null=True)
    family_medical_history = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['phone_number']),
        ]

    def __str__(self):
        return f"{self.user.username} - Patient"