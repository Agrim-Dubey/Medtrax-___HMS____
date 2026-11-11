from rest_framework import serializers

from ai_agents.core.sanitizer import PromptInjectionError, sanitize_clinical_text


class ProposedMedicationItemSerializer(serializers.Serializer):
    medicine_name = serializers.CharField(max_length=200)
    dosage = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    dosage_frequency = serializers.CharField(max_length=50, required=False, default="once_daily")
    duration_value = serializers.IntegerField(required=False, default=7, min_value=1, max_value=365)
    duration_unit = serializers.ChoiceField(
        choices=["days", "weeks", "months"],
        required=False,
        default="days",
    )

    def validate_medicine_name(self, value):
        try:
            clean = sanitize_clinical_text(value, max_length=200).text
        except PromptInjectionError as exc:
            raise serializers.ValidationError(str(exc))
        if len(clean) < 2:
            raise serializers.ValidationError("Medication name must be at least 2 characters.")
        return clean


class ClinicalSafetyCheckRequestSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(min_value=1, help_text="Target patient ID")
    diagnosis = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    medications = serializers.ListField(
        child=ProposedMedicationItemSerializer(),
        allow_empty=False,
        max_length=30,
        help_text="List of medications proposed by the doctor (max 30)",
    )

    def validate_diagnosis(self, value):
        if not value:
            return ""
        try:
            return sanitize_clinical_text(value, max_length=500).text
        except PromptInjectionError as exc:
            raise serializers.ValidationError(str(exc))


class InteractionItemSerializer(serializers.Serializer):
    type = serializers.CharField()
    severity = serializers.CharField()
    drug = serializers.CharField(required=False)
    drugs = serializers.ListField(child=serializers.CharField(), required=False)
    conflict_with = serializers.CharField(required=False)
    condition = serializers.CharField(required=False)
    explanation = serializers.CharField()
    recommendation = serializers.CharField()


class ClinicalSafetyCheckResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["APPROVED", "WARNING", "BLOCKED"])
    safety_score = serializers.IntegerField()
    risk_level = serializers.ChoiceField(choices=["LOW", "MODERATE", "HIGH", "CRITICAL"])
    summary = serializers.CharField()
    interactions_count = serializers.IntegerField()
    interactions = InteractionItemSerializer(many=True)
    active_medications_checked = serializers.ListField(child=serializers.CharField())
    patient_instructions = serializers.ListField(child=serializers.CharField())
    agent_metadata = serializers.DictField()
