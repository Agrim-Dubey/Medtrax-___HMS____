from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import date, time
from Authapi.models import CustomUser, Doctor, Patient
from appointments.models import Appointment

class DoctorDashboardStatsAndAgendaAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="st_doc_u", email="sdu@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="st_pat_u", email="spu@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Atul", last_name="Gawande", date_of_birth="1965-01-01",
            gender="M", blood_group="A-", city="Boston", phone_number="+1555123444"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Oliver", last_name="Sacks", date_of_birth="1933-01-01",
            blood_group="O+", gender="M", city="New York", phone_number="+1555234555"
        )
        Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date=date.today(), appointment_time=time(11, 0), status="confirmed"
        )
        self.client.force_authenticate(user=self.doc_u)

    def test_get_dashboard_stats(self):
        url = reverse("doctor-dashboard-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_patients", response.data)
        self.assertIn("today_appointments", response.data)

    def test_get_today_appointments(self):
        url = reverse("doctor-today-appointments")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_get_weekly_stats(self):
        url = reverse("doctor-weekly-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("weekly_stats", response.data)
