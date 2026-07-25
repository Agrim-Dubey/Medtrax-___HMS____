from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser, Doctor, Patient
from appointments.models import Appointment

class AppointmentBookingAPITests(APITestCase):
    def setUp(self):
        self.doc_user = CustomUser.objects.create_user(username="doc_b", email="db@med.com", password="P1", role="doctor")
        self.pat_user = CustomUser.objects.create_user(username="pat_b", email="pb@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_user, first_name="James", last_name="Wilson", date_of_birth="1975-01-01",
            gender="M", blood_group="A+", city="Princeton", phone_number="+1555666777"
        )
        self.patient = Patient.objects.create(
            user=self.pat_user, first_name="Lisa", last_name="Cuddy", date_of_birth="1978-01-01",
            blood_group="O-", gender="F", city="Princeton", phone_number="+1555888999"
        )
        self.client.force_authenticate(user=self.pat_user)

    @patch("appointments.services.send_immediate_appointment_notification.delay")
    def test_patient_can_book_appointment(self, mock_notify):
        url = reverse("patient-book-appointment")
        payload = {
            "doctor": self.doctor.id,
            "appointment_date": "2026-12-05",
            "appointment_time": "11:00",
            "reason": "Routine checkup"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Appointment.objects.filter(doctor=self.doctor, patient=self.patient).exists())
