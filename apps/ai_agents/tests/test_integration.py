from datetime import date, timedelta
from unittest.mock import patch
import requests

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from appointments.models import Appointment
from authentication.models import CustomUser, Doctor, Patient
from prescription.models import Medication, Prescription


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "int-test"}},
)
class AIAgentsSystemIntegrationTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

        self.doc_user = CustomUser.objects.create_user(
            username="int_doc", email="int_doc@medtrax.me", password="Pass123!@#", role="doctor"
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            first_name="Sonia",
            last_name="Gill",
            date_of_birth=date(1980, 1, 1),
            gender="F",
            blood_group="A+",
            city="Delhi",
            phone_number="9888888881",
            specialization="Pulmonology",
        )
        self.pat_user = CustomUser.objects.create_user(
            username="int_pat", email="int_pat@medtrax.me", password="Pass123!@#", role="patient"
        )
        self.patient = Patient.objects.create(
            user=self.pat_user,
            first_name="Kabir",
            last_name="Sharma",
            date_of_birth=date(1990, 5, 5),
            gender="M",
            blood_group="O+",
            city="Delhi",
            phone_number="9888888882",
            known_allergies="Penicillin",
            chronic_diseases="Asthma",
        )

    def test_registry_endpoint_lists_all_five_agents(self):
        self.client.force_authenticate(user=self.pat_user)
        resp = self.client.get(reverse("ai-agents-registry"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data["data"]
        self.assertEqual(data["agents_count"], 5)
        agent_ids = {a["id"] for a in data["agents"]}
        self.assertEqual(
            agent_ids,
            {"safety_agent", "triage_agent", "summarizer_agent", "care_plan_agent", "appointment_agent"},
        )

    def test_end_to_end_patient_and_doctor_journey(self):
        # 1. Patient runs symptom triage
        self.client.force_authenticate(user=self.pat_user)
        triage_resp = self.client.post(
            reverse("ai-symptom-triage"),
            data={"symptoms": "Persistent cough and wheezing", "severity": "moderate", "duration_days": 4},
            format="json",
        )
        self.assertEqual(triage_resp.status_code, status.HTTP_200_OK)
        self.assertIn("Pulmonology", triage_resp.data["data"]["recommended_specializations"])

        # 2. Patient gets smart appointment slots
        appt_resp = self.client.post(
            reverse("ai-appointment-assistant"),
            data={"doctor_id": self.doctor.id, "preferred_date": (date.today() + timedelta(days=1)).isoformat()},
            format="json",
        )
        self.assertEqual(appt_resp.status_code, status.HTTP_200_OK)
        self.assertGreater(len(appt_resp.data["data"]["recommended_slots"]), 0)

        # Book appointment & establish relationship
        Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time="10:00:00",
            status="pending",
        )

        # 3. Doctor runs safety check (catches Penicillin cross-reactivity with Amoxicillin)
        self.client.force_authenticate(user=self.doc_user)
        safety_resp = self.client.post(
            reverse("ai-clinical-safety-check"),
            data={
                "patient_id": self.patient.id,
                "diagnosis": "Asthma with bronchitis",
                "medications": [{"medicine_name": "Amoxicillin 500mg"}],
            },
            format="json",
        )
        self.assertEqual(safety_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(safety_resp.data["data"]["status"], "BLOCKED")

        # Safe alternative prescription created
        rx = Prescription.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            chief_complaint="Wheezing and cough",
            diagnosis="Acute Bronchitis on Asthma",
            follow_up_date=date.today() + timedelta(days=7),
        )
        Medication.objects.create(
            prescription=rx,
            medicine_name="Montelukast 10mg",
            dosage="1 tablet",
            frequency="at_bedtime",
            duration=14,
            duration_unit="days",
        )

        # 4. Doctor summarizes as SOAP note
        soap_resp = self.client.post(
            reverse("ai-clinical-summarize"),
            data={"mode": "clinical_soap", "prescription_id": rx.id},
            format="json",
        )
        self.assertEqual(soap_resp.status_code, status.HTTP_200_OK)
        self.assertIn("Montelukast 10mg", soap_resp.data["data"]["soap_note"]["plan"])

        # 5. Patient generates personalized care plan
        self.client.force_authenticate(user=self.pat_user)
        cp_resp = self.client.post(
            reverse("ai-care-plan"),
            data={"prescription_id": rx.id},
            format="json",
        )
        self.assertEqual(cp_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(cp_resp.data["data"]["active_medications_count"], 1)

    @override_settings(AI_LLM_PROVIDER="gemini", AI_LLM_API_KEY="fake-key")
    @patch("ai_agents.core.llm_client.requests.post", side_effect=requests.Timeout("LLM down"))
    def test_hybrid_llm_outage_falls_back_cleanly_across_agents(self, _mock_post):
        self.client.force_authenticate(user=self.pat_user)
        resp = self.client.post(
            reverse("ai-symptom-triage"),
            data={"symptoms": "Mild sore throat and fever"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        meta = resp.data["data"]["agent_metadata"]
        self.assertEqual(meta["mode"], "deterministic")
        self.assertFalse(meta["llm_enhanced"])
        self.assertEqual(meta["fallback_reason"], "timeout")

