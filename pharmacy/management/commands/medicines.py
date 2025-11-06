from django.core.management.base import BaseCommand
from pharmacy.models import Medicine
from datetime import datetime, timedelta
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate database with dummy medicines'

    def handle(self, *args, **kwargs):
        medicines_data = [
            {
                'name': 'Paracetamol',
                'description': 'Pain reliever and fever reducer',
                'manufacturer': 'PharmaCorp',
                'category': 'tablet',
                'price': Decimal('15.00'),
                'quantity_available': 500,
                'dosage': '500mg',
                'expiry_date': datetime.now().date() + timedelta(days=730),
                'requires_prescription': False,
                'image_url': 'https://via.placeholder.com/200x200?text=Paracetamol'
            },
            {
                'name': 'Amoxicillin',
                'description': 'Antibiotic for bacterial infections',
                'manufacturer': 'MediPharma',
                'category': 'capsule',
                'price': Decimal('120.00'),
                'quantity_available': 300,
                'dosage': '250mg',
                'expiry_date': datetime.now().date() + timedelta(days=365),
                'requires_prescription': True,
                'image_url': 'https://via.placeholder.com/200x200?text=Amoxicillin'
            },
            {
                'name': 'Cough Syrup',
                'description': 'Relief from cough and cold',
                'manufacturer': 'HealthPlus',
                'category': 'syrup',
                'price': Decimal('85.00'),
                'quantity_available': 200,
                'dosage': '100ml',
                'expiry_date': datetime.now().date() + timedelta(days=540),
                'requires_prescription': False,
                'image_url': 'https://via.placeholder.com/200x200?text=Cough+Syrup'
            },
            {
                'name': 'Insulin',
                'description': 'Controls blood sugar in diabetes',
                'manufacturer': 'DiabetesCare',
                'category': 'injection',
                'price': Decimal('450.00'),
                'quantity_available': 150,
                'dosage': '10ml',
                'expiry_date': datetime.now().date() + timedelta(days=365),
                'requires_prescription': True,
                'image_url': 'https://via.placeholder.com/200x200?text=Insulin'
            },
            {
                'name': 'Aspirin',
                'description': 'Pain reliever and anti-inflammatory',
                'manufacturer': 'PharmaCorp',
                'category': 'tablet',
                'price': Decimal('25.00'),
                'quantity_available': 600,
                'dosage': '75mg',
                'expiry_date': datetime.now().date() + timedelta(days=900),
                'requires_prescription': False,
                'image_url': 'https://via.placeholder.com/200x200?text=Aspirin'
            },
            {
                'name': 'Ciprofloxacin',
                'description': 'Antibiotic for bacterial infections',
                'manufacturer': 'BioMed',
                'category': 'tablet',
                'price': Decimal('180.00'),
                'quantity_available': 250,
                'dosage': '500mg',
                'expiry_date': datetime.now().date() + timedelta(days=450),
                'requires_prescription': True,
                'image_url': 'https://via.placeholder.com/200x200?text=Ciprofloxacin'
            },
            {
                'name': 'Hydrocortisone Cream',
                'description': 'Treats skin inflammation and itching',
                'manufacturer': 'DermaCare',
                'category': 'ointment',
                'price': Decimal('95.00'),
                'quantity_available': 180,
                'dosage': '30g',
                'expiry_date': datetime.now().date() + timedelta(days=600),
                'requires_prescription': False,
                'image_url': 'https://via.placeholder.com/200x200?text=Hydrocortisone'
            },
            {
                'name': 'Eye Drops',
                'description': 'Relief from dry and irritated eyes',
                'manufacturer': 'VisionCare',
                'category': 'drops',
                'price': Decimal('65.00'),
                'quantity_available': 220,
                'dosage': '10ml',
                'expiry_date': datetime.now().date() + timedelta(days=365),
                'requires_prescription': False,
                'image_url': 'https://via.placeholder.com/200x200?text=Eye+Drops'
            },
            {
                'name': 'Albuterol Inhaler',
                'description': 'Bronchodilator for asthma',
                'manufacturer': 'RespiraTech',
                'category': 'inhaler',
                'price': Decimal('320.00'),
                'quantity_available': 100,
                'dosage': '200 doses',
                'expiry_date': datetime.now().date() + timedelta(days=540),
                'requires_prescription': True,
                'image_url': 'https://via.placeholder.com/200x200?text=Inhaler'
            },
            {
                'name': 'Vitamin D3',
                'description': 'Supports bone health and immunity',
                'manufacturer': 'NutriHealth',
                'category': 'capsule',
                'price': Decimal('150.00'),
                'quantity_available': 400,
                'dosage': '1000 IU',
                'expiry_date': datetime.now().date() + timedelta(days=730),
                'requires_prescription': False,
                'image_url': 'https://via.placeholder.com/200x200?text=Vitamin+D3'
            },
            {
                'name': 'Omeprazole',
                'description': 'Reduces stomach acid production',
                'manufacturer': 'GastroCare',
                'category': 'capsule',
                'price': Decimal('110.00'),
                'quantity_available': 350,
                'dosage': '20mg',
                'expiry_date': datetime.now().date() + timedelta(days=600),
                'requires_prescription': True,
                'image_url': 'https://via.placeholder.com/200x200?text=Omeprazole'
            },
            {
                'name': 'Ibuprofen',
                'description': 'Anti-inflammatory pain reliever',
                'manufacturer': 'PharmaCorp',
                'category': 'tablet',
                'price': Decimal('40.00'),
                'quantity_available': 550,
                'dosage': '400mg',
                'expiry_date': datetime.now().date() + timedelta(days=800),
                'requires_prescription': False,
                'image_url': 'https://via.placeholder.com/200x200?text=Ibuprofen'
            },
            {
                'name': 'Metformin',
                'description': 'Controls blood sugar in type 2 diabetes',
                'manufacturer': 'DiabetesCare',
                'category': 'tablet',
                'price': Decimal('75.00'),
                'quantity_available': 400,
                'dosage': '500mg',
                'expiry_date': datetime.now().date() + timedelta(days=540),
                'requires_prescription': True,
                'image_url': 'https://via.placeholder.com/200x200?text=Metformin'
            },
            {
                'name': 'Antihistamine Syrup',
                'description': 'Relief from allergies',
                'manufacturer': 'AllergyCare',
                'category': 'syrup',
                'price': Decimal('90.00'),
                'quantity_available': 280,
                'dosage': '120ml',
                'expiry_date': datetime.now().date() + timedelta(days=450),
                'requires_prescription': False,
                'image_url': 'https://via.placeholder.com/200x200?text=Antihistamine'
            },
            {
                'name': 'Atorvastatin',
                'description': 'Lowers cholesterol levels',
                'manufacturer': 'CardioCare',
                'category': 'tablet',
                'price': Decimal('200.00'),
                'quantity_available': 320,
                'dosage': '10mg',
                'expiry_date': datetime.now().date() + timedelta(days=600),
                'requires_prescription': True,
                'image_url': 'https://via.placeholder.com/200x200?text=Atorvastatin'
            },
        ]

        created_count = 0
        for medicine_data in medicines_data:
            medicine, created = Medicine.objects.get_or_create(
                name=medicine_data['name'],
                dosage=medicine_data['dosage'],
                defaults=medicine_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {medicine.name} - {medicine.dosage}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Already exists: {medicine.name} - {medicine.dosage}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {created_count} new medicines')
        )
        self.stdout.write(
            self.style.SUCCESS(f'✓ Total medicines in database: {Medicine.objects.count()}')
        )
        