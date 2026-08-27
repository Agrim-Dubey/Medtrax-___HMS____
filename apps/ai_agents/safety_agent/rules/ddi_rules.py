"""
Drug-Drug Interaction (DDI) Clinical Knowledge Base.
Contains critical, high, and moderate interaction rules with pharmacology explanations.
"""

DRUG_DRUG_INTERACTIONS = [
    {
        "drugs": ["warfarin", "aspirin"],
        "severity": "CRITICAL",
        "explanation": "Concurrent use of Warfarin and Aspirin dramatically increases risk of severe internal gastrointestinal and intracranial hemorrhage.",
        "recommendation": "Avoid combination unless explicitly monitored with regular INR checks; consider alternative antiplatelet strategy."
    },
    {
        "drugs": ["warfarin", "ibuprofen"],
        "severity": "CRITICAL",
        "explanation": "NSAIDs competitively inhibit platelet function and can induce gastric mucosal damage while Warfarin impairs clotting factor synthesis.",
        "recommendation": "Use Acetaminophen (Paracetamol) for analgesia instead of NSAIDs."
    },
    {
        "drugs": ["sildenafil", "nitroglycerin"],
        "severity": "CRITICAL",
        "explanation": "PDE5 inhibitors potently amplify the vasodilatory action of nitrates, causing profound and potentially fatal hypotension.",
        "recommendation": "Strictly contraindicated. Do not co-administer nitrates within 24-48 hours of PDE5 inhibitors."
    },
    {
        "drugs": ["lisinopril", "potassium"],
        "severity": "HIGH",
        "explanation": "ACE inhibitors reduce aldosterone secretion, causing potassium retention. Adding potassium supplements can trigger fatal hyperkalemia.",
        "recommendation": "Monitor serum potassium levels closely or discontinue potassium supplementation."
    },
    {
        "drugs": ["tramadol", "sertraline"],
        "severity": "HIGH",
        "explanation": "Both agents elevate synaptic serotonin concentrations. Concurrent use poses a high risk of life-threatening Serotonin Syndrome.",
        "recommendation": "Avoid combination or monitor rigorously for tremors, hyperthermia, and agitation."
    },
    {
        "drugs": ["metformin", "contrast"],
        "severity": "HIGH",
        "explanation": "Iodinated radiocontrast agents can cause acute renal failure, leading to toxic accumulation of Metformin and lactic acidosis.",
        "recommendation": "Temporarily withhold Metformin 48 hours prior to and after contrast imaging."
    },
    {
        "drugs": ["ciprofloxacin", "theophylline"],
        "severity": "MODERATE",
        "explanation": "Ciprofloxacin inhibits the CYP1A2 enzyme, significantly increasing plasma theophylline levels to toxic ranges.",
        "recommendation": "Reduce theophylline dosage by 30-50% and monitor serum levels."
    },
    {
        "drugs": ["simvastatin", "amiodarone"],
        "severity": "HIGH",
        "explanation": "Amiodarone inhibits CYP3A4, causing simvastatin accumulation and increasing the risk of rhabdomyolysis and myopathy.",
        "recommendation": "Limit simvastatin dose to 20mg daily or switch to pravastatin / rosuvastatin."
    },
]
