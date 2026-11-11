"""
Patient Care Plan & Medication Adherence AI Agent.
Builds daily medication schedules, tracks active vs completed courses, generates
condition-specific lifestyle & monitoring guidance, and highlights follow-ups.
"""
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from ai_agents.core import (
    HybridLLMClient,
    build_agent_metadata,
    calculate_age,
    is_non_clinical_placeholder,
)
from authentication.models import Patient
from prescription.models import Prescription

from .rules import CHRONIC_CONDITION_PLANS, FREQUENCY_TIME_SLOTS

_CARE_PLAN_SYSTEM_PROMPT = (
    "You are a patient care-plan and medication adherence coach. Given de-identified "
    "age, chronic conditions, active medications count, and upcoming follow-ups, return JSON with keys: "
    "'coaching_summary' (2 encouraging, practical sentences) and "
    "'adherence_tips' (array of up to 3 actionable adherence tips)."
)


def _duration_to_days(duration: int, unit: str) -> int:
    if unit == "weeks":
        return duration * 7
    if unit == "months":
        return duration * 30
    return duration


class CarePlanAgent:
    """Generates personalized daily medication schedules and chronic-care adherence plans."""

    def __init__(self, model_name: str = "care-plan-v1.0", llm_client: Optional[HybridLLMClient] = None):
        self.model_name = model_name
        self.llm_client = llm_client or HybridLLMClient()

    def build_care_plan(
        self,
        *,
        patient: Patient,
        prescription: Optional[Prescription] = None,
        reference_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        today = reference_date or date.today()

        if prescription is not None:
            prescriptions = [prescription]
        else:
            prescriptions = list(
                Prescription.objects.filter(patient=patient)
                .prefetch_related("medications", "lab_tests")
                .order_by("-created_at")[:5]
            )

        daily_schedule: Dict[str, List[Dict[str, Any]]] = {
            "morning": [],
            "afternoon": [],
            "evening": [],
            "bedtime": [],
            "as_needed": [],
        }
        active_medications: List[Dict[str, Any]] = []
        completed_medications: List[Dict[str, Any]] = []
        lab_checklist: List[Dict[str, Any]] = []
        follow_ups: List[Dict[str, Any]] = []
        diagnoses: List[str] = []

        for rx in prescriptions:
            if rx.diagnosis:
                diagnoses.append(rx.diagnosis)

            rx_start = rx.created_at.date() if rx.created_at else today

            for med in rx.medications.all():
                total_days = max(1, _duration_to_days(int(med.duration or 1), med.duration_unit or "days"))
                end_date = rx_start + timedelta(days=total_days)
                days_remaining = (end_date - today).days

                med_entry = {
                    "medicine_name": med.medicine_name,
                    "dosage": med.dosage,
                    "frequency": med.frequency,
                    "end_date": end_date.isoformat(),
                    "days_remaining": max(0, days_remaining),
                    "instructions": med.instructions or "",
                }

                if days_remaining >= 0:
                    active_medications.append(med_entry)
                    slots = FREQUENCY_TIME_SLOTS.get(med.frequency, ["morning"])
                    timing_note = ""
                    if med.frequency == "before_meals":
                        timing_note = "Take 30 minutes before meals."
                    elif med.frequency == "after_meals":
                        timing_note = "Take immediately after meals."
                    for slot in slots:
                        daily_schedule[slot].append({
                            "medicine_name": med.medicine_name,
                            "dosage": med.dosage,
                            "timing_note": timing_note or med.instructions or "Take with water.",
                        })
                else:
                    completed_medications.append(med_entry)

            for lt in rx.lab_tests.all():
                lab_checklist.append({
                    "test_name": lt.test_name,
                    "instructions": lt.instructions or "Schedule with laboratory.",
                    "ordered_on": rx_start.isoformat(),
                })

            if rx.follow_up_date:
                delta = (rx.follow_up_date - today).days
                if delta < 0:
                    fu_status = "overdue"
                elif delta <= 3:
                    fu_status = "due_soon"
                else:
                    fu_status = "scheduled"
                follow_ups.append({
                    "follow_up_date": rx.follow_up_date.isoformat(),
                    "status": fu_status,
                    "days_until": delta,
                    "diagnosis": rx.diagnosis,
                })

        # Condition-specific monitoring and lifestyle plans
        combined_conditions = " ".join([
            "" if is_non_clinical_placeholder(patient.chronic_diseases) else str(patient.chronic_diseases),
            " ".join(diagnoses),
        ]).lower()

        condition_guidance: List[Dict[str, Any]] = []
        for plan in CHRONIC_CONDITION_PLANS:
            if any(kw in combined_conditions for kw in plan["keywords"]):
                condition_guidance.append({
                    "condition": plan["condition"],
                    "monitoring": plan["monitoring"],
                    "lifestyle": plan["lifestyle"],
                    "warning_signs": plan["warning_signs"],
                })

        active_count = len(active_medications)
        if active_count >= 4:
            adherence_complexity = "HIGH"
        elif active_count >= 2:
            adherence_complexity = "MODERATE"
        else:
            adherence_complexity = "LOW"

        adherence_tips = self._build_adherence_tips(
            active_count=active_count,
            adherence_complexity=adherence_complexity,
            follow_ups=follow_ups,
        )

        summary = self._build_summary(
            active_count=active_count,
            completed_count=len(completed_medications),
            lab_count=len(lab_checklist),
            follow_ups=follow_ups,
            condition_count=len(condition_guidance),
        )

        llm_result = self.llm_client.generate_json(
            system_prompt=_CARE_PLAN_SYSTEM_PROMPT,
            user_payload={
                "age_years": calculate_age(getattr(patient, "date_of_birth", None)),
                "chronic_diseases": None if is_non_clinical_placeholder(patient.chronic_diseases) else patient.chronic_diseases,
                "active_medications_count": active_count,
                "adherence_complexity": adherence_complexity,
                "conditions_matched": [c["condition"] for c in condition_guidance],
                "pending_labs_count": len(lab_checklist),
            },
            required_keys=("coaching_summary", "adherence_tips"),
        )
        if llm_result.success and llm_result.data:
            coach = str(llm_result.data.get("coaching_summary", "")).strip()
            if coach:
                summary = f"{summary} {coach}"
            llm_tips = llm_result.data.get("adherence_tips") or []
            if isinstance(llm_tips, list):
                for tip in llm_tips[:3]:
                    if isinstance(tip, str) and tip.strip() and tip.strip() not in adherence_tips:
                        adherence_tips.append(tip.strip())

        return {
            "summary": summary,
            "adherence_complexity": adherence_complexity,
            "active_medications_count": active_count,
            "active_medications": active_medications,
            "completed_medications_count": len(completed_medications),
            "daily_schedule": daily_schedule,
            "condition_guidance": condition_guidance,
            "lab_checklist": lab_checklist,
            "follow_ups": follow_ups,
            "adherence_tips": adherence_tips,
            "agent_metadata": build_agent_metadata(
                agent_name="MedTrax Patient Care Plan Agent",
                version=self.model_name,
                llm_result=llm_result,
            ),
        }

    def _build_adherence_tips(
        self,
        *,
        active_count: int,
        adherence_complexity: str,
        follow_ups: List[Dict[str, Any]],
    ) -> List[str]:
        tips: List[str] = []
        if active_count == 0:
            tips.append("No currently active medications found; continue healthy lifestyle monitoring.")
        else:
            tips.append("Link medication times to daily habits (e.g., brushing teeth or meals) to avoid missed doses.")
            if adherence_complexity == "HIGH":
                tips.append("Use a weekly pill organizer and set smartphone reminders for each time slot.")
            tips.append("If you miss a dose, never double the next dose unless explicitly instructed by your doctor.")

        if any(f["status"] == "overdue" for f in follow_ups):
            tips.append("You have an overdue follow-up visit; please book an appointment promptly.")
        return tips

    def _build_summary(
        self,
        *,
        active_count: int,
        completed_count: int,
        lab_count: int,
        follow_ups: List[Dict[str, Any]],
        condition_count: int,
    ) -> str:
        parts = [
            f"Care plan active with {active_count} ongoing medication(s)"
            + (f" ({completed_count} completed course(s))" if completed_count else "")
            + "."
        ]
        if lab_count:
            parts.append(f"{lab_count} diagnostic lab test(s) on your checklist.")
        if follow_ups:
            overdue = sum(1 for f in follow_ups if f["status"] == "overdue")
            if overdue:
                parts.append(f"Attention: {overdue} follow-up date(s) overdue.")
            else:
                parts.append(f"Next follow-up scheduled for {follow_ups[0]['follow_up_date']}.")
        if condition_count:
            parts.append(f"Includes tailored monitoring for {condition_count} chronic condition(s).")
        return " ".join(parts)
