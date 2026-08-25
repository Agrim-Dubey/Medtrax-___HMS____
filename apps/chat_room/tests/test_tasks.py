from django.test import TestCase
from datetime import date, time
from django.utils import timezone
from authentication.models import CustomUser, Doctor, Patient
from appointments.models import Appointment
from chat_room.models import ChatRoom
from chat_room.tasks import disable_expired_chats

class ChatExpiryTasksTests(TestCase):
    def setUp(self):
        self.u_d = CustomUser.objects.create_user(username="exp_d", email="ed@med.com", password="P1", role="doctor")
        self.u_p = CustomUser.objects.create_user(username="exp_p", email="ep@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.u_d, first_name="Dana", last_name="Scully", date_of_birth="1974-01-01",
            gender="F", blood_group="O+", city="DC", phone_number="+1555000999"
        )
        self.patient = Patient.objects.create(
            user=self.u_p, first_name="Fox", last_name="Mulder", date_of_birth="1971-01-01",
            blood_group="A+", gender="M", city="DC", phone_number="+1555000888"
        )

    def test_disable_expired_chats(self):
        past_appt = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date=date(2020, 1, 1), appointment_time=time(10, 0), status="completed"
        )
        room = ChatRoom.objects.create(
            room_type="patient_doctor", is_active=True, appointment=past_appt
        )
        result = disable_expired_chats()
        self.assertIn("Disabled", result)
        room.refresh_from_db()
        self.assertFalse(room.is_active)
