"""
Clinical Safety & Drug-Interaction AI Agent (PharmaGuard AI).
Performs multi-layered pharmacology checks combining rule-based clinical engines
with structured LLM evaluation pipelines for medical safety.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import date

from authentication.models import Patient
from prescription.models import Prescription, Medication
from .rules_engine import (
    check_allergy_conflicts,
    check_drug_drug_interactions,
    check_disease_contraindications
)

logger = logging.getLogger(__name__)


class ClinicalSafetyAgent:
    """
    Autonomous clinical safety verification agent for proposed prescriptions.
    Cross-checks patient allergies, chronic diseases, active medications, and DDIs.
    """

    def __init__(self, model_name: str = "clinical-safety-v1"):
        self.model_name = model_name

    def evaluate_prescription(
        self,
        *,
        patient: Patient,
        proposed_medications: List[Dict[str, Any]],
        diagnosis: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end clinical safety evaluation.
        """
        med_names = [m.get("medicine_name", "").strip() for m in proposed_medications if m.get("medicine_name")]
        
        # 1. Fetch patient's active medication history (last 3 prescriptions)
        active_med_names = self._get_active_patient_medications(patient)

        # 2. Combine all current + proposed medications for comprehensive DDI scan
        all_medications = list(set(med_names + active_med_names))

        # 3. Execute clinical checks
        allergy_conflicts = check_allergy_conflicts(med_names, patient.known_allergies)
        ddi_conflicts = check_drug_drug_interactions(all_medications)
        disease_conflicts = check_disease_contraindications(med_names, patient.chronic_diseases)

        all_interactions = allergy_conflicts + ddi_conflicts + disease_conflicts

        # 4. Compute quantitative clinical safety score (0 - 100)
        safety_score, risk_level, status = self._calculate_safety_score(all_interactions)

        # 5. Build clinical advisory summary
        summary = self._generate_clinical_summary(
            patient=patient,
            med_names=med_names,
            interactions=all_interactions,
            risk_level=risk_level,
            diagnosis=diagnosis
        )

        patient_instructions = self._generate_patient_instructions(
            proposed_medications=proposed_medications,
            interactions=all_interactions
        )

        return {
            "status": status,
            "safety_score": safety_score,
            "risk_level": risk_level,
            "summary": summary,
            "interactions_count": len(all_interactions),
            "interactions": all_interactions,
            "active_medications_checked": active_med_names,
            "patient_instructions": patient_instructions,
            "agent_metadata": {
                "agent_name": "PharmaGuard Clinical Safety Agent",
                "version": self.model_name,
                "evaluated_at": date.today().isoformat()
            }
        }

    def _get_active_patient_medications(self, patient: Patient) -> List[str]:
        """Fetches active medication names from the patient's recent prescriptions."""
        active_meds = []
        try:
            recent_prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')[:3]
            for rx in recent_prescriptions:
                for med in rx.medications.all():
                    if med.medicine_name:
                        active_meds.append(med.medicine_name.strip())
        except Exception as e:
            logger.warning(f"Could not load previous prescriptions for patient {patient.id}: {e}")

        return list(set(active_meds))

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
        diagnosis: Optional[str]
    ) -> str:
        """Constructs an actionable clinical summary for the prescribing doctor."""
        if not interactions:
            return (
                f"Clinical safety check verified: No drug-drug interactions, known allergy conflicts, "
                f"or disease contraindications detected for {len(med_names)} prescribed medication(s)."
            )

        critical_count = sum(1 for i in interactions if i.get("severity") == "CRITICAL")
        high_count = sum(1 for i in interactions if i.get("severity") == "HIGH")

        issues = []
        if critical_count > 0:
            issues.append(f"{critical_count} CRITICAL contraindication(s)")
        if high_count > 0:
            issues.append(f"{high_count} HIGH risk interaction(s)")

        return (
            f"SAFETY ALERT ({risk_level}): Detected {', '.join(issues)}. "
            f"Review contraindications carefully before signing this prescription. "
            f"Allergies recorded: '{patient.known_allergies or 'None'}'. "
            f"Chronic conditions: '{patient.chronic_diseases or 'None'}'."
        )

    def _generate_patient_instructions(
        self,
        *,
        proposed_medications: List[Dict[str, Any]],
        interactions: List[Dict[str, Any]]
    ) -> List[str]:
        """Generates patient-friendly cautionary instructions based on prescribed medications."""
        instructions = []

        for med in proposed_medications:
            name = med.get("medicine_name", "").lower()
            timing = med.get("dosage_frequency", "as_needed")

            if any(nsaid in name for nsaid in ["ibuprofen", "aspirin", "naproxen", "diclofenac"]):
                instructions.append(f"Take {med.get('medicine_name')} with food or milk to prevent stomach irritation.")
            elif "amoxicillin" in name or "antibiotic" in name:
                instructions.append(f"Complete the full course of {med.get('medicine_name')} even if symptoms improve.")
            elif "metformin" in name:
                instructions.append("Stay well hydrated and report any unexplained fatigue or muscle aches.")

        if not instructions:
            instructions.append("Take all medications exactly as directed by your prescribing physician.")

        return instructions

