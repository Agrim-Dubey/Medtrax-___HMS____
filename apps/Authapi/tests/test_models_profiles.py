from django.test import TestCase
from datetime import date
from Authapi.models import CustomUser, Doctor, Patient

class ProfileModelsTests(TestCase):
    def setUp(self):
        self.doctor_user = CustomUser.objects.create_user(
            username="doc_test", email="doc@example.com", password="Pass123!Safe", role="doctor"
        )
        self.patient_user = CustomUser.objects.create_user(
            username="pat_test", email="pat@example.com", password="Pass123!Safe", role="patient"
        )

    def test_doctor_profile_creation(self):
        doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name="Gregory",
            last_name="House",
            date_of_birth=date(1975, 5, 15),
            gender="M",
            blood_group="O+",
            city="Princeton",
            phone_number="+1555019283",
            registration_number="REG-9912",
            specialization="Diagnostics"
        )
        self.assertEqual(doctor.get_full_name(), "Gregory House")
        self.assertIn("Dr. Gregory House", str(doctor))
        self.assertFalse(doctor.is_approved)

    def test_patient_profile_creation(self):
        patient = Patient.objects.create(
            user=self.patient_user,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            blood_group="A+",
            gender="M",
            city="New York",
            phone_number="+1555987654",
            is_insurance=True,
            ins_company_name="BlueShield"
        )
        self.assertEqual(patient.get_full_name(), "John Doe")
        self.assertIn("John Doe - Patient", str(patient))
        self.assertTrue(patient.is_insurance)
