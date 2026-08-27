"""
Drug-Allergy Cross-Reactivity Knowledge Base.
Maps allergen classes to specific medication brand & generic compounds.
"""

ALLERGY_CROSS_REACTIVITY = {
    "penicillin": ["amoxicillin", "ampicillin", "augmentin", "piperacillin", "oxacillin", "penicillin"],
    "sulfa": ["sulfamethoxazole", "bactrim", "septra", "sulfasalazine", "sulfadiazine"],
    "nsaid": ["ibuprofen", "aspirin", "naproxen", "diclofenac", "ketorolac", "celecoxib", "meloxicam"],
    "aspirin": ["aspirin", "ibuprofen", "naproxen", "diclofenac"],
    "codeine": ["codeine", "morphine", "tramadol", "oxycodone", "hydrocodone"],
    "tetracycline": ["doxycycline", "tetracycline", "minocycline"],
    "cephalosporin": ["cephalexin", "cefuroxime", "ceftriaxone", "cefixime"],
    "macrolide": ["azithromycin", "clarithromycin", "erythromycin"],
}
