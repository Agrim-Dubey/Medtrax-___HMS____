from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Avg, Count
from appointments.models import Appointment
from .models import DoctorReview, PatientVisit
from datetime import timedelta

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats(request):

    user = request.user

    if user.role != 'doctor':
        return Response({
            'error': 'Only doctors can access this endpoint'
        }, status=403)

    try:
        doctor = user.doctor_profile
    except Exception as e:
        return Response({
            'error': 'Doctor profile not found'
        }, status=404)

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_upcoming_appointments(request):

    user = request.user
 
    if user.role != 'doctor':
        return Response({
            'error': 'Only doctors can access this endpoint'
        }, status=403)
 
    try:
        doctor = user.doctor_profile
    except:
        return Response({
            'error': 'Doctor profile not found'
        }, status=404)

    today = timezone.now().date()

    appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today,
        status__in=['pending', 'confirmed']
    ).select_related('patient', 'patient__user').order_by('appointment_time')

    appointments_data = []
    for apt in appointments:
        appointments_data.append({
            'id': apt.id,
            'patient_name': apt.patient.get_full_name(),
            'patient_age': calculate_age(apt.patient.date_of_birth),
            'patient_gender': apt.patient.get_gender_display(),
            'patient_phone': apt.patient.phone_number,
            'appointment_time': apt.appointment_time.strftime('%I:%M %p'),
            'reason': apt.reason or 'General Checkup',
            'status': apt.status,
            'patient_blood_group': apt.patient.blood_group,
        })
    
    return Response({
        'count': len(appointments_data),
        'appointments': appointments_data
    }, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_reviews(request):

    
    user = request.user

    if user.role != 'doctor':
        return Response({
            'error': 'Only doctors can access this endpoint'
        }, status=403)

    try:
        doctor = user.doctor_profile
    except:
        return Response({
            'error': 'Doctor profile not found'
        }, status=404)
    

    reviews = DoctorReview.objects.filter(
        doctor=doctor
    ).select_related('patient').order_by('-created_at')[:5]

    reviews_data = []
    for review in reviews:
        reviews_data.append({
            'id': review.id,
            'patient_name': review.patient.get_full_name(),
            'rating': review.rating,
            'comment': review.comment,
            'date': review.created_at.strftime('%B %d, %Y'),
            'time_ago': get_time_ago(review.created_at),
        })
    
    return Response({
        'count': len(reviews_data),
        'reviews': reviews_data
    }, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_weekly_patient_stats(request):
    """
    Returns patient visit count for last 7 days (for graph)
    """
    
    user = request.user

    if user.role != 'doctor':
        return Response({
            'error': 'Only doctors can access this endpoint'
        }, status=403)

    try:
        doctor = user.doctor_profile
    except:
        return Response({
            'error': 'Doctor profile not found'
        }, status=404)

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
    }, status=200)


def calculate_age(birth_date):
    """Calculate age from birth date"""
    today = timezone.now().date()
    age = today.year - birth_date.year

    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age


def get_time_ago(datetime_obj):
    now = timezone.now()
    diff = now - datetime_obj
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"