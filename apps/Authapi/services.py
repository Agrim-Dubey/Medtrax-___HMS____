from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
import random
import logging

from Authapi.models import CustomUser
from Authapi.tasks import send_otp_email_task

logger = logging.getLogger(__name__)

@transaction.atomic
def create_user_account(*, email: str, password: str, role: str) -> CustomUser:
    """
    Creates a new user account or resets an unverified one, and queues an OTP email.
    """
    otp = str(random.randint(100000, 999999))

    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            'username': email,
            'role': role,
            'is_verified': False,
            'is_profile_complete': False
        }
    )

    if not created and user.is_verified:
        raise ValidationError("This email is already registered.")

    # Always reset the password and OTP fields for unverified accounts trying to sign up again
    user.set_password(password)
    user.role = role
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.otp_attempts = 0
    user.otp_locked_until = None
    user.save()

    try:
        send_otp_email_task.delay(email, otp, "Verification")
        logger.info(f"OTP email queued via Celery for {email}")
    except Exception as e:
        logger.error(f"Failed to queue email task: {e}")
        raise

    return user
