from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Appointment
from .serializers import (
    AppointmentSerializer,
    AppointmentRequestSerializer,
    DoctorAppointmentListSerializer
)
from Authapi.models import Doctor
from django_q.tasks import async_task
from datetime import datetime
from .utils import get_available_slots


class PatientBookAppointmentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            patient = request.user.patient_profile
            serializer = AppointmentRequestSerializer(data=request.data)
            
            if serializer.is_valid():
                appointment = serializer.save(patient=patient, status='pending')

                async_task(
                    'appointments.tasks.send_immediate_appointment_notification',
                    appointment.id,
                    'created'
                )
                
                return Response(
                    {
                        "message": "Appointment request sent successfully",
                        "appointment": AppointmentSerializer(appointment).data
                    },
                    status=status.HTTP_201_CREATED
                )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except AttributeError:
            return Response(
                {"error": "Only patients can book appointments"},
                status=status.HTTP_403_FORBIDDEN
            )


class PatientAppointmentListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            patient = request.user.patient_profile
            appointments = Appointment.objects.filter(
                patient=patient
            ).select_related('doctor', 'doctor__user').order_by('-appointment_date')
            
            serializer = AppointmentSerializer(appointments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only patients can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )


class DoctorAppointmentRequestsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            today = timezone.now().date()
            
            requests = Appointment.objects.filter(
                doctor=doctor,
                status='pending',
                appointment_date__gte=today
            ).select_related('patient', 'patient__user').order_by('appointment_date', 'appointment_time')
            
            serializer = DoctorAppointmentListSerializer(requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )


class DoctorAppointmentsListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            today = timezone.now().date()
            
            appointments = Appointment.objects.filter(
                doctor=doctor,
                status__in=['confirmed', 'completed'],
                appointment_date__gte=today
            ).select_related('patient', 'patient__user').order_by('appointment_date', 'appointment_time')
            
            serializer = DoctorAppointmentListSerializer(appointments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )


class DoctorAcceptAppointmentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, appointment_id):
        try:
            doctor = request.user.doctor_profile
            appointment = get_object_or_404(
                Appointment,
                id=appointment_id,
                doctor=doctor,
                status='pending'
            )
            
            appointment.status = 'confirmed'
            appointment.save()
            
            async_task(
                'appointments.tasks.send_immediate_appointment_notification',
                appointment.id,
                'confirmed'
            )
            
            return Response(
                {
                    "message": "Appointment accepted successfully",
                    "appointment": DoctorAppointmentListSerializer(appointment).data
                },
                status=status.HTTP_200_OK
            )
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can accept appointments"},
                status=status.HTTP_403_FORBIDDEN
            )


class DoctorRejectAppointmentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, appointment_id):
        try:
            doctor = request.user.doctor_profile
            appointment = get_object_or_404(
                Appointment,
                id=appointment_id,
                doctor=doctor,
                status='pending'
            )
            
            appointment.status = 'cancelled'
            appointment.save()
            
            async_task(
                'appointments.tasks.send_immediate_appointment_notification',
                appointment.id,
                'cancelled'
            )
            
            return Response(
                {
                    "message": "Appointment rejected successfully",
                    "appointment": DoctorAppointmentListSerializer(appointment).data
                },
                status=status.HTTP_200_OK
            )
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can reject appointments"},
                status=status.HTTP_403_FORBIDDEN
            )


class AvailableDoctorsListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .serializers import DoctorListSerializer
        
        doctors = Doctor.objects.filter(
            user__is_active=True
        ).select_related('user')
        
        serializer = DoctorListSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DoctorAvailableSlotsView(APIView):
        permission_classes = [IsAuthenticated]
        
        def get(self, request, doctor_id):
            """
            Get available time slots for a doctor on a specific date
            
            Query params:
                date: YYYY-MM-DD format (e.g., 2025-11-05)
            """
            try:
                # Get date from query params
                date_str = request.query_params.get('date')
                if not date_str:
                    return Response(
                        {"error": "Date parameter is required (format: YYYY-MM-DD)"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Parse date
                try:
                    appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    return Response(
                        {"error": "Invalid date format. Use YYYY-MM-DD"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
               
                from django.utils import timezone
                if appointment_date < timezone.now().date():
                    return Response(
                        {"error": "Cannot book appointments in the past"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                doctor = get_object_or_404(Doctor, id=doctor_id)
                available_slots = get_available_slots(doctor, appointment_date)
                
                return Response(
                    {
                        "doctor_id": doctor.id,
                        "doctor_name": f"Dr. {doctor.get_full_name()}",
                        "date": date_str,
                        "available_slots": available_slots,
                        "total_available": len(available_slots)
                    },
                    status=status.HTTP_200_OK
                )
                
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )