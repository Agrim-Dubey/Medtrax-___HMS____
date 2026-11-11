from datetime import date, time
from unittest.mock import patch
from django.test import TestCase, override_settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from appointments.models import Appointment
from authentication.models import CustomUser, Doctor, Patient
from ai_agents.permissions import (
    IsDoctor,
    IsDoctorOrPatient,
    IsPatient,
    resolve_authorized_patient,
)
from ai_agents.throttles import AIAgentBurstThrottle


class _MockThrottledView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIAgentBurstThrottle]

    def get(self, request):
        return Response({"ok": True})


class PermissionsAndOwnershipTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.doc_user = CustomUser.objects.create_user(
            username="sec_doc", email="sec_doc@medtrax.me", password="Pass123!@#", role="doctor"
        )
        self.doctor = Doctor.objects.create(
            user=self.doc_user,
            first_name="Elena",
            last_name="Vance",
            date_of_birth=date(1982, 4, 10),
            gender="F",
            blood_group="A+",
            phone_number="9000000001",
            city="Delhi",
            specialization="Cardiology",
        )
        self.patient_user_1 = CustomUser.objects.create_user(
            username="sec_pat1", email="sec_pat1@medtrax.me", password="Pass123!@#", role="patient"
        )
        self.patient_1 = Patient.objects.create(
            user=self.patient_user_1,
            first_name="Alice",
            last_name="One",
            date_of_birth=date(1992, 1, 10),
            gender="F",
            blood_group="O+",
            city="Delhi",
            phone_number="9000000002",
        )
        self.patient_user_2 = CustomUser.objects.create_user(
            username="sec_pat2", email="sec_pat2@medtrax.me", password="Pass123!@#", role="patient"
        )
        self.patient_2 = Patient.objects.create(
            user=self.patient_user_2,
            first_name="Bob",
            last_name="Two",
            date_of_birth=date(1988, 2, 20),
            gender="M",
            blood_group="B+",
            city="Mumbai",
            phone_number="9000000003",
        )

    def test_role_permissions(self):
        req_doc = self.factory.get("/")
        req_doc.user = self.doc_user
        req_pat = self.factory.get("/")
        req_pat.user = self.patient_user_1

        self.assertTrue(IsDoctor().has_permission(req_doc, None))
        self.assertFalse(IsDoctor().has_permission(req_pat, None))
        self.assertTrue(IsPatient().has_permission(req_pat, None))
        self.assertFalse(IsPatient().has_permission(req_doc, None))
        self.assertTrue(IsDoctorOrPatient().has_permission(req_doc, None))
        self.assertTrue(IsDoctorOrPatient().has_permission(req_pat, None))

    def test_patient_cannot_access_other_patient(self):
        req = self.factory.get("/")
        req.user = self.patient_user_1
        patient, err = resolve_authorized_patient(req, self.patient_2.id)
        self.assertIsNone(patient)
        self.assertEqual(err.status_code, 403)

    def test_patient_auto_resolves_self(self):
        req = self.factory.get("/")
        req.user = self.patient_user_1
        patient, err = resolve_authorized_patient(req, None)
        self.assertIsNone(err)
        self.assertEqual(patient, self.patient_1)

    def test_doctor_requires_relationship_when_enforced(self):
        req = self.factory.get("/")
        req.user = self.doc_user

        patient, err = resolve_authorized_patient(
            req, self.patient_1.id, require_doctor_relationship=True
        )
        self.assertIsNone(patient)
        self.assertEqual(err.status_code, 403)

        Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient_1,
            appointment_date=date(2026, 11, 20),
            appointment_time=time(10, 0),
            status="pending",
        )
        patient, err = resolve_authorized_patient(
            req, self.patient_1.id, require_doctor_relationship=True
        )
        self.assertIsNone(err)
        self.assertEqual(patient, self.patient_1)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "throttle-test"}},
)
class RateLimitingTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = CustomUser.objects.create_user(
            username="throttle_user", email="throttle@medtrax.me", password="Pass123!@#", role="patient"
        )
        self.view = _MockThrottledView.as_view()

    def test_burst_throttle_blocks_after_limit(self):
        from django.core.cache import cache
        cache.clear()

        with patch.dict(AIAgentBurstThrottle.THROTTLE_RATES, {"ai_burst": "2/minute"}):
            for _ in range(2):
                req = self.factory.get("/")
                force_authenticate(req, user=self.user)
                resp = self.view(req)
                self.assertEqual(resp.status_code, 200)

            req = self.factory.get("/")
            force_authenticate(req, user=self.user)
            resp = self.view(req)
            self.assertEqual(resp.status_code, 429)
