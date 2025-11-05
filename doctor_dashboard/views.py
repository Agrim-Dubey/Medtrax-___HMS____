from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from appointments.models import Appointment
from .models import DoctorReview
from .serializers import (
    DoctorDashboardProfileSerializer,
    DashboardAppointmentSerializer,
    DoctorReviewSerializer, DoctorCompleteProfileSerializer
)


class DoctorDashboardProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get doctor's profile information",
        operation_summary="Retrieve Doctor Profile",
        tags=['Doctor Profile'],
        responses={
            200: openapi.Response(
                description="Profile retrieved successfully",
                schema=DoctorDashboardProfileSerializer,
                examples={
                    "application/json": {
                        "id": 1,
                        "full_name": "Dr.Agrim Dubey",
                        "email": "agrimxyz@gmail.com",
                        "specialization": "Cardiology",
                        "phone_number": "+1234567890",
                        "years_of_experience": 10,
                        "registration_number": "MED123456"
                    }
                }
            ),
            403: openapi.Response(
                description="Access denied - User is not a doctor",
                examples={
                    "application/json": {
                        "error": "Only doctors can access this endpoint"
                    }
                }
            ),
            401: "Unauthorized - Authentication required"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            serializer = DoctorDashboardProfileSerializer(doctor)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get comprehensive dashboard statistics",
        operation_summary="Retrieve Dashboard Stats",
        tags=['Dashboard Statistics'],
        responses={
            200: openapi.Response(
                description="Statistics retrieved successfully",
                examples={
                    "application/json": {
                        "total_appointments_today": 8,
                        "pending_appointments": 12,
                        "upcoming_appointments": 25,
                        "completed_appointments": 156,
                        "average_rating": 4.6,
                        "total_reviews": 45
                    }
                }
            ),
            403: "Access denied - User is not a doctor",
            401: "Unauthorized - Authentication required"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            today = timezone.now().date()
            
            total_appointments_today = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=today
            ).count()
            
            pending_appointments = Appointment.objects.filter(
                doctor=doctor,
                status='pending'
            ).count()

            upcoming_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date__gte=today,
                status__in=['pending', 'confirmed']
            ).count()
            
            completed_appointments = Appointment.objects.filter(
                doctor=doctor,
                status='completed'
            ).count()
            
            reviews = DoctorReview.objects.filter(doctor=doctor)
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            
            stats = {
                'total_appointments_today': total_appointments_today,
                'pending_appointments': pending_appointments,
                'upcoming_appointments': upcoming_appointments,
                'completed_appointments': completed_appointments,
                'average_rating': round(avg_rating, 1),
                'total_reviews': reviews.count()
            }
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorTodayAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get today's appointments (pending/confirmed only)",
        operation_summary="List Today's Appointments",
        tags=['Appointments'],
        responses={
            200: openapi.Response(
                description="Today's appointments retrieved successfully",
                schema=DashboardAppointmentSerializer(many=True),
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "patient_name": "John Doe",
                            "patient_age": 35,
                            "patient_gender": "Male",
                            "patient_phone": "+1234567890",
                            "patient_blood_group": "O+",
                            "appointment_date": "2024-11-03",
                            "appointment_time": "10:00:00",
                            "appointment_time_formatted": "10:00 AM",
                            "reason": "Regular checkup",
                            "status": "confirmed"
                        }
                    ]
                }
            ),
            403: "Access denied",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            today = timezone.now().date()
            
            appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=today,
                status__in=['pending', 'confirmed']
            ).select_related('patient', 'patient__user').order_by('appointment_time')[:10]
            
            serializer = DashboardAppointmentSerializer(appointments, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorUpcomingAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get upcoming appointments for next 7 days",
        operation_summary="List Upcoming Appointments",
        tags=['Appointments'],
        responses={
            200: openapi.Response(
                description="Upcoming appointments retrieved successfully",
                schema=DashboardAppointmentSerializer(many=True)
            ),
            403: "Access denied",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            today = timezone.now().date()
            week_later = today + timedelta(days=7)
            
            appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date__range=[today, week_later],
                status__in=['pending', 'confirmed']
            ).select_related('patient', 'patient__user').order_by('appointment_date', 'appointment_time')[:10]
            
            serializer = DashboardAppointmentSerializer(appointments, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorRecentReviewsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get 5 most recent patient reviews",
        operation_summary="List Recent Reviews",
        tags=['Reviews'],
        responses={
            200: openapi.Response(
                description="Recent reviews retrieved successfully",
                schema=DoctorReviewSerializer(many=True),
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "patient_name": "Jane Smith",
                            "rating": 5,
                            "comment": "Excellent doctor, very professional",
                            "created_at": "2024-11-01T10:30:00Z",
                            "date_formatted": "November 01, 2024",
                            "time_ago": "2 days ago"
                        }
                    ]
                }
            ),
            403: "Access denied",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            
            reviews = DoctorReview.objects.filter(
                doctor=doctor
            ).select_related('patient').order_by('-created_at')[:5]
            
            serializer = DoctorReviewSerializer(reviews, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorCompleteProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get complete doctor profile with all fields",
        operation_summary="Retrieve Complete Doctor Profile",
        tags=['Doctor Profile'],
        responses={
            200: openapi.Response(
                description="Complete profile retrieved successfully",
                schema=DoctorCompleteProfileSerializer,
                examples={
                    "application/json": {
                        "email": "agrimxyz@gmail.com",
                        "username": "dr_agrim",
                        "is_verified": True,
                        "first_name": "Agrim",
                        "last_name": "Dubey",
                        "date_of_birth": "1985-05-15",
                        "gender": "M",
                        "blood_group": "O+",
                        "marital_status": "Married",
                        "address": "123 Medical Street",
                        "city": "New Delhi",
                        "state": "Delhi",
                        "pincode": "110001",
                        "country": "India",
                        "registration_number": "MED123456",
                        "specialization": "Cardiology",
                        "qualification": "MBBS, MD Cardiology",
                        "years_of_experience": 10,
                        "department": "Cardiology",
                        "clinic_name": "Heart Care Clinic",
                        "phone_number": "+911234567890",
                        "alternate_phone_number": "+919876543210",
                        "alternate_email": "agrim.alternate@gmail.com",
                        "emergency_contact_person": "Jane Dubey",
                        "emergency_contact_number": "+911122334455",
                        "is_approved": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-11-01T14:20:00Z"
                    }
                }
            ),
            403: openapi.Response(
                description="Access denied - User is not a doctor",
                examples={
                    "application/json": {
                        "error": "Only doctors can access this endpoint"
                    }
                }
            ),
            401: "Unauthorized - Authentication required"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            serializer = DoctorCompleteProfileSerializer(doctor)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def patch(self, request):
        try:
            doctor = request.user.doctor_profile
            editable_fields = ['first_name', 'last_name', 
                'phone_number', 'alternate_phone_number', 'alternate_email',
                'address', 'city', 'state', 'pincode', 'country',
                'marital_status', 'qualification', 'years_of_experience',
                'department', 'clinic_name', 'emergency_contact_person',
                'emergency_contact_number'
            ]

            filtered_data = {
                key: value for key, value in request.data.items() 
                if key in editable_fields
            }
            serializer = DoctorCompleteProfileSerializer(
                doctor, 
                data=filtered_data, 
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Profile updated successfully",
                        "data": serializer.data
                    },
                    status=status.HTTP_200_OK
                )
            
            return Response(
                {"error": "Invalid data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class DoctorWeeklyStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="""
        Get daily completed appointment counts for the last 7 days.
        Returns data formatted for chart visualization.
        Uses optimized single-query aggregation for better performance.
        """,
        operation_summary="Weekly Stats for Charts",
        tags=['Dashboard Statistics'],
        responses={
            200: openapi.Response(
                description="Weekly statistics retrieved successfully",
                examples={
                    "application/json": {
                        "weekly_stats": [
                            {
                                "date": "2024-10-28",
                                "day_name": "Mon",
                                "day_short": "28 Oct",
                                "patient_count": 5
                            },
                            {
                                "date": "2024-10-29",
                                "day_name": "Tue",
                                "day_short": "29 Oct",
                                "patient_count": 3
                            },
                            {
                                "date": "2024-10-30",
                                "day_name": "Wed",
                                "day_short": "30 Oct",
                                "patient_count": 7
                            },
                            {
                                "date": "2024-10-31",
                                "day_name": "Thu",
                                "day_short": "31 Oct",
                                "patient_count": 2
                            },
                            {
                                "date": "2024-11-01",
                                "day_name": "Fri",
                                "day_short": "01 Nov",
                                "patient_count": 4
                            },
                            {
                                "date": "2024-11-02",
                                "day_name": "Sat",
                                "day_short": "02 Nov",
                                "patient_count": 6
                            },
                            {
                                "date": "2024-11-03",
                                "day_name": "Sun",
                                "day_short": "03 Nov",
                                "patient_count": 3
                            }
                        ],
                        "total_week": 30
                    }
                }
            ),
            403: "Access denied",
            401: "Unauthorized"
        },
        security=[{'Bearer': []}]
    )
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            today = timezone.now().date()
            start_date = today - timedelta(days=6)
            appointments_by_date = Appointment.objects.filter(
                doctor=doctor,
                appointment_date__gte=start_date,
                appointment_date__lte=today,
                status='completed'
            ).values('appointment_date').annotate(
                patient_count=Count('id')
            ).order_by('appointment_date')
            date_counts = {
                item['appointment_date']: item['patient_count'] 
                for item in appointments_by_date
            }
            last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
            weekly_data = [
                {
                    'date': day.strftime('%Y-%m-%d'),
                    'day_name': day.strftime('%a'),
                    'day_short': day.strftime('%d %b'),
                    'patient_count': date_counts.get(day, 0)
                }
                for day in last_7_days
            ]
            
            total_week = sum(date_counts.values())
            
            return Response({
                'weekly_stats': weekly_data,
                'total_week': total_week
            }, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )