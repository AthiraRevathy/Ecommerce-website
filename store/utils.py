# otp_utils.py
from django.core.mail import send_mail
from django.conf import settings
from .models import OTPVerification
import random
from django.utils import timezone

def send_otp(user):
    otp = str(random.randint(100000, 999999))
    OTPVerification.objects.update_or_create(user=user, defaults={'otp': otp, 'created_at': timezone.now()})
    send_mail(
        'Your OTP Code',
        f'Your OTP code is {otp}',
        'from@example.com',
        [user.email],
        fail_silently=False,
    )

def verify_otp(user, otp):
    try:
        otp_verification = OTPVerification.objects.get(user=user)
        if otp_verification.otp == otp and otp_verification.is_valid():
            return True
        return False
    except OTPVerification.DoesNotExist:
        return False