
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin , 
from django.db import models
from accounts.from django.db import models import CustomUser
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.validators import RegexValidator


class Doctors(models.Model):
    gender_choice = (('male','Male'),
                   ('female','Female'),
                   ('Prefer not to say','Prefer not to say')
                   ),
    phone_validator = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE)
    date_of_birth = models.DateField(help_text="DD-MM-YYYY",verbose_name="Date",blank=False)
    gender = models.CharField(max_length=20,choices = gender_choice,blank=False)
    specialization = models.CharField(max_length=100,blank=False)
    department = models.CharField(max_length= 100,blank=False)
    experience = models.IntegerField(validators=[MinValueValidator(0)],blank=False)
    clinicaladdress = models.CharField(max_length = 100)
    phone_number = models.CharField(
    max_length=15,
    validators=[phone_validator],
    blank=False
)

    license_number = models.CharField(max_length=30, blank=False)
    medical_degree = models.FileField(upload_to='degrees/',blank=False)
    license_certificate = models.FileField(upload_to='licenses/',blank=False)
    university = models.CharField(max_length=60,blank=False)

    def __str__(self):
        return f"{self.user.username} - {self.specialization}"






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
