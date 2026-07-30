from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser, Doctor
from chat_room.models import DoctorConnection

class DoctorConnectionAPITests(APITestCase):
    def setUp(self):
        self.u1 = CustomUser.objects.create_user(username="dapi1", email="da1@med.com", password="P1", role="doctor", is_verified=True)
        self.u2 = CustomUser.objects.create_user(username="dapi2", email="da2@med.com", password="P1", role="doctor", is_verified=True)
        self.doc1 = Doctor.objects.create(
            user=self.u1, first_name="Leonard", last_name="McCoy", date_of_birth="1970-01-01",
            gender="M", blood_group="B+", city="SF", phone_number="+1555123987", is_approved=True
        )
        self.doc2 = Doctor.objects.create(
            user=self.u2, first_name="Beverly", last_name="Crusher", date_of_birth="1975-01-01",
            gender="F", blood_group="AB+", city="SF", phone_number="+1555987123", is_approved=True
        )
        self.client.force_authenticate(user=self.u1)

    def test_send_connection_request(self):
        url = reverse("doctor-send-request")
        response = self.client.post(url, {"to_doctor_id": self.doc2.id}, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(DoctorConnection.objects.filter(from_doctor=self.doc1, to_doctor=self.doc2).exists())

    def test_accept_connection_request(self):
        conn = DoctorConnection.objects.create(from_doctor=self.doc2, to_doctor=self.doc1, status="pending")
        url = reverse("doctor-accept", kwargs={"pk": conn.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conn.refresh_from_db()
        self.assertEqual(conn.status, "accepted")
        self.assertIsNotNone(conn.chat_room)
