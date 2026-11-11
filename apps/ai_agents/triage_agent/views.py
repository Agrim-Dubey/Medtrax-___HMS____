from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from ai_agents.core import PromptInjectionError
from ai_agents.permissions import IsDoctorOrPatient, resolve_authorized_patient
from ai_agents.throttles import AIAgentBurstThrottle, TriageAgentThrottle

from .agent import SymptomTriageAgent
from .serializers import SymptomTriageRequestSerializer, SymptomTriageResponseSerializer


class SymptomTriageView(APIView):
    """
    AI Symptom Triage & Doctor Recommendation Endpoint:
    Evaluates patient symptoms & optional vitals, detects emergency red flags,
    determines urgency level, and matches active doctors by specialization.
    """

    permission_classes = [IsAuthenticated, IsDoctorOrPatient]
    throttle_classes = [AIAgentBurstThrottle, TriageAgentThrottle]

    @swagger_auto_schema(
        operation_summary="Assess Symptoms & Recommend Doctors (Triage AI)",
        operation_description=(
            "Evaluates reported symptoms and vitals for emergency red flags, classifies urgency "
            "(SELF_CARE / ROUTINE / URGENT / EMERGENCY), and recommends matching active doctors."
        ),
        request_body=SymptomTriageRequestSerializer,
        responses={
            200: SymptomTriageResponseSerializer,
            400: "Invalid symptoms, vitals, or unsafe input",
            403: "Unauthorized access to patient data",
            404: "Patient not found",
            429: "Rate limit exceeded",
        },
        tags=["AI Clinical Agents"],
    )
    def post(self, request):
        serializer = SymptomTriageRequestSerializer(data=request.data)
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

        agent = SymptomTriageAgent()
        try:
            result = agent.assess_symptoms(
                patient=patient,
                symptoms=data["symptoms"],
                duration_days=data.get("duration_days"),
                severity=data.get("severity", "moderate"),
                vitals=data.get("vitals"),
                preferred_city=data.get("preferred_city"),
            )
        except (PromptInjectionError, ValueError) as exc:
            return Response(
                {"success": False, "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)
