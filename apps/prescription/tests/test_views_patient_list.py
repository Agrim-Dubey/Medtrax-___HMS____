from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser, Doctor, Patient
from prescription.models import Prescription

class PatientPrescriptionsListAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="p_rx_d", email="prxd@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="p_rx_p", email="prxp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Charles", last_name="Winchester", date_of_birth="1965-01-01",
            gender="M", blood_group="AB-", city="Boston", phone_number="+1555778800"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Kelly", last_name="Nakahara", date_of_birth="1982-01-01",
            blood_group="A+", gender="F", city="Oahu", phone_number="+1555889900"
        )
        self.rx = Prescription.objects.create(
            doctor=self.doctor, patient=self.patient,
            chief_complaint="Allergic rhinitis", diagnosis="Seasonal allergies"
        )
        self.client.force_authenticate(user=self.pat_u)

    def test_patient_can_view_own_prescriptions(self):
        url = reverse("patient-prescriptions-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_patient_can_filter_prescriptions_by_doctor(self):
        url = reverse("patient-prescriptions-by-doctor", kwargs={"doctor_id": self.doctor.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
