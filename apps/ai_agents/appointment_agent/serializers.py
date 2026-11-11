from datetime import date, timedelta
from rest_framework import serializers

from ai_agents.core.sanitizer import PromptInjectionError, sanitize_clinical_text


class AppointmentAssistantRequestSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Optional for patients (defaults to self); required for doctors",
    )
    doctor_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Optional specific doctor ID to check slots and queue",
    )
    specialization = serializers.CharField(
        required=False,
        max_length=100,
        allow_blank=True,
        default="",
        help_text="Optional preferred specialization",
    )
    preferred_date = serializers.DateField(
        required=False,
        help_text="Target date (YYYY-MM-DD); defaults to today",
    )
    preferred_time_of_day = serializers.ChoiceField(
        choices=["any", "morning", "afternoon"],
        required=False,
        default="any",
    )
    reason = serializers.CharField(
        required=False,
        max_length=1000,
        allow_blank=True,
        default="",
        help_text="Reason for consultation",
    )

    def validate_preferred_date(self, value):
        today = date.today()
        if value < today:
            raise serializers.ValidationError("preferred_date cannot be in the past.")
        if value > today + timedelta(days=90):
            raise serializers.ValidationError("preferred_date cannot be more than 90 days in the future.")
        return value

    def validate_specialization(self, value):
        if not value:
            return ""
        try:
            return sanitize_clinical_text(value, max_length=100).text
        except PromptInjectionError as exc:
            raise serializers.ValidationError(str(exc))

    def validate_reason(self, value):
        if not value:
            return ""
        try:
            return sanitize_clinical_text(value, max_length=1000).text
        except PromptInjectionError as exc:
            raise serializers.ValidationError(str(exc))


class AppointmentAssistantResponseSerializer(serializers.Serializer):
    summary = serializers.CharField()
    follow_up_alerts = serializers.ListField(child=serializers.DictField())
    conflict_warnings = serializers.ListField(child=serializers.CharField())
    recommended_slots = serializers.ListField(child=serializers.DictField())
    pre_visit_checklist = serializers.ListField(child=serializers.CharField())
    agent_metadata = serializers.DictField()
