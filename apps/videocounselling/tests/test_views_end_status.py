from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import CustomUser, Doctor, Patient
from appointments.models import Appointment
from videocounselling.models import VideoCall

class EndAndStatusVideoCallAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="es_d", email="esd@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="es_p", email="esp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Miranda", last_name="Bailey", date_of_birth="1975-01-01",
            gender="F", blood_group="B-", city="Seattle", phone_number="+1555678901"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="George", last_name="OMalley", date_of_birth="1980-01-01",
            blood_group="O+", gender="M", city="Seattle", phone_number="+1555789012"
        )
        self.appt = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date="2026-12-04", appointment_time="12:00", status="confirmed"
        )
        self.call = VideoCall.objects.create(appointment=self.appt, initiated_by=self.doc_u, status="active")
        self.client.force_authenticate(user=self.doc_u)

    def test_check_video_call_status(self):
        url = reverse("video-call-status", kwargs={"appointment_id": self.appt.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "active")

    def test_end_video_call(self):
        url = reverse("end-video-call", kwargs={"appointment_id": self.appt.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.call.refresh_from_db()
        self.assertEqual(self.call.status, "ended")
