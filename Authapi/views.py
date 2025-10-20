from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging
import random

from Authapi.models import CustomUser, Doctor, Patient
from .serializers import (
    SignupSerializer, VerifySignupOTPSerializer, ResendSignupOTPSerializer,
    DoctorDetailsSerializer, PatientDetailsSerializer,
    DoctorLoginSerializer, PatientLoginSerializer,
    ForgotPasswordSerializer, VerifyPasswordResetOTPSerializer,
    ResetPasswordSerializer, ResendPasswordResetOTPSerializer,
    OTPEmailService
)

logger = logging.getLogger(__name__)


class SignupView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user account (Doctor or Patient)",
        operation_summary="User Signup",
        request_body=SignupSerializer,
        responses={
            201: openapi.Response(
                description="Account created successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Account created! OTP sent to your email. Valid for 3 minutes.",
                        "email": "user@example.com",
                        "username": "johndoe",
                        "role": "doctor",
                        "next_step": "verify_otp"
                    }
                }
            ),
            400: openapi.Response(
                description="Validation error",
                examples={
                    "application/json": {
                        "success": False,
                        "errors": {
                            "email": ["User with this email already exists."],
                            "username": ["This field is required."]
                        }
                    }
                }
            ),
            500: openapi.Response(
                description="Server error",
                examples={
                    "application/json": {
                        "success": False,
                        "error": "Signup failed. Please try again."
                    }
                }
            )
        },
        tags=['Authentication']
    )
    @transaction.atomic
    def post(self, request):
        try:
            serializer = SignupSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            email = serializer.validated_data['email']
            password = serializer.validated_data['password1']
            role = serializer.validated_data['role']

            otp = str(random.randint(100000, 999999))

            user = CustomUser.objects.create(
                username=email,
                email=email,
                role=role,
                otp=otp,
                otp_created_at=timezone.now(),
                otp_type='verification',
                is_verified=False,
                is_profile_complete=False
            )
            user.set_password(password)
            user.save()

            try:
                OTPEmailService.send_email(email, otp, 'verification')
            except Exception as e:
                logger.error(f"Failed to send OTP email for signup: {str(e)}")
                user.delete()
                return Response(
                    {'success': False, 'error': 'Failed to send verification email. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response({
                'success': True,
                'message': 'Account created! OTP sent to your email. Valid for 3 minutes.',
                'email': email,
                'role': role,
                'next_step': 'verify_otp'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Signup failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifySignupOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Verify email using OTP sent during signup",
        operation_summary="Verify Signup OTP",
        request_body=VerifySignupOTPSerializer,
        responses={
            200: openapi.Response(
                description="Email verified successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Email verified successfully! Please complete your profile.",
                        "email": "user@example.com",
                        "username": "johndoe",
                        "role": "doctor",
                        "next_step": "complete_profile"
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid or expired OTP",
                examples={
                    "application/json": {
                        "success": False,
                        "errors": {
                            "otp": ["Invalid OTP"],
                            "non_field_errors": ["OTP has expired"]
                        }
                    }
                }
            ),
            500: "Server error"
        },
        tags=['Authentication']
    )
    @transaction.atomic
    def post(self, request):
        try:
            serializer = VerifySignupOTPSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = serializer.validated_data['user']

            user.is_verified = True
            user.clear_otp()
            user.save()

            return Response({
                'success': True,
                'message': 'Email verified successfully! Please complete your profile.',
                'email': user.email,
                'role': user.role,
                'next_step': 'complete_profile'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"OTP verification error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Verification failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResendSignupOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Request a new OTP for email verification",
        operation_summary="Resend Signup OTP",
        request_body=ResendSignupOTPSerializer,
        responses={
            200: openapi.Response(
                description="New OTP sent successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "New OTP sent to your email. Valid for 3 minutes.",
                        "email": "user@example.com"
                    }
                }
            ),
            400: "Invalid request or user not found",
            500: "Failed to send OTP"
        },
        tags=['Authentication']
    )
    def post(self, request):
        try:
            serializer = ResendSignupOTPSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = serializer.validated_data['user']
            email = user.email
            otp = str(random.randint(100000, 999999))

            user.otp = otp
            user.otp_created_at = timezone.now()
            user.otp_attempts = 0
            user.otp_locked_until = None
            user.save()

            try:
                OTPEmailService.send_email(email, otp, 'resend')
            except Exception as e:
                logger.error(f"Failed to resend OTP email: {str(e)}")
                return Response(
                    {'success': False, 'error': 'Failed to resend OTP. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response({
                'success': True,
                'message': 'New OTP sent to your email. Valid for 3 minutes.',
                'email': email
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Resend OTP error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Failed to resend OTP. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorDetailsView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Create complete doctor profile with medical credentials",
        operation_summary="Complete Doctor Profile",
        request_body=DoctorDetailsSerializer,
        responses={
            201: openapi.Response(
                description="Doctor profile created successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Doctor profile created successfully! You can now login.",
                        "doctor_id": 123,
                        "specialization": "Cardiology",
                        "department": "Cardiology",
                        "username": "Dr. Smith",
                        "email": "doctor@example.com",
                        "next_step": "login"
                    }
                }
            ),
            400: "Validation error or profile already exists",
            404: "User account not found",
            500: "Profile creation failed"
        },
        tags=['Profile Management']
    )
    @transaction.atomic
    def post(self, request):
        try:
            serializer = DoctorDetailsSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            email = serializer.validated_data['email']

            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'No account found. Please sign up first.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not user.is_verified:
                return Response(
                    {'success': False, 'error': 'Please verify your email first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.role != 'doctor':
                return Response(
                    {'success': False, 'error': 'This account is not registered as a doctor.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Doctor.objects.filter(user=user).exists():
                return Response(
                    {'success': False, 'error': 'Doctor profile already exists for this account.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            doctor = Doctor.objects.create(
                user=user,
                date_of_birth=serializer.validated_data['date_of_birth'],
                gender=serializer.validated_data['gender'],
                specialization=serializer.validated_data['specialization'],
                department=serializer.validated_data['department'],
                experience=serializer.validated_data['experience'],
                clinicaladdress=serializer.validated_data['clinicaladdress'],
                phone_number=serializer.validated_data['phone_number'],
                license_number=serializer.validated_data['license_number'],
                medical_degree=serializer.validated_data['medical_degree'],
                license_certificate=serializer.validated_data['license_certificate'],
                university=serializer.validated_data['university']
            )

            user.is_profile_complete = True
            user.save()

            return Response({
                'success': True,
                'message': 'Doctor profile created successfully! You can now login.',
                'doctor_id': doctor.id,
                'specialization': doctor.specialization,
                'department': doctor.department,
                'username': doctor.user.username,
                'email': doctor.user.email,
                'next_step': 'login'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Doctor profile creation error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Profile creation failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PatientDetailsView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Create complete patient profile with medical history",
        operation_summary="Complete Patient Profile",
        request_body=PatientDetailsSerializer,
        responses={
            201: openapi.Response(
                description="Patient profile created successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Patient profile created successfully! You can now login.",
                        "patient_id": 456,
                        "username": "johndoe",
                        "email": "patient@example.com",
                        "next_step": "login"
                    }
                }
            ),
            400: "Validation error or profile already exists",
            404: "User account not found",
            500: "Profile creation failed"
        },
        tags=['Profile Management']
    )
    @transaction.atomic
    def post(self, request):
        try:
            serializer = PatientDetailsSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            email = serializer.validated_data['email']

            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'No account found. Please sign up first.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not user.is_verified:
                return Response(
                    {'success': False, 'error': 'Please verify your email first.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.role != 'patient':
                return Response(
                    {'success': False, 'error': 'This account is not registered as a patient.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if Patient.objects.filter(user=user).exists():
                return Response(
                    {'success': False, 'error': 'Patient profile already exists for this account.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            patient = Patient.objects.create(
                user=user,
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                date_of_birth=serializer.validated_data['date_of_birth'],
                blood_group=serializer.validated_data['blood_group'],
                gender=serializer.validated_data['gender'],
                city=serializer.validated_data['city'],
                phone_number=serializer.validated_data['phone_number'],
                emergency_contact=serializer.validated_data.get('emergency_contact', ''),
                emergency_email=serializer.validated_data.get('emergency_email', ''),
                is_insurance=serializer.validated_data.get('is_insurance', False),
                ins_company_name=serializer.validated_data.get('ins_company_name', ''),
                ins_policy_number=serializer.validated_data.get('ins_policy_number', ''),
                known_allergies=serializer.validated_data.get('known_allergies', ''),
                chronic_diseases=serializer.validated_data.get('chronic_diseases', ''),
                previous_surgeries=serializer.validated_data.get('previous_surgeries', ''),
                family_medical_history=serializer.validated_data.get('family_medical_history', '')
            )

            username = f"{serializer.validated_data['first_name'].lower()}{serializer.validated_data['last_name'].lower()}"
            base_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user.username = username
            user.is_profile_complete = True
            user.save()

            return Response({
                'success': True,
                'message': 'Patient profile created successfully! You can now login.',
                'patient_id': patient.id,
                'username': user.username,
                'email': user.email,
                'next_step': 'login'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Patient profile creation error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Profile creation failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DoctorLoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Authenticate doctor and receive JWT tokens",
        operation_summary="Doctor Login",
        request_body=DoctorLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Login successful!",
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "user": {
                            "user_id": 1,
                            "username": "Dr. Smith",
                            "email": "doctor@example.com",
                            "role": "doctor",
                            "doctor_id": 123,
                            "specialization": "Cardiology",
                            "department": "Cardiology",
                            "is_approved": True
                        }
                    }
                }
            ),
            400: "Invalid credentials",
            404: "Profile not found",
            500: "Login failed"
        },
        tags=['Authentication']
    )
    def post(self, request):
        try:
            serializer = DoctorLoginSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = serializer.validated_data['user']

            try:
                doctor = Doctor.objects.get(user=user)
            except Doctor.DoesNotExist:
                logger.error(f"Doctor profile not found for user: {user.email}")
                return Response(
                    {'success': False, 'error': 'Profile not found. Please complete your profile.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            refresh = RefreshToken.for_user(user)

            return Response({
                'success': True,
                'message': 'Login successful!',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'doctor_id': doctor.id,
                    'specialization': doctor.specialization,
                    'department': doctor.department,
                    'is_approved': doctor.is_approved
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Doctor login error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Login failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PatientLoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Authenticate patient and receive JWT tokens",
        operation_summary="Patient Login",
        request_body=PatientLoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Login successful!",
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "user": {
                            "user_id": 2,
                            "username": "John Doe",
                            "email": "patient@example.com",
                            "role": "patient",
                            "patient_id": 456,
                            "gender": "Male",
                            "phone_number": "+1234567890"
                        }
                    }
                }
            ),
            400: "Invalid credentials",
            404: "Profile not found",
            500: "Login failed"
        },
        tags=['Authentication']
    )
    def post(self, request):
        try:
            serializer = PatientLoginSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = serializer.validated_data['user']

            try:
                patient = Patient.objects.get(user=user)
            except Patient.DoesNotExist:
                logger.error(f"Patient profile not found for user: {user.email}")
                return Response(
                    {'success': False, 'error': 'Profile not found. Please complete your profile.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            refresh = RefreshToken.for_user(user)

            return Response({
                'success': True,
                'message': 'Login successful!',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'patient_id': patient.id,
                    'gender': patient.gender,
                    'phone_number': patient.phone_number
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Patient login error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Login failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Request password reset OTP via email",
        operation_summary="Forgot Password",
        request_body=ForgotPasswordSerializer,
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "OTP sent to your email. Valid for 3 minutes.",
                        "email": "user@example.com",
                        "next_step": "verify_reset_otp"
                    }
                }
            ),
            400: "Invalid email or user not found",
            500: "Failed to send OTP"
        },
        tags=['Password Management']
    )
    def post(self, request):
        try:
            serializer = ForgotPasswordSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({
                'success': True,
                'message': 'OTP sent to your email. Valid for 3 minutes.',
                'email': request.data.get('email'),
                'next_step': 'verify_reset_otp'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Forgot password error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Failed to send OTP. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyPasswordResetOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Verify OTP for password reset",
        operation_summary="Verify Password Reset OTP",
        request_body=VerifyPasswordResetOTPSerializer,
        responses={
            200: openapi.Response(
                description="OTP verified successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "OTP verified successfully! You can now reset your password.",
                        "email": "user@example.com",
                        "next_step": "reset_password"
                    }
                }
            ),
            400: "Invalid or expired OTP",
            500: "Verification failed"
        },
        tags=['Password Management']
    )
    def post(self, request):
        try:
            serializer = VerifyPasswordResetOTPSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({
                'success': True,
                'message': 'OTP verified successfully! You can now reset your password.',
                'email': request.data.get('email'),
                'next_step': 'reset_password'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Password reset OTP verification error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Verification failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Set new password after OTP verification",
        operation_summary="Reset Password",
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password reset successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Password reset successfully! Please login with your new password.",
                        "next_step": "login"
                    }
                }
            ),
            400: "Validation error or passwords don't match",
            500: "Password reset failed"
        },
        tags=['Password Management']
    )
    @transaction.atomic
    def post(self, request):
        try:
            serializer = ResetPasswordSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save()

            return Response({
                'success': True,
                'message': 'Password reset successfully! Please login with your new password.',
                'next_step': 'login'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Password reset failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResendPasswordResetOTPView(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Request a new OTP for password reset",
        operation_summary="Resend Password Reset OTP",
        request_body=ResendPasswordResetOTPSerializer,
        responses={
            200: openapi.Response(
                description="New OTP sent successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "New OTP sent to your email. Valid for 3 minutes.",
                        "email": "user@example.com"
                    }
                }
            ),
            400: "Invalid request or user not found",
            500: "Failed to resend OTP"
        },
        tags=['Password Management']
    )
    def post(self, request):
        try:
            serializer = ResendPasswordResetOTPSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = serializer.validated_data['user']
            email = user.email
            otp = str(random.randint(100000, 999999))

            user.otp = otp
            user.otp_created_at = timezone.now()
            user.otp_attempts = 0
            user.otp_locked_until = None
            user.save()

            try:
                OTPEmailService.send_email(email, otp, 'reset')
            except Exception as e:
                logger.error(f"Failed to resend password reset OTP email: {str(e)}")
                return Response(
                    {'success': False, 'error': 'Failed to resend OTP. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response({
                'success': True,
                'message': 'New OTP sent to your email. Valid for 3 minutes.',
                'email': email
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Resend password reset OTP error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Failed to resend OTP. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckAccountStatusView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Check account status and get next registration step",
        operation_summary="Check Account Status",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description='Email address to check',
                    example='user@example.com'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Account status retrieved",
                examples={
                    "application/json": {
                        "success": True,
                        "status": "registered",
                        "message": "Account fully registered. Please login.",
                        "role": "doctor",
                        "next_step": "login"
                    }
                }
            ),
            400: openapi.Response(
                description="Email not provided",
                examples={
                    "application/json": {
                        "success": False,
                        "error": "Email is required."
                    }
                }
            ),
            500: "Status check failed"
        },
        tags=['Utility']
    )
    def post(self, request):
        try:
            email = request.data.get('email', '').strip()

            if not email:
                return Response(
                    {'success': False, 'error': 'Email is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({
                    'success': True,
                    'status': 'not_registered',
                    'message': 'No account found. Please sign up.',
                    'next_step': 'signup'
                }, status=status.HTTP_200_OK)

            if not user.is_verified:
                return Response({
                    'success': True,
                    'status': 'pending_verification',
                    'message': 'Email verification pending.',
                    'email': user.email,
                    
                    'role': user.role,
                    'next_step': 'verify_otp'
                }, status=status.HTTP_200_OK)

            if user.is_verified and not user.is_profile_complete:
                return Response({
                    'success': True,
                    'status': 'pending_profile',
                    'message': 'Please complete your profile.',
                    'email': user.email,
                    
                    'role': user.role,
                    'next_step': 'complete_profile'
                }, status=status.HTTP_200_OK)

            return Response({
                'success': True,
                'status': 'registered',
                'message': 'Account fully registered. Please login.',
                'role': user.role,
                'next_step': 'login'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Account status check error: {str(e)}")
            return Response(
                {'success': False, 'error': 'Status check failed.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )