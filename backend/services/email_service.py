import os
import smtplib
from email.message import EmailMessage

EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')

def send_otp_email(to_email: str, otp: str):
    """Send OTP email using Gmail SMTP.
    Args:
        to_email: Recipient email address.
        otp: 6‑digit verification code.
    """
    if not EMAIL_USER or not EMAIL_PASS:
        raise RuntimeError('Email credentials not configured')

    msg = EmailMessage()
    msg['Subject'] = 'StudyMate AI Verification Code'
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg.set_content(f"""
------------------------------------------------

StudyMate AI

Verify your account

Your verification code is:

{otp}

This code expires in 5 minutes.

If you didn't request this account,
please ignore this email.

------------------------------------------------
""")
    # Gmail SMTP server
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
