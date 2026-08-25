from django.test import TestCase
from authentication.models import CustomUser, Doctor, Patient
from appointments.models import Appointment
from chat_room.models import ChatRoom

class AppointmentSignalsTests(TestCase):
    def setUp(self):
        self.doc_user = CustomUser.objects.create_user(username="sig_d", email="sd@med.com", password="P1", role="doctor")
        self.pat_user = CustomUser.objects.create_user(username="sig_p", email="sp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_user, first_name="Chris", last_name="Taub", date_of_birth="1972-01-01",
            gender="M", blood_group="O+", city="Trenton", phone_number="+1555888123"
        )
        self.patient = Patient.objects.create(
            user=self.pat_user, first_name="Remy", last_name="Hadley", date_of_birth="1984-01-01",
            blood_group="AB-", gender="F", city="Trenton", phone_number="+1555888456"
        )

    def test_confirming_appointment_creates_chat_room(self):
        appt = Appointment.objects.create(
            doctor=self.doctor, patient=self.patient,
            appointment_date="2026-12-10", appointment_time="15:00", status="pending"
        )
        self.assertEqual(ChatRoom.objects.filter(appointment=appt).count(), 0)

        appt.status = "confirmed"
        appt.save()

        chat = ChatRoom.objects.filter(appointment=appt).first()
        self.assertIsNotNone(chat)
        self.assertEqual(chat.room_type, "patient_doctor")
        self.assertTrue(chat.is_active)
        self.assertTrue(chat.participants.filter(id=self.doc_user.id).exists())
        self.assertTrue(chat.participants.filter(id=self.pat_user.id).exists())
