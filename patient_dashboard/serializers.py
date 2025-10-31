from rest_framework import serializers
from Authapi.models  import Patient

class PatientDashboardserializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            'first_name',
            'last_name', 
            'date_of_birth',
            'blood_group',
            'known_allergies',
            'chronic_diseases'
        ]

