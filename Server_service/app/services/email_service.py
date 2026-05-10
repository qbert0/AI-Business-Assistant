import logging
import smtplib
from email.message import EmailMessage

from app.config import SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_SENDER, SMTP_USERNAME, SMTP_USE_TLS


logger = logging.getLogger(__name__)


def send_email(*, to_email: str, subject: str, body: str) -> bool:
    if not SMTP_HOST or not to_email.strip():
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_SENDER
    message["To"] = to_email.strip()
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
            if SMTP_USE_TLS:
                smtp.starttls()
            if SMTP_USERNAME:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(message)
        return True
    except Exception:
        logger.exception("Unable to send email invite to %s", to_email)
        return False
