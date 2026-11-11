import re
from rest_framework import serializers

from ai_agents.core.sanitizer import PromptInjectionError, sanitize_clinical_text

_BP_RE = re.compile(r"^\d{2,3}/\d{2,3}$")


class VitalsInputSerializer(serializers.Serializer):
    temperature_f = serializers.FloatField(required=False, min_value=85.0, max_value=115.0)
    heart_rate = serializers.IntegerField(required=False, min_value=20, max_value=260)
    spo2 = serializers.IntegerField(required=False, min_value=40, max_value=100)
    blood_pressure = serializers.CharField(required=False, max_length=12)

    def validate_blood_pressure(self, value):
        cleaned = value.strip()
        if not _BP_RE.match(cleaned):
            raise serializers.ValidationError("Blood pressure must be in 'SYS/DIA' format, e.g., '120/80'.")
        sys_val, dia_val = map(int, cleaned.split("/"))
        if not (40 <= sys_val <= 300 and 20 <= dia_val <= 200):
            raise serializers.ValidationError("Blood pressure values are outside physiological bounds.")
        return cleaned


class SymptomTriageRequestSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Optional for patients (defaults to self); required for doctors",
    )
    symptoms = serializers.CharField(
        max_length=2000,
        help_text="Patient's reported symptoms description",
    )
    duration_days = serializers.IntegerField(required=False, min_value=0, max_value=3650)
    severity = serializers.ChoiceField(
        choices=["mild", "moderate", "severe"],
        required=False,
        default="moderate",
    )
    vitals = VitalsInputSerializer(required=False)
    preferred_city = serializers.CharField(required=False, max_length=100, allow_blank=True)

    def validate_symptoms(self, value):
        try:
            clean = sanitize_clinical_text(value, max_length=2000).text
        except PromptInjectionError as exc:
            raise serializers.ValidationError(str(exc))
        if len(clean) < 3:
            raise serializers.ValidationError("Symptoms description must be at least 3 characters.")
        return clean

    def validate_preferred_city(self, value):
        if not value:
            return ""
        try:
            return sanitize_clinical_text(value, max_length=100).text
        except PromptInjectionError as exc:
            raise serializers.ValidationError(str(exc))


class SymptomTriageResponseSerializer(serializers.Serializer):
    urgency_level = serializers.ChoiceField(choices=["SELF_CARE", "ROUTINE", "URGENT", "EMERGENCY"])
    seek_immediate_care = serializers.BooleanField()
    recommended_timeframe = serializers.CharField()
    red_flags_detected = serializers.ListField(child=serializers.DictField())
    vital_alerts = serializers.ListField(child=serializers.CharField())
    risk_factors = serializers.ListField(child=serializers.CharField())
    recommended_specializations = serializers.ListField(child=serializers.CharField())
    recommended_doctors = serializers.ListField(child=serializers.DictField())
    clinical_guidance = serializers.CharField()
    questions_for_doctor = serializers.ListField(child=serializers.CharField())
    agent_metadata = serializers.DictField()
