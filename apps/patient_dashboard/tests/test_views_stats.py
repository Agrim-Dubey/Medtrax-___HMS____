from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import date, time, timedelta
from Authapi.models import CustomUser, Doctor, Patient
from appointments.models import Appointment

class PatientDashboardStatsAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="pst_d", email="pstd@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="pst_p", email="pstp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Charles", last_name="Bingley", date_of_birth="1991-01-01",
            gender="M", blood_group="AB+", city="London", phone_number="+4477788899"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Georgiana", last_name="Darcy", date_of_birth="1998-01-01",
            blood_group="A-", gender="F", city="Derbyshire", phone_number="+4477799900"
        )
        Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date=date.today() + timedelta(days=2), appointment_time=time(15, 30), status="confirmed"
        )
        self.client.force_authenticate(user=self.pat_u)

    def test_get_patient_dashboard_stats(self):
        url = reverse("patient-dashboard-stats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_appointments", response.data)
        self.assertIn("upcoming_appointments", response.data)
