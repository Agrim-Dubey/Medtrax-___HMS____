from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import CustomUser, Doctor, Patient
from appointments.models import Appointment

class InitiateVideoCallAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="init_d", email="id@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="init_p", email="ip@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Cristina", last_name="Yang", date_of_birth="1979-01-01",
            gender="F", blood_group="B+", city="Seattle", phone_number="+1555234567"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Preston", last_name="Burke", date_of_birth="1973-01-01",
            blood_group="AB+", gender="M", city="Seattle", phone_number="+1555345678"
        )
        self.appt = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date="2026-12-02", appointment_time="10:00", status="confirmed"
        )

    def test_doctor_can_initiate_video_call(self):
        self.client.force_authenticate(user=self.doc_u)
        url = reverse("initiate-video-call", kwargs={"appointment_id": self.appt.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
