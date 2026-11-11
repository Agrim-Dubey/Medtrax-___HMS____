"""
Clinical Triage Rules & Specialization Mapping Knowledge Base.
"""

EMERGENCY_RED_FLAGS = [
    {
        "category": "CARDIAC_EMERGENCY",
        "keywords": [
            "chest pain",
            "crushing chest",
            "chest pressure",
            "pain radiating to arm",
            "pain radiating to jaw",
        ],
        "explanation": "Chest pain or pressure may indicate acute coronary syndrome or another life-threatening cardiac event.",
        "immediate_action": "Call emergency services (911/112) or go to the nearest emergency department immediately. Do not drive yourself.",
    },
    {
        "category": "RESPIRATORY_ANAPHYLAXIS",
        "keywords": [
            "cannot breathe",
            "severe shortness of breath",
            "difficulty breathing",
            "throat swelling",
            "tongue swelling",
            "lips swelling",
            "anaphylaxis",
            "coughing up blood",
            "blue lips",
        ],
        "explanation": "Acute airway compromise, severe dyspnea, or hemoptysis requires immediate emergency stabilization.",
        "immediate_action": "Seek emergency medical attention immediately. Use prescribed epinephrine auto-injector if anaphylaxis is suspected.",
    },
    {
        "category": "NEUROLOGICAL_STROKE",
        "keywords": [
            "facial droop",
            "slurred speech",
            "one-sided weakness",
            "sudden numbness",
            "loss of consciousness",
            "fainted",
            "seizure",
            "worst headache of my life",
        ],
        "explanation": "Focal neurological deficits, seizures, or sudden severe headache can indicate acute stroke or intracranial emergency.",
        "immediate_action": "Call emergency services immediately; time-critical neurological evaluation is required.",
    },
    {
        "category": "MENTAL_HEALTH_CRISIS",
        "keywords": [
            "suicidal",
            "kill myself",
            "self-harm",
            "self harm",
            "want to die",
            "end my life",
        ],
        "explanation": "Immediate safety and crisis intervention support are required.",
        "immediate_action": "Please contact your local emergency services or a 24/7 crisis helpline (e.g., 988 in US/Canada, 112/KIRAN 1800-599-0019 in India) immediately.",
    },
    {
        "category": "SEVERE_HEMORRHAGE_OR_ABDOMEN",
        "keywords": [
            "vomiting blood",
            "uncontrolled bleeding",
            "severe abdominal pain",
            "black tarry stool",
        ],
        "explanation": "Signs of acute internal hemorrhage or surgical abdomen require urgent hospital evaluation.",
        "immediate_action": "Proceed to the nearest emergency room immediately.",
    },
]

SYMPTOM_SPECIALIZATION_MAP = [
    {
        "specialization": "Cardiology",
        "keywords": ["palpitations", "irregular heartbeat", "rapid pulse", "high blood pressure", "hypertension", "chest tightness", "ankle swelling"],
        "default_urgency": "URGENT",
        "questions": ["Do symptoms worsen with physical exertion?", "Have you checked your blood pressure and pulse today?"],
    },
    {
        "specialization": "Pulmonology",
        "keywords": ["wheezing", "asthma", "persistent cough", "shortness of breath", "bronchitis", "phlegm", "chest congestion"],
        "default_urgency": "URGENT",
        "questions": ["Are you experiencing wheezing or needing your rescue inhaler more often?", "Is the cough productive or dry?"],
    },
    {
        "specialization": "Neurology",
        "keywords": ["migraine", "headache", "vertigo", "dizziness", "tingling", "numbness", "tremor", "memory loss"],
        "default_urgency": "ROUTINE",
        "questions": ["When did the headache or neurological symptoms start?", "Are there visual disturbances or sensitivity to light?"],
    },
    {
        "specialization": "Gastroenterology",
        "keywords": ["stomach pain", "abdominal pain", "nausea", "vomiting", "acid reflux", "heartburn", "diarrhea", "constipation", "bloating"],
        "default_urgency": "ROUTINE",
        "questions": ["Are symptoms related to meals?", "Have you noticed any fever or inability to keep fluids down?"],
    },
    {
        "specialization": "Dermatology",
        "keywords": ["rash", "itching", "hives", "eczema", "acne", "skin lesion", "psoriasis", "blister", "redness"],
        "default_urgency": "ROUTINE",
        "questions": ["Have you started any new medications, soaps, or foods recently?", "Is the rash spreading rapidly or painful?"],
    },
    {
        "specialization": "Orthopedics",
        "keywords": ["joint pain", "knee pain", "back pain", "sprain", "fracture", "arthritis", "shoulder pain", "neck pain", "swollen joint"],
        "default_urgency": "ROUTINE",
        "questions": ["Was there a recent fall, injury, or heavy lifting?", "Are you able to bear weight or move the joint normally?"],
    },
    {
        "specialization": "ENT",
        "keywords": ["sore throat", "ear pain", "sinus", "earache", "tonsils", "nasal congestion", "hoarseness", "hearing loss"],
        "default_urgency": "ROUTINE",
        "questions": ["Do you have a fever or difficulty swallowing?", "How long has the ear or throat discomfort lasted?"],
    },
    {
        "specialization": "Psychiatry",
        "keywords": ["anxiety", "depression", "insomnia", "panic attack", "stress", "mood", "sleep trouble"],
        "default_urgency": "ROUTINE",
        "questions": ["How long have these feelings or sleep difficulties persisted?", "Are they interfering with daily work or relationships?"],
    },
    {
        "specialization": "General Physician",
        "keywords": ["fever", "fatigue", "cold", "flu", "body ache", "weakness", "chills", "malaise", "cough"],
        "default_urgency": "ROUTINE",
        "questions": ["What is your highest recorded temperature?", "Have you been in contact with anyone who is unwell?"],
    },
]
