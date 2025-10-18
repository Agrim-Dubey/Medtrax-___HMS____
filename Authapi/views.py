from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.utils import timezone
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

    @transaction.atomic
    def post(self, request):
        try:
            serializer = SignupSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {'success': False, 'errors': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            role = serializer.validated_data['role']

            otp = str(random.randint(100000, 999999))

            user = CustomUser.objects.create(
                username=username,
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
                'username': username,
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
                'username': user.username,
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
                date_of_birth=serializer.validated_data['date_of_birth'],
                gender=serializer.validated_data['gender'],
                address=serializer.validated_data['address'],
                phone_number=serializer.validated_data['phone_number'],
                emergency_contact=serializer.validated_data.get('emergency_contact', ''),
                is_insurance=serializer.validated_data.get('is_insurance', False),
                ins_company_name=serializer.validated_data.get('ins_company_name', ''),
                ins_id_number=serializer.validated_data.get('ins_id_number', ''),
                tobacco_user=serializer.validated_data.get('tobacco_user', False),
                is_alcoholic=serializer.validated_data.get('is_alcoholic', False),
                known_allergies=serializer.validated_data.get('known_allergies', ''),
                current_medications=serializer.validated_data.get('current_medications', '')
            )

            user.is_profile_complete = True
            user.save()

            return Response({
                'success': True,
                'message': 'Patient profile created successfully! You can now login.',
                'patient_id': patient.id,
                'username': patient.user.username,
                'email': patient.user.email,
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
                    'username': user.username,
                    'role': user.role,
                    'next_step': 'verify_otp'
                }, status=status.HTTP_200_OK)

            if user.is_verified and not user.is_profile_complete:
                return Response({
                    'success': True,
                    'status': 'pending_profile',
                    'message': 'Please complete your profile.',
                    'email': user.email,
                    'username': user.username,
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