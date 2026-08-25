from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import date, time, timedelta
from authentication.models import CustomUser, Doctor, Patient
from appointments.models import Appointment

class PatientAppointmentsAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="pa_d", email="pad@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="pa_p", email="pap@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Fitzwilliam", last_name="Darcy", date_of_birth="1990-01-01",
            gender="M", blood_group="O+", city="Derbyshire", phone_number="+445556677"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Jane", last_name="Bennet", date_of_birth="1993-01-01",
            blood_group="B+", gender="F", city="Hertfordshire", phone_number="+445557788"
        )
        Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date=date.today() + timedelta(days=5), appointment_time=time(14, 0), status="confirmed"
        )
        Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date=date.today() - timedelta(days=10), appointment_time=time(10, 0), status="completed"
        )
        self.client.force_authenticate(user=self.pat_u)

    def test_get_upcoming_appointments(self):
        url = reverse("patient-upcoming-appointments")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_get_recent_appointments(self):
        url = reverse("patient-recent-appointments")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
