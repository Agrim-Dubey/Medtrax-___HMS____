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



class PatientBookAppointmentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            patient = request.user.patient_profile
            serializer = AppointmentRequestSerializer(data=request.data)
            
            if serializer.is_valid():
                appointment = serializer.save(patient=patient, status='pending')
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
        from Authapi.serializers import DoctorListSerializer
        
        doctors = Doctor.objects.filter(
            user__is_active=True
        ).select_related('user')
        
        serializer = DoctorListSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
