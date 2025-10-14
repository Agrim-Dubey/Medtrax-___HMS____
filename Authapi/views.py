from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (RegisterSerializer,OTPVerificationSerializer,LoginSerializer,ForgotPasswordSerializer,ResetPasswordSerializer)
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import random

CustomUser = get_user_model()

error_400_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description='Validation errors from the request'
        )
    },
    example={"error": {"email": ["A user with this email already exists."]}}
)

error_404_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_OBJECT)
    },
    example={"error": {"email": "No user found with this email address."}}
)

error_500_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING)
    },
    example={"error": "Internal server error"}
)
@swagger_auto_schema(
    method='post',
    request_body=RegisterSerializer,
    responses={
        201: openapi.Response(
            description='User registered successfully. OTP sent to email.',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                    'username': openapi.Schema(type=openapi.TYPE_STRING)
                },
                example={
                    "message": "Registration successful! Please check your email for OTP verification.",
                    "email": "user@example.com",
                    "username": "johndoe"
                }
            )
        ),
        400: openapi.Response(
            description='Bad Request - Validation failed (invalid email, password mismatch, weak password, duplicate email/username)',
            schema=error_400_schema
        ),
        500: openapi.Response(
            description='Internal Server Error - Email sending failed or database error',
            schema=error_500_schema
        )
    },
    tags=['Authentication']
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
            {"error": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST 
        )
@swagger_auto_schema(
    method='post',
    request_body=OTPVerificationSerializer,
    responses={
        200: openapi.Response(
            description='Email verified successfully. Account is now active.',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'username': openapi.Schema(type=openapi.TYPE_STRING),
                    'email': openapi.Schema(type=openapi.TYPE_STRING),
                    'role': openapi.Schema(type=openapi.TYPE_STRING)
                },
                example={
                    "message": "Email verified successfully! You can now login.",
                    "user_id": 1,
                    "username": "johndoe",
                    "email": "user@example.com",
                    "role": "patient"
                }
            )
        ),
        400: openapi.Response(
            description='Bad Request - Invalid OTP, expired OTP, or email not found',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_OBJECT)
                },
                example={
                    "error": {
                        "otp": ["Invalid OTP. Please check and try again."]
                    }
                }
            )
        ),
        404: openapi.Response(
            description='Not Found - User with given email does not exist',
            schema=error_404_schema
        ),
        500: openapi.Response(
            description='Internal Server Error - Database error',
            schema=error_500_schema
        )
    },
    tags=['Authentication']
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
            {"error": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST 
        )
@swagger_auto_schema(
    method='post',
    request_body=LoginSerializer,
    responses={
        200: openapi.Response(
            description='Login successful. Returns JWT tokens and user details.',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'username': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                            'role': openapi.Schema(type=openapi.TYPE_STRING),
                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'last_name': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                },
                example={
                    "message": "Login successful",
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "user": {
                        "user_id": 1,
                        "username": "johndoe",
                        "email": "user@example.com",
                        "role": "patient",
                        "first_name": "John",
                        "last_name": "Doe"
                    }
                }
            )
        ),
        400: openapi.Response(
            description='Bad Request - Invalid credentials, user not verified, or role mismatch',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_OBJECT)
                },
                example={
                    "error": {
                        "non_field_errors": ["Invalid email or password."]
                    }
                }
            )
        ),
        401: openapi.Response(
            description='Unauthorized - Email not verified or wrong role selected',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_OBJECT)
                },
                example={
                    "error": {
                        "non_field_errors": ["Please verify your email before logging in."]
                    }
                }
            )
        ),
        403: openapi.Response(
            description='Forbidden - Account has been deactivated',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_OBJECT)
                },
                example={
                    "error": {
                        "non_field_errors": ["Your account has been deactivated."]
                    }
                }
            )
        ),
        404: openapi.Response(
            description='Not Found - User does not exist',
            schema=error_404_schema
        ),
        500: openapi.Response(
            description='Internal Server Error',
            schema=error_500_schema
        )
    },
    tags=['Authentication']
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
        {"error": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST 
    )
@swagger_auto_schema(
    method='post',
    request_body=ForgotPasswordSerializer,
    responses={
        200: openapi.Response(
            description='OTP sent successfully to registered email address.',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'email': openapi.Schema(type=openapi.TYPE_STRING)
                },
                example={
                    "message": "OTP has been sent to your email. Please check your inbox.",
                    "email": "user@example.com"
                }
            )
        ),
        400: openapi.Response(
            description='Bad Request - User not found, not verified, or account deactivated',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_OBJECT)
                },
                example={
                    "error": {
                        "email": ["No patient account found with this email address."]
                    }
                }
            )
        ),
        401: openapi.Response(
            description='Unauthorized - Account is not verified or is deactivated',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_OBJECT)
                },
                example={
                    "error": {
                        "email": ["This account is not verified. Please complete registration first."]
                    }
                }
            )
        ),
        404: openapi.Response(
            description='Not Found - No account with provided email and role',
            schema=error_404_schema
        ),
        500: openapi.Response(
            description='Internal Server Error - Email sending failed',
            schema=error_500_schema
        )
    },
    tags=['Password Management']
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
        {"error": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )
@swagger_auto_schema(
    method='post',
    request_body=ResetPasswordSerializer,
    responses={
        200: openapi.Response(
            description='Password reset successfully. Confirmation email sent.',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                },
                example={
                    "message": "Password has been reset successfully! You can now login with your new password."
                }
            )
        ),
        400: openapi.Response(
            description='Bad Request - Invalid OTP, expired OTP, password validation failed, or user not found',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_OBJECT)
                },
                example={
                    "error": {
                        "new_password": ["Password must be at least 8 characters long."]
                    }
                }
            )
        ),
        401: openapi.Response(
            description='Unauthorized - Invalid or expired OTP',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_OBJECT)
                },
                example={
                    "error": {
                        "otp": ["OTP has expired. Please request a new password reset."]
                    }
                }
            )
        ),
        404: openapi.Response(
            description='Not Found - No account with provided email and role',
            schema=error_404_schema
        ),
        500: openapi.Response(
            description='Internal Server Error - Database or email error',
            schema=error_500_schema
        )
    },
    tags=['Password Management']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_view(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Password has been reset successfully! You can now login with your new password."
            },
            status=status.HTTP_200_OK
        )
    return Response(
        {"error": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST
    )
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={'email': openapi.Schema(type=openapi.TYPE_STRING)},
        required=['email']
    ),
    responses={200: openapi.Response(description='OTP resent successfully')},
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp_view(request):
    email = request.data.get('email')
    try:
        user = CustomUser.objects.get(email=email, is_verified=False)
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()
        
        from django.core.mail import send_mail
        from django.conf import settings
        subject = 'Your New OTP - MedTrax'
        message = f'Your new OTP is: {otp}\n\nThis OTP will expire in 10 minutes.'
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email], fail_silently=False)
        
        return Response(
            {"message": "OTP resent successfully to your email."},
            status=status.HTTP_200_OK
        )
    except CustomUser.DoesNotExist:
        return Response(
            {"error": {"email": "No unverified account found with this email."}},
            status=status.HTTP_404_NOT_FOUND
        )