from unittest.mock import patch
from django.test import TestCase
from Authapi.models import CustomUser, Doctor, Patient
from appointments.models import Appointment
from appointments.tasks import send_patient_reminder, send_doctor_reminder

class AppointmentTasksTests(TestCase):
    def setUp(self):
        self.doc_user = CustomUser.objects.create_user(username="task_d", email="td@med.com", password="P1", role="doctor")
        self.pat_user = CustomUser.objects.create_user(username="task_p", email="tp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_user, first_name="Lawrence", last_name="Kutner", date_of_birth="1982-01-01",
            gender="M", blood_group="A+", city="NJ", phone_number="+1555999000"
        )
        self.patient = Patient.objects.create(
            user=self.pat_user, first_name="Amber", last_name="Volakis", date_of_birth="1983-01-01",
            blood_group="B-", gender="F", city="NJ", phone_number="+1555999111"
        )
        self.appt = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date="2026-12-15", appointment_time="10:00", status="confirmed"
        )

    @patch("appointments.tasks.send_mail")
    def test_send_patient_reminder_email(self, mock_mail):
        result = send_patient_reminder(self.appt.id)
        self.assertTrue(result)
        mock_mail.assert_called_once()

    @patch("appointments.tasks.send_mail")
    def test_send_doctor_reminder_email(self, mock_mail):
        result = send_doctor_reminder(self.appt.id)
        self.assertTrue(result)
        mock_mail.assert_called_once()
