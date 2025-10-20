from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta, date
from django.core.mail import send_mail
from django.conf import settings
import re
import random

from Authapi.models import CustomUser, Doctor, Patient


class OTPEmailService:
    @staticmethod
    def send_email(email, otp, email_type='verification'):
        templates = {
            'verification': {
                'subject': 'Verify Your Email with OTP - MedTrax Hospital Management',
                'message': f'Hello,\n\nThank you for registering with MedTrax!\n\nYour OTP for email verification is: {otp}\n\nThis OTP will expire in 3 minutes.\n\nIf you did not trigger this request, please ignore this email.\n\nBest regards,\nMedTrax Team'
            },
            'reset': {
                'subject': 'Password Reset OTP - MedTrax Hospital Management',
                'message': f'Hello,\n\nWe received a request to reset your password for your MedTrax account.\n\nYour OTP for password reset is: {otp}\n\nThis OTP will expire in 3 minutes for security reasons.\n\nIf you did not request this, please ignore this email.\n\nBest regards,\nMedTrax Support Team'
            },
            'resend': {
                'subject': 'Your New OTP - MedTrax Hospital Management',
                'message': f'Hello,\n\nYour new OTP for verification is: {otp}\n\nThis OTP will expire in 3 minutes.\n\nIf you did not request this, please ignore this email.\n\nBest regards,\nMedTrax Team'
            }
        }

        template = templates.get(email_type, templates['verification'])

        try:
            send_mail(
                template['subject'],
                template['message'],
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")


class PasswordValidator:
    @staticmethod
    def validate(password):
        if len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if len(password) > 20:
            raise serializers.ValidationError("Password must be only 20 characters long.")
        if ' ' in password:
            raise serializers.ValidationError("Password cannot contain spaces.")
        if not re.search(r'[a-z]', password):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', password):
            raise serializers.ValidationError("Password must contain at least one digit.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;]', password):
            raise serializers.ValidationError("Password must contain at least one special character (!@#$%^&* etc.).")
        return True


class PhoneValidator:
    @staticmethod
    def validate(phone):
        if not re.match(r'^[0-9]{10,15}$', phone):
            raise serializers.ValidationError("Phone number must be 10-15 digits.")
        return True


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=3, max_length=20)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=8,max_length=20,
    trim_whitespace=False)
    role = serializers.ChoiceField(choices=['doctor', 'patient'], required=True)

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Username cannot be empty.")
        if len(value) < 3:
            raise serializers.ValidationError(f"Username too short. You entered {len(value)} characters, minimum is 3.")
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError(f"Username too long. You entered {len(value)} characters, maximun is 20.")
        if len(value) > 20:
            raise serializers.ValidationError("Username cannot exceed 20 characters.")
        if not re.match(r'^[a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, and underscores.")
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_password(self, value):
        PasswordValidator.validate(value)
        return value

    def validate_role(self, value):
        if value not in ['doctor', 'patient']:
            raise serializers.ValidationError("Invalid role. Choose either 'doctor' or 'patient'.")
        return value


class VerifySignupOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value

    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Email not found. Please register first.")

        if user.is_verified:
            raise serializers.ValidationError("This email is already verified. Please log in.")

        if user.is_otp_locked():
            if user.otp_locked_until:
                remaining = max(0, (user.otp_locked_until - timezone.now()).total_seconds() // 60)
                raise serializers.ValidationError(f"Too many OTP attempts. Try again in {int(remaining) + 1} minutes.")
            raise serializers.ValidationError("Account temporarily locked. Try again later.")

        if not user.otp:
            raise serializers.ValidationError("No OTP found. Request a new one.")

        if user.is_otp_expired():
            user.clear_otp()
            raise serializers.ValidationError("OTP expired. Request a new one.")

        if user.otp != otp:
            user.otp_attempts += 1
            if user.otp_attempts >= 3:
                user.otp_locked_until = timezone.now() + timedelta(minutes=10)
            user.save()
            attempts_left = max(0, 3 - user.otp_attempts)
            raise serializers.ValidationError(f"Invalid OTP. {attempts_left} attempts remaining.")

        data['user'] = user
        return data


class ResendSignupOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, data):
        email = data.get('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No account found with this email.")

        if user.is_verified:
            raise serializers.ValidationError("This email is already verified. Please log in.")

        if user.is_otp_locked():
            if user.otp_locked_until:
                remaining = max(0, (user.otp_locked_until - timezone.now()).total_seconds() // 60)
                raise serializers.ValidationError(f"Too many attempts. Try again in {int(remaining) + 1} minutes.")
            raise serializers.ValidationError("Account temporarily locked. Try again later.")

        data['user'] = user
        return data


class DoctorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if user.is_login_locked():
            if user.login_locked_until:
                remaining = max(0, (user.login_locked_until - timezone.now()).total_seconds() // 60)
                raise serializers.ValidationError(f"Account locked due to multiple failed attempts. Try again in {int(remaining) + 1} minutes.")
            raise serializers.ValidationError("Account temporarily locked. Try again later.")

        if not user.check_password(password):
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.login_locked_until = timezone.now() + timedelta(minutes=15)
            user.save()
            raise serializers.ValidationError("Invalid email or password.")

        user.reset_login_attempts()

        if user.role != 'doctor':
            raise serializers.ValidationError("This account is not authorized for doctor login.")

        if not user.is_verified:
            raise serializers.ValidationError("Your account is not verified. Please verify your email first.")

        if not user.is_profile_complete:
            raise serializers.ValidationError("Your profile is incomplete. Please complete your profile details.")

        data['user'] = user
        return data


class PatientLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if user.is_login_locked():
            if user.login_locked_until:
                remaining = max(0, (user.login_locked_until - timezone.now()).total_seconds() // 60)
                raise serializers.ValidationError(f"Account locked due to multiple failed attempts. Try again in {int(remaining) + 1} minutes.")
            raise serializers.ValidationError("Account temporarily locked. Try again later.")

        if not user.check_password(password):
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.login_locked_until = timezone.now() + timedelta(minutes=15)
            user.save()
            raise serializers.ValidationError("Invalid email or password.")

        user.reset_login_attempts()

        if user.role != 'patient':
            raise serializers.ValidationError("This account is not authorized for patient login.")

        if not user.is_verified:
            raise serializers.ValidationError("Your account is not verified. Please verify your email first.")

        if not user.is_profile_complete:
            raise serializers.ValidationError("Your profile is incomplete. Please complete your profile details.")

        data['user'] = user
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, data):
        email = data.get('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No account found with this email. Please sign up.")

        if not user.is_verified:
            raise serializers.ValidationError("Your account is not verified. Please complete registration first.")

        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.otp_type = 'reset'
        user.otp_attempts = 0
        user.otp_locked_until = None
        user.save()

        try:
            OTPEmailService.send_email(email, otp, 'reset')
        except Exception as e:
            raise serializers.ValidationError(f"Failed to send OTP. {str(e)}")

        data['user'] = user
        return data


class VerifyPasswordResetOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value

    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No account found with this email.")

        if user.is_otp_locked():
            if user.otp_locked_until:
                remaining = max(0, (user.otp_locked_until - timezone.now()).total_seconds() // 60)
                raise serializers.ValidationError(f"Too many attempts. Try again in {int(remaining) + 1} minutes.")
            raise serializers.ValidationError("Account temporarily locked. Try again later.")

        if not user.otp:
            raise serializers.ValidationError("No OTP generated. Request a new one.")

        if user.is_otp_expired():
            user.clear_otp()
            raise serializers.ValidationError("OTP expired. Request a new one.")

        if user.otp != otp:
            user.otp_attempts += 1
            if user.otp_attempts >= 3:
                user.otp_locked_until = timezone.now() + timedelta(minutes=10)
            user.save()
            attempts_left = max(0, 3 - user.otp_attempts)
            raise serializers.ValidationError(f"Invalid OTP. {attempts_left} attempts remaining.")

        data['user'] = user
        return data


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True, min_length=8)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_new_password(self, value):
        PasswordValidator.validate(value)
        return value

    def validate_confirm_password(self, value):
        return value

    def validate(self, data):
        email = data.get('email')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No account found with this email.")

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

        if user.check_password(new_password):
            raise serializers.ValidationError("New password cannot be the same as your current password.")

        data['user'] = user
        return data

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.clear_otp()
        user.save()
        return user


class ResendPasswordResetOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, data):
        email = data.get('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No account found with this email.")

        if not user.is_verified:
            raise serializers.ValidationError("Your account is not verified.")

        if user.is_otp_locked():
            if user.otp_locked_until:
                remaining = max(0, (user.otp_locked_until - timezone.now()).total_seconds() // 60)
                raise serializers.ValidationError(f"Too many attempts. Try again in {int(remaining) + 1} minutes.")
            raise serializers.ValidationError("Account temporarily locked. Try again later.")

        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.otp_type = 'reset'
        user.otp_attempts = 0
        user.otp_locked_until = None
        user.save()

        try:
            OTPEmailService.send_email(email, otp, 'reset')
        except Exception as e:
            raise serializers.ValidationError(f"Failed to send OTP. {str(e)}")

        data['user'] = user
        return data


class DoctorDetailsSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'], required=True)
    specialization = serializers.CharField(required=True, max_length=100)
    department = serializers.CharField(required=True, max_length=100)
    experience = serializers.IntegerField(required=True, min_value=0, max_value=70)
    clinicaladdress = serializers.CharField(required=True, max_length=500)
    phone_number = serializers.CharField(required=True, max_length=15)
    license_number = serializers.CharField(required=True, max_length=50)
    medical_degree = serializers.FileField(required=True)
    license_certificate = serializers.FileField(required=True)
    university = serializers.CharField(required=True, max_length=100)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_date_of_birth(self, value):
        today = date.today()
        if value > today:
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        age = (today - value).days // 365
        if age < 25:
            raise serializers.ValidationError("Doctor must be at least 25 years old.")
        if age > 100:
            raise serializers.ValidationError("Please enter a valid date of birth.")
        return value

    def validate_phone_number(self, value):
        value = value.strip()
        PhoneValidator.validate(value)
        if Doctor.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value

    def validate_license_number(self, value):
        value = value.strip().upper()
        if Doctor.objects.filter(license_number=value).exists():
            raise serializers.ValidationError("License number already registered.")
        return value

    def validate_specialization(self, value):
        if not value.strip():
            raise serializers.ValidationError("Specialization cannot be empty.")
        return value.strip()

    def validate_department(self, value):
        if not value.strip():
            raise serializers.ValidationError("Department cannot be empty.")
        return value.strip()

    def validate_clinicaladdress(self, value):
        if not value.strip():
            raise serializers.ValidationError("Clinical address cannot be empty.")
        return value.strip()

    def validate_university(self, value):
        if not value.strip():
            raise serializers.ValidationError("University cannot be empty.")
        return value.strip()

    def validate_medical_degree(self, value):
        if not value:
            raise serializers.ValidationError("Medical degree file is required.")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Medical degree file must be under 5MB.")
        return value

    def validate_license_certificate(self, value):
        if not value:
            raise serializers.ValidationError("License certificate file is required.")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("License certificate file must be under 5MB.")
        return value

    def validate(self, data):
        if data['experience'] < 0:
            raise serializers.ValidationError("Experience cannot be negative.")
        return data


class PatientDetailsSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'], required=True)
    address = serializers.CharField(required=True, max_length=500)
    phone_number = serializers.CharField(required=True, max_length=15)
    emergency_contact = serializers.CharField(required=False, allow_blank=True, max_length=15)
    is_insurance = serializers.BooleanField(required=False, default=False)
    ins_company_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    ins_id_number = serializers.CharField(required=False, allow_blank=True, max_length=50)
    tobacco_user = serializers.BooleanField(required=False, default=False)
    is_alcoholic = serializers.BooleanField(required=False, default=False)
    known_allergies = serializers.CharField(required=False, allow_blank=True, max_length=500)
    current_medications = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_date_of_birth(self, value):
        today = date.today()
        if value > today:
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        age = (today - value).days // 365
        if age < 18:
            raise serializers.ValidationError("Patient must be at least 18 years old.")
        if age > 150:
            raise serializers.ValidationError("Please enter a valid date of birth.")
        return value

    def validate_phone_number(self, value):
        value = value.strip()
        PhoneValidator.validate(value)
        if Patient.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value

    def validate_emergency_contact(self, value):
        if value and value.strip():
            value = value.strip()
            PhoneValidator.validate(value)
        return value

    def validate_address(self, value):
        if not value.strip():
            raise serializers.ValidationError("Address cannot be empty.")
        return value.strip()

    def validate_ins_company_name(self, value):
        if value:
            return value.strip()
        return value

    def validate_ins_id_number(self, value):
        if value:
            return value.strip()
        return value

    def validate_known_allergies(self, value):
        if value:
            return value.strip()
        return value

    def validate_current_medications(self, value):
        if value:
            return value.strip()
        return value

    def validate(self, data):
        is_insurance = data.get('is_insurance', False)
        ins_company = data.get('ins_company_name', '').strip() if data.get('ins_company_name') else ''
        ins_id = data.get('ins_id_number', '').strip() if data.get('ins_id_number') else ''

        if is_insurance:
            if not ins_company:
                raise serializers.ValidationError("Insurance company name is required when insurance is selected.")
            if not ins_id:
                raise serializers.ValidationError("Insurance ID number is required when insurance is selected.")

        return data