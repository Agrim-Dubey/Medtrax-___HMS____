from datetime import date, timedelta
from decimal import Decimal
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ai_agents.summarizer_agent.agent import ClinicalSummarizerAgent
from authentication.models import CustomUser, Doctor, Patient
from prescription.models import LabTest, Medication, Prescription


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "sum-test"}},
)
class ClinicalSummarizerTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("ai-clinical-summarize")

        self.doc_user = CustomUser.objects.create_user(
            username="sum_doc", email="sum_doc@medtrax.me", password="Pass123!@#", role="doctor"
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            first_name="Vikram",
            last_name="Rao",
            date_of_birth=date(1980, 5, 5),
            gender="M",
            blood_group="O+",
            city="Delhi",
            phone_number="9555555551",
            specialization="General Physician",
        )
        self.pat1_user = CustomUser.objects.create_user(
            username="sum_pat1", email="sum_pat1@medtrax.me", password="Pass123!@#", role="patient"
        )
        self.pat1 = Patient.objects.create(
            user=self.pat1_user,
            first_name="Kiran",
            last_name="Das",
            date_of_birth=date(1988, 6, 15),
            gender="M",
            blood_group="A+",
            city="Delhi",
            phone_number="9555555552",
            chronic_diseases="Hypertension",
        )
        self.pat2_user = CustomUser.objects.create_user(
            username="sum_pat2", email="sum_pat2@medtrax.me", password="Pass123!@#", role="patient"
        )
        self.pat2 = Patient.objects.create(
            user=self.pat2_user,
            first_name="Other",
            last_name="Pat",
            date_of_birth=date(1992, 6, 15),
            gender="F",
            blood_group="B+",
            city="Delhi",
            phone_number="9555555553",
        )
        self.prescription = Prescription.objects.create(
            doctor=self.doctor,
            patient=self.pat1,
            chief_complaint="High fever and persistent headache for 3 days",
            diagnosis="Viral Pyrexia with Elevated BP",
            blood_pressure="150/95",
            temperature=Decimal("101.6"),
            pulse_rate=108,
            additional_notes="Hydrate well and monitor BP twice daily.",
            follow_up_date=date.today() + timedelta(days=5),
        )
        Medication.objects.create(
            prescription=self.prescription,
            medicine_name="Paracetamol 500mg",
            dosage="1 tablet",
            frequency="thrice_daily",
            duration=5,
            duration_unit="days",
        )
        LabTest.objects.create(
            prescription=self.prescription,
            test_name="Fasting Lipid Profile",
        )

    def test_doctor_soap_note_generation_and_abnormal_vitals(self):
        self.client.force_authenticate(user=self.doc_user)
        resp = self.client.post(
            self.url,
            data={"mode": "clinical_soap", "prescription_id": self.prescription.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data["data"]
        self.assertEqual(data["mode"], "clinical_soap")
        self.assertIsNotNone(data["soap_note"])
        self.assertIn("Elevated BP", " ".join(data["abnormal_vitals"]))
        self.assertIn("Febrile", " ".join(data["abnormal_vitals"]))
        self.assertIn("Tachycardia", " ".join(data["abnormal_vitals"]))

    def test_patient_friendly_summary_for_own_prescription(self):
        self.client.force_authenticate(user=self.pat1_user)
        resp = self.client.post(
            self.url,
            data={"mode": "patient_friendly", "prescription_id": self.prescription.id},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data["data"]
        self.assertEqual(data["mode"], "patient_friendly")
        self.assertIsNone(data["soap_note"])
        self.assertEqual(len(data["medication_guide"]), 1)
        self.assertIn("Fasting for 8-12 hours", data["lab_test_guide"][0]["preparation"])

    def test_patient_blocked_from_clinical_soap_and_other_patient_rx(self):
        self.client.force_authenticate(user=self.pat1_user)
        resp_soap = self.client.post(
            self.url,
            data={"mode": "clinical_soap", "prescription_id": self.prescription.id},
            format="json",
        )
        self.assertEqual(resp_soap.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.pat2_user)
        resp_idor = self.client.post(
            self.url,
            data={"mode": "patient_friendly", "prescription_id": self.prescription.id},
            format="json",
        )
        self.assertEqual(resp_idor.status_code, status.HTTP_403_FORBIDDEN)

    def test_edge_cases_empty_payload_and_malformed_bp(self):
        self.client.force_authenticate(user=self.doc_user)
        resp_empty = self.client.post(self.url, data={"mode": "clinical_soap"}, format="json")
        self.assertEqual(resp_empty.status_code, status.HTTP_400_BAD_REQUEST)

        agent = ClinicalSummarizerAgent()
        res = agent.summarize(
            mode="clinical_soap",
            chief_complaint="Routine check",
            vitals={"blood_pressure": "not-valid"},
        )
        self.assertEqual(res["abnormal_vitals"], [])
