from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from ai_agents.core import HybridLLMClient, MEDICAL_DISCLAIMER
from ai_agents.permissions import IsDoctorOrPatient
from ai_agents.throttles import AIAgentBurstThrottle


class AIAgentsRegistryView(APIView):
    """
    Lists available MedTrax AI clinical agents, their endpoints, required roles,
    and whether hybrid LLM enhancement is active (without exposing secrets).
    """

    permission_classes = [IsAuthenticated, IsDoctorOrPatient]
    throttle_classes = [AIAgentBurstThrottle]

    @swagger_auto_schema(
        operation_summary="List AI Clinical Agents & Status",
        operation_description="Returns metadata and endpoint capabilities for all MedTrax AI agents.",
        responses={200: "Agent catalog"},
        tags=["AI Clinical Agents"],
    )
    def get(self, request):
        llm_client = HybridLLMClient()
        mode = "hybrid_llm" if llm_client.is_configured() else "deterministic"

        agents = [
            {
                "id": "safety_agent",
                "name": "PharmaGuard Clinical Safety Agent",
                "endpoint": "/api/ai/safety-check/",
                "allowed_roles": ["doctor"],
                "rate_limit": "60/hour (15/minute burst)",
                "capabilities": ["drug-drug interactions", "allergy cross-reactivity", "disease contraindications"],
            },
            {
                "id": "triage_agent",
                "name": "MedTrax Symptom Triage Agent",
                "endpoint": "/api/ai/triage/",
                "allowed_roles": ["patient", "doctor"],
                "rate_limit": "30/hour (15/minute burst)",
                "capabilities": ["emergency red-flag detection", "vital sign alerts", "specialist doctor matching"],
            },
            {
                "id": "summarizer_agent",
                "name": "MedTrax Clinical Summarizer Agent",
                "endpoint": "/api/ai/summarize/",
                "allowed_roles": ["doctor", "patient (patient_friendly only)"],
                "rate_limit": "40/hour (15/minute burst)",
                "capabilities": ["SOAP note generation", "abnormal vital flags", "plain-language patient summaries"],
            },
            {
                "id": "care_plan_agent",
                "name": "MedTrax Patient Care Plan Agent",
                "endpoint": "/api/ai/care-plan/",
                "allowed_roles": ["patient", "doctor"],
                "rate_limit": "30/hour (15/minute burst)",
                "capabilities": ["daily medication schedules", "chronic care monitoring", "adherence complexity scoring"],
            },
            {
                "id": "appointment_agent",
                "name": "MedTrax Smart Appointment Assistant",
                "endpoint": "/api/ai/appointment-assistant/",
                "allowed_roles": ["patient", "doctor"],
                "rate_limit": "40/hour (15/minute burst)",
                "capabilities": ["follow-up gap alerts", "live slot & queue recommendations", "pre-visit checklists"],
            },
        ]

        return Response(
            {
                "success": True,
                "data": {
                    "intelligence_mode": mode,
                    "llm_provider": llm_client.provider if llm_client.is_configured() else "none",
                    "agents_count": len(agents),
                    "agents": agents,
                    "disclaimer": MEDICAL_DISCLAIMER,
                },
            },
            status=status.HTTP_200_OK,
        )

