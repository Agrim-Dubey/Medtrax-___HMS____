from django.test import TestCase
from Authapi.models import CustomUser
from chat_room.models import ChatRoom, Message

class ChatRoomAndMessageModelTests(TestCase):
    def setUp(self):
        self.u1 = CustomUser.objects.create_user(username="chat_u1", email="u1@test.com", password="P1")
        self.u2 = CustomUser.objects.create_user(username="chat_u2", email="u2@test.com", password="P1")
        self.room = ChatRoom.objects.create(room_type="patient_doctor", is_active=True)
        self.room.participants.add(self.u1, self.u2)

    def test_chatroom_creation_and_participants(self):
        self.assertEqual(self.room.room_type, "patient_doctor")
        self.assertTrue(self.room.is_active)
        self.assertEqual(self.room.participants.count(), 2)

    def test_message_creation_and_defaults(self):
        msg = Message.objects.create(room=self.room, sender=self.u1, content="Hello Doctor")
        self.assertFalse(msg.is_read)
        self.assertEqual(msg.content, "Hello Doctor")
        self.assertIn("Hello Doctor", str(msg))
