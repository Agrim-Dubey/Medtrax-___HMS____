from django.test import TestCase
from Authapi.models import CustomUser, Doctor, Patient
from prescription.models import Prescription, Medication, LabTest

class PrescriptionModelsTests(TestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="rx_d", email="rxd@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="rx_p", email="rxp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="Hawkeye", last_name="Pierce", date_of_birth="1970-01-01",
            gender="M", blood_group="A+", city="Seoul", phone_number="+1555112233"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Radar", last_name="OReilly", date_of_birth="1980-01-01",
            blood_group="O+", gender="M", city="Seoul", phone_number="+1555445566"
        )

    def test_prescription_and_nested_entities(self):
        rx = Prescription.objects.create(
            doctor=self.doctor, patient=self.patient,
            chief_complaint="Severe cough and fever",
            diagnosis="Acute bronchitis",
            temperature=101.5,
            blood_pressure="120/80"
        )
        med = Medication.objects.create(
            prescription=rx, medicine_name="Amoxicillin", dosage="500mg",
            frequency="thrice_daily", duration=7, duration_unit="days"
        )
        lab = LabTest.objects.create(
            prescription=rx, test_name="Chest X-Ray", instructions="PA View"
        )
        self.assertIn("Prescription for Radar OReilly", str(rx))
        self.assertIn("Amoxicillin", str(med))
        self.assertIn("Chest X-Ray", str(lab))
        self.assertEqual(rx.medications.count(), 1)
        self.assertEqual(rx.lab_tests.count(), 1)
