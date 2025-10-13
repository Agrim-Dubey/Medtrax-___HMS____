from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (RegisterSerializer,OTPVerificationSerializer,LoginSerializer,ForgotPasswordSerializer,ResetPasswordSerializer)
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

CustomUser = get_user_model()


@swagger_auto_schema(
    method='post',
    request_body=RegisterSerializer,
    responses={201: openapi.Response('User registered successfully', RegisterSerializer)}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Registration successful! Please check your email for OTP verification.",
                "email": user.email,
                "username": user.username
            },
            status=status.HTTP_201_CREATED
        )
    else:
        return Response(
            {
                "error": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST 
        )
    

@swagger_auto_schema(
    method='post',
    request_body=OTPVerificationSerializer,
    responses={200: openapi.Response('Email verified successfully', OTPVerificationSerializer)}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Email verified successfully! You can now login.",
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            },
            status=status.HTTP_200_OK 
        )
    else:
        return Response(
            {
                "error": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST 
        )
    

@swagger_auto_schema(
    method='post',
    request_body=LoginSerializer,
    responses={200: openapi.Response('Login successful', LoginSerializer)}
)    
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        access_token = serializer.validated_data['access']
        refresh_token = serializer.validated_data['refresh']
        user_id = serializer.validated_data['user_id']
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        role = serializer.validated_data['role']
        first_name = serializer.validated_data['first_name']
        last_name = serializer.validated_data['last_name']
        return Response(
            {
                "message": "Login successful",
                "access": access_token,
                "refresh": refresh_token,
                "user": {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "role": role,
                    "first_name": first_name,
                    "last_name": last_name
                }
            },
            status=status.HTTP_200_OK 
        )
    return Response(
            {
                "error": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST 
        )

@swagger_auto_schema(
    method='post',
    request_body=ForgotPasswordSerializer,
    responses={200: openapi.Response('OTP sent to email', ForgotPasswordSerializer)}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_view(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        return Response(
            {
                "message": "OTP has been sent to your email. Please check your inbox.",
                "email": serializer.validated_data['email']
            },
            status=status.HTTP_200_OK
        )
    return Response(
        {
            "error": serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    method='post',
    request_body=ForgotPasswordSerializer,
    responses={200: openapi.Response('OTP sent to email', ForgotPasswordSerializer)}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_view(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        return Response(
            {
                "message": "Password has been reset successfully! You can now login with your new password."
            },
            status=status.HTTP_200_OK
        )
    return Response(
        {
            "error": serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )