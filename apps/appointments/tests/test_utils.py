from django.test import TestCase
from datetime import date, time, datetime
from authentication.models import CustomUser, Doctor, Patient
from appointments.models import Appointment
from appointments.utils import get_available_slots, get_doctor_queue_info

class AppointmentUtilsTests(TestCase):
    def setUp(self):
        self.doc_user = CustomUser.objects.create_user(username="d_util", email="d_util@med.com", password="P1", role="doctor")
        self.doctor = Doctor.objects.create(
            user=self.doc_user, first_name="Gregory", last_name="House", date_of_birth="1970-01-01",
            gender="M", blood_group="O+", city="Princeton", phone_number="+1555777888"
        )

    def test_available_slots_calculation(self):
        target_date = date(2026, 11, 20)
        slots = get_available_slots(self.doctor, target_date)
        self.assertIn("09:00", slots)
        self.assertIn("16:30", slots)
        self.assertTrue(len(slots) > 0)

    def test_queue_info_structure(self):
        info = get_doctor_queue_info(self.doctor)
        self.assertIn("current_queue_count", info)
        self.assertIn("estimated_wait_time", info)
        self.assertIn("current_session", info)
        self.assertEqual(info["current_queue_count"], 0)
