from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import CustomUser

class PasswordResetAPITests(APITestCase):
    def setUp(self):
        self.forgot_url = reverse("forgot_password")
        self.verify_reset_url = reverse("verify_password_reset_otp")
        self.reset_url = reverse("reset_password")
        self.user = CustomUser.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="OldPassword123!",
            is_verified=True
        )

    @patch("authentication.services.send_otp_email_task.delay")
    def test_forgot_password_generates_otp(self, mock_email_task):
        response = self.client.post(self.forgot_url, {"email": "reset@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_email_task.assert_called_once()

    def test_complete_password_reset_flow(self):
        self.user.otp = "998877"
        self.user.otp_created_at = timezone.now()
        self.user.otp_type = "reset"
        self.user.save()

        verify_res = self.client.post(
            self.verify_reset_url, {"email": "reset@example.com", "otp": "998877"}, format="json"
        )
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)

        reset_res = self.client.post(
            self.reset_url,
            {"email": "reset@example.com", "new_password": "NewStrongPass123!"},
            format="json"
        )
        self.assertEqual(reset_res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass123!"))
