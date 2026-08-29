from rest_framework import serializers


class ProposedMedicationItemSerializer(serializers.Serializer):
    medicine_name = serializers.CharField(max_length=200)
    dosage = serializers.CharField(max_length=50, required=False, default="")
    dosage_frequency = serializers.CharField(max_length=50, required=False, default="once_daily")
    duration_value = serializers.IntegerField(required=False, default=7)
    duration_unit = serializers.CharField(max_length=20, required=False, default="days")


class ClinicalSafetyCheckRequestSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(help_text="Target patient ID")
    diagnosis = serializers.CharField(required=False, allow_blank=True, default="")
    medications = serializers.ListField(
        child=ProposedMedicationItemSerializer(),
        allow_empty=False,
        help_text="List of medications proposed by the doctor"
    )


class InteractionItemSerializer(serializers.Serializer):
    type = serializers.CharField()
    severity = serializers.CharField()
    involved_drugs = serializers.ListField(child=serializers.CharField())
    contraindicated_with = serializers.CharField()
    clinical_explanation = serializers.CharField()
    recommended_alternative = serializers.CharField()


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

