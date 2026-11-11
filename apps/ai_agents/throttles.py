"""
Per-agent DRF rate limiting throttles with resilient in-memory fallback when Redis is unavailable.
"""
import logging

from django.core.cache.backends.locmem import LocMemCache
from rest_framework.throttling import UserRateThrottle

logger = logging.getLogger(__name__)

_LOCAL_THROTTLE_CACHE = LocMemCache("ai_agents_throttle_fallback", {})


class ResilientUserRateThrottle(UserRateThrottle):
    """
    UserRateThrottle that falls back to a local in-memory cache if the primary
    Redis cache backend is temporarily unreachable, preventing 500s while still
    enforcing rate limits.
    """

    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as exc:
            logger.warning(
                "Primary throttle cache unavailable for %s (%s); using local fallback.",
                self.scope,
                type(exc).__name__,
            )
            self.cache = _LOCAL_THROTTLE_CACHE
            return super().allow_request(request, view)


class AIAgentBurstThrottle(ResilientUserRateThrottle):
    scope = "ai_burst"


class SafetyAgentThrottle(ResilientUserRateThrottle):
    scope = "ai_safety"


class TriageAgentThrottle(ResilientUserRateThrottle):
    scope = "ai_triage"


class SummarizerAgentThrottle(ResilientUserRateThrottle):
    scope = "ai_summarizer"


class CarePlanAgentThrottle(ResilientUserRateThrottle):
    scope = "ai_care_plan"


class AppointmentAgentThrottle(ResilientUserRateThrottle):
    scope = "ai_appointment"
