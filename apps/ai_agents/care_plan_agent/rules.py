"""
Condition-Specific Lifestyle, Monitoring, and Medication Scheduling Rules.
"""

FREQUENCY_TIME_SLOTS = {
    "once_daily": ["morning"],
    "twice_daily": ["morning", "evening"],
    "thrice_daily": ["morning", "afternoon", "evening"],
    "four_times_daily": ["morning", "afternoon", "evening", "bedtime"],
    "before_meals": ["morning", "evening"],
    "after_meals": ["morning", "evening"],
    "at_bedtime": ["bedtime"],
    "as_needed": ["as_needed"],
}

CHRONIC_CONDITION_PLANS = [
    {
        "keywords": ["hypertension", "high blood pressure", "bp"],
        "condition": "Hypertension",
        "monitoring": "Measure blood pressure once in the morning and once in the evening; record readings in a log.",
        "lifestyle": [
            "Limit dietary sodium (<2g/day) and avoid heavily processed or salted foods.",
            "Engage in 30 minutes of moderate walking or aerobic activity 5 days per week if cleared by your doctor.",
        ],
        "warning_signs": "Seek immediate care for BP >= 180/120 mmHg, chest pain, severe headache, or vision changes.",
    },
    {
        "keywords": ["diabetes", "diabetic", "blood sugar", "hyperglycemia"],
        "condition": "Diabetes Mellitus",
        "monitoring": "Check fasting and 2-hour post-meal blood glucose as advised by your physician.",
        "lifestyle": [
            "Maintain consistent meal timings and pair complex carbohydrates with fiber and lean protein.",
            "Inspect feet daily for cuts, redness, or swelling and stay well hydrated.",
        ],
        "warning_signs": "Watch for hypoglycemia symptoms (shakiness, sweating, confusion) or persistent glucose > 300 mg/dL.",
    },
    {
        "keywords": ["asthma", "copd", "bronchitis"],
        "condition": "Asthma / Airway Disease",
        "monitoring": "Track rescue inhaler usage frequency and peak flow readings if available.",
        "lifestyle": [
            "Avoid known triggers such as smoke, heavy dust, strong fragrances, and cold dry air.",
            "Always keep your prescribed rescue inhaler accessible.",
        ],
        "warning_signs": "Seek urgent care if rescue inhaler does not relieve wheezing or speaking in full sentences becomes difficult.",
    },
    {
        "keywords": ["kidney", "renal", "ckd"],
        "condition": "Chronic Kidney Disease",
        "monitoring": "Track daily fluid intake, weight changes, and scheduled renal function blood tests.",
        "lifestyle": [
            "Avoid over-the-counter NSAID painkillers (e.g., ibuprofen, naproxen) unless specifically approved by your doctor.",
            "Follow prescribed sodium, potassium, and protein guidance.",
        ],
        "warning_signs": "Report sudden leg/ankle swelling, reduced urine output, or persistent nausea.",
    },
]
