import asyncio
import unittest
from unittest.mock import MagicMock, patch

from app.utils.email_util import (
    _build_otp_html,
    _build_otp_text,
    _send_email,
    send_reset_otp_email,
    send_reset_otp_email_async,
    send_reset_otp_email_background,
)


class TestEmailUtil(unittest.IsolatedAsyncioTestCase):

    def test_build_otp_html_contains_code_and_minutes(self):
        html = _build_otp_html(otp="123456", expire_minutes=10)
        self.assertIn("123456", html)
        self.assertIn("10 minutes", html)
        self.assertIn("Password Reset Verification", html)

    def test_build_otp_text_contains_code(self):
        text = _build_otp_text(otp="654321", expire_minutes=5)
        self.assertIn("654321", text)
        self.assertIn("5 minutes", text)

    @patch("app.utils.email_util.settings")
    @patch("smtplib.SMTP")
    def test_send_email_tls(self, mock_smtp_cls, mock_settings):
        mock_settings.SMTP_USERNAME = "test@gmail.com"
        mock_settings.SMTP_PASSWORD = "apppassword"
        mock_settings.SMTP_HOST = "smtp.gmail.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USE_TLS = True
        mock_settings.SMTP_TIMEOUT = 10
        mock_settings.EMAIL_FROM = "noreply@mailsentry.app"
        mock_settings.EMAIL_FROM_NAME = "MailSentry"

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        _send_email(
            to_email="user@example.com",
            subject="Test Subject",
            html_body="<p>Test</p>",
            text_body="Test",
        )

        mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 587, timeout=10)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "apppassword")
        mock_server.sendmail.assert_called_once()

    @patch("app.utils.email_util.settings")
    @patch("smtplib.SMTP_SSL")
    def test_send_email_ssl(self, mock_smtp_ssl_cls, mock_settings):
        mock_settings.SMTP_USERNAME = "test@gmail.com"
        mock_settings.SMTP_PASSWORD = "apppassword"
        mock_settings.SMTP_HOST = "smtp.gmail.com"
        mock_settings.SMTP_PORT = 465
        mock_settings.SMTP_USE_TLS = False
        mock_settings.SMTP_TIMEOUT = 10
        mock_settings.EMAIL_FROM = "noreply@mailsentry.app"
        mock_settings.EMAIL_FROM_NAME = "MailSentry"

        mock_server = MagicMock()
        mock_smtp_ssl_cls.return_value.__enter__.return_value = mock_server

        _send_email(
            to_email="user@example.com",
            subject="Test Subject",
            html_body="<p>Test</p>",
            text_body="Test",
        )

        mock_smtp_ssl_cls.assert_called_once_with("smtp.gmail.com", 465, timeout=10)
        mock_server.login.assert_called_once_with("test@gmail.com", "apppassword")
        mock_server.sendmail.assert_called_once()

    @patch("app.utils.email_util._send_email")
    def test_send_reset_otp_email(self, mock_internal_send):
        send_reset_otp_email(email="test@example.com", otp="999888", expire_minutes=10)
        mock_internal_send.assert_called_once()
        args, kwargs = mock_internal_send.call_args
        self.assertEqual(kwargs["to_email"], "test@example.com")
        self.assertIn("999888", kwargs["html_body"])

    @patch("app.utils.email_util.send_reset_otp_email")
    async def test_send_reset_otp_email_async(self, mock_sync_send):
        await send_reset_otp_email_async(email="async@example.com", otp="112233", expire_minutes=5)
        mock_sync_send.assert_called_once_with(
            email="async@example.com", otp="112233", expire_minutes=5
        )

    @patch("app.utils.email_util.send_reset_otp_email")
    def test_send_reset_otp_email_background(self, mock_sync_send):
        send_reset_otp_email_background(email="bg@example.com", otp="445566", expire_minutes=5)
        # Give a small moment for thread pool execution
        import time
        time.sleep(0.1)
        mock_sync_send.assert_called_once_with(
            email="bg@example.com", otp="445566", expire_minutes=5
        )


if __name__ == "__main__":
    unittest.main()
