import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from .models import PasswordResetOTP

SUBJECT = 'Your DevInsight password reset code'

_HTML_TEMPLATE = """\
<div style="background:#000000;padding:40px 20px;font-family:-apple-system,'Segoe UI',Roboto,sans-serif;">
  <table role="presentation" width="100%" style="max-width:420px;margin:0 auto;border-collapse:collapse;">
    <tr>
      <td style="padding-bottom:24px;">
        <span style="display:inline-flex;align-items:center;gap:8px;">
          <span style="display:inline-block;width:26px;height:26px;border-radius:6px;background:#6b2c35;
                       color:#ffffff;font-family:monospace;font-weight:700;font-size:14px;
                       line-height:26px;text-align:center;">&lt;/&gt;</span>
          <span style="color:#ffffff;font-weight:700;font-size:16px;">DevInsight</span>
        </span>
      </td>
    </tr>
    <tr>
      <td style="background:#18181b;border:1px solid #27272a;border-radius:16px;padding:32px;">
        <p style="color:#e4e4e7;font-size:15px;margin:0 0 20px;">
          Use this code to reset your DevInsight password:
        </p>
        <div style="background:#000000;border:1px solid #3f3f46;border-radius:10px;padding:18px;
                    text-align:center;margin-bottom:20px;">
          <span style="color:#c99aa1;font-size:32px;font-weight:700;letter-spacing:0.35em;
                       font-family:monospace;">{code}</span>
        </div>
        <p style="color:#a1a1aa;font-size:13px;line-height:1.6;margin:0;">
          This code expires in {minutes} minutes. If you didn't request this, you can safely ignore this email.
        </p>
      </td>
    </tr>
  </table>
</div>
"""


def _send_via_sendgrid(email, text_body, html_body):
    resp = requests.post(
        'https://api.sendgrid.com/v3/mail/send',
        headers={'Authorization': f'Bearer {settings.SENDGRID_API_KEY}'},
        json={
            'personalizations': [{'to': [{'email': email}]}],
            'from': {'email': settings.SENDGRID_FROM_EMAIL, 'name': settings.SENDGRID_FROM_NAME},
            'reply_to': {'email': settings.SENDGRID_FROM_EMAIL, 'name': settings.SENDGRID_FROM_NAME},
            'subject': SUBJECT,
            'content': [
                {'type': 'text/plain', 'value': text_body},
                {'type': 'text/html', 'value': html_body},
            ],
        },
        timeout=15,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f'SendGrid API returned {resp.status_code}: {resp.text[:500]}')


def _send_via_django_backend(email, text_body, html_body):
    message = EmailMultiAlternatives(
        subject=SUBJECT,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    message.attach_alternative(html_body, 'text/html')
    message.send(fail_silently=False)


def send_otp_email(email, otp):
    text_body = (
        f'Your password reset code is: {otp.code}\n\n'
        f'This code expires in {PasswordResetOTP.OTP_LIFETIME_MINUTES} minutes.\n\n'
        "If you didn't request this, you can safely ignore this email."
    )
    html_body = _HTML_TEMPLATE.format(code=otp.code, minutes=PasswordResetOTP.OTP_LIFETIME_MINUTES)

    try:
        # Render's free tier blocks outbound SMTP entirely (confirmed via a real "Network is
        # unreachable" error in production) but not HTTPS, so SendGrid is used whenever it's
        # configured; otherwise this falls back to whatever EMAIL_BACKEND is set to (console for
        # local dev, or SMTP if someone configures it directly), completely unchanged from before.
        if settings.SENDGRID_API_KEY:
            _send_via_sendgrid(email, text_body, html_body)
        else:
            _send_via_django_backend(email, text_body, html_body)
    except Exception as exc:  # noqa: BLE001
        # ForgotPasswordView always returns the same generic response regardless of send
        # success, so this print is the *only* place a real send failure would ever be visible.
        print(f'[accounts] Failed to send OTP email to {email}: {exc}', flush=True)
