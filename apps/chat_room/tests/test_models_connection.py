from django.test import TestCase
from Authapi.models import CustomUser, Doctor
from chat_room.models import DoctorConnection

class DoctorConnectionModelTests(TestCase):
    def setUp(self):
        self.u1 = CustomUser.objects.create_user(username="dconn1", email="dc1@med.com", password="P1", role="doctor")
        self.u2 = CustomUser.objects.create_user(username="dconn2", email="dc2@med.com", password="P1", role="doctor")
        self.doc1 = Doctor.objects.create(
            user=self.u1, first_name="Arthur", last_name="Conan", date_of_birth="1970-01-01",
            gender="M", blood_group="A+", city="London", phone_number="+441234567"
        )
        self.doc2 = Doctor.objects.create(
            user=self.u2, first_name="John", last_name="Watson", date_of_birth="1972-01-01",
            gender="M", blood_group="O+", city="London", phone_number="+447654321"
        )

    def test_connection_creation_default_status(self):
        conn = DoctorConnection.objects.create(from_doctor=self.doc1, to_doctor=self.doc2)
        self.assertEqual(conn.status, "pending")
        self.assertIn("Arthur Conan", str(conn))
        self.assertIn("John Watson", str(conn))
