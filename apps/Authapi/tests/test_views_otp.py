from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser

class OTPVerificationTests(APITestCase):
    def setUp(self):
        self.verify_url = reverse("verify_signup_otp")
        self.resend_url = reverse("resend_signup_otp")
        self.user = CustomUser.objects.create_user(
            username="otpuser",
            email="otpuser@example.com",
            password="Password123!",
            role="patient"
        )
        self.user.otp = "654321"
        self.user.otp_created_at = timezone.now()
        self.user.otp_type = "verification"
        self.user.save()

    def test_successful_otp_verification(self):
        payload = {"email": "otpuser@example.com", "otp": "654321"}
        response = self.client.post(self.verify_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)
        self.assertIsNone(self.user.otp)

    def test_invalid_otp_increments_attempts(self):
        payload = {"email": "otpuser@example.com", "otp": "000000"}
        response = self.client.post(self.verify_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.otp_attempts, 1)

    @patch("Authapi.services.send_otp_email_task.delay")
    def test_resend_otp_success(self, mock_email_task):
        payload = {"email": "otpuser@example.com"}
        response = self.client.post(self.resend_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_email_task.assert_called_once()
