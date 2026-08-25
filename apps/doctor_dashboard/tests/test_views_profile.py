from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import CustomUser, Doctor

class DoctorDashboardProfileAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="p_doc_u", email="pdu@med.com", password="P1", role="doctor")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Paul", last_name="Farmer", date_of_birth="1959-01-01",
            gender="M", blood_group="AB+", city="Boston", phone_number="+1555999888",
            specialization="Infectious Disease", registration_number="REG-BOS-1959"
        )
        self.client.force_authenticate(user=self.doc_u)

    def test_get_doctor_profile(self):
        url = reverse("doctor-dashboard-profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], "Dr. Paul Farmer")
        self.assertEqual(response.data["specialization"], "Infectious Disease")
