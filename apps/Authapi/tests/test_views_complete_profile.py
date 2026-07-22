from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser

class CompleteProfileAPITests(APITestCase):
    def setUp(self):
        self.patient_user = CustomUser.objects.create_user(
            username="profile_pat", email="ppat@example.com", password="Pass123!Safe", role="patient", is_verified=True
        )
        self.doctor_user = CustomUser.objects.create_user(
            username="profile_doc", email="pdoc@example.com", password="Pass123!Safe", role="doctor", is_verified=True
        )

    def test_complete_patient_profile(self):
        self.client.force_authenticate(user=self.patient_user)
        url = reverse("complete_patient_profile")
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "date_of_birth": "1995-04-12",
            "blood_group": "B+",
            "gender": "F",
            "city": "Boston",
            "phone_number": "+16175550192"
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.patient_user.refresh_from_db()
        self.assertTrue(self.patient_user.is_profile_complete)

    def test_complete_doctor_profile(self):
        self.client.force_authenticate(user=self.doctor_user)
        url = reverse("complete_doctor_profile")
        payload = {
            "first_name": "Robert",
            "last_name": "Wilson",
            "date_of_birth": "1980-08-20",
            "gender": "M",
            "blood_group": "AB+",
            "city": "Chicago",
            "phone_number": "+13125550143",
            "registration_number": "MED-IL-4421",
            "specialization": "Oncology",
            "years_of_experience": 12
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.doctor_user.refresh_from_db()
        self.assertTrue(self.doctor_user.is_profile_complete)
