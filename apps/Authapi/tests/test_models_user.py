from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from Authapi.models import CustomUser

class CustomUserModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="patient_test",
            email="patient@example.com",
            password="SecurePassword123!",
            role="patient"
        )

    def test_user_creation_and_string_representation(self):
        self.assertEqual(self.user.email, "patient@example.com")
        self.assertEqual(self.user.role, "patient")
        self.assertFalse(self.user.is_verified)
        self.assertIn("patient_test", str(self.user))

    def test_otp_expiration_check(self):
        self.user.otp_created_at = timezone.now() - timedelta(minutes=4)
        self.user.save()
        self.assertTrue(self.user.is_otp_expired())

        self.user.otp_created_at = timezone.now() - timedelta(minutes=1)
        self.user.save()
        self.assertFalse(self.user.is_otp_expired())

    def test_otp_lockout_mechanism(self):
        self.user.otp_locked_until = timezone.now() + timedelta(minutes=15)
        self.user.otp_attempts = 5
        self.user.save()
        self.assertTrue(self.user.is_otp_locked())

        self.user.reset_otp_attempts()
        self.assertEqual(self.user.otp_attempts, 0)
        self.assertIsNone(self.user.otp_locked_until)
        self.assertFalse(self.user.is_otp_locked())

    def test_login_lockout_and_clear_otp(self):
        self.user.login_locked_until = timezone.now() + timedelta(minutes=10)
        self.user.login_attempts = 5
        self.user.save()
        self.assertTrue(self.user.is_login_locked())

        self.user.reset_login_attempts()
        self.assertEqual(self.user.login_attempts, 0)
        self.assertIsNone(self.user.login_locked_until)

        self.user.otp = "123456"
        self.user.clear_otp()
        self.assertIsNone(self.user.otp)
