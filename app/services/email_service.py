"""Email service with pluggable backends (console and SMTP).

- console backend: prints the email to stdout (for development)
- smtp backend: sends via a real SMTP server (for production)
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config.mail_config import MailSettings, get_mail_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Sends emails using the configured backend."""

    def __init__(self, settings: MailSettings | None = None):
        self._settings = settings or get_mail_settings()

    @property
    def backend(self) -> str:
        return self._settings.backend

    def send_verification_code(self, to_email: str, code: str) -> None:
        """Send a verification code to the given email address."""
        subject = "iCommerce — Código de Verificação de Email"
        body = (
            f"Olá!\n\n"
            f"Seu código de verificação é: {code}\n\n"
            f"Este código expira em 15 minutos.\n\n"
            f"Se você não solicitou este código, ignore este email.\n\n"
            f"— Equipe iCommerce"
        )
        html_body = (
            f"<h2>iCommerce — Verificação de Email</h2>"
            f"<p>Olá!</p>"
            f"<p>Seu código de verificação é:</p>"
            f'<p style="font-size:24px;font-weight:bold;letter-spacing:4px;'
            f'background:#f0f0f0;padding:12px;display:inline-block;border-radius:6px;">'
            f"{code}</p>"
            f"<p>Este código expira em <strong>15 minutos</strong>.</p>"
            f"<p>Se você não solicitou este código, ignore este email.</p>"
            f"<hr><p style='color:#888;font-size:12px;'>Equipe iCommerce</p>"
        )
        self._send(to_email, subject, body, html_body)

    def _send(self, to_email: str, subject: str, body: str, html_body: str) -> None:
        """Dispatch to the appropriate backend."""
        if self._settings.backend == "smtp":
            self._send_smtp(to_email, subject, body, html_body)
        else:
            self._send_console(to_email, subject, body)

    def _send_console(self, to_email: str, subject: str, body: str) -> None:
        """Print the email to the console (development backend)."""
        separator = "=" * 60
        logger.info(
            "\n%s\n[CONSOLE EMAIL]\nTo: %s\nSubject: %s\n\n%s\n%s",
            separator, to_email, subject, body, separator,
        )
        print(f"\n{separator}")
        print(f"[CONSOLE EMAIL] To: {to_email}")
        print(f"Subject: {subject}")
        print(f"\n{body}")
        print(f"{separator}\n")

    def _send_smtp(self, to_email: str, subject: str, body: str, html_body: str) -> None:
        """Send the email via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self._settings.from_name} <{self._settings.from_address}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            if self._settings.smtp_tls:
                server = smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port)

            if self._settings.username and self._settings.password:
                server.login(self._settings.username, self._settings.password)

            server.sendmail(self._settings.from_address, to_email, msg.as_string())
            server.quit()
            logger.info("Email sent successfully to %s", to_email)
        except smtplib.SMTPException as e:
            logger.error("Failed to send email to %s: %s", to_email, e)
            raise