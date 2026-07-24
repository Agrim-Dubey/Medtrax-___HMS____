from django.test import TestCase
from datetime import date, time
from Authapi.models import CustomUser, Doctor, Patient
from appointments.models import Appointment

class AppointmentModelTests(TestCase):
    def setUp(self):
        self.doc_user = CustomUser.objects.create_user(username="d1", email="d1@med.com", password="P1", role="doctor")
        self.pat_user = CustomUser.objects.create_user(username="p1", email="p1@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_user, first_name="Sarah", last_name="Connor", date_of_birth="1980-01-01",
            gender="F", blood_group="A+", city="LA", phone_number="+1555111222"
        )
        self.patient = Patient.objects.create(
            user=self.pat_user, first_name="Kyle", last_name="Reese", date_of_birth="1990-01-01",
            blood_group="O+", gender="M", city="LA", phone_number="+1555333444"
        )

    def test_appointment_creation_and_defaults(self):
        appt = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            appointment_date=date(2026, 12, 1),
            appointment_time=time(10, 30),
            reason="Cardiology follow up"
        )
        self.assertEqual(appt.status, "pending")
        self.assertIn("Kyle Reese with Dr. Sarah Connor", str(appt))
        self.assertIsNone(appt.notes)
