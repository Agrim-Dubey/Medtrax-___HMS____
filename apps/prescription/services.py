from django.db import transaction
from Authapi.models import Doctor
from .models import Prescription
from .serializers import CreatePrescriptionSerializer

@transaction.atomic
def create_prescription(*, doctor: Doctor, data: dict) -> Prescription:
    serializer = CreatePrescriptionSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    prescription = serializer.save(doctor=doctor)
    return prescription
