from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import CustomUser
from chat_room.models import ChatRoom, Message

class ChatMessagingAPITests(APITestCase):
    def setUp(self):
        self.u1 = CustomUser.objects.create_user(username="msg_u1", email="mu1@med.com", password="P1")
        self.u2 = CustomUser.objects.create_user(username="msg_u2", email="mu2@med.com", password="P1")
        self.room = ChatRoom.objects.create(room_type="patient_doctor", is_active=True)
        self.room.participants.add(self.u1, self.u2)
        self.client.force_authenticate(user=self.u1)

    def test_send_message_via_rest(self):
        url = reverse("chat-send-message", kwargs={"pk": self.room.id})
        response = self.client.post(url, {"content": "Checking on symptoms"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Message.objects.filter(room=self.room, content="Checking on symptoms").exists())

    def test_mark_messages_as_read(self):
        msg = Message.objects.create(room=self.room, sender=self.u2, content="Patient query")
        url = reverse("chat-mark-read", kwargs={"pk": self.room.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)
