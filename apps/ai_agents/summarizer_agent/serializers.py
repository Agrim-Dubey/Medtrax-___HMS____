from rest_framework import serializers

from ai_agents.core.sanitizer import PromptInjectionError, sanitize_clinical_text


class SummarizerMedicationSerializer(serializers.Serializer):
    medicine_name = serializers.CharField(max_length=200)
    dosage = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    frequency = serializers.CharField(max_length=50, required=False, default="once_daily")
    duration = serializers.IntegerField(required=False, min_value=1, max_value=365, default=7)
    duration_unit = serializers.ChoiceField(choices=["days", "weeks", "months"], required=False, default="days")
    instructions = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class SummarizerLabTestSerializer(serializers.Serializer):
    test_name = serializers.CharField(max_length=200)
    instructions = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class ClinicalSummarizerRequestSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(
        choices=["clinical_soap", "patient_friendly"],
        required=False,
        default="clinical_soap",
    )
    prescription_id = serializers.IntegerField(required=False, min_value=1)
    appointment_id = serializers.IntegerField(required=False, min_value=1)
    chief_complaint = serializers.CharField(max_length=1500, required=False, allow_blank=True, default="")
    clinical_notes = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")
    diagnosis = serializers.CharField(max_length=1000, required=False, allow_blank=True, default="")
    vitals = serializers.DictField(required=False, default=dict)
    medications = serializers.ListField(
        child=SummarizerMedicationSerializer(), required=False, max_length=30, default=list
    )
    lab_tests = serializers.ListField(
        child=SummarizerLabTestSerializer(), required=False, max_length=20, default=list
    )
    follow_up_date = serializers.DateField(required=False, allow_null=True)

    def _sanitize(self, value: str, max_len: int) -> str:
        if not value:
            return ""
        try:
            return sanitize_clinical_text(value, max_length=max_len).text
        except PromptInjectionError as exc:
            raise serializers.ValidationError(str(exc))

    def validate_chief_complaint(self, value):
        return self._sanitize(value, 1500)

    def validate_clinical_notes(self, value):
        return self._sanitize(value, 2000)

    def validate_diagnosis(self, value):
        return self._sanitize(value, 1000)

    def validate(self, attrs):
        has_context = any([
            attrs.get("prescription_id"),
            attrs.get("appointment_id"),
            attrs.get("chief_complaint"),
            attrs.get("clinical_notes"),
            attrs.get("diagnosis"),
            attrs.get("medications"),
        ])
        if not has_context:
            raise serializers.ValidationError(
                "Provide at least a prescription_id, appointment_id, diagnosis, or clinical notes to summarize."
            )
        return attrs


class ClinicalSummarizerResponseSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["clinical_soap", "patient_friendly"])
    summary = serializers.CharField()
    soap_note = serializers.DictField(allow_null=True)
    abnormal_vitals = serializers.ListField(child=serializers.CharField())
    medication_guide = serializers.ListField(child=serializers.DictField())
    lab_test_guide = serializers.ListField(child=serializers.DictField())
    key_highlights = serializers.ListField(child=serializers.CharField())
    agent_metadata = serializers.DictField()
