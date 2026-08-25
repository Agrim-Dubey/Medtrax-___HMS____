from django.test import TestCase
from authentication.models import CustomUser, Doctor, Patient
from prescription.models import Prescription
from prescription.selectors import get_doctor_prescriptions, get_patient_prescriptions

class PrescriptionSelectorsTests(TestCase):
    def setUp(self):
        self.doc_u = CustomUser.objects.create_user(username="sel_d", email="seld@med.com", password="P1", role="doctor")
        self.pat_u = CustomUser.objects.create_user(username="sel_p", email="selp@med.com", password="P1", role="patient")
        self.doctor = Doctor.objects.create(
            user=self.doc_u, first_name="John", last_name="Watson", date_of_birth="1970-01-01",
            gender="M", blood_group="O+", city="London", phone_number="+44123890"
        )
        self.patient = Patient.objects.create(
            user=self.pat_u, first_name="Irene", last_name="Adler", date_of_birth="1980-01-01",
            blood_group="B+", gender="F", city="London", phone_number="+44890123"
        )
        self.rx = Prescription.objects.create(
            doctor=self.doctor, patient=self.patient,
            chief_complaint="Fatigue", diagnosis="Anemia"
        )

    def test_prescription_selectors_return_records(self):
        doc_rxs = get_doctor_prescriptions(self.doctor)
        pat_rxs = get_patient_prescriptions(self.patient)
        self.assertIn(self.rx, doc_rxs)
        self.assertIn(self.rx, pat_rxs)
