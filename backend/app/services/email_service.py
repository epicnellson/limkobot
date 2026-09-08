import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    if not (settings.EMAIL_USER and settings.EMAIL_PASSWORD):
        logger.info("Email credentials not set; skipping email to %s: %s", to, subject)
        return

    message = EmailMessage()
    message["From"] = settings.EMAIL_USER
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
        server.starttls()
        server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
        server.send_message(message)