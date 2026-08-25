from django.test import TestCase
from authentication.models import CustomUser, Doctor, Patient
from doctor_dashboard.models import DoctorReview

class DoctorReviewModelTests(TestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="rev_d", email="rd@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="rev_p", email="rp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Sanjay", last_name="Gupta", date_of_birth="1969-01-01",
            gender="M", blood_group="O+", city="Atlanta", phone_number="+1555333777"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Jane", last_name="Roe", date_of_birth="1988-01-01",
            blood_group="A+", gender="F", city="Atlanta", phone_number="+1555444888"
        )

    def test_doctor_review_creation(self):
        review = DoctorReview.objects.create(
            doctor=self.doctor, patient=self.patient, rating=5, comment="Exceptional care and clear explanations."
        )
        self.assertEqual(review.rating, 5)
        self.assertIn("rated Dr. Sanjay Gupta - 5★", str(review))
