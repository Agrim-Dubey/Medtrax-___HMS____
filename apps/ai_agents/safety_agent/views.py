from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from authentication.models import Patient
from .serializers import (
    ClinicalSafetyCheckRequestSerializer,
    ClinicalSafetyCheckResponseSerializer
)
from .agent import ClinicalSafetyAgent


class ClinicalSafetyCheckView(APIView):
    """
    AI Safety Agent Endpoint:
    Analyzes proposed prescriptions for drug-drug interactions, patient allergy conflicts,
    and chronic disease contraindications before the prescription is finalized.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    @swagger_auto_schema(
        operation_summary="Evaluate Prescription Safety (PharmaGuard AI)",
        operation_description=(
            "Autonomous clinical pharmacology agent that analyzes proposed medications against "
            "the patient's documented allergies, chronic conditions, and recent active prescriptions. "
            "Returns a quantitative safety score (0-100) and actionable clinical warnings."
        ),
        request_body=ClinicalSafetyCheckRequestSerializer,
        responses={
            200: ClinicalSafetyCheckResponseSerializer,
            400: "Invalid payload or medications list",
            404: "Patient not found",
        },
        tags=['AI Clinical Agents']
    )
    def post(self, request):
        serializer = ClinicalSafetyCheckRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        patient_id = data["patient_id"]
        diagnosis = data.get("diagnosis", "")
        medications = data["medications"]

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response(
                {"success": False, "error": f"Patient with ID {patient_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        agent = ClinicalSafetyAgent()
        result = agent.evaluate_prescription(
            patient=patient,
            proposed_medications=medications,
            diagnosis=diagnosis
        )

        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)
