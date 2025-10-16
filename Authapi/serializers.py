from rest_framework import serializers
from django.contrib.auth import authenticate
from Authapi.models import CustomUser, Doctor, Patient
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
import random


class DoctorRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    
    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        
        if not email or not username or not password:
            raise serializers.ValidationError("Email, username, and password are required")
        
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists")
        
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists")
        
        return data


class PatientRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True, min_length=8)
    
    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        
        if not email or not username or not password:
            raise serializers.ValidationError("Email, username, and password are required")
        
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists")
        
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists")
        
        return data


class GenerateOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        
        if not email or not username or not password:
            raise serializers.ValidationError("Email, username, and password are required")
        
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists")
        
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists")
        
        return data
    
    def generate_and_send_otp(self, email):
        otp = str(random.randint(100000, 999999))
        subject = 'Verify Your Email with OTP - MedTrax Hospital Management'
        message = f'''
Hello,

Thank you for registering with MedTrax!

Your OTP for email verification is: {otp}

This OTP will expire in 3 minutes.

If you didn't trigger this request, please ignore this email.

Best regards,
MedTrax Team
        '''
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return otp


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    otp = serializers.CharField(required=True, write_only=True, max_length=6, min_length=6)
    
    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')
        
        if not email or not otp:
            raise serializers.ValidationError("Email and OTP are required")
        
        try:
            temp_user = CustomUser.objects.get(email=email)
            if temp_user.is_verified:
                raise serializers.ValidationError("Email already registered. Please login")
        except CustomUser.DoesNotExist:
            pass
        
        return data


class DoctorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Enter both email and password")
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")
        
        if user.role != 'doctor':
            raise serializers.ValidationError("This login is for doctors only. You don't have doctor access.")
        
        if not user.is_verified:
            raise serializers.ValidationError("Your account is not verified. Please complete your profile details.")
        
        if not user.is_active:
            raise serializers.ValidationError("Your profile is incomplete. Please complete your details.")
        
        data['user'] = user
        return data


class PatientLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Enter both email and password")
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")
        
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")
        
        if user.role != 'patient':
            raise serializers.ValidationError("This login is for patients only. You don't have patient access.")
        
        if not user.is_verified:
            raise serializers.ValidationError("Your account is not verified. Please complete your profile details.")
        
        if not user.is_active:
            raise serializers.ValidationError("Your profile is incomplete. Please complete your details.")
        
        data['user'] = user
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        
        if not email:
            raise serializers.ValidationError("Email is required")
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No account found with this email")
        
        if not user.is_verified:
            raise serializers.ValidationError("This account is not verified. Please complete registration first")
        
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated. Please contact support")
        
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.otp_attempts = 0
        user.otp_locked_until = None
        user.save()
        self.send_otp_email(user.email, otp)
        data['user'] = user
        return data
    
    def send_otp_email(self, email, otp):
        subject = 'Password Reset OTP - MedTrax Hospital Management'
        message = f'''
Hello,

We received a request to reset your password for your MedTrax account.

Your OTP for password reset is: {otp}

This OTP will expire in 3 minutes for security reasons.

If you didn't request this password reset, please ignore this email or contact our support team immediately.

Best regards,
MedTrax Support Team
        '''
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)


class VerifyPasswordResetOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    otp = serializers.CharField(required=True, write_only=True, max_length=6, min_length=6)
    
    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')
        
        if not email or not otp:
            raise serializers.ValidationError("Email and OTP are required")
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No account found with this email")
        
        if not user.otp:
            raise serializers.ValidationError("No OTP generated for this email")
        
        if user.otp_locked_until and timezone.now() < user.otp_locked_until:
            remaining_time = (user.otp_locked_until - timezone.now()).seconds // 60
            raise serializers.ValidationError(f"Too many failed attempts. Try again in {remaining_time} minutes")
        
        if user.otp != otp:
            user.otp_attempts = user.otp_attempts + 1
            
            if user.otp_attempts >= 3:
                user.otp_locked_until = timezone.now() + timedelta(minutes=10)
                user.save()
                raise serializers.ValidationError("Invalid OTP. Maximum attempts exceeded. Try again in 10 minutes")
            
            user.save()
            raise serializers.ValidationError(f"Invalid OTP. {3 - user.otp_attempts} attempts remaining")
        
        if timezone.now() - user.otp_created_at > timedelta(minutes=3):
            raise serializers.ValidationError("OTP expired")
        
        data['user'] = user
        return data


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True, min_length=8)
    
    def validate(self, data):
        email = data.get('email')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not email or not new_password or not confirm_password:
            raise serializers.ValidationError("All fields are required")
        
        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No account found with this email")
        
        data['user'] = user
        data['new_password'] = new_password
        return data
    
    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.otp = None
        user.otp_created_at = None
        user.otp_attempts = 0
        user.otp_locked_until = None
        user.save()
        return user


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        
        if not email:
            raise serializers.ValidationError("Email is required")
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No account found with this email")
        
        if user.otp_locked_until and timezone.now() < user.otp_locked_until:
            remaining_time = (user.otp_locked_until - timezone.now()).seconds // 60
            raise serializers.ValidationError(f"Too many failed attempts. Try again in {remaining_time} minutes")
        
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.otp_attempts = 0
        user.otp_locked_until = None
        user.save()
        self.send_otp_email(user.email, otp)
        data['user'] = user
        return data
    
    def send_otp_email(self, email, otp):
        subject = 'Your New OTP - MedTrax Hospital Management'
        message = f'''
Hello,

Your new OTP for verification is: {otp}

This OTP will expire in 3 minutes.

If you didn't request this, please ignore this email.

Best regards,
MedTrax Team
        '''
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)


class DoctorDetailsSerializer(serializers.Serializer):
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.CharField(required=True)
    specialization = serializers.CharField(required=True)
    department = serializers.CharField(required=True)
    experience = serializers.IntegerField(required=True, min_value=0)
    clinicaladdress = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    license_number = serializers.CharField(required=True)
    medical_degree = serializers.FileField(required=True)
    license_certificate = serializers.FileField(required=True)
    university = serializers.CharField(required=True)
    
    def validate(self, data):
        required_fields = ['date_of_birth', 'gender', 'specialization', 'department', 'experience', 'clinicaladdress', 'phone_number', 'license_number', 'medical_degree', 'license_certificate', 'university']
        
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"{field} is required")
        
        return data
    
    def create(self, validated_data, user):
        doctor = Doctor.objects.create(
            user=user,
            date_of_birth=validated_data['date_of_birth'],
            gender=validated_data['gender'],
            specialization=validated_data['specialization'],
            department=validated_data['department'],
            experience=validated_data['experience'],
            clinicaladdress=validated_data['clinicaladdress'],
            phone_number=validated_data['phone_number'],
            license_number=validated_data['license_number'],
            medical_degree=validated_data['medical_degree'],
            license_certificate=validated_data['license_certificate'],
            university=validated_data['university']
        )
        user.is_active = True
        user.is_verified = True
        user.save()
        return doctor


class PatientDetailsSerializer(serializers.Serializer):
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    is_insurance = serializers.BooleanField(required=False, default=False)
    ins_company_name = serializers.CharField(required=False, allow_blank=True)
    ins_id_number = serializers.CharField(required=False, allow_blank=True)
    tobacco_user = serializers.BooleanField(required=False, default=False)
    is_alcoholic = serializers.BooleanField(required=False, default=False)
    known_allergies = serializers.CharField(required=False, allow_blank=True)
    current_medications = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        required_fields = ['date_of_birth', 'gender', 'address', 'phone_number']
        
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"{field} is required")
        
        if data.get('is_insurance'):
            if not data.get('ins_company_name') or not data.get('ins_id_number'):
                raise serializers.ValidationError("Insurance company name and ID are required when insurance is selected")
        
        return data
    
    def create(self, validated_data, user):
        patient = Patient.objects.create(
            user=user,
            date_of_birth=validated_data['date_of_birth'],
            gender=validated_data['gender'],
            address=validated_data['address'],
            phone_number=validated_data['phone_number'],
            is_insurance=validated_data.get('is_insurance', False),
            ins_company_name=validated_data.get('ins_company_name', ''),
            ins_id_number=validated_data.get('ins_id_number', ''),
            tobacco_user=validated_data.get('tobacco_user', False),
            is_alcoholic=validated_data.get('is_alcoholic', False),
            known_allergies=validated_data.get('known_allergies', ''),
            current_medications=validated_data.get('current_medications', '')
        )
        user.is_active = True
        user.is_verified = True
        user.save()
        return patient
