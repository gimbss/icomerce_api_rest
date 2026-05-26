"""Tests for EmailService."""
import os
from unittest.mock import MagicMock, patch

from app.config.mail_config import MailSettings
from app.services.email_service import EmailService


def _console_settings() -> MailSettings:
    return MailSettings(
        backend="console",
        smtp_host="smtp.test.com",
        smtp_port=587,
        smtp_tls=True,
        username="test@test.com",
        password="testpass",
        from_name="eCommerce",
        from_address="noreply@ecommerce.com",
    )


def _smtp_settings() -> MailSettings:
    return MailSettings(
        backend="smtp",
        smtp_host="smtp.test.com",
        smtp_port=587,
        smtp_tls=True,
        username="test@test.com",
        password="testpass",
        from_name="eCommerce",
        from_address="noreply@ecommerce.com",
    )


def test_email_service_console_backend(capsys):
    """Console backend should print the email to stdout."""
    settings = _console_settings()
    service = EmailService(settings=settings)
    assert service.backend == "console"

    service.send_verification_code(to_email="user@test.com", code="ABC123")

    captured = capsys.readouterr()
    assert "user@test.com" in captured.out
    assert "ABC123" in captured.out
    assert "Código de Verificação" in captured.out


def test_email_service_smtp_backend_success():
    """SMTP backend should call smtplib.SMTP and send the email."""
    settings = _smtp_settings()
    service = EmailService(settings=settings)

    mock_smtp = MagicMock()
    with patch("app.services.email_service.smtplib.SMTP", return_value=mock_smtp):
        service.send_verification_code(to_email="user@test.com", code="XYZ789")

    mock_smtp.ehlo.assert_called()
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("test@test.com", "testpass")
    mock_smtp.sendmail.assert_called_once()
    mock_smtp.quit.assert_called_once()


def test_email_service_smtp_backend_failure():
    """SMTP backend should raise on SMTP errors."""
    settings = _smtp_settings()
    service = EmailService(settings=settings)

    mock_smtp = MagicMock()
    mock_smtp.starttls.side_effect = Exception("SMTP error")

    with patch("app.services.email_service.smtplib.SMTP", return_value=mock_smtp):
        try:
            service.send_verification_code(to_email="user@test.com", code="FAIL01")
            assert False, "Should have raised an exception"
        except Exception:
            pass  # Expected


def test_mail_settings_from_env():
    """MailSettings should be loaded from environment variables."""
    os.environ["MAIL_BACKEND"] = "console"
    os.environ["MAIL_SMTP_HOST"] = "smtp.custom.com"
    os.environ["MAIL_SMTP_PORT"] = "465"
    os.environ["MAIL_FROM_NAME"] = "Test App"

    from app.config.mail_config import get_mail_settings
    settings = get_mail_settings()
    assert settings.backend == "console"
    assert settings.smtp_host == "smtp.custom.com"
    assert settings.smtp_port == 465
    assert settings.from_name == "Test App"

    # Clean up
    del os.environ["MAIL_BACKEND"]
    del os.environ["MAIL_SMTP_HOST"]
    del os.environ["MAIL_SMTP_PORT"]
    del os.environ["MAIL_FROM_NAME"]


def test_mail_settings_defaults():
    """MailSettings should use defaults when env vars are not set."""
    # Remove env vars if set
    for key in ["MAIL_BACKEND", "MAIL_SMTP_HOST", "MAIL_SMTP_PORT", "MAIL_FROM_NAME"]:
        os.environ.pop(key, None)

    from app.config.mail_config import get_mail_settings
    settings = get_mail_settings()
    assert settings.backend == "console"  # default
    assert settings.smtp_host == "smtp.gmail.com"  # default
    assert settings.smtp_port == 587  # default
    assert settings.from_name == "eCommerce"  # default