from django.test import TestCase
from rest_framework.test import APIRequestFactory
from Authapi.throttles import OTPRateThrottle, LoginRateThrottle, AuthAnonRateThrottle

class ThrottlingUnitTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_throttle_scopes_configured(self):
        self.assertEqual(OTPRateThrottle().scope, "otp")
        self.assertEqual(LoginRateThrottle().scope, "login")
        self.assertEqual(AuthAnonRateThrottle().scope, "auth_anon")

    def test_throttle_rate_cache_keys(self):
        throttle = OTPRateThrottle()
        request = self.factory.post("/api/auth/verify-signup-otp/")
        ident = throttle.get_ident(request)
        key = throttle.get_cache_key(request, None)
        self.assertIn("throttle_otp", key)
        self.assertIn(ident, key)
