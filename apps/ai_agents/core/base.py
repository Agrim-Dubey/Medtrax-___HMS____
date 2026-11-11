"""
Shared utilities for AI clinical agent metadata, disclaimers, and patient demographics.
"""
from datetime import date
from typing import Any, Dict, Optional

from .llm_client import LLMResult

MEDICAL_DISCLAIMER = (
    "Clinical decision-support output only. This does not replace professional "
    "medical judgment, physical examination, or emergency care."
)


def calculate_age(dob: Optional[date], reference_date: Optional[date] = None) -> Optional[int]:
    """Safely computes integer age in years from date of birth."""
    if not dob:
        return None
    today = reference_date or date.today()
    if dob > today:
        return 0
    years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return max(0, years)


def build_agent_metadata(
    *,
    agent_name: str,
    version: str,
    llm_result: Optional[LLMResult] = None,
) -> Dict[str, Any]:
    """Builds standardized metadata for every AI clinical agent response."""
    llm_enhanced = bool(llm_result and llm_result.success)
    meta: Dict[str, Any] = {
        "agent_name": agent_name,
        "version": version,
        "mode": "hybrid_llm" if llm_enhanced else "deterministic",
        "llm_enhanced": llm_enhanced,
        "evaluated_at": date.today().isoformat(),
        "disclaimer": MEDICAL_DISCLAIMER,
    }
    if llm_result:
        meta["llm_provider"] = llm_result.provider
        if llm_result.fallback_reason:
            meta["fallback_reason"] = llm_result.fallback_reason
    return meta
