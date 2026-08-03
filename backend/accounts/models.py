import random
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_otp_code():
    return f'{random.randint(0, 999999):06d}'


class PasswordResetOTP(models.Model):
    OTP_LIFETIME_MINUTES = 10

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reset_otps')
    code = models.CharField(max_length=6, default=generate_otp_code)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=self.OTP_LIFETIME_MINUTES)

    def __str__(self):
        return f'PasswordResetOTP({self.user}, used={self.used})'
