from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser
import random
from django.utils import timezone
from datetime import timedelta

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField( write_only=True,required=True,style={'input_type': 'password'})
    password2 = serializers.CharField( write_only=True,required=True,style={'input_type': 'password'},label="Confirm Password")
    email = serializers.EmailField(required=True,validators=[])
    
    role = serializers.ChoiceField(choices=['doctor', 'patient'],required=True)
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2', 'role', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': True}, 
            'last_name': {'required': True}, 
        }
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value
    
    def validate(self, data):        
      
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        if len(data['password']) < 8:
            raise serializers.ValidationError({
                "password": "Password must be at least 8 characters long."
            })
        if len(data['password'])>20:
            raise serializers.ValidationError({
                "password": "Password must be within 20 characters limit."
            })
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        otp = str(random.randint(100000, 999999))
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data['role'],
            otp=otp,
            otp_created_at=timezone.now(), 
            is_verified=False, 
            is_active=False 
        )
        user.save()
        self.send_otp_email(user.email, otp)
        return user
    
    def send_otp_email(self, email, otp):
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = 'Verify Your Email with OTP - MedTrax Hospital Management'
        message = f'''
        Hello,
        
        Thank you for registering with MedTrax!
        
        Your OTP for email verification is: {otp}
        
        This OTP will expire in 10 minutes.
        If you didn't trigger this request, please ignore this email.
        Best regards,
        MedTrax Team
        '''
        from_email = settings.EMAIL_HOST_USER 
        recipient_list = [email] 
        send_mail(subject,message,from_email,recipient_list,fail_silently=False,)

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6, min_length=6)
    def validate(self, data):
        email = data.get('email') 
        otp = data.get('otp')  
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({
                "email": "No user found with this email address."
            })
        if not user.otp:
            raise serializers.ValidationError({
                "otp": "No OTP found. Please request a new one."
            })
        if user.otp != otp:
            raise serializers.ValidationError({
                "otp": "Invalid OTP. Please check and try again."
            })
        if user.otp_created_at:
            time_elapsed = timezone.now() - user.otp_created_at
            if time_elapsed > timedelta(minutes=10):
                raise serializers.ValidationError({
                    "otp": "OTP has expired. Please request a new one."
                })
        data['user'] = user
        return data
    def save(self):
        user = self.validated_data['user']
        user.is_active = True
        user.is_verified = True
        user.otp = None
        user.otp_created_at = None
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'})
    role = serializers.ChoiceField(
        choices=['doctor', 'patient'],
        required=True
    )
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({
                "non_field_errors": ["Invalid email or password."]
            })
        if not user.is_verified:
            raise serializers.ValidationError({
                "non_field_errors": ["Please verify your email before logging in. Check your inbox for the OTP."]
            })
        if not user.is_active:
            raise serializers.ValidationError({
                "non_field_errors": ["Your account has been deactivated. Please contact support."]
            })
        if user.role != role:
            raise serializers.ValidationError({
                "non_field_errors": [f"This account is registered as a {user.role}, not a {role}."]
            })
        user_authenticated = authenticate(username=user.username, password=password)
        if user_authenticated is None:
         
            raise serializers.ValidationError({
                "non_field_errors": ["Invalid email or password."]
            })
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        refresh = str(refresh)
        data['access'] = access
        data['refresh'] = refresh
        data['user_id'] = user.id
        data['username'] = user.username
        data['email'] = user.email
        data['role'] = user.role
        data['first_name'] = user.first_name
        data['last_name'] = user.last_name
        return data

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(
        choices=['doctor', 'patient'],
        required=True
    )
    def validate(self, data):
        email = data.get('email')
        role = data.get('role')
        try:
            user = CustomUser.objects.get(email=email, role=role)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({
                "email": f"No {role} account found with this email address."
            })
        if not user.is_verified:
            raise serializers.ValidationError({
                "email": "This account is not verified. Please complete registration first."
            })
        if not user.is_active:
            raise serializers.ValidationError({
                "email": "This account has been deactivated. Please contact support."
            })
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()
        self.send_otp_email(user.email, otp, user.first_name)
        data['user'] = user
        return data
    def send_otp_email(self, email, otp, first_name):
        from django.core.mail import send_mail
        from django.conf import settings

        subject = 'Password Reset OTP - MedTrax Hospital Management'
        message = f'''
Hello {first_name},

We received a request to reset your password for your MedTrax account.

Your OTP for password reset is  {otp}

This OTP will expire in 10 minutes for security reasons.

If you didn't request this password reset, please ignore this email or contact our support team immediately.

Best regards,
MedTrax Support Team
        '''
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(
            subject,          
            message,          
            from_email,       
            recipient_list,    
            fail_silently=False,  
        )
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    otp = serializers.CharField(
        required=True,
        max_length=6,
        min_length=6
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}, 
        min_length=8 
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    role = serializers.ChoiceField(
        choices=['doctor', 'patient'],
        required=True
    )
    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        role = data.get('role')
        if new_password != confirm_password:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match. Please try again."
            })
        if len(new_password) < 8:
            raise serializers.ValidationError({
                "new_password": "Password must be at least 8 characters long."
            })
        if new_password.isdigit():
            raise serializers.ValidationError({
                "new_password": "Password cannot be entirely numeric. Please include letters."
            })
        if new_password.lower() == 'password':
            raise serializers.ValidationError({
                "new_password": "Password cannot be 'password'. Please choose a stronger password."
            })
        try:
            user = CustomUser.objects.get(email=email, role=role)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({
                "email": f"No {role} account found with this email address."
            })
        if not user.otp:
            raise serializers.ValidationError({
                "otp": "No OTP found. Please request a new password reset."
            })
        if user.otp != otp:
            raise serializers.ValidationError({
                "otp": "Invalid OTP. Please check and try again."
            })
        if user.otp_created_at:
            time_elapsed = timezone.now() - user.otp_created_at
            if time_elapsed > timedelta(minutes=10):
                raise serializers.ValidationError({
                    "otp": "OTP has expired. Please request a new password reset."
                })
        data['user'] = user
        return data
    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.otp = None
        user.otp_created_at = None
        user.save()
        self.send_password_reset_confirmation(user.email, user.first_name)
        return user
    def send_password_reset_confirmation(self, email, first_name):
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = 'Password Successfully Reset - MedTrax'
        
        message = f'''
Hello {first_name},

Your password has been successfully reset for your MedTrax account.

If you made this change, you can safely ignore this email.

If you did NOT reset your password, your account may be compromised. Please contact our support team immediately at support@medtrax.com or call us at 1-800-MEDTRAX.

For your security:
- Never share your password with anyone
- Use a unique password for your MedTrax account
- Enable two-factor authentication if available

Best regards,
MedTrax Security Team'''
      
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject,message,from_email,recipient_list,fail_silently=False,
        )