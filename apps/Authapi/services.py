from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
import random
import logging

from Authapi.models import CustomUser, Doctor, Patient
from Authapi.tasks import send_otp_email_task

logger = logging.getLogger(__name__)

@transaction.atomic
def create_user_account(*, email: str, password: str, role: str) -> CustomUser:
    """
    Creates a new user account or resets an unverified one, and queues an OTP email.
    """
    otp = str(random.randint(100000, 999999))

    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            'username': email,
            'role': role,
            'is_verified': False,
            'is_profile_complete': False
        }
    )

    if not created and user.is_verified:
        raise ValidationError("This email is already registered.")

    # Always reset the password and OTP fields for unverified accounts trying to sign up again
    user.set_password(password)
    user.role = role
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.otp_attempts = 0
    user.otp_locked_until = None
    user.save()

    try:
        send_otp_email_task.delay(email, otp, "Verification")
        logger.info(f"OTP email queued via Celery for {email}")
    except Exception as e:
        logger.error(f"Failed to queue email task: {e}")
        raise

    return user

@transaction.atomic
def create_doctor_profile(*, user: CustomUser, data: dict) -> tuple[CustomUser, Doctor]:
    """
    Creates a doctor profile for the given verified user and updates the user's username and profile status.
    """
    if not user.is_verified:
        raise ValidationError("Please verify your email first.")

    if user.role != 'doctor':
        raise ValidationError("This account is not registered as a doctor.")

    if Doctor.objects.filter(user=user).exists():
        raise ValidationError("Doctor profile already exists for this account.")

    try:
        doctor = Doctor.objects.create(
            user=user,
            first_name=data['first_name'],
            last_name=data['last_name'],
            date_of_birth=data['date_of_birth'],
            gender=data['gender'],
            blood_group=data['blood_group'],
            marital_status=data.get('marital_status', ''),
            address=data.get('address', ''),
            city=data['city'],
            state=data.get('state', ''),
            pincode=data.get('pincode', ''),
            country=data.get('country', ''),
            registration_number=data.get('registration_number', ''),
            specialization=data.get('specialization', ''),
            qualification=data.get('qualification', ''),
            years_of_experience=data.get('years_of_experience'),
            department=data.get('department', ''),
            clinic_name=data.get('clinic_name', ''),
            phone_number=data['phone_number'],
            alternate_phone_number=data.get('alternate_phone_number', ''),
            alternate_email=data.get('alternate_email', ''),
            emergency_contact_person=data.get('emergency_contact_person', ''),
            emergency_contact_number=data.get('emergency_contact_number', '')
        )
    except Exception as e:
        # Assuming IntegrityError indicates a unique constraint violation like phone number
        raise ValidationError("Phone number already registered. Please use a different number.")

    # Generate a unique username based on name
    username = f"{data['first_name'].lower()}{data['last_name'].lower()}"
    base_username = username
    counter = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    user.username = username
    user.is_profile_complete = True
    user.save()

    return user, doctor

@transaction.atomic
def create_patient_profile(*, user: CustomUser, data: dict) -> tuple[CustomUser, Patient]:
    """
    Creates a patient profile for the given verified user and updates the user's username and profile status.
    """
    if not user.is_verified:
        raise ValidationError("Please verify your email first.")

    if user.role != 'patient':
        raise ValidationError("This account is not registered as a patient.")

    if Patient.objects.filter(user=user).exists():
        raise ValidationError("Patient profile already exists for this account.")

    try:
        patient = Patient.objects.create(
            user=user,
            first_name=data['first_name'],
            last_name=data['last_name'],
            date_of_birth=data['date_of_birth'],
            blood_group=data['blood_group'],
            gender=data['gender'],
            city=data['city'],
            phone_number=data['phone_number'],
            emergency_contact=data.get('emergency_contact', ''),
            emergency_email=data.get('emergency_email', ''),
            is_insurance=data.get('is_insurance', False),
            ins_company_name=data.get('ins_company_name', ''),
            ins_policy_number=data.get('ins_policy_number', ''),
            known_allergies=data.get('known_allergies', ''),
            chronic_diseases=data.get('chronic_diseases', ''),
            previous_surgeries=data.get('previous_surgeries', ''),
            family_medical_history=data.get('family_medical_history', '')
        )
    except Exception as e:
        # Assuming IntegrityError indicates a unique constraint violation like phone number
        raise ValidationError("Phone number already registered. Please use a different number.")

    # Generate a unique username based on name
    username = f"{data['first_name'].lower()}{data['last_name'].lower()}"
    base_username = username
    counter = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    user.username = username
    user.is_profile_complete = True
    user.save()

    return user, patient

@transaction.atomic
def request_password_reset(*, email: str) -> CustomUser:
    """
    Validates user and sends a password reset OTP.
    """
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        raise ValidationError("No account found with this email. Please sign up.")

    if not user.is_verified:
        raise ValidationError("Your account is not verified. Please complete registration first.")

    otp = str(random.randint(100000, 999999))
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.otp_type = 'reset'
    user.otp_attempts = 0
    user.otp_locked_until = None
    user.save()

    try:
       send_otp_email_task.delay(email, otp, 'reset')
    except Exception as e:
        raise ValidationError(f"Failed to send OTP. {str(e)}")

    return user
