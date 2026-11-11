from rest_framework import serializers


class CarePlanRequestSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Optional for patients (defaults to self); required for doctors",
    )
    prescription_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Optional specific prescription ID to build the care plan around",
    )


class CarePlanResponseSerializer(serializers.Serializer):
    summary = serializers.CharField()
    adherence_complexity = serializers.ChoiceField(choices=["LOW", "MODERATE", "HIGH"])
    active_medications_count = serializers.IntegerField()
    active_medications = serializers.ListField(child=serializers.DictField())
    completed_medications_count = serializers.IntegerField()
    daily_schedule = serializers.DictField()
    condition_guidance = serializers.ListField(child=serializers.DictField())
    lab_checklist = serializers.ListField(child=serializers.DictField())
    follow_ups = serializers.ListField(child=serializers.DictField())
    adherence_tips = serializers.ListField(child=serializers.CharField())
    agent_metadata = serializers.DictField()
