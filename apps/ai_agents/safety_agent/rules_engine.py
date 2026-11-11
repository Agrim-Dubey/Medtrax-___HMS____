"""
Deterministic Clinical Pharmacology Rules Engine.
Acts as a verified medical baseline for drug-drug, drug-allergy, and drug-disease safety checks.
"""
from typing import Any, Dict, List, Optional, Set, Tuple

from ai_agents.core.sanitizer import is_non_clinical_placeholder
from .rules import (
    ALLERGY_CROSS_REACTIVITY,
    DISEASE_DRUG_CONTRAINDICATIONS,
    DRUG_DRUG_INTERACTIONS,
)


def _normalize_name(name: Optional[str]) -> str:
    return name.lower().strip() if name else ""


def _drug_matches(candidate: str, target: str) -> bool:
    """
    Matches drug or allergen keywords safely without false-matching tiny substrings.
    """
    c = _normalize_name(candidate)
    t = _normalize_name(target)
    if len(c) < 3 or len(t) < 3:
        return False
    return c in t or t in c


def check_allergy_conflicts(
    med_names: List[str],
    patient_allergies: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Detects if any proposed medicine matches or cross-reacts with patient allergies.
    Deduplicates identical (drug, allergy) findings.
    """
    conflicts: List[Dict[str, Any]] = []
    if is_non_clinical_placeholder(patient_allergies):
        return conflicts

    allergy_tokens = [
        _normalize_name(a)
        for a in str(patient_allergies).replace(";", ",").split(",")
        if not is_non_clinical_placeholder(a)
    ]
    normalized_meds = list(dict.fromkeys(_normalize_name(m) for m in med_names if len(_normalize_name(m)) >= 3))

    seen: Set[Tuple[str, str]] = set()
    for allergy in allergy_tokens:
        cross_reactives = ALLERGY_CROSS_REACTIVITY.get(allergy, [allergy])
        for med in normalized_meds:
            if any(_drug_matches(cr, med) for cr in cross_reactives):
                key = (med, allergy)
                if key in seen:
                    continue
                seen.add(key)
                conflicts.append({
                    "type": "ALLERGY_CONFLICT",
                    "severity": "CRITICAL",
                    "drug": med,
                    "conflict_with": allergy,
                    "explanation": (
                        f"Patient has documented allergy to '{allergy}'. Prescribing '{med}' "
                        f"poses high risk of severe hypersensitivity/anaphylaxis."
                    ),
                    "recommendation": (
                        f"Immediately substitute '{med}' with an alternative non-cross-reactive drug class."
                    ),
                })
    return conflicts


def check_drug_drug_interactions(all_medications: List[str]) -> List[Dict[str, Any]]:
    """
    Evaluates potential pairwise drug-drug interactions between all medications.
    """
    detected: List[Dict[str, Any]] = []
    norm_meds = list(dict.fromkeys(_normalize_name(m) for m in all_medications if len(_normalize_name(m)) >= 3))
    if len(norm_meds) < 2:
        return detected

    seen_rules: Set[Tuple[str, ...]] = set()
    for rule in DRUG_DRUG_INTERACTIONS:
        rule_drugs = [_normalize_name(d) for d in rule["drugs"]]
        matches = [d for d in rule_drugs if any(_drug_matches(d, m) for m in norm_meds)]
        if len(matches) == len(rule_drugs):
            rule_key = tuple(sorted(rule_drugs))
            if rule_key in seen_rules:
                continue
            seen_rules.add(rule_key)
            detected.append({
                "type": "DRUG_DRUG_INTERACTION",
                "severity": rule["severity"],
                "drugs": rule["drugs"],
                "explanation": rule["explanation"],
                "recommendation": rule["recommendation"],
            })
    return detected


def check_disease_contraindications(
    med_names: List[str],
    chronic_diseases: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Verifies whether proposed drugs are contraindicated for any of the patient's documented chronic conditions.
    """
    contraindications: List[Dict[str, Any]] = []
    if is_non_clinical_placeholder(chronic_diseases):
        return contraindications

    disease_text = str(chronic_diseases).lower()
    norm_meds = list(dict.fromkeys(_normalize_name(m) for m in med_names if len(_normalize_name(m)) >= 3))

    seen: Set[Tuple[str, str]] = set()
    for rule in DISEASE_DRUG_CONTRAINDICATIONS:
        disease_matched = any(kw in disease_text for kw in rule["disease_keywords"])
        if disease_matched:
            condition = rule["disease_keywords"][0]
            for med in norm_meds:
                if any(_drug_matches(cd, med) for cd in rule["contraindicated_drugs"]):
                    key = (med, condition)
                    if key in seen:
                        continue
                    seen.add(key)
                    contraindications.append({
                        "type": "DRUG_DISEASE_CONTRAINDICATION",
                        "severity": rule["severity"],
                        "drug": med,
                        "condition": condition,
                        "explanation": rule["explanation"],
                        "recommendation": rule["recommendation"],
                    })
    return contraindications
