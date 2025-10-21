from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_otp_email_task(email, otp, email_type):
    subject_map = {
        'verification': 'Verify Your Email - OTP',
        'reset': 'Reset Your Password - OTP',
        'resend': 'Your New Verification OTP'
    }
    
    subject = subject_map.get(email_type, 'Your OTP Code')
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 5px; margin-top: 20px; }}
            .otp {{ font-size: 32px; font-weight: bold; color: #4CAF50; text-align: center; padding: 20px; background-color: white; border-radius: 5px; margin: 20px 0; letter-spacing: 5px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Medtrax Healthcare</h1>
            </div>
            <div class="content">
                <h2>Your OTP Code</h2>
                <p>Hello,</p>
                <p>Your OTP code is:</p>
                <div class="otp">{otp}</div>
                <p><strong>This code is valid for 3 minutes.</strong></p>
                <p>If you didn't request this code, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Medtrax. All rights reserved.</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_message = f"""
    Hello,
    
    Your OTP code is: {otp}
    
    This code is valid for 3 minutes.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    Medtrax Healthcare Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
            html_message=html_message
        )
        logger.info(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        raise