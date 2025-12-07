import smtplib
import logging
from email.message import EmailMessage
from typing import Dict
from sqlmodel import Session, select
from app.models import SystemSetting

logger = logging.getLogger("email")


def _bool_val(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "on"}


def load_settings(session: Session) -> Dict[str, str]:
    settings = session.exec(select(SystemSetting)).all()
    return {s.key: s.value for s in settings}


def send_email(to_email: str, subject: str, body: str, session: Session) -> bool:
    settings = load_settings(session)
    host = settings.get("smtp_host")
    port = int(settings.get("smtp_port", "0") or 0)
    username = settings.get("smtp_username")
    password = settings.get("smtp_password")
    use_tls = _bool_val(settings.get("smtp_use_tls", "true"))
    use_ssl = _bool_val(settings.get("smtp_use_ssl", "false"))
    sender = settings.get("smtp_sender") or username

    if not host or not port or not sender:
        return False

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=10) as server:
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=10) as server:
                if use_tls:
                    server.starttls()
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
