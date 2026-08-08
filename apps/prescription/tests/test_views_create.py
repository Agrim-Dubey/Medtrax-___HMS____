from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser, Doctor, Patient
from prescription.models import Prescription

class CreatePrescriptionAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="cp_d", email="cpd@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="cp_p", email="cpp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="B.J.", last_name="Hunnicutt", date_of_birth="1972-01-01",
            gender="M", blood_group="A+", city="Mill Valley", phone_number="+1555223344"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Klinger", last_name="Maxwell", date_of_birth="1978-01-01",
            blood_group="O-", gender="M", city="Toledo", phone_number="+1555334455"
        )
        self.client.force_authenticate(user=self.doc_u)

    def test_create_prescription_with_medications_and_tests(self):
        url = reverse("create-prescription")
        payload = {
            "patient": self.patient.id,
            "chief_complaint": "Migraine and photophobia",
            "diagnosis": "Tension headache",
            "blood_pressure": "118/75",
            "medications": [
                {
                    "medicine_name": "Ibuprofen",
                    "dosage": "400mg",
                    "frequency": "as_needed",
                    "duration": 5,
                    "duration_unit": "days",
                    "instructions": "Take after food"
                }
            ],
            "lab_tests": [
                {
                    "test_name": "Complete Blood Count",
                    "instructions": "Fasting not required"
                }
            ]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Prescription.objects.filter(doctor=self.doctor, patient=self.patient).exists())
