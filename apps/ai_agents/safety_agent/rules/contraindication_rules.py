"""
Disease-Drug Contraindication Knowledge Base.
Contains conditions and contraindicated drugs with physiological rationale.
"""

DISEASE_DRUG_CONTRAINDICATIONS = [
    {
        "disease_keywords": ["asthma", "copd", "bronchospasm"],
        "contraindicated_drugs": ["propranolol", "timolol", "atenolol", "metoprolol", "carvedilol"],
        "severity": "CRITICAL",
        "explanation": "Non-cardioselective beta-blockers trigger potent bronchoconstriction and life-threatening asthma exacerbation.",
        "recommendation": "Use cardioselective beta-blockers with extreme caution or switch to calcium channel blockers."
    },
    {
        "disease_keywords": ["kidney", "renal", "ckd", "renal failure"],
        "contraindicated_drugs": ["ibuprofen", "naproxen", "diclofenac", "ketorolac", "nsaid"],
        "severity": "CRITICAL",
        "explanation": "NSAIDs inhibit prostaglandin-mediated afferent arteriolar vasodilation, precipitating acute kidney injury.",
        "recommendation": "Avoid systemic NSAIDs in renal insufficiency; consider topical agents or acetaminophen."
    },
    {
        "disease_keywords": ["peptic ulcer", "gastric ulcer", "gerd", "gastrointestinal bleeding"],
        "contraindicated_drugs": ["aspirin", "ibuprofen", "naproxen", "ketorolac", "prednisone", "dexamethasone"],
        "severity": "HIGH",
        "explanation": "NSAIDs and corticosteroids erode gastric mucosal protective barriers, leading to severe GI ulceration or hemorrhage.",
        "recommendation": "Co-prescribe a proton pump inhibitor (PPI) if therapy is unavoidable, or select COX-2 selective agents."
    },
    {
        "disease_keywords": ["heart failure", "chf"],
        "contraindicated_drugs": ["diltiazem", "verapamil", "ibuprofen"],
        "severity": "HIGH",
        "explanation": "Non-dihydropyridine calcium channel blockers exert negative inotropic effects, and NSAIDs cause fluid retention, worsening heart failure.",
        "recommendation": "Use amlodipine for hypertension; avoid NSAIDs."
    },
]
