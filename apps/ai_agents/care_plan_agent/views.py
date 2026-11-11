from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from ai_agents.permissions import IsDoctorOrPatient, resolve_authorized_patient
from ai_agents.throttles import AIAgentBurstThrottle, CarePlanAgentThrottle
from prescription.models import Prescription

from .agent import CarePlanAgent
from .serializers import CarePlanRequestSerializer, CarePlanResponseSerializer


class CarePlanView(APIView):
    """
    AI Patient Care Plan & Medication Adherence Endpoint:
    Builds a personalized daily medication schedule, chronic condition guidance,
    lab checklist, and follow-up tracker.
    """

    permission_classes = [IsAuthenticated, IsDoctorOrPatient]
    throttle_classes = [AIAgentBurstThrottle, CarePlanAgentThrottle]

    @swagger_auto_schema(
        operation_summary="Generate Patient Care Plan & Medication Schedule (CarePlan AI)",
        operation_description=(
            "Generates a time-of-day medication schedule, remaining course durations, "
            "chronic condition monitoring guidance, and lab/follow-up checklists."
        ),
        request_body=CarePlanRequestSerializer,
        responses={
            200: CarePlanResponseSerializer,
            400: "Invalid request parameters",
            403: "Unauthorized access to patient or prescription",
            404: "Patient or prescription not found",
            429: "Rate limit exceeded",
        },
        tags=["AI Clinical Agents"],
    )
    def post(self, request):
        serializer = CarePlanRequestSerializer(data=request.data)
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

        prescription = None
        if data.get("prescription_id"):
            try:
                prescription = (
                    Prescription.objects.prefetch_related("medications", "lab_tests")
                    .get(id=data["prescription_id"])
                )
            except Prescription.DoesNotExist:
                return Response(
                    {"success": False, "error": f"Prescription {data['prescription_id']} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if prescription.patient_id != patient.id:
                return Response(
                    {"success": False, "error": "Prescription does not belong to the authorized patient."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        agent = CarePlanAgent()
        result = agent.build_care_plan(patient=patient, prescription=prescription)
        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)
