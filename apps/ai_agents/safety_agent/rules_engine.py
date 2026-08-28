"""
Deterministic Clinical Pharmacology Rules Engine.
Acts as a verified medical baseline for drug-drug, drug-allergy, and drug-disease safety checks.
"""
from typing import List, Dict, Any, Optional
from .rules import (
    ALLERGY_CROSS_REACTIVITY,
    DRUG_DRUG_INTERACTIONS,
    DISEASE_DRUG_CONTRAINDICATIONS,
)


def _normalize_name(name: str) -> str:
    return name.lower().strip() if name else ""


def check_allergy_conflicts(med_names: List[str], patient_allergies: Optional[str]) -> List[Dict[str, Any]]:
    """
    Detects if any proposed medicine matches or cross-reacts with patient allergies.
    """
    conflicts = []
    if not patient_allergies:
        return conflicts

    allergy_tokens = [_normalize_name(a) for a in patient_allergies.replace(";", ",").split(",") if a.strip()]
    normalized_meds = [_normalize_name(m) for m in med_names]

    for allergy in allergy_tokens:
        cross_reactives = ALLERGY_CROSS_REACTIVITY.get(allergy, [allergy])
        for med in normalized_meds:
            if any(cr in med or med in cr for cr in cross_reactives):
                conflicts.append({
                    "type": "ALLERGY_CONFLICT",
                    "severity": "CRITICAL",
                    "drug": med,
                    "conflict_with": allergy,
                    "explanation": f"Patient has documented allergy to '{allergy}'. Prescribing '{med}' poses high risk of severe hypersensitivity/anaphylaxis.",
                    "recommendation": f"Immediately substitute '{med}' with an alternative non-cross-reactive drug class."
                })
    return conflicts


def check_drug_drug_interactions(all_medications: List[str]) -> List[Dict[str, Any]]:
    """
    Evaluates potential pairwise drug-drug interactions between all medications.
    """
    detected = []
    norm_meds = [_normalize_name(m) for m in all_medications]

    for rule in DRUG_DRUG_INTERACTIONS:
        rule_drugs = [_normalize_name(d) for d in rule["drugs"]]
        matches = [d for d in rule_drugs if any(d in m or m in d for m in norm_meds)]
        if len(matches) == len(rule_drugs):
            detected.append({
                "type": "DRUG_DRUG_INTERACTION",
                "severity": rule["severity"],
                "drugs": rule["drugs"],
                "explanation": rule["explanation"],
                "recommendation": rule["recommendation"]
            })
    return detected


def check_disease_contraindications(med_names: List[str], chronic_diseases: Optional[str]) -> List[Dict[str, Any]]:
    """
    Verifies whether proposed drugs are contraindicated for any of the patient's documented chronic conditions.
    """
    contraindications = []
    if not chronic_diseases:
        return contraindications

    disease_text = chronic_diseases.lower()
    norm_meds = [_normalize_name(m) for m in med_names]

    for rule in DISEASE_DRUG_CONTRAINDICATIONS:
        disease_matched = any(kw in disease_text for kw in rule["disease_keywords"])
        if disease_matched:
            for med in norm_meds:
                if any(cd in med or med in cd for cd in rule["contraindicated_drugs"]):
                    contraindications.append({
                        "type": "DISEASE_CONTRAINDICATION",
                        "severity": rule["severity"],
                        "drug": med,
                        "condition": rule["disease_keywords"][0],
                        "explanation": rule["explanation"],
                        "recommendation": rule["recommendation"]
                    })
    return contraindications
