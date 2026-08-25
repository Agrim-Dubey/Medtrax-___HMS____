from django.db import transaction
from authentication.models import Patient

@transaction.atomic
def update_patient_profile(*, patient: Patient, data: dict) -> Patient:
    editable_fields = [
        'first_name', 'last_name',
        'phone_number', 'emergency_contact', 'emergency_email',
        'city', 'is_insurance', 'ins_company_name', 'ins_policy_number',
        'known_allergies', 'chronic_diseases', 'previous_surgeries',
        'family_medical_history'
    ]
    
    filtered_data = {
        key: value for key, value in data.items() 
        if key in editable_fields
    }
    
    from .serializers import PatientCompleteProfileSerializer
    serializer = PatientCompleteProfileSerializer(
        patient, 
        data=filtered_data, 
        partial=True
    )
    serializer.is_valid(raise_exception=True)
    updated_patient = serializer.save()
    
    return updated_patient
