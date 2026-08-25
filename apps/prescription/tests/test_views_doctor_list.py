from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import CustomUser, Doctor, Patient
from prescription.models import Prescription

class DoctorPrescriptionsListAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="d_lst_u", email="dlu@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="p_lst_u", email="plu@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Sherman", last_name="Potter", date_of_birth="1960-01-01",
            gender="M", blood_group="O+", city="Hannibal", phone_number="+1555556677"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Sidney", last_name="Freedman", date_of_birth="1965-01-01",
            blood_group="B+", gender="M", city="Chicago", phone_number="+1555667788"
        )
        Prescription.objects.create(
            doctor=self.doctor, patient=self.patient,
            chief_complaint="Insomnia", diagnosis="Mild anxiety"
        )
        self.client.force_authenticate(user=self.doc_u)

    def test_doctor_can_list_issued_prescriptions(self):
        url = reverse("doctor-prescriptions-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
