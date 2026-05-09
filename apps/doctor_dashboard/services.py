from django.db import transaction
from Authapi.models import Doctor

@transaction.atomic
def update_doctor_profile(*, doctor: Doctor, data: dict) -> Doctor:
    editable_fields = [
        'first_name', 'last_name', 
        'phone_number', 'alternate_phone_number', 'alternate_email',
        'address', 'city', 'state', 'pincode', 'country',
        'marital_status', 'qualification', 'years_of_experience',
        'department', 'clinic_name', 'emergency_contact_person',
        'emergency_contact_number'
    ]
    
    # Filter only editable fields
    filtered_data = {
        key: value for key, value in data.items() 
        if key in editable_fields
    }
    
    # Update Doctor model fields (those that are direct attributes)
    # Note: first_name and last_name are usually on the User model in a custom setup,
    # but looking at the serializers, they might be on Doctor or handled via User.
    # In DoctorCompleteProfileSerializer, it looks like they are handled.
    
    from .serializers import DoctorCompleteProfileSerializer
    serializer = DoctorCompleteProfileSerializer(
        doctor, 
        data=filtered_data, 
        partial=True
    )
    serializer.is_valid(raise_exception=True)
    updated_doctor = serializer.save()
    
    return updated_doctor
