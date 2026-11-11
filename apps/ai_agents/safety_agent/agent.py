"""
Clinical Safety & Drug-Interaction AI Agent (PharmaGuard AI).
Performs multi-layered pharmacology checks combining deterministic clinical engines
with optional structured LLM evaluation and automatic fallback.
"""
import logging
from typing import Any, Dict, List, Optional

from ai_agents.core import (
    HybridLLMClient,
    PromptInjectionError,
    build_agent_metadata,
    calculate_age,
    is_non_clinical_placeholder,
    sanitize_clinical_text,
)
from authentication.models import Patient
from prescription.models import Prescription

from .rules_engine import (
    check_allergy_conflicts,
    check_disease_contraindications,
    check_drug_drug_interactions,
)

logger = logging.getLogger(__name__)

_SAFETY_SYSTEM_PROMPT = (
    "You are PharmaGuard, a clinical pharmacology decision-support assistant. "
    "Given de-identified patient allergies, chronic conditions, proposed medications, "
    "and deterministic rule findings, return JSON with keys: "
    "'clinical_note' (1-2 concise sentences for the prescribing physician) and "
    "'extra_precautions' (array of up to 3 short clinical monitoring tips)."
)


class ClinicalSafetyAgent:
    """
    Autonomous clinical safety verification agent for proposed prescriptions.
    Cross-checks patient allergies, chronic diseases, active medications, and DDIs.
    """

    def __init__(self, model_name: str = "clinical-safety-v1.1", llm_client: Optional[HybridLLMClient] = None):
        self.model_name = model_name
        self.llm_client = llm_client or HybridLLMClient()

    def evaluate_prescription(
        self,
        *,
        patient: Patient,
        proposed_medications: List[Dict[str, Any]],
        diagnosis: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end clinical safety evaluation.
        """
        safe_diagnosis = sanitize_clinical_text(diagnosis, max_length=500).text if diagnosis else ""

        cleaned_meds: List[Dict[str, Any]] = []
        seen_names = set()
        duplicate_names = []
        for med in proposed_medications:
            raw_name = med.get("medicine_name", "")
            clean_name = sanitize_clinical_text(raw_name, max_length=200).text
            if not clean_name:
                continue
            lower_name = clean_name.lower()
            if lower_name in seen_names:
                duplicate_names.append(clean_name)
                continue
            seen_names.add(lower_name)
            cleaned_meds.append({**med, "medicine_name": clean_name})

        if not cleaned_meds:
            raise ValueError("At least one valid medication name is required.")

        med_names = [m["medicine_name"] for m in cleaned_meds]
        active_med_names = self._get_active_patient_medications(patient)
        all_medications = list(dict.fromkeys(med_names + active_med_names))

        allergy_conflicts = check_allergy_conflicts(med_names, patient.known_allergies)
        ddi_conflicts = check_drug_drug_interactions(all_medications)
        disease_conflicts = check_disease_contraindications(med_names, patient.chronic_diseases)

        all_interactions = allergy_conflicts + ddi_conflicts + disease_conflicts

        safety_score, risk_level, status = self._calculate_safety_score(all_interactions)

        summary = self._generate_clinical_summary(
            patient=patient,
            med_names=med_names,
            interactions=all_interactions,
            risk_level=risk_level,
            diagnosis=safe_diagnosis,
            duplicate_names=duplicate_names,
        )

        patient_instructions = self._generate_patient_instructions(
            proposed_medications=cleaned_meds,
            interactions=all_interactions,
        )

        llm_result = self.llm_client.generate_json(
            system_prompt=_SAFETY_SYSTEM_PROMPT,
            user_payload={
                "age_years": calculate_age(getattr(patient, "date_of_birth", None)),
                "gender": getattr(patient, "gender", None),
                "allergies": None if is_non_clinical_placeholder(patient.known_allergies) else patient.known_allergies,
                "chronic_diseases": None if is_non_clinical_placeholder(patient.chronic_diseases) else patient.chronic_diseases,
                "diagnosis": safe_diagnosis,
                "proposed_medications": med_names,
                "active_medications": active_med_names,
                "rule_findings_count": len(all_interactions),
                "risk_level": risk_level,
            },
            required_keys=("clinical_note", "extra_precautions"),
        )

        if llm_result.success and llm_result.data:
            extra_note = str(llm_result.data.get("clinical_note", "")).strip()
            if extra_note:
                summary = f"{summary} AI Note: {extra_note}"
            extra_tips = llm_result.data.get("extra_precautions") or []
            if isinstance(extra_tips, list):
                for tip in extra_tips[:3]:
                    if isinstance(tip, str) and tip.strip():
                        patient_instructions.append(tip.strip())

        return {
            "status": status,
            "safety_score": safety_score,
            "risk_level": risk_level,
            "summary": summary,
            "interactions_count": len(all_interactions),
            "interactions": all_interactions,
            "active_medications_checked": active_med_names,
            "patient_instructions": patient_instructions,
            "agent_metadata": build_agent_metadata(
                agent_name="PharmaGuard Clinical Safety Agent",
                version=self.model_name,
                llm_result=llm_result,
            ),
        }

    def _get_active_patient_medications(self, patient: Patient) -> List[str]:
        """Fetches active medication names from the patient's recent prescriptions."""
        active_meds = []
        try:
            recent_prescriptions = (
                Prescription.objects.filter(patient=patient)
                .prefetch_related("medications")
                .order_by("-created_at")[:3]
            )
            for rx in recent_prescriptions:
                for med in rx.medications.all():
                    if med.medicine_name and med.medicine_name.strip():
                        active_meds.append(med.medicine_name.strip())
        except Exception as exc:
            logger.warning("Could not load previous prescriptions for patient %s: %s", patient.id, exc)

        return list(dict.fromkeys(active_meds))

    def _calculate_safety_score(self, interactions: List[Dict[str, Any]]) -> tuple[int, str, str]:
        """Calculates safety score (0-100), risk level, and authorization status."""
        score = 100

        for item in interactions:
            sev = item.get("severity", "LOW")
            if sev == "CRITICAL":
                score -= 40
            elif sev == "HIGH":
                score -= 25
            elif sev == "MODERATE":
                score -= 10
            else:
                score -= 5

        score = max(0, min(100, score))

        if score < 50 or any(i.get("severity") == "CRITICAL" for i in interactions):
            risk_level = "CRITICAL"
            status = "BLOCKED"
        elif score < 75 or any(i.get("severity") == "HIGH" for i in interactions):
            risk_level = "HIGH"
            status = "WARNING"
        elif score < 95 or len(interactions) > 0:
            risk_level = "MODERATE"
            status = "WARNING"
        else:
            risk_level = "LOW"
            status = "APPROVED"

        return score, risk_level, status

    def _generate_clinical_summary(
        self,
        *,
        patient: Patient,
        med_names: List[str],
        interactions: List[Dict[str, Any]],
        risk_level: str,
        diagnosis: Optional[str],
        duplicate_names: Optional[List[str]] = None,
    ) -> str:
        """Constructs an actionable clinical summary for the prescribing doctor."""
        dup_notice = ""
        if duplicate_names:
            dup_notice = f" Duplicate entries deduplicated: {', '.join(duplicate_names)}."

        if not interactions:
            diag_ctx = f" for '{diagnosis}'" if diagnosis else ""
            return (
                f"Clinical safety check verified{diag_ctx}: No drug-drug interactions, known allergy conflicts, "
                f"or disease contraindications detected for {len(med_names)} prescribed medication(s).{dup_notice}"
            )

        critical_count = sum(1 for i in interactions if i.get("severity") == "CRITICAL")
        high_count = sum(1 for i in interactions if i.get("severity") == "HIGH")
        moderate_count = sum(1 for i in interactions if i.get("severity") == "MODERATE")

        issues = []
        if critical_count > 0:
            issues.append(f"{critical_count} CRITICAL contraindication(s)")
        if high_count > 0:
            issues.append(f"{high_count} HIGH risk interaction(s)")
        if moderate_count > 0:
            issues.append(f"{moderate_count} MODERATE interaction(s)")

        allergies_label = "None" if is_non_clinical_placeholder(patient.known_allergies) else patient.known_allergies
        diseases_label = "None" if is_non_clinical_placeholder(patient.chronic_diseases) else patient.chronic_diseases

        return (
            f"SAFETY ALERT ({risk_level}): Detected {', '.join(issues)}. "
            f"Review contraindications carefully before signing this prescription. "
            f"Allergies recorded: '{allergies_label}'. "
            f"Chronic conditions: '{diseases_label}'.{dup_notice}"
        )

    def _generate_patient_instructions(
        self,
        *,
        proposed_medications: List[Dict[str, Any]],
        interactions: List[Dict[str, Any]],
    ) -> List[str]:
        """Generates patient-friendly cautionary instructions based on prescribed medications."""
        instructions = []

        for med in proposed_medications:
            name = med.get("medicine_name", "").lower()

            if any(nsaid in name for nsaid in ["ibuprofen", "aspirin", "naproxen", "diclofenac"]):
                instructions.append(
                    f"Take {med.get('medicine_name')} with food or milk to prevent stomach irritation."
                )
            elif "amoxicillin" in name or "antibiotic" in name:
                instructions.append(
                    f"Complete the full course of {med.get('medicine_name')} even if symptoms improve."
                )
            elif "metformin" in name:
                instructions.append(
                    "Stay well hydrated and report any unexplained fatigue or muscle aches."
                )

        if not instructions:
            instructions.append("Take all medications exactly as directed by your prescribing physician.")

        return instructions
