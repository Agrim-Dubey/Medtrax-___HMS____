from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import CustomUser, Patient

class PatientDashboardProfileAPITests(APITestCase):
    def setUp(self):
        self.pat_u = CustomUser.objects.create_user(username="prof_pat_u", email="ppu2@med.com", password="P1", role="patient")
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Elizabeth", last_name="Bennet", date_of_birth="1995-02-14",
            blood_group="A+", gender="F", city="Hertfordshire", phone_number="+441234455",
            known_allergies="Penicillin"
        )
        self.client.force_authenticate(user=self.pat_u)

    def test_get_patient_dashboard_profile(self):
        url = reverse("patient-dashboard-profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], "Elizabeth Bennet")
        self.assertEqual(response.data["known_allergies"], "Penicillin")
