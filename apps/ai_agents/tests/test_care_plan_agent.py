from datetime import date, timedelta
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from ai_agents.care_plan_agent.agent import CarePlanAgent
from authentication.models import CustomUser, Doctor, Patient
from prescription.models import LabTest, Medication, Prescription


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "cp-test"}},
)
class CarePlanAgentTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("ai-care-plan")

        self.doc_user = CustomUser.objects.create_user(
            username="cp_doc", email="cp_doc@medtrax.me", password="Pass123!@#", role="doctor"
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            first_name="Asha",
            last_name="Verma",
            date_of_birth=date(1981, 4, 4),
            gender="F",
            blood_group="O+",
            city="Delhi",
            phone_number="9666666661",
            specialization="Endocrinology",
        )
        self.pat1_user = CustomUser.objects.create_user(
            username="cp_pat1", email="cp_pat1@medtrax.me", password="Pass123!@#", role="patient"
        )
        self.pat1 = Patient.objects.create(
            user=self.pat1_user,
            first_name="Rohan",
            last_name="Sen",
            date_of_birth=date(1975, 8, 15),
            gender="M",
            blood_group="A+",
            city="Delhi",
            phone_number="9666666662",
            chronic_diseases="Type 2 Diabetes, Hypertension",
        )
        self.pat2_user = CustomUser.objects.create_user(
            username="cp_pat2", email="cp_pat2@medtrax.me", password="Pass123!@#", role="patient"
        )
        self.pat2 = Patient.objects.create(
            user=self.pat2_user,
            first_name="Zara",
            last_name="Ali",
            date_of_birth=date(1994, 3, 12),
            gender="F",
            blood_group="B+",
            city="Delhi",
            phone_number="9666666663",
        )
        self.rx = Prescription.objects.create(
            doctor=self.doctor,
            patient=self.pat1,
            chief_complaint="Routine diabetes & BP review",
            diagnosis="Hypertension and Diabetes Mellitus",
            follow_up_date=date.today() - timedelta(days=1),
        )
        for name, freq in [
            ("Metformin 500mg", "twice_daily"),
            ("Amlodipine 5mg", "once_daily"),
            ("Atorvastatin 10mg", "at_bedtime"),
            ("Vitamin D3", "after_meals"),
        ]:
            Medication.objects.create(
                prescription=self.rx,
                medicine_name=name,
                dosage="1 tab",
                frequency=freq,
                duration=2,
                duration_unit="weeks",
            )
        LabTest.objects.create(prescription=self.rx, test_name="HbA1c")

    def test_care_plan_schedule_complexity_and_chronic_guidance(self):
        agent = CarePlanAgent()
        result = agent.build_care_plan(patient=self.pat1)
        self.assertEqual(result["active_medications_count"], 4)
        self.assertEqual(result["adherence_complexity"], "HIGH")
        self.assertGreaterEqual(len(result["daily_schedule"]["morning"]), 3)
        self.assertGreaterEqual(len(result["daily_schedule"]["bedtime"]), 1)
        self.assertEqual(result["follow_ups"][0]["status"], "overdue")
        conditions = [c["condition"] for c in result["condition_guidance"]]
        self.assertIn("Hypertension", conditions)
        self.assertIn("Diabetes Mellitus", conditions)

    def test_expired_medication_excluded_from_active(self):
        old_rx = Prescription.objects.create(
            doctor=self.doctor,
            patient=self.pat2,
            chief_complaint="Cold",
            diagnosis="Viral URI",
        )
        Prescription.objects.filter(id=old_rx.id).update(
            created_at=timezone.now() - timedelta(days=30)
        )
        Medication.objects.create(
            prescription=old_rx,
            medicine_name="Cetirizine 10mg",
            dosage="1 tab",
            frequency="once_daily",
            duration=5,
            duration_unit="days",
        )
        agent = CarePlanAgent()
        result = agent.build_care_plan(patient=self.pat2)
        self.assertEqual(result["active_medications_count"], 0)
        self.assertEqual(result["completed_medications_count"], 1)

    def test_endpoint_ownership_and_idor_blocked(self):
        self.client.force_authenticate(user=self.pat1_user)
        resp_ok = self.client.post(self.url, data={}, format="json")
        self.assertEqual(resp_ok.status_code, status.HTTP_200_OK)
        self.assertTrue(resp_ok.data["success"])

        self.client.force_authenticate(user=self.pat2_user)
        resp_idor = self.client.post(
            self.url,
            data={"prescription_id": self.rx.id},
            format="json",
        )
        self.assertEqual(resp_idor.status_code, status.HTTP_403_FORBIDDEN)
