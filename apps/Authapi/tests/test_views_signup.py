from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser

class SignupAPITests(APITestCase):
    def setUp(self):
        self.signup_url = reverse("signup")

    @patch("Authapi.services.send_otp_email_task.delay")
    def test_successful_patient_signup(self, mock_email_task):
        payload = {
            "username": "newpatient",
            "email": "newpatient@example.com",
            "password": "StrongPassword123!",
            "role": "patient"
        }
        response = self.client.post(self.signup_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = CustomUser.objects.get(email="newpatient@example.com")
        self.assertEqual(user.role, "patient")
        self.assertFalse(user.is_verified)
        self.assertIsNotNone(user.otp)
        mock_email_task.assert_called_once()

    def test_signup_duplicate_email_fails(self):
        CustomUser.objects.create_user(
            username="firstuser", email="dup@example.com", password="Password123!"
        )
        payload = {
            "username": "seconduser",
            "email": "dup@example.com",
            "password": "Password123!",
            "role": "patient"
        }
        response = self.client.post(self.signup_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
