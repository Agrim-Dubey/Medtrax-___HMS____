from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser, Patient

class PatientCompleteProfileUpdateAPITests(APITestCase):
    def setUp(self):
        self.pat_u = CustomUser.objects.create_user(username="upd_pat_u", email="upu@med.com", password="P1", role="patient")
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="George", last_name="Wickham", date_of_birth="1990-01-01",
            blood_group="O-", gender="M", city="Brighton", phone_number="+4466655544"
        )
        self.client.force_authenticate(user=self.pat_u)

    def test_update_patient_profile_details(self):
        url = reverse("patient-complete-profile")
        payload = {
            "city": "Newcastle",
            "emergency_contact": "+4411122233"
        }
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.city, "Newcastle")
        self.assertEqual(self.patient.emergency_contact, "+4411122233")
