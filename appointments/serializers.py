from rest_framework import serializers
from .models import Appointment
from Authapi.models import Doctor


class AppointmentRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason']
    
    def validate_appointment_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Cannot book appointments in the past")
        return value


class AppointmentSerializer(serializers.ModelSerializer):

    doctor_name = serializers.SerializerMethodField()
    doctor_specialization = serializers.CharField(source='doctor.specialization', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'doctor_specialization',
            'appointment_date',
            'appointment_time',
            'reason',
            'status',
            'status_display',
            'notes',
            'created_at'
        ]
    
    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"


class DoctorAppointmentListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_phone = serializers.CharField(source='patient.phone_number', read_only=True)
    patient_age = serializers.SerializerMethodField()
    patient_gender = serializers.CharField(source='patient.get_gender_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient_name',
            'patient_phone',
            'patient_age',
            'patient_gender',
            'appointment_date',
            'appointment_time',
            'reason',
            'status',
            'status_display',
            'notes',
            'created_at'
        ]
    
    def get_patient_name(self, obj):
        return obj.patient.get_full_name()
    
    def get_patient_age(self, obj):
        from django.utils import timezone
        if obj.patient.date_of_birth:
            today = timezone.now().date()
            age = today.year - obj.patient.date_of_birth.year
            if today.month < obj.patient.date_of_birth.month or \
               (today.month == obj.patient.date_of_birth.month and today.day < obj.patient.date_of_birth.day):
                age -= 1
            return age
        return None
    
class DoctorListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Doctor
        fields = [
            'id',
            'full_name',
            'email',
            'specialization',
            'qualification',
            'years_of_experience',
            'department',
            'city',
            'phone_number',
            'is_approved'
        ]
    
    def get_full_name(self, obj):
        return f"Dr. {obj.get_full_name()}"