"""
Symptom Triage & Doctor Recommendation AI Agent.
Combines clinical red-flag triage, vital-sign thresholds, specialty routing,
live doctor matching, and optional LLM clinical reasoning with deterministic fallback.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Avg, Count

from ai_agents.core import (
    HybridLLMClient,
    build_agent_metadata,
    calculate_age,
    is_non_clinical_placeholder,
    sanitize_clinical_text,
)
from authentication.models import Doctor, Patient

from .rules import EMERGENCY_RED_FLAGS, SYMPTOM_SPECIALIZATION_MAP

logger = logging.getLogger(__name__)

_TRIAGE_SYSTEM_PROMPT = (
    "You are a clinical triage decision-support assistant. Never diagnose definitively. "
    "Given de-identified age, gender, chronic conditions, symptoms, vitals, and deterministic urgency, "
    "return JSON with keys: 'clinical_guidance' (2 concise educational sentences) and "
    "'questions_for_doctor' (array of up to 3 relevant questions the patient should ask)."
)

_URGENCY_RANK = {
    "SELF_CARE": 0,
    "ROUTINE": 1,
    "URGENT": 2,
    "EMERGENCY": 3,
}


class SymptomTriageAgent:
    """Evaluates reported symptoms and vitals to determine urgency and recommend doctors."""

    def __init__(self, model_name: str = "symptom-triage-v1.0", llm_client: Optional[HybridLLMClient] = None):
        self.model_name = model_name
        self.llm_client = llm_client or HybridLLMClient()

    def assess_symptoms(
        self,
        *,
        patient: Optional[Patient],
        symptoms: str,
        duration_days: Optional[int] = None,
        severity: str = "moderate",
        vitals: Optional[Dict[str, Any]] = None,
        preferred_city: Optional[str] = None,
    ) -> Dict[str, Any]:
        clean_symptoms = sanitize_clinical_text(symptoms, max_length=2000).text
        if len(clean_symptoms) < 3:
            raise ValueError("Please provide a clear symptom description of at least 3 characters.")

        symptoms_lower = clean_symptoms.lower()
        vitals = vitals or {}
        age = calculate_age(getattr(patient, "date_of_birth", None)) if patient else None
        chronic = getattr(patient, "chronic_diseases", None) if patient else None

        # 1. Red-flag emergency detection
        red_flags = self._detect_red_flags(symptoms_lower)
        vital_alerts, vital_urgency = self._evaluate_vitals(vitals)

        urgency_level = "ROUTINE"
        if severity == "mild" and (duration_days is None or duration_days <= 3):
            urgency_level = "SELF_CARE"
        elif severity == "severe":
            urgency_level = "URGENT"

        if duration_days is not None and duration_days >= 14 and _URGENCY_RANK[urgency_level] < _URGENCY_RANK["URGENT"]:
            urgency_level = "URGENT"

        if vital_urgency and _URGENCY_RANK[vital_urgency] > _URGENCY_RANK[urgency_level]:
            urgency_level = vital_urgency

        if red_flags:
            urgency_level = "EMERGENCY"

        # Pediatric / elderly / chronic risk escalation
        risk_factors: List[str] = []
        if age is not None and (age < 5 or age >= 65):
            risk_factors.append(f"Age risk group ({age} years)")
            if urgency_level == "SELF_CARE":
                urgency_level = "ROUTINE"
        if not is_non_clinical_placeholder(chronic):
            risk_factors.append(f"Documented chronic conditions: {chronic}")
            if urgency_level == "SELF_CARE" and severity != "mild":
                urgency_level = "ROUTINE"

        # 2. Specialization matching
        specializations, matched_questions = self._match_specializations(symptoms_lower, age=age)

        # 3. Query live doctors from MedTrax DB
        recommended_doctors = self._recommend_doctors(
            specializations=specializations,
            preferred_city=preferred_city or (getattr(patient, "city", None) if patient else None),
        )

        seek_immediate_care = urgency_level == "EMERGENCY"
        timeframe_map = {
            "EMERGENCY": "Immediate emergency care (call emergency services or go to ER now)",
            "URGENT": "Within 24 hours (same-day or urgent clinic visit)",
            "ROUTINE": "Within 2-5 days (schedule a standard appointment)",
            "SELF_CARE": "Monitor at home for 48-72 hours; book a visit if symptoms worsen",
        }

        guidance = self._build_deterministic_guidance(
            urgency_level=urgency_level,
            red_flags=red_flags,
            vital_alerts=vital_alerts,
            specializations=specializations,
        )

        questions_for_doctor = matched_questions[:3] or [
            "What warning signs mean I should seek urgent care?",
            "What diagnostic tests or follow-up are recommended?",
        ]

        llm_result = self.llm_client.generate_json(
            system_prompt=_TRIAGE_SYSTEM_PROMPT,
            user_payload={
                "age_years": age,
                "gender": getattr(patient, "gender", None) if patient else None,
                "chronic_diseases": None if is_non_clinical_placeholder(chronic) else chronic,
                "symptoms": clean_symptoms,
                "duration_days": duration_days,
                "severity": severity,
                "vitals": vitals,
                "deterministic_urgency": urgency_level,
                "recommended_specializations": specializations,
            },
            required_keys=("clinical_guidance", "questions_for_doctor"),
        )

        if llm_result.success and llm_result.data:
            llm_guidance = str(llm_result.data.get("clinical_guidance", "")).strip()
            if llm_guidance:
                guidance = f"{guidance} {llm_guidance}"
            llm_qs = llm_result.data.get("questions_for_doctor")
            if isinstance(llm_qs, list):
                cleaned_qs = [str(q).strip() for q in llm_qs if isinstance(q, str) and q.strip()]
                if cleaned_qs:
                    questions_for_doctor = cleaned_qs[:3]

        return {
            "urgency_level": urgency_level,
            "seek_immediate_care": seek_immediate_care,
            "recommended_timeframe": timeframe_map[urgency_level],
            "red_flags_detected": red_flags,
            "vital_alerts": vital_alerts,
            "risk_factors": risk_factors,
            "recommended_specializations": specializations,
            "recommended_doctors": recommended_doctors,
            "clinical_guidance": guidance,
            "questions_for_doctor": questions_for_doctor,
            "agent_metadata": build_agent_metadata(
                agent_name="MedTrax Symptom Triage Agent",
                version=self.model_name,
                llm_result=llm_result,
            ),
        }

    def _detect_red_flags(self, symptoms_lower: str) -> List[Dict[str, str]]:
        findings: List[Dict[str, str]] = []
        for rule in EMERGENCY_RED_FLAGS:
            matched_kw = next((kw for kw in rule["keywords"] if kw in symptoms_lower), None)
            if matched_kw:
                findings.append({
                    "category": rule["category"],
                    "matched_symptom": matched_kw,
                    "explanation": rule["explanation"],
                    "immediate_action": rule["immediate_action"],
                })
        return findings

    def _evaluate_vitals(self, vitals: Dict[str, Any]) -> Tuple[List[str], Optional[str]]:
        alerts: List[str] = []
        highest_urgency: Optional[str] = None

        def bump(level: str) -> None:
            nonlocal highest_urgency
            if highest_urgency is None or _URGENCY_RANK[level] > _URGENCY_RANK[highest_urgency]:
                highest_urgency = level

        spo2 = vitals.get("spo2")
        if spo2 is not None:
            if spo2 < 90:
                alerts.append(f"Critically low oxygen saturation (SpO2: {spo2}%).")
                bump("EMERGENCY")
            elif spo2 < 94:
                alerts.append(f"Borderline low oxygen saturation (SpO2: {spo2}%).")
                bump("URGENT")

        temp_f = vitals.get("temperature_f")
        if temp_f is not None:
            if temp_f >= 104.0:
                alerts.append(f"Very high fever ({temp_f}°F) requiring immediate medical evaluation.")
                bump("EMERGENCY")
            elif temp_f >= 100.4:
                alerts.append(f"Elevated fever ({temp_f}°F).")
                bump("URGENT")
            elif temp_f < 95.0:
                alerts.append(f"Hypothermic reading ({temp_f}°F).")
                bump("EMERGENCY")

        hr = vitals.get("heart_rate")
        if hr is not None:
            if hr >= 130 or hr <= 40:
                alerts.append(f"Critical heart rate ({hr} bpm).")
                bump("EMERGENCY")
            elif hr > 100 or hr < 55:
                alerts.append(f"Abnormal heart rate ({hr} bpm).")
                bump("URGENT")

        bp = vitals.get("blood_pressure")
        if bp and "/" in str(bp):
            try:
                sys_str, dia_str = str(bp).split("/", 1)
                systolic, diastolic = int(sys_str), int(dia_str)
                if systolic >= 180 or diastolic >= 120:
                    alerts.append(f"Hypertensive crisis range BP ({systolic}/{diastolic} mmHg).")
                    bump("EMERGENCY")
                elif systolic < 85 or diastolic < 55:
                    alerts.append(f"Hypotensive BP reading ({systolic}/{diastolic} mmHg).")
                    bump("EMERGENCY")
                elif systolic >= 140 or diastolic >= 90:
                    alerts.append(f"Elevated blood pressure ({systolic}/{diastolic} mmHg).")
                    bump("URGENT")
            except ValueError:
                pass

        return alerts, highest_urgency

    def _match_specializations(self, symptoms_lower: str, *, age: Optional[int]) -> Tuple[List[str], List[str]]:
        matched_specs: List[str] = []
        questions: List[str] = []

        if age is not None and age < 18:
            matched_specs.append("Pediatrics")

        for entry in SYMPTOM_SPECIALIZATION_MAP:
            if any(kw in symptoms_lower for kw in entry["keywords"]):
                spec = entry["specialization"]
                if spec not in matched_specs:
                    matched_specs.append(spec)
                for q in entry["questions"]:
                    if q not in questions:
                        questions.append(q)

        if not matched_specs:
            matched_specs.append("General Physician")

        return matched_specs[:3], questions

    def _recommend_doctors(
        self,
        *,
        specializations: List[str],
        preferred_city: Optional[str],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        qs = (
            Doctor.objects.filter(user__is_active=True)
            .annotate(avg_rating=Avg("reviews__rating"), review_count=Count("reviews"))
        )

        candidates = list(qs)
        if not candidates:
            return []

        spec_lower = [s.lower() for s in specializations]
        city_lower = preferred_city.lower().strip() if preferred_city else ""

        def score_doctor(doc: Doctor) -> Tuple[int, int, float, int]:
            doc_spec = (doc.specialization or "").lower()
            spec_match = 0
            for idx, s in enumerate(spec_lower):
                if s in doc_spec or doc_spec in s and doc_spec:
                    spec_match = len(spec_lower) - idx
                    break
            if spec_match == 0 and "general" in doc_spec:
                spec_match = 1
            city_match = 1 if (city_lower and doc.city and city_lower in doc.city.lower()) else 0
            rating = float(doc.avg_rating or 0.0)
            exp = int(doc.years_of_experience or 0)
            return (spec_match, city_match, rating, exp)

        ranked = sorted(candidates, key=score_doctor, reverse=True)
        matched_only = [d for d in ranked if score_doctor(d)[0] > 0]
        selected = matched_only[:limit] if matched_only else ranked[:limit]

        return [
            {
                "doctor_id": doc.id,
                "name": f"Dr. {doc.get_full_name()}",
                "specialization": doc.specialization or "General Physician",
                "city": doc.city,
                "years_of_experience": doc.years_of_experience,
                "average_rating": round(float(doc.avg_rating), 1) if doc.avg_rating is not None else None,
                "review_count": doc.review_count,
            }
            for doc in selected
        ]

    def _build_deterministic_guidance(
        self,
        *,
        urgency_level: str,
        red_flags: List[Dict[str, str]],
        vital_alerts: List[str],
        specializations: List[str],
    ) -> str:
        if urgency_level == "EMERGENCY":
            action = red_flags[0]["immediate_action"] if red_flags else "Proceed to the nearest emergency room immediately."
            return f"EMERGENCY ALERT: Potential high-risk symptoms or critical vitals detected. {action}"
        if urgency_level == "URGENT":
            return (
                f"Urgent clinical review recommended within 24 hours with {', '.join(specializations)}. "
                f"{' '.join(vital_alerts)} Seek emergency care if breathing worsens, chest pain develops, or fever spikes."
            ).strip()
        if urgency_level == "SELF_CARE":
            return (
                f"Symptoms currently appear mild. Rest, stay hydrated, and consider consulting a "
                f"{specializations[0]} if symptoms persist beyond 72 hours or worsen."
            )
        return (
            f"Recommended consultation with {', '.join(specializations)} within 2-5 days for proper physical "
            f"examination and diagnosis."
        )
