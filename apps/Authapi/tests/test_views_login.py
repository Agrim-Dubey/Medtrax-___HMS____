from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser

class LoginAPITests(APITestCase):
    def setUp(self):
        self.login_url = reverse("login")
        self.user = CustomUser.objects.create_user(
            username="verifieduser",
            email="login@example.com",
            password="CorrectPassword123!",
            role="patient",
            is_verified=True
        )

    def test_successful_login_sets_cookies(self):
        payload = {"email": "login@example.com", "password": "CorrectPassword123!"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_unverified_user_cannot_login(self):
        self.user.is_verified = False
        self.user.save()
        payload = {"email": "login@example.com", "password": "CorrectPassword123!"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_password_increments_attempts(self):
        payload = {"email": "login@example.com", "password": "WrongPassword!"}
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.login_attempts, 1)
