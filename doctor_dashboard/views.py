from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Avg
from datetime import timedelta
from appointments.models import Appointment
from .models import DoctorReview


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats(request):
  
    user = request.user
    if user.role != 'doctor':
        return Response({'error': 'Only doctors can access this'}, status=403)
    
    try:
        doctor = user.doctor_profile 
    except Exception as e:
        return Response({'error': 'Doctor profile not found'}, status=404)

    today = timezone.now().date()

    total_appointments_today = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today
    ).count()
    
    pending_appointments = Appointment.objects.filter(
        doctor=doctor,
        status='pending'
    ).count()

    reviews = DoctorReview.objects.filter(doctor=doctor)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    data = {
        'doctor_name': doctor.get_full_name(),
        'total_appointments_today': total_appointments_today,
        'pending_appointments': pending_appointments,
        'average_rating': round(avg_rating, 1),
        'total_reviews': reviews.count()
    }

    return Response(data, status=200)