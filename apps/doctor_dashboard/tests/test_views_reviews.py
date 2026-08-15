from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser, Doctor, Patient
from doctor_dashboard.models import DoctorReview

class DoctorRecentReviewsAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="rw_doc_u", email="rwdu@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="rw_pat_u", email="rwpu@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Abraham", last_name="Verghese", date_of_birth="1955-01-01",
            gender="M", blood_group="B+", city="Stanford", phone_number="+1555678123"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Henry", last_name="Marsh", date_of_birth="1950-01-01",
            blood_group="A+", gender="M", city="London", phone_number="+445551234"
        )
        DoctorReview.objects.create(
            doctor=self.doctor, patient=self.patient, rating=5, comment="Compassionate bedside manner."
        )
        self.client.force_authenticate(user=self.doc_u)

    def test_get_recent_reviews(self):
        url = reverse("doctor-recent-reviews")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        self.assertEqual(response.data[0]["rating"], 5)
