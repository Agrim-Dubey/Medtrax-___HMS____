from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser, Doctor, Patient
from appointments.models import Appointment
from videocounselling.models import VideoCall

class JoinVideoCallAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="jn_d", email="jd@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="jn_p", email="jp@med.com", password="P1", role="patient")
        self.other_u = CustomUser.objects.create_user(username="jn_oth", email="joth@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Alex", last_name="Karev", date_of_birth="1980-01-01",
            gender="M", blood_group="O+", city="Seattle", phone_number="+1555456789"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Izzie", last_name="Stevens", date_of_birth="1980-01-01",
            blood_group="A-", gender="F", city="Seattle", phone_number="+1555567890"
        )
        self.appt = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date="2026-12-03", appointment_time="11:00", status="confirmed"
        )
        self.call = VideoCall.objects.create(appointment=self.appt, initiated_by=self.doc_u, status="waiting")

    def test_authorized_patient_can_join_call(self):
        self.client.force_authenticate(user=self.pat_u)
        url = reverse("join-video-call", kwargs={"appointment_id": self.appt.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unrelated_user_cannot_join_call(self):
        self.client.force_authenticate(user=self.other_u)
        url = reverse("join-video-call", kwargs={"appointment_id": self.appt.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
