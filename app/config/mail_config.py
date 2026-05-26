"""Email configuration loaded from environment variables."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class MailSettings:
    """Immutable email configuration settings."""

    backend: str  # "console" or "smtp"
    smtp_host: str
    smtp_port: int
    smtp_tls: bool
    username: str
    password: str
    from_name: str
    from_address: str


def get_mail_settings() -> MailSettings:
    """Build and return MailSettings from environment variables."""
    backend = os.getenv("MAIL_BACKEND", "console").lower()
    return MailSettings(
        backend=backend,
        smtp_host=os.getenv("MAIL_SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.getenv("MAIL_SMTP_PORT", "587")),
        smtp_tls=os.getenv("MAIL_SMTP_TLS", "true").lower() == "true",
        username=os.getenv("MAIL_USERNAME", ""),
        password=os.getenv("MAIL_PASSWORD", ""),
        from_name=os.getenv("MAIL_FROM_NAME", "eCommerce"),
        from_address=os.getenv("MAIL_FROM_ADDRESS", "noreply@ecommerce.com"),
    )