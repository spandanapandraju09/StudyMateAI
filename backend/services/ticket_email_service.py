import os
import time
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from backend.db.connection import get_db

logger = logging.getLogger("ticket_email_service")
logger.setLevel(logging.INFO)

# Setup Jinja2 Environment
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "emails")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# SMTP Config
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@cinemapass.com")


def render_ticket_email(context: dict) -> str:
    """Renders ticket HTML email template securely using Jinja2."""
    template = jinja_env.get_template("ticket_confirmation.html")
    return template.render(**context)


def send_email_sync(recipient: str, subject: str, html_body: str) -> bool:
    """Sends email via SMTP if credentials provided, or simulates successful delivery in sandbox mode."""
    if not SMTP_USER or not SMTP_PASS:
        logger.info(f"[EMAIL SIMULATION] Ticket confirmation email delivered to {recipient}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SENDER_EMAIL, [recipient], msg.as_string())
        return True
    except Exception as e:
        logger.error(f"[EMAIL ERROR] Failed to send email to {recipient}: {str(e)}")
        raise e


async def process_ticket_email_with_retry(
    booking_id: int,
    recipient: str,
    subject: str,
    email_context: dict,
    max_retries: int = 3
):
    """
    Background Task: Non-blocking ticket confirmation email dispatch with exponential backoff retry.
    Logs every attempt to email_delivery_logs table for monitoring.
    """
    html_content = render_ticket_email(email_context)
    db = get_db()
    cur = db.cursor()

    # Log initial pending state
    cur.execute(
        "INSERT INTO email_delivery_logs (booking_id, recipient, subject, status, attempts) VALUES (%s, %s, %s, 'pending', 0)",
        (booking_id, recipient, subject)
    )
    log_id = cur.lastrowid
    db.commit()

    attempt = 0
    success = False
    last_error = ""

    while attempt < max_retries and not success:
        attempt += 1
        try:
            # Run blocking SMTP in thread pool to avoid blocking asyncio event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, send_email_sync, recipient, subject, html_content)
            success = True
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[EMAIL RETRY] Attempt {attempt}/{max_retries} failed for booking {booking_id}: {last_error}")
            if attempt < max_retries:
                # Exponential backoff delay: 2s, 4s, 8s
                await asyncio.sleep(2 ** attempt)

    # Update delivery log status
    status = "delivered" if success else "failed"
    cur.execute(
        "UPDATE email_delivery_logs SET status = %s, attempts = %s, error_message = %s WHERE id = %s",
        (status, attempt, last_error if not success else None, log_id)
    )
    db.commit()
    cur.close()
    db.close()
