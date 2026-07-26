from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser, Doctor, Patient
from appointments.models import Appointment

class DoctorAppointmentActionsAPITests(APITestCase):
    def setUp(self):
        self.doc_user = CustomUser.objects.create_user(username="doc_act", email="dact@med.com", password="P1", role="doctor")
        self.pat_user = CustomUser.objects.create_user(username="pat_act", email="pact@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_user, first_name="Eric", last_name="Foreman", date_of_birth="1980-01-01",
            gender="M", blood_group="B+", city="NJ", phone_number="+1555333222"
        )
        self.patient = Patient.objects.create(
            user=self.pat_user, first_name="Allison", last_name="Cameron", date_of_birth="1984-01-01",
            blood_group="A-", gender="F", city="NJ", phone_number="+1555222111"
        )
        self.appointment = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date="2026-11-28", appointment_time="14:00", status="pending"
        )
        self.client.force_authenticate(user=self.doc_user)

    @patch("appointments.services.send_immediate_appointment_notification.delay")
    @patch("appointments.services.broadcast_queue_update")
    def test_doctor_accept_appointment(self, mock_broadcast, mock_notify):
        url = reverse("doctor-accept-appointment", kwargs={"appointment_id": self.appointment.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "confirmed")

    @patch("appointments.services.send_immediate_appointment_notification.delay")
    def test_doctor_reject_appointment(self, mock_notify):
        url = reverse("doctor-reject-appointment", kwargs={"appointment_id": self.appointment.id})
        response = self.client.post(url, {"reason": "Doctor unavailable"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "cancelled")
