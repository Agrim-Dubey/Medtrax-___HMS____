from datetime import date, time, timedelta
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from appointments.models import Appointment
from authentication.models import CustomUser, Doctor, Patient
from prescription.models import LabTest, Prescription


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "appt-ai-test"}},
)
class SmartAppointmentAgentTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("ai-appointment-assistant")

        self.doc_user = CustomUser.objects.create_user(
            username="aa_doc", email="aa_doc@medtrax.me", password="Pass123!@#", role="doctor"
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            first_name="Meera",
            last_name="Nair",
            date_of_birth=date(1983, 2, 14),
            gender="F",
            blood_group="A+",
            city="Chennai",
            phone_number="9777777771",
            specialization="Cardiology",
        )
        self.pat1_user = CustomUser.objects.create_user(
            username="aa_pat1", email="aa_pat1@medtrax.me", password="Pass123!@#", role="patient"
        )
        self.pat1 = Patient.objects.create(
            user=self.pat1_user,
            first_name="Dev",
            last_name="Patel",
            date_of_birth=date(1987, 10, 10),
            gender="M",
            blood_group="O+",
            city="Chennai",
            phone_number="9777777772",
            chronic_diseases="Hypertension",
        )
        self.pat2_user = CustomUser.objects.create_user(
            username="aa_pat2", email="aa_pat2@medtrax.me", password="Pass123!@#", role="patient"
        )
        self.pat2 = Patient.objects.create(
            user=self.pat2_user,
            first_name="Nina",
            last_name="Roy",
            date_of_birth=date(1996, 12, 1),
            gender="F",
            blood_group="B+",
            city="Chennai",
            phone_number="9777777773",
        )

        self.rx = Prescription.objects.create(
            doctor=self.doctor,
            patient=self.pat1,
            chief_complaint="BP monitoring",
            diagnosis="Hypertension",
            follow_up_date=date.today() - timedelta(days=2),
        )
        LabTest.objects.create(prescription=self.rx, test_name="Lipid Panel")

    def test_slot_recommendation_follow_up_alert_and_conflict(self):
        tomorrow = date.today() + timedelta(days=1)

        # Before booking: overdue follow-up alert is surfaced
        self.client.force_authenticate(user=self.pat1_user)
        resp_before = self.client.post(
            self.url,
            data={"doctor_id": self.doctor.id, "preferred_date": tomorrow.isoformat()},
            format="json",
        )
        self.assertEqual(resp_before.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_before.data["data"]["follow_up_alerts"][0]["urgency"], "OVERDUE")

        # Once booked: conflict warning triggers, 09:00 slot is excluded, and follow-up alert clears
        Appointment.objects.create(
            doctor=self.doctor,
            patient=self.pat1,
            appointment_date=tomorrow,
            appointment_time=time(9, 0),
            status="pending",
        )

        resp = self.client.post(
            self.url,
            data={
                "doctor_id": self.doctor.id,
                "preferred_date": tomorrow.isoformat(),
                "preferred_time_of_day": "morning",
                "reason": "Follow up with fasting blood test",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.data["data"]
        self.assertEqual(data["follow_up_alerts"], [])
        self.assertGreater(len(data["conflict_warnings"]), 0)
        slots = data["recommended_slots"][0]["slots"]
        self.assertNotIn("09:00", slots)
        self.assertTrue(all(s < "12:00" for s in slots))
        self.assertTrue(any("Lipid Panel" in item for item in data["pre_visit_checklist"]))

    def test_past_date_rejected_and_idor_blocked(self):
        self.client.force_authenticate(user=self.pat1_user)
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        resp_past = self.client.post(self.url, data={"preferred_date": yesterday}, format="json")
        self.assertEqual(resp_past.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(user=self.pat2_user)
        resp_idor = self.client.post(self.url, data={"patient_id": self.pat1.id}, format="json")
        self.assertEqual(resp_idor.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_doctor_returns_404(self):
        self.client.force_authenticate(user=self.pat1_user)
        resp = self.client.post(self.url, data={"doctor_id": 999999}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
