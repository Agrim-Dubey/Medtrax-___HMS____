from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Appointment
from .serializers import (
    AppointmentSerializer,
    AppointmentRequestSerializer,
    DoctorAppointmentListSerializer
)
from Authapi.models import Doctor
from datetime import datetime
from .utils import get_available_slots
from appointments.throttles import AppointmentBookingThrottle, AppointmentActionsThrottle, DashboardThrottle
from .selectors import (
    get_patient_appointments, get_doctor_pending_requests, get_available_doctors,
    get_doctor_dashboard_stats, get_patient_dashboard_stats, get_patient_upcoming_appointments,
    get_patient_recent_appointments, get_doctor_all_appointments
)
from .services import (
    create_appointment_request, accept_appointment_request, reject_appointment_request
)

class PatientBookAppointmentView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AppointmentBookingThrottle]
    @swagger_auto_schema(
        operation_summary="Book a new appointment",
        operation_description="Allows a patient to book an appointment with a doctor",
        request_body=AppointmentRequestSerializer,
        responses={
            201: openapi.Response(
                description="Appointment created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            example="Appointment request sent successfully"
                        ),
                        'appointment': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Appointment details"
                        )
                    }
                )
            ),
            400: openapi.Response(description="Bad request - validation errors"),
            403: openapi.Response(description="Only patients can book appointments")
        },
        tags=['Patient Appointments']
    )
    def post(self, request):
        try:
            patient = request.user.patient_profile
            
            # create_appointment_request service handles validation and creation
            from rest_framework.exceptions import ValidationError
            try:
                appointment = create_appointment_request(patient=patient, data=request.data)
            except ValidationError as e:
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
                
            return Response(
                {
                    "message": "Appointment request sent successfully",
                    "appointment": AppointmentSerializer(appointment).data
                },
                status=status.HTTP_201_CREATED
            )
            
        except AttributeError:
            return Response(
                {"error": "Only patients can book appointments"},
                status=status.HTTP_403_FORBIDDEN
            )


class PatientAppointmentListView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Get patient's appointments",
        operation_description="Retrieve all appointments for the authenticated patient",
        responses={
            200: AppointmentSerializer(many=True),
            403: openapi.Response(description="Only patients can access this endpoint")
        },
        tags=['Patient Appointments']
    )
    def get(self, request):
        try:
            patient = request.user.patient_profile
            appointments = get_patient_appointments(patient=patient)
            
            serializer = AppointmentSerializer(appointments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only patients can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )


class DoctorAppointmentRequestsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get pending appointment requests",
        operation_description="Retrieve all pending appointment requests for the authenticated doctor",
        responses={
            200: DoctorAppointmentListSerializer(many=True),
            403: openapi.Response(description="Only doctors can access this endpoint")
        },
        tags=['Doctor Appointments']
    )
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            today = timezone.now().date()
            
            requests = get_doctor_pending_requests(doctor=doctor, date=today)
            
            serializer = DoctorAppointmentListSerializer(requests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )


class DoctorAcceptAppointmentView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AppointmentActionsThrottle]
    @swagger_auto_schema(
        operation_summary="Accept appointment request",
        operation_description="Doctor accepts a pending appointment request",
        manual_parameters=[
            openapi.Parameter(
                'appointment_id',
                openapi.IN_PATH,
                description="ID of the appointment to accept",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Appointment accepted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            example="Appointment accepted successfully"
                        ),
                        'appointment': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Updated appointment details"
                        )
                    }
                )
            ),
            403: openapi.Response(description="Only doctors can accept appointments"),
            404: openapi.Response(description="Appointment not found")
        },
        tags=['Doctor Appointments']
    )
    def patch(self, request, appointment_id):
        try:
            doctor = request.user.doctor_profile
            
            from django.http import Http404
            try:
                appointment = accept_appointment_request(appointment_id=appointment_id, doctor=doctor)
            except Http404:
                return Response(
                    {"error": "Appointment not found"},
                    status=status.HTTP_404_NOT_FOUND
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
    throttle_classes = [AppointmentActionsThrottle]
    @swagger_auto_schema(
        operation_summary="Reject appointment request",
        operation_description="Doctor rejects a pending appointment request",
        manual_parameters=[
            openapi.Parameter(
                'appointment_id',
                openapi.IN_PATH,
                description="ID of the appointment to reject",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Appointment rejected successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            example="Appointment rejected successfully"
                        ),
                        'appointment': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Updated appointment details"
                        )
                    }
                )
            ),
            403: openapi.Response(description="Only doctors can reject appointments"),
            404: openapi.Response(description="Appointment not found")
        },
        tags=['Doctor Appointments']
    )
    def patch(self, request, appointment_id):
        try:
            doctor = request.user.doctor_profile
            from django.http import Http404
            try:
                appointment = reject_appointment_request(appointment_id=appointment_id, doctor=doctor)
            except Http404:
                return Response(
                    {"error": "Appointment not found"},
                    status=status.HTTP_404_NOT_FOUND
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
    @swagger_auto_schema(
        operation_summary="Get list of available doctors",
        operation_description="Retrieve all active doctors",
        responses={
            200: openapi.Response(
                description="List of available doctors",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            )
        },
        tags=['Doctors']
    )
    def get(self, request):
        from .serializers import DoctorListSerializer
        
        doctors = get_available_doctors()
        
        serializer = DoctorListSerializer(doctors, many=True) 
        return Response(serializer.data, status=status.HTTP_200_OK)


class DoctorAvailableSlotsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get doctor's available time slots",
        operation_description="Retrieve available appointment slots for a specific doctor on a given date",
        manual_parameters=[
            openapi.Parameter(
                'doctor_id',
                openapi.IN_PATH,
                description="ID of the doctor",
                type=openapi.TYPE_INTEGER,
                required=True
            ),
            openapi.Parameter(
                'date',
                openapi.IN_QUERY,
                description="Date for which to fetch available slots (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
                required=True,
                example="2025-11-15"
            )
        ],
        responses={
            200: openapi.Response(
                description="Available slots fetched successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'doctor_id': openapi.Schema(
                            type=openapi.TYPE_INTEGER, 
                            example=1
                        ),
                        'doctor_name': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            example="Dr. John Doe"
                        ),
                        'specialization': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            example="Cardiologist"
                        ),
                        'date': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            example="2025-11-15"
                        ),
                        'available_slots': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="09:00"
                            )
                        ),
                        'total_available': openapi.Schema(
                            type=openapi.TYPE_INTEGER, 
                            example=8
                        )
                    }
                )
            ),
            400: openapi.Response(description="Invalid date format or missing date parameter"),
            404: openapi.Response(description="Doctor not found"),
            500: openapi.Response(description="Internal server error")
        },
        tags=['Doctors']
    )
    def get(self, request, doctor_id):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {"error": "Date parameter is required (format: YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if appointment_date < timezone.now().date():
            return Response(
                {"error": "Cannot book appointments in the past"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            doctor = Doctor.objects.get(id=doctor_id, user__is_active=True)
        except Doctor.DoesNotExist:
            return Response(
                {"error": f"Doctor with ID {doctor_id} not found or inactive"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            available_slots = get_available_slots(doctor, appointment_date)
            
            return Response(
                {
                    "doctor_id": doctor.id,
                    "doctor_name": f"Dr. {doctor.get_full_name()}",
                    "specialization": doctor.specialization,
                    "date": date_str,
                    "available_slots": available_slots,
                    "total_available": len(available_slots)
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            import traceback
            print(f"Error in get_available_slots: {str(e)}")
            print(traceback.format_exc())
            
            return Response(
                {"error": f"Failed to fetch available slots: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [DashboardThrottle]
    @swagger_auto_schema(
        operation_summary="Get doctor dashboard statistics",
        operation_description="Retrieve statistics for doctor's dashboard including total appointments, today's appointments, total patients, and pending requests",
        responses={
            200: openapi.Response(
                description="Dashboard statistics",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_appointments': openapi.Schema(
                            type=openapi.TYPE_INTEGER, 
                            description='Total number of appointments',
                            example=150
                        ),
                        'today_appointments': openapi.Schema(
                            type=openapi.TYPE_INTEGER, 
                            description='Appointments scheduled for today',
                            example=5
                        ),
                        'total_patients': openapi.Schema(
                            type=openapi.TYPE_INTEGER, 
                            description='Total unique patients',
                            example=80
                        ),
                        'pending_requests': openapi.Schema(
                            type=openapi.TYPE_INTEGER, 
                            description='Pending appointment requests',
                            example=3
                        )
                    }
                )
            ),
            403: openapi.Response(description="Only doctors can access this")
        },
        tags=['Doctor Dashboard']
    )
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            today = timezone.now().date()
            
            stats = get_doctor_dashboard_stats(doctor=doctor, date=today)
            
            return Response(stats, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({"error": "Only doctors can access this"}, status=status.HTTP_403_FORBIDDEN)


class PatientDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [DashboardThrottle]
    @swagger_auto_schema(
        operation_summary="Get patient dashboard statistics",
        operation_description="Retrieve statistics for patient's dashboard including total, upcoming, completed, and pending appointments",
        responses={
            200: openapi.Response(
                description="Dashboard statistics",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_appointments': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description='Total number of appointments',
                            example=25
                        ),
                        'upcoming': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description='Upcoming confirmed appointments',
                            example=2
                        ),
                        'completed': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description='Completed appointments',
                            example=20
                        ),
                        'pending': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description='Pending appointment requests',
                            example=3
                        )
                    }
                )
            ),
            403: openapi.Response(description="Only patients can access this")
        },
        tags=['Patient Dashboard']
    )
    def get(self, request):
        try:
            patient = request.user.patient_profile
            today = timezone.now().date()
            
            stats = get_patient_dashboard_stats(patient=patient, date=today)
            
            return Response(stats, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({"error": "Only patients can access this"}, status=status.HTTP_403_FORBIDDEN)


class PatientUpcomingAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get patient's upcoming appointments",
        operation_description="Retrieve the next 5 upcoming confirmed appointments for the patient",
        responses={
            200: openapi.Response(
                description="List of upcoming appointments",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=1
                            ),
                            'doctor_name': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="Dr. John Doe"
                            ),
                            'specialization': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="Cardiologist"
                            ),
                            'date': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="2025-11-15"
                            ),
                            'time': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="09:00"
                            )
                        }
                    )
                )
            ),
            403: openapi.Response(description="Only patients can access this")
        },
        tags=['Patient Dashboard']
    )
    def get(self, request):
        try:
            patient = request.user.patient_profile
            today = timezone.now().date()
            appointments = get_patient_upcoming_appointments(patient=patient, date=today, limit=5)
            
            data = [{
                'id': apt.id,
                'doctor_name': f"Dr. {apt.doctor.get_full_name()}",
                'specialization': apt.doctor.specialization,
                'date': apt.appointment_date.strftime('%Y-%m-%d'),
                'time': apt.appointment_time.strftime('%H:%M')
            } for apt in appointments]
            
            return Response(data, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({"error": "Only patients can access this"}, status=status.HTTP_403_FORBIDDEN)


class PatientRecentAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get patient's recent appointments",
        operation_description="Retrieve the last 5 completed appointments for the patient",
        responses={
            200: openapi.Response(
                description="List of recent appointments",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=1
                            ),
                            'doctor_name': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="Dr. John Doe"
                            ),
                            'specialization': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="Cardiologist"
                            ),
                            'date': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="2025-10-20"
                            ),
                            'status': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="Completed"
                            )
                        }
                    )
                )
            ),
            403: openapi.Response(description="Only patients can access this")
        },
        tags=['Patient Dashboard']
    )
    def get(self, request):
        try:
            patient = request.user.patient_profile
            appointments = get_patient_recent_appointments(patient=patient, limit=5)
            
            data = [{
                'id': apt.id,
                'doctor_name': f"Dr. {apt.doctor.get_full_name()}",
                'specialization': apt.doctor.specialization,
                'date': apt.appointment_date.strftime('%Y-%m-%d'),
                'status': apt.get_status_display()
            } for apt in appointments]
            
            return Response(data, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({"error": "Only patients can access this"}, status=status.HTTP_403_FORBIDDEN)


class DoctorAppointmentsListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get all doctor's appointments",
        operation_description="Retrieve all appointments (past and upcoming) for the authenticated doctor",
        responses={
            200: DoctorAppointmentListSerializer(many=True),
            403: openapi.Response(description="Only doctors can access this endpoint")
        },
        tags=['Doctor Appointments']
    )
    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            appointments = get_doctor_all_appointments(doctor=doctor)
            
            serializer = DoctorAppointmentListSerializer(appointments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
class DoctorQueueInfoView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get doctor's live queue info",
        operation_description="Returns the current queue count and estimated wait time for a given doctor",
        manual_parameters=[
            openapi.Parameter(
                'doctor_id',
                openapi.IN_PATH,
                description="Doctor ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Doctor queue info",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'doctor_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                        'doctor_name': openapi.Schema(type=openapi.TYPE_STRING, example="Dr. John Doe"),
                        'current_queue_count': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                        'estimated_wait_time': openapi.Schema(type=openapi.TYPE_INTEGER, example=90),
                        'current_session': openapi.Schema(type=openapi.TYPE_STRING, example="09:30 - 10:00"),
                    }
                )
            )
        },
        tags=['Doctors']
    )

    def get(self, request, doctor_id):
        from .utils import get_doctor_queue_info
        from Authapi.models import Doctor

        try:
            doctor = Doctor.objects.get(id=doctor_id, user__is_active=True)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=404)

        queue_data = get_doctor_queue_info(doctor)
        return Response({
            "doctor_id": doctor.id,
            "doctor_name": f"Dr. {doctor.get_full_name()}",
            **queue_data
        }, status=200)
