from rest_framework import serializers
from Authapi.models  import Patient
from appointments.models import Appointment

class PatientDashboardSerializer(serializers.ModelSerializer):
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

class DashboardAppointmentSerializer(serializers.ModelSerialzier):
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor_name',
            'appointment_date',
            'appointment_time',
            'reason',
            'status'
        ]
    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

