from django.core.management.base import BaseCommand
from appointments.models import Appointment
from chat_room.models import ChatRoom

class Command(BaseCommand):
    help = 'Create chat rooms for confirmed appointments that don\'t have them'

    def handle(self, *args, **options):
        confirmed_appointments = Appointment.objects.filter(status='confirmed')
        created_count = 0
        
        for appointment in confirmed_appointments:
            if not hasattr(appointment, 'chat_room') or appointment.chat_room is None:
                chat_room = ChatRoom.objects.create(
                    room_type='patient_doctor',
                    is_active=True,
                    appointment=appointment
                )
                chat_room.participants.add(appointment.patient.user, appointment.doctor.user)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created chat room {chat_room.id} for appointment {appointment.id}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n Created {created_count} chat rooms')
        )