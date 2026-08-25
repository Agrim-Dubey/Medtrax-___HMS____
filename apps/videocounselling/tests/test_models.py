from django.test import TestCase
from authentication.models import CustomUser, Doctor, Patient
from appointments.models import Appointment
from videocounselling.models import VideoCall

class VideoCallModelTests(TestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="vid_d", email="vd@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="vid_p", email="vp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Meredith", last_name="Grey", date_of_birth="1978-01-01",
            gender="F", blood_group="A+", city="Seattle", phone_number="+1555777123"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Derek", last_name="Shepherd", date_of_birth="1975-01-01",
            blood_group="O+", gender="M", city="Seattle", phone_number="+1555777456"
        )
        self.appt = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date="2026-12-01", appointment_time="14:00", status="confirmed"
        )

    def test_videocall_creation_and_defaults(self):
        call = VideoCall.objects.create(appointment=self.appt, initiated_by=self.doc_u)
        self.assertEqual(call.status, "waiting")
        self.assertEqual(call.initiated_by, self.doc_u)
        self.assertIn("Call for", str(call))
