
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin , 
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.validators import RegexValidator
from accounts.models  import CustomUser
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Doctors(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    gender_choice = (('male','Male'),('female','Female'), ('Prefer not to say','Prefer not to say'))
    phone_validator = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be in format '+999999999'.")
    
    date_of_birth = models.DateField(help_text="DD-MM-YYYY", verbose_name="Date")
    gender = models.CharField(max_length=20, choices=gender_choice)
    specialization = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    experience = models.IntegerField(validators=[MinValueValidator(0)])
    clinicaladdress = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, validators=[phone_validator])
    license_number = models.CharField(max_length=30)
    medical_degree = models.FileField(upload_to='degrees/')
    license_certificate = models.FileField(upload_to='licenses/')
    university = models.CharField(max_length=60)

    def __str__(self):
        return f"{self.user.username} - {self.specialization}"
class Patient(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    gender_choice = (('male','Male'),('female','Female'), ('Prefer not to say','Prefer not to say'))
    phone_validator = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be in format '+999999999'.")
    insurance_id_validator = RegexValidator(regex=r'^\d{2}-\d{7}$', message="Insurance ID must be of the format XX-XXXXXXX")

    date_of_birth = models.DateField(verbose_name="Date")
    gender = models.CharField(max_length=20, choices=gender_choice)
    address = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, validators=[phone_validator])
    is_insurance = models.BooleanField(default=False)
    ins_company_name = models.CharField(max_length=50, null=True, blank=True)
    ins_id_number = models.CharField(max_length=15, validators=[insurance_id_validator], null=True, blank=True)
    tobacco_user = models.BooleanField(default=False)
    is_alcoholic = models.BooleanField(default=False)
    known_allergies = models.TextField(null=True, blank=True)
    current_medications = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Patient - {self.phone_number}"



##################################################################################################################
# class CustomUser(AbstractUser):
#     ROLE_CHOICES = (
#         ('doctor', 'Doctor'),
#         ('patient', 'Patient'),
#     )
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES)
#     otp = models.CharField(max_length=6, blank = True, null = True)
#     otp_created_at = models.DateTimeField(blank=True, null=True)
#     is_verified = models.BooleanField(default=False)

#     def __str__(self):
#         return f"{self.username} ({self.role})"
