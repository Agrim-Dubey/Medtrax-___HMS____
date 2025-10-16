from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from Authapi.models import CustomUser, Doctor, Patient
from .serializers import (
    DoctorRegisterSerializer, PatientRegisterSerializer, GenerateOTPSerializer,
    VerifyOTPSerializer, DoctorLoginSerializer, PatientLoginSerializer,
    ForgotPasswordSerializer, VerifyPasswordResetOTPSerializer, ResetPasswordSerializer,
    ResendOTPSerializer, DoctorDetailsSerializer, PatientDetailsSerializer
)


class DoctorRegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = DoctorRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            otp_generator = GenerateOTPSerializer(data=request.data)
            if otp_generator.is_valid():
                otp = otp_generator.generate_and_send_otp(request.data['email'])
                return Response({
                    'message': 'OTP sent to your email. Valid for 3 minutes',
                    'email': request.data['email']
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientRegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PatientRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            otp_generator = GenerateOTPSerializer(data=request.data)
            if otp_generator.is_valid():
                otp = otp_generator.generate_and_send_otp(request.data['email'])
                return Response({
                    'message': 'OTP sent to your email. Valid for 3 minutes',
                    'email': request.data['email']
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        role = request.data.get('role')
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not all([email, otp, role, username, password]):
            return Response({
                'error': 'Email, OTP, role, username, and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = VerifyOTPSerializer(data={'email': email, 'otp': otp})
        
        if serializer.is_valid():
            user = CustomUser.objects.create(
                email=email,
                username=username,
                role=role,
                is_verified=False,
                is_active=False,
                otp=None,
                otp_created_at=None,
                otp_attempts=0
            )
            user.set_password(password)
            user.save()
            
            return Response({
                'message': 'OTP verified successfully. Please complete your profile details',
                'email': email,
                'role': role,
                'username': username
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckRegistrationStatusView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
            
            if user.is_verified:
                return Response({
                    'status': 'complete',
                    'message': 'Registration complete. You can login'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'incomplete',
                    'message': 'Please complete your profile details',
                    'email': email,
                    'role': user.role,
                    'username': user.username
                }, status=status.HTTP_200_OK)
        
        except CustomUser.DoesNotExist:
            return Response({
                'status': 'not_registered',
                'message': 'Please register first'
            }, status=status.HTTP_200_OK)


class DoctorLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = DoctorLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            refresh = RefreshToken.for_user(user)
            
            doctor = Doctor.objects.get(user=user)
            
            return Response({
                'message': 'Doctor login successful',
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'doctor_id': doctor.id
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientLoginView(APIView):
    def post(self, request):
        serializer = PatientLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            refresh = RefreshToken.for_user(user)
            
            patient = Patient.objects.get(user=user)
            
            return Response({
                'message': 'Patient login successful',
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'patient_id': patient.id
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            return Response({
                'message': 'OTP sent to your email. Valid for 3 minutes',
                'email': request.data['email']
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyPasswordResetOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = VerifyPasswordResetOTPSerializer(data=request.data)
        
        if serializer.is_valid():
            return Response({
                'message': 'OTP verified. You can now reset your password',
                'email': request.data['email']
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            
            return Response({
                'message': 'Password reset successfully. Please login with your new password'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        
        if serializer.is_valid():
            return Response({
                'message': 'New OTP sent to your email. Valid for 3 minutes',
                'email': request.data['email']
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorDetailsView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found. Please verify OTP first'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.role != 'doctor':
            return Response({
                'error': 'Only doctors can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if user.is_verified:
            return Response({
                'error': 'Your profile is already complete'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = DoctorDetailsSerializer(data=request.data)
        
        if serializer.is_valid():
            doctor = serializer.create(serializer.validated_data, user)
            
            return Response({
                'message': 'Doctor profile created successfully. Please login to continue',
                'doctor_id': doctor.id,
                'specialization': doctor.specialization,
                'department': doctor.department,
                'user_id': user.id,
                'username': user.username
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientDetailsView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found. Please verify OTP first'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.role != 'patient':
            return Response({
                'error': 'Only patients can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if user.is_verified:
            return Response({
                'error': 'Your profile is already complete'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PatientDetailsSerializer(data=request.data)
        
        if serializer.is_valid():
            patient = serializer.create(serializer.validated_data, user)
            
            return Response({
                'message': 'Patient profile created successfully. Please login to continue',
                'patient_id': patient.id,
                'address': patient.address,
                'user_id': user.id,
                'username': user.username
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)