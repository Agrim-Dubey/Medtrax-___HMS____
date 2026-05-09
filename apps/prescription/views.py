from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Prescription
from .serializers import (
    CreatePrescriptionSerializer,
    PrescriptionDetailSerializer,
    PrescriptionListSerializer,
    DoctorPatientListSerializer
)
from Authapi.models import Patient
from appointments.models import Appointment
from .selectors import (
    get_doctor_patients,
    get_doctor_prescriptions,
    get_patient_prescriptions
)
from .services import create_prescription


class DoctorPatientsListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get doctor's patients list",
        operation_description="Retrieve all patients the authenticated doctor has had confirmed/completed appointments with",
        responses={
            200: openapi.Response(
                description="List of patients",
                schema=DoctorPatientListSerializer(many=True)
            ),
            403: openapi.Response(description="Only doctors can access this endpoint")
        },
        tags=['Doctor Prescriptions']
    )

    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            sorted_patients = get_doctor_patients(doctor=doctor)
            
            serializer = DoctorPatientListSerializer(
                sorted_patients,
                many=True,
                context={'doctor': doctor}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )


class CreatePrescriptionView(APIView):

    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
    operation_summary="Create prescription",
    operation_description="Doctor creates a new prescription for a patient they've had appointments with",
    request_body=CreatePrescriptionSerializer,
    responses={
        201: openapi.Response(
            description="Prescription created successfully",
            schema=PrescriptionDetailSerializer()
        ),
        400: openapi.Response(description="Validation error"),
        403: openapi.Response(description="Only doctors can create prescriptions")
    },
    tags=['Doctor Prescriptions']
)

    def post(self, request):
        try:
            doctor = request.user.doctor_profile
            
            from rest_framework.exceptions import ValidationError
            try:
                prescription = create_prescription(doctor=doctor, data=request.data)
                return Response(
                    {
                        "message": "Prescription created successfully",
                        "prescription": PrescriptionDetailSerializer(prescription).data
                    },
                    status=status.HTTP_201_CREATED
                )
            except ValidationError as e:
                return Response(
                    {"errors": e.detail},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can create prescriptions"},
                status=status.HTTP_403_FORBIDDEN
            )


class DoctorPrescriptionsListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
    operation_summary="Get doctor's prescriptions",
    operation_description="Retrieve all prescriptions created by the authenticated doctor",
    manual_parameters=[
        openapi.Parameter(
            'patient_id',
            openapi.IN_QUERY,
            description="Filter by patient ID (optional)",
            type=openapi.TYPE_INTEGER
        )
    ],
    responses={
        200: openapi.Response(
            description="List of prescriptions",
            schema=PrescriptionListSerializer(many=True)
        ),
        403: openapi.Response(description="Only doctors can access this endpoint")
    },
    tags=['Doctor Prescriptions']
)

    def get(self, request):
        try:
            doctor = request.user.doctor_profile
            patient_id = request.query_params.get('patient_id')
            
            prescriptions = get_doctor_prescriptions(doctor=doctor, patient_id=patient_id)
            
            serializer = PrescriptionListSerializer(prescriptions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only doctors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )


class PatientPrescriptionsListView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
    operation_summary="Get patient's prescriptions",
    operation_description="Retrieve all prescriptions for the authenticated patient",
    responses={
        200: openapi.Response(
            description="List of prescriptions",
            schema=PrescriptionListSerializer(many=True)
        ),
        403: openapi.Response(description="Only patients can access this endpoint")
    },
    tags=['Patient Prescriptions']
)

    def get(self, request):
        try:
            patient = request.user.patient_profile
            
            prescriptions = get_patient_prescriptions(patient=patient)
            
            serializer = PrescriptionListSerializer(prescriptions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only patients can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )

class PatientPrescriptionsByDoctorView(APIView):

    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
    operation_summary="Get prescriptions by doctor",
    operation_description="Patient can view all prescriptions from a specific doctor",
    responses={
        200: openapi.Response(
            description="List of prescriptions",
            schema=PrescriptionListSerializer(many=True)
        ),
        403: openapi.Response(description="Only patients can access this endpoint")
    },
    tags=['Patient Prescriptions']
)

    def get(self, request, doctor_id):
        try:
            patient = request.user.patient_profile
            
            prescriptions = get_patient_prescriptions(patient=patient, doctor_id=doctor_id)
            
            serializer = PrescriptionListSerializer(prescriptions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except AttributeError:
            return Response(
                {"error": "Only patients can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )