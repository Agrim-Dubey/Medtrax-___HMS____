"""
Smart Appointment & Follow-Up Assistant AI Agent.
Detects unscheduled prescription follow-ups, checks appointment conflicts,
scans live doctor slots and queue wait times, and prepares pre-visit checklists.
"""
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from ai_agents.core import (
    HybridLLMClient,
    build_agent_metadata,
    is_non_clinical_placeholder,
    sanitize_clinical_text,
)
from appointments.models import Appointment
from appointments.utils import get_available_slots, get_doctor_queue_info
from authentication.models import Doctor, Patient
from prescription.models import Prescription

_APPT_SYSTEM_PROMPT = (
    "You are a smart healthcare scheduling assistant. Given de-identified scheduling "
    "context (follow-up alerts, available slot counts, wait time, and visit reason), "
    "return JSON with keys: 'scheduling_summary' (1-2 helpful sentences) and "
    "'prep_tips' (array of up to 2 short pre-visit preparation tips)."
)


class SmartAppointmentAgent:
    """Recommends optimal appointment slots, detects follow-up gaps, and builds pre-visit checklists."""

    def __init__(self, model_name: str = "smart-appointment-v1.0", llm_client: Optional[HybridLLMClient] = None):
        self.model_name = model_name
        self.llm_client = llm_client or HybridLLMClient()

    def assist(
        self,
        *,
        patient: Patient,
        doctor: Optional[Doctor] = None,
        specialization: str = "",
        preferred_date: Optional[date] = None,
        preferred_time_of_day: str = "any",
        reason: str = "",
    ) -> Dict[str, Any]:
        today = date.today()
        target_date = preferred_date or today
        clean_reason = sanitize_clinical_text(reason, max_length=1000).text if reason else ""
        clean_spec = sanitize_clinical_text(specialization, max_length=100).text if specialization else ""

        # 1. Detect follow-up gaps from recent prescriptions
        follow_up_alerts = self._check_follow_up_alerts(patient=patient, today=today)

        # 2. Check existing upcoming appointments for conflicts
        conflict_warnings = self._check_conflicts(
            patient=patient,
            doctor=doctor,
            target_date=target_date,
        )

        # 3. Resolve candidate doctors
        if doctor is not None:
            candidate_doctors = [doctor]
        else:
            qs = Doctor.objects.filter(user__is_active=True)
            if clean_spec:
                spec_qs = qs.filter(specialization__icontains=clean_spec)
                candidate_doctors = list(spec_qs[:5]) if spec_qs.exists() else list(qs[:5])
            else:
                candidate_doctors = list(qs[:5])

        # 4. Find best available slots (scanning up to 7 days if target_date is full)
        recommended_slots = self._find_recommended_slots(
            doctors=candidate_doctors,
            start_date=target_date,
            preferred_time_of_day=preferred_time_of_day,
        )

        # 5. Pre-visit preparation checklist
        pre_visit_checklist = self._build_pre_visit_checklist(
            patient=patient,
            reason=clean_reason,
        )

        summary = self._build_summary(
            recommended_slots=recommended_slots,
            follow_up_alerts=follow_up_alerts,
            conflict_warnings=conflict_warnings,
            target_date=target_date,
        )

        llm_result = self.llm_client.generate_json(
            system_prompt=_APPT_SYSTEM_PROMPT,
            user_payload={
                "reason": clean_reason,
                "specialization": clean_spec,
                "preferred_date": target_date.isoformat(),
                "preferred_time_of_day": preferred_time_of_day,
                "recommended_doctors_count": len(recommended_slots),
                "follow_up_alerts_count": len(follow_up_alerts),
                "conflict_warnings_count": len(conflict_warnings),
            },
            required_keys=("scheduling_summary", "prep_tips"),
        )
        if llm_result.success and llm_result.data:
            sched_sum = str(llm_result.data.get("scheduling_summary", "")).strip()
            if sched_sum:
                summary = f"{summary} {sched_sum}"
            prep_tips = llm_result.data.get("prep_tips") or []
            if isinstance(prep_tips, list):
                for tip in prep_tips[:2]:
                    if isinstance(tip, str) and tip.strip() and tip.strip() not in pre_visit_checklist:
                        pre_visit_checklist.append(tip.strip())

        return {
            "summary": summary,
            "follow_up_alerts": follow_up_alerts,
            "conflict_warnings": conflict_warnings,
            "recommended_slots": recommended_slots,
            "pre_visit_checklist": pre_visit_checklist,
            "agent_metadata": build_agent_metadata(
                agent_name="MedTrax Smart Appointment Assistant",
                version=self.model_name,
                llm_result=llm_result,
            ),
        }

    def _check_follow_up_alerts(self, *, patient: Patient, today: date) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        upcoming_appts = Appointment.objects.filter(
            patient=patient,
            appointment_date__gte=today,
            status__in=["pending", "confirmed"],
        )

        recent_rxs = (
            Prescription.objects.filter(patient=patient, follow_up_date__isnull=False)
            .select_related("doctor")
            .order_by("-follow_up_date")[:3]
        )
        for rx in recent_rxs:
            has_booked = upcoming_appts.filter(doctor=rx.doctor).exists()
            if has_booked:
                continue
            delta = (rx.follow_up_date - today).days
            if delta < 0:
                urgency = "OVERDUE"
                msg = f"Follow-up with Dr. {rx.doctor.get_full_name()} was due on {rx.follow_up_date.isoformat()}."
            elif delta <= 7:
                urgency = "DUE_SOON"
                msg = f"Follow-up with Dr. {rx.doctor.get_full_name()} is due in {delta} day(s) ({rx.follow_up_date.isoformat()})."
            else:
                urgency = "UPCOMING"
                msg = f"Upcoming follow-up recommended on {rx.follow_up_date.isoformat()} with Dr. {rx.doctor.get_full_name()}."

            alerts.append({
                "doctor_id": rx.doctor_id,
                "doctor_name": f"Dr. {rx.doctor.get_full_name()}",
                "follow_up_date": rx.follow_up_date.isoformat(),
                "urgency": urgency,
                "message": msg,
            })
        return alerts

    def _check_conflicts(
        self,
        *,
        patient: Patient,
        doctor: Optional[Doctor],
        target_date: date,
    ) -> List[str]:
        warnings: List[str] = []
        same_day = Appointment.objects.filter(
            patient=patient,
            appointment_date=target_date,
            status__in=["pending", "confirmed"],
        ).select_related("doctor")

        for appt in same_day:
            time_str = appt.appointment_time.strftime("%H:%M") if appt.appointment_time else ""
            if doctor and appt.doctor_id == doctor.id:
                warnings.append(
                    f"You already have a {appt.status} appointment with Dr. {appt.doctor.get_full_name()} "
                    f"on {target_date.isoformat()} at {time_str}."
                )
            else:
                warnings.append(
                    f"Note: You have another {appt.status} appointment on {target_date.isoformat()} at {time_str} "
                    f"with Dr. {appt.doctor.get_full_name()}."
                )
        return warnings

    def _find_recommended_slots(
        self,
        *,
        doctors: List[Doctor],
        start_date: date,
        preferred_time_of_day: str,
    ) -> List[Dict[str, Any]]:
        recommendations: List[Dict[str, Any]] = []

        for doc in doctors:
            queue = get_doctor_queue_info(doc)
            chosen_date = None
            chosen_slots: List[str] = []
            window_matched = True

            for offset in range(7):
                check_date = start_date + timedelta(days=offset)
                raw_slots = get_available_slots(doc, check_date)
                if not raw_slots:
                    continue

                filtered = self._filter_by_time_of_day(raw_slots, preferred_time_of_day)
                if filtered:
                    chosen_date = check_date
                    chosen_slots = filtered[:5]
                    window_matched = True
                    break
                elif chosen_date is None:
                    chosen_date = check_date
                    chosen_slots = raw_slots[:5]
                    window_matched = False

            if chosen_date and chosen_slots:
                recommendations.append({
                    "doctor_id": doc.id,
                    "doctor_name": f"Dr. {doc.get_full_name()}",
                    "specialization": doc.specialization or "General Physician",
                    "suggested_date": chosen_date.isoformat(),
                    "slots": chosen_slots,
                    "preferred_window_matched": window_matched,
                    "today_queue_count": queue["current_queue_count"],
                    "estimated_wait_minutes": queue["estimated_wait_time"],
                })
        return recommendations

    def _filter_by_time_of_day(self, slots: List[str], window: str) -> List[str]:
        if window == "morning":
            return [s for s in slots if s < "12:00"]
        if window == "afternoon":
            return [s for s in slots if s >= "12:00"]
        return slots

    def _build_pre_visit_checklist(self, *, patient: Patient, reason: str) -> List[str]:
        checklist = [
            "Bring government photo ID and insurance details (if applicable).",
            "Keep a list of current medications and allergies ready for review.",
        ]
        if not is_non_clinical_placeholder(patient.chronic_diseases):
            checklist.append(f"Bring recent monitoring logs relevant to: {patient.chronic_diseases}.")

        recent_labs = (
            Prescription.objects.filter(patient=patient)
            .prefetch_related("lab_tests")
            .order_by("-created_at")
            .first()
        )
        if recent_labs:
            lab_names = [lt.test_name for lt in recent_labs.lab_tests.all()]
            if lab_names:
                checklist.append(f"Carry results for previously ordered lab test(s): {', '.join(lab_names[:3])}.")

        if reason and any(k in reason.lower() for k in ("blood", "fasting", "sugar", "cholesterol", "lipid")):
            checklist.append("Confirm with the clinic whether 8-12 hours fasting is needed before lab draw.")

        return checklist

    def _build_summary(
        self,
        *,
        recommended_slots: List[Dict[str, Any]],
        follow_up_alerts: List[Dict[str, Any]],
        conflict_warnings: List[str],
        target_date: date,
    ) -> str:
        parts = []
        if recommended_slots:
            first = recommended_slots[0]
            parts.append(
                f"Found {len(recommended_slots)} doctor option(s); earliest available slot is "
                f"{first['suggested_date']} at {first['slots'][0]} with {first['doctor_name']}."
            )
        else:
            parts.append(f"No open slots found within 7 days starting {target_date.isoformat()}.")

        if follow_up_alerts:
            parts.append(f"{len(follow_up_alerts)} unscheduled follow-up reminder(s) detected.")
        if conflict_warnings:
            parts.append(f"{len(conflict_warnings)} scheduling conflict note(s) flagged.")
        return " ".join(parts)
