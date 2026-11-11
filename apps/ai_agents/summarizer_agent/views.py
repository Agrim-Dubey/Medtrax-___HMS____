from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from ai_agents.core import PromptInjectionError
from ai_agents.permissions import IsDoctorOrPatient, get_doctor_profile, get_patient_profile
from ai_agents.throttles import AIAgentBurstThrottle, SummarizerAgentThrottle
from appointments.models import Appointment
from prescription.models import Prescription

from .agent import ClinicalSummarizerAgent
from .serializers import ClinicalSummarizerRequestSerializer, ClinicalSummarizerResponseSerializer


class ClinicalSummarizerView(APIView):
    """
    AI Clinical Note & Prescription Summarizer Endpoint:
    Generates structured SOAP notes for doctors or plain-language patient guides.
    """

    permission_classes = [IsAuthenticated, IsDoctorOrPatient]
    throttle_classes = [AIAgentBurstThrottle, SummarizerAgentThrottle]

    @swagger_auto_schema(
        operation_summary="Summarize Clinical Notes or Prescription (Summarizer AI)",
        operation_description=(
            "Generates a structured SOAP note (doctor-only mode='clinical_soap') or a "
            "plain-language medication/lab guide (mode='patient_friendly')."
        ),
        request_body=ClinicalSummarizerRequestSerializer,
        responses={
            200: ClinicalSummarizerResponseSerializer,
            400: "Validation or input safety error",
            403: "Unauthorized role or ownership violation",
            404: "Prescription or appointment not found",
            429: "Rate limit exceeded",
        },
        tags=["AI Clinical Agents"],
    )
    def post(self, request):
        serializer = ClinicalSummarizerRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        mode = data.get("mode", "clinical_soap")
        doctor = get_doctor_profile(request.user)
        patient = get_patient_profile(request.user)

        if mode == "clinical_soap" and doctor is None:
            return Response(
                {"success": False, "error": "Only authenticated doctors can generate clinical SOAP notes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        prescription = None
        if data.get("prescription_id"):
            try:
                prescription = (
                    Prescription.objects.select_related("doctor", "patient", "appointment")
                    .prefetch_related("medications", "lab_tests")
                    .get(id=data["prescription_id"])
                )
            except Prescription.DoesNotExist:
                return Response(
                    {"success": False, "error": f"Prescription {data['prescription_id']} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if patient is not None and prescription.patient_id != patient.id:
                return Response(
                    {"success": False, "error": "You can only summarize your own prescriptions."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if doctor is not None and prescription.doctor_id != doctor.id:
                return Response(
                    {"success": False, "error": "You can only summarize prescriptions you authored."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        appointment = None
        if data.get("appointment_id"):
            try:
                appointment = Appointment.objects.select_related("doctor", "patient").get(
                    id=data["appointment_id"]
                )
            except Appointment.DoesNotExist:
                return Response(
                    {"success": False, "error": f"Appointment {data['appointment_id']} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if patient is not None and appointment.patient_id != patient.id:
                return Response(
                    {"success": False, "error": "You can only summarize your own appointments."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if doctor is not None and appointment.doctor_id != doctor.id:
                return Response(
                    {"success": False, "error": "You can only summarize your own appointments."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        agent = ClinicalSummarizerAgent()
        try:
            result = agent.summarize(
                mode=mode,
                prescription=prescription,
                appointment=appointment,
                chief_complaint=data.get("chief_complaint", ""),
                clinical_notes=data.get("clinical_notes", ""),
                diagnosis=data.get("diagnosis", ""),
                vitals=data.get("vitals"),
                medications=data.get("medications"),
                lab_tests=data.get("lab_tests"),
                follow_up_date=data.get("follow_up_date"),
            )
        except (PromptInjectionError, ValueError) as exc:
            return Response(
                {"success": False, "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)
