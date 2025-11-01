from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta, date
from appointments.models import Appointment
from .models import DoctorReview
from .serializers import (
    DoctorDashboardProfileSerializer,
    DashboardAppointmentSerializer,
    DoctorReviewSerializer
)


class DoctorDashboardProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
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


class DoctorWeeklyStatsView(APIView):

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            today = timezone.now().date()
            last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
            
            weekly_data = []
            for day in last_7_days:
                count = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=day,
                    status='completed'
                ).count()
                
                weekly_data.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'day_name': day.strftime('%a'),
                    'day_short': day.strftime('%d %b'),
                    'patient_count': count
                })
            
            return Response({
                'weekly_stats': weekly_data,
                'total_week': sum(item['patient_count'] for item in weekly_data)
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