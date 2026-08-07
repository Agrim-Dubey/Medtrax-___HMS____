from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser, Doctor, Patient
from appointments.models import Appointment

class DoctorPatientsListAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="d_pt_u", email="dpu@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="p_pt_u", email="ppu@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Trapper", last_name="McIntyre", date_of_birth="1970-01-01",
            gender="M", blood_group="B+", city="SF", phone_number="+1555778899"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Margaret", last_name="Houlihan", date_of_birth="1975-01-01",
            blood_group="AB+", gender="F", city="SF", phone_number="+1555001122"
        )
        Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date="2026-11-15", appointment_time="09:30", status="confirmed"
        )
        self.client.force_authenticate(user=self.doc_u)

    def test_doctor_can_list_consulted_patients(self):
        url = reverse("doctor-patients-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
