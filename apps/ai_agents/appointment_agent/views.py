from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from ai_agents.core import PromptInjectionError
from ai_agents.permissions import IsDoctorOrPatient, resolve_authorized_patient
from ai_agents.throttles import AIAgentBurstThrottle, AppointmentAgentThrottle
from authentication.models import Doctor

from .agent import SmartAppointmentAgent
from .serializers import (
    AppointmentAssistantRequestSerializer,
    AppointmentAssistantResponseSerializer,
)


class SmartAppointmentAssistantView(APIView):
    """
    AI Smart Appointment & Follow-Up Assistant Endpoint:
    Analyzes unscheduled follow-ups, checks appointment conflicts, finds available
    doctor slots & queue wait times, and generates a pre-visit preparation checklist.
    """

    permission_classes = [IsAuthenticated, IsDoctorOrPatient]
    throttle_classes = [AIAgentBurstThrottle, AppointmentAgentThrottle]

    @swagger_auto_schema(
        operation_summary="Smart Appointment & Follow-Up Assistant (Appointment AI)",
        operation_description=(
            "Finds optimal open slots across doctors, detects overdue/upcoming prescription "
            "follow-ups, checks same-day conflicts, and builds a pre-visit checklist."
        ),
        request_body=AppointmentAssistantRequestSerializer,
        responses={
            200: AppointmentAssistantResponseSerializer,
            400: "Validation error or invalid date",
            403: "Unauthorized access to patient data",
            404: "Doctor or patient not found",
            429: "Rate limit exceeded",
        },
        tags=["AI Clinical Agents"],
    )
    def post(self, request):
        serializer = AppointmentAssistantRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        patient, err_response = resolve_authorized_patient(
            request,
            data.get("patient_id"),
            require_doctor_relationship=True,
        )
        if err_response is not None:
            return err_response

        doctor = None
        if data.get("doctor_id"):
            try:
                doctor = Doctor.objects.get(id=data["doctor_id"], user__is_active=True)
            except Doctor.DoesNotExist:
                return Response(
                    {"success": False, "error": f"Active doctor with ID {data['doctor_id']} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        agent = SmartAppointmentAgent()
        try:
            result = agent.assist(
                patient=patient,
                doctor=doctor,
                specialization=data.get("specialization", ""),
                preferred_date=data.get("preferred_date"),
                preferred_time_of_day=data.get("preferred_time_of_day", "any"),
                reason=data.get("reason", ""),
            )
        except (PromptInjectionError, ValueError) as exc:
            return Response(
                {"success": False, "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)
