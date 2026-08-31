# backend/utils/email_sender.py
"""Utility for sending emails via SMTP.

Relies on SMTP configuration variables defined in backend/config.py:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM
"""
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from backend.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM


def send_email(to_address: str, subject: str, body: str) -> None:
    """Send a plain‑text email.

    Args:
        to_address: Recipient email address.
        subject: Email subject line.
        body: Plain text email body.
    """
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Study Companion", EMAIL_FROM))
    msg["To"] = to_address

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        # Fallback: log email content to console for debugging
        print("[EmailSender] Failed to send email via SMTP. Exception:", e)
        print("--- Email Details ---")
        print(f"To: {to_address}\nSubject: {subject}\n\n{body}\n--- End ---")
        # Optionally, re-raise or silently ignore based on environment
        # Here we choose to ignore to allow application flow to continue.
        pass
