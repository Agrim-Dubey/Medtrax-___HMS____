from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from Authapi.models import CustomUser, Doctor, Patient
from chat_room.models import ChatRoom

class ChatListAPITests(APITestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="chat_doc", email="cd@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="chat_pat", email="cp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Stephen", last_name="Strange", date_of_birth="1978-01-01",
            gender="M", blood_group="A+", city="NY", phone_number="+1555432109"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Peter", last_name="Parker", date_of_birth="2001-01-01",
            blood_group="O+", gender="M", city="NY", phone_number="+1555098765"
        )
        self.room = ChatRoom.objects.create(room_type="patient_doctor", is_active=True)
        self.room.participants.add(self.doc_u, self.pat_u)

    def test_patient_can_list_their_chats(self):
        self.client.force_authenticate(user=self.pat_u)
        url = reverse("patient-chats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_doctor_can_list_patient_chats(self):
        self.client.force_authenticate(user=self.doc_u)
        url = reverse("doctor-patient-chats")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
