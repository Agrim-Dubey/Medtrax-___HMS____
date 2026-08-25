from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import CustomUser, Doctor

class AvailableDoctorsAndSlotsAPITests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="patient_v", email="pv@med.com", password="P1", role="patient")
        self.doc_user = CustomUser.objects.create_user(username="doc_v", email="dv@med.com", password="P1", role="doctor")
        self.doctor = Doctor.objects.create(
            user=self.doc_user, first_name="Alice", last_name="Smith", date_of_birth="1982-03-04",
            gender="F", blood_group="B+", city="Seattle", phone_number="+1555444555",
            specialization="Pediatrics", is_approved=True
        )
        self.client.force_authenticate(user=self.user)

    def test_get_available_doctors_list(self):
        url = reverse("available-doctors")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_get_doctor_available_slots(self):
        url = reverse("doctor-available-slots", kwargs={"doctor_id": self.doctor.id})
        response = self.client.get(f"{url}?date=2026-11-25")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("available_slots", response.data)
