from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date

from authentication.models import CustomUser, Patient, Doctor
from ai_agents.safety_agent.agent import ClinicalSafetyAgent


from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date

from authentication.models import CustomUser, Patient, Doctor
from ai_agents.safety_agent.agent import ClinicalSafetyAgent


class ClinicalSafetyAgentTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testpatient",
            email="patient@medtrax.me",
            password="SecurePassword123!",
            role="patient"
        )
        self.patient = Patient.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 5, 15),
            gender="M",
            blood_group="O+",
            phone_number="9876543210",
            known_allergies="Penicillin",
            chronic_diseases="Asthma, Hypertension"
        )
        self.agent = ClinicalSafetyAgent()

    def test_safe_prescription_evaluation(self):
        """Prescribing safe drugs should pass with score 100 and APPROVED status."""
        medications = [
            {"medicine_name": "Paracetamol", "dosage": "500mg", "dosage_frequency": "thrice_daily"},
            {"medicine_name": "Cetirizine", "dosage": "10mg", "dosage_frequency": "once_daily"}
        ]
        result = self.agent.evaluate_prescription(
            patient=self.patient,
            proposed_medications=medications,
            diagnosis="Seasonal Rhinitis"
        )

        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["risk_level"], "LOW")
        self.assertEqual(result["safety_score"], 100)
        self.assertEqual(len(result["interactions"]), 0)

    def test_allergy_conflict_detection(self):
        """Prescribing Amoxicillin to a patient with a Penicillin allergy must trigger a critical/high warning."""
        medications = [
            {"medicine_name": "Amoxicillin 500mg", "dosage": "500mg", "dosage_frequency": "twice_daily"}
        ]
        result = self.agent.evaluate_prescription(
            patient=self.patient,
            proposed_medications=medications,
            diagnosis="Bacterial Infection"
        )

        self.assertIn(result["status"], ["WARNING", "BLOCKED"])
        self.assertGreater(len(result["interactions"]), 0)
        interaction_types = [i["type"] for i in result["interactions"]]
        self.assertTrue(any("ALLERGY" in t for t in interaction_types))

    def test_drug_drug_interaction_detection(self):
        """Prescribing Warfarin and Aspirin concurrently must trigger a CRITICAL DDI alert."""
        medications = [
            {"medicine_name": "Warfarin Sodium", "dosage": "5mg"},
            {"medicine_name": "Aspirin Dispersible", "dosage": "75mg"}
        ]
        result = self.agent.evaluate_prescription(
            patient=self.patient,
            proposed_medications=medications
        )

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["risk_level"], "CRITICAL")
        self.assertTrue(any(i["type"] == "DRUG_DRUG_INTERACTION" for i in result["interactions"]))

    def test_disease_contraindication_detection(self):
        """Prescribing a beta-blocker to an Asthma patient must trigger a disease contraindication."""
        medications = [
            {"medicine_name": "Propranolol HCl", "dosage": "40mg"}
        ]
        result = self.agent.evaluate_prescription(
            patient=self.patient,
            proposed_medications=medications
        )

        self.assertIn(result["status"], ["WARNING", "BLOCKED"])
        self.assertTrue(any(i["type"] == "DRUG_DISEASE_CONTRAINDICATION" for i in result["interactions"]))


class ClinicalSafetyEndpointTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.doc_user = CustomUser.objects.create_user(
            username="testdoctor",
            email="doctor@medtrax.me",
            password="SecurePassword123!",
            role="doctor"
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            first_name="Sarah",
            last_name="Connor",
            date_of_birth=date(1985, 3, 20),
            gender="F",
            blood_group="A+",
            phone_number="9123456780",
            specialization="General Physician"
        )
        self.patient_user = CustomUser.objects.create_user(
            username="testpatient2",
            email="patient2@medtrax.me",
            password="SecurePassword123!",
            role="patient"
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            first_name="Robert",
            last_name="Smith",
            date_of_birth=date(1975, 11, 2),
            gender="M",
            blood_group="B+",
            phone_number="9876543219",
            known_allergies="Aspirin",
            chronic_diseases="Chronic Kidney Disease"
        )
        self.client.force_authenticate(user=self.doc_user)
        self.url = reverse('ai-clinical-safety-check')

    def test_endpoint_returns_safety_evaluation(self):
        payload = {
            "patient_id": self.patient.id,
            "diagnosis": "Severe Knee Pain",
            "medications": [
                {"medicine_name": "Ibuprofen 400mg", "dosage": "400mg", "dosage_frequency": "thrice_daily"}
            ]
        }
        response = self.client.post(self.url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertIn("status", data)
        self.assertIn("safety_score", data)
        self.assertIn("interactions", data)
