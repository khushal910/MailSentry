"""
email_util.py
-------------
High-performance, non-blocking email delivery service built on Python's stdlib smtplib.

Design decisions
----------------
* Non-blocking background execution:
  OTP delivery can run in dedicated worker threads (via ThreadPoolExecutor or asyncio.to_thread)
  so API endpoints respond in <30ms without stalling the user or blocking the event loop.

* stdlib only — no heavy external dependencies.
  The SMTP protocol support built into Python's smtplib is fast, lightweight, and reliable.

* Timeout protection:
  Socket timeouts prevent SMTP network hangs if DNS or packets drop.

* High-contrast, responsive HTML template with plain-text fallback.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import logging
import smtplib
import time

from app.core.config import settings

logger = logging.getLogger("mailsentry.email_util")

# Dedicated worker thread pool for fast, non-blocking email dispatch
_EMAIL_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mail_sender")


# ── Internal sender ────────────────────────────────────────────────────────────


def _send_email(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    """
    Low-level helper that opens an SMTP connection, authenticates, and
    delivers a multipart/alternative email (HTML + plain-text fallback).

    Args:
        to_email  (str): Recipient email address.
        subject   (str): Email subject line.
        html_body (str): Full HTML content of the email.
        text_body (str): Plain-text fallback (shown when HTML cannot render).

    Raises:
        RuntimeError: If SMTP credentials are not configured.
        smtplib.SMTPException: On connection or authentication failure.
    """
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP credentials are not configured. "
            "Set SMTP_USERNAME and SMTP_PASSWORD in your .env file."
        )

    # Build a multipart/alternative message.
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((settings.EMAIL_FROM_NAME, settings.EMAIL_FROM))
    msg["To"] = to_email

    # Attach plain-text first (lower priority — fallback)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))

    # Attach HTML second (higher priority — preferred rendering)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    timeout = getattr(settings, "SMTP_TIMEOUT", 10)
    t0 = time.perf_counter()

    if settings.SMTP_USE_TLS:
        # STARTTLS: connect on port 587, upgrade to TLS, then authenticate
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
    else:
        # SMTP_SSL: entire connection is wrapped in TLS from the start (port 465)
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())

    duration = time.perf_counter() - t0
    logger.info(f"[EmailService] Delivered '{subject}' to {to_email} in {duration:.2f}s")


# ── HTML template builder ──────────────────────────────────────────────────────


def _build_otp_html(otp: str, expire_minutes: int = 10) -> str:
    """
    Build a classic, high-contrast, clean HTML email body for OTP delivery.
    Compatible with Gmail, Outlook, Apple Mail, and mobile clients.
    """
    app_name = settings.APP_NAME or "MailSentry"
    from_name = settings.EMAIL_FROM_NAME or app_name

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <title>Your Verification Code — {app_name}</title>
</head>
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">

  <!-- Main Wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f1f5f9;padding:40px 16px;">
    <tr>
      <td align="center">

        <!-- Outer Container Card -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:540px;background-color:#ffffff;border-radius:12px;border:1px solid #e2e8f0;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);overflow:hidden;">

          <!-- Header Banner -->
          <tr>
            <td style="background:linear-gradient(135deg, #4f46e5 0%, #6d28d9 100%);padding:32px 40px;text-align:center;">
              <h1 style="margin:0;font-size:24px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">
                🛡️ {app_name}
              </h1>
              <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.85);font-weight:400;">
                Secure Email Protection
              </p>
            </td>
          </tr>

          <!-- Main Content Body -->
          <tr>
            <td style="padding:40px 40px 32px;">
              <h2 style="margin:0 0 12px;font-size:20px;font-weight:700;color:#0f172a;line-height:1.3;">
                Password Reset Verification
              </h2>
              <p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">
                We received a request to reset your password. Use the 6-digit code below to verify your request. This code will expire in <strong style="color:#4f46e5;">{expire_minutes} minutes</strong>.
              </p>

              <!-- OTP Code Display Card -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:28px;">
                <tr>
                  <td align="center">
                    <div style="background-color:#f8fafc;border:2px dashed #6366f1;border-radius:12px;padding:24px 32px;display:inline-block;">
                      <span style="display:block;font-size:11px;font-weight:700;color:#64748b;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">
                        YOUR VERIFICATION CODE
                      </span>
                      <span style="display:block;font-size:38px;font-weight:800;color:#1e1b4b;letter-spacing:10px;font-family:'Courier New',Courier,monospace;">
                        {otp}
                      </span>
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Security Notice -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#fffbeb;border-left:4px solid #f59e0b;border-radius:6px;margin-bottom:28px;">
                <tr>
                  <td style="padding:14px 16px;">
                    <p style="margin:0;font-size:13px;color:#92400e;line-height:1.5;">
                      <strong>Security Tip:</strong> If you did not request a password reset, please ignore this email or contact support if you have concerns. Never share your code with anyone.
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin:0;font-size:13px;color:#64748b;line-height:1.5;">
                Thank you,<br/>
                <strong style="color:#334155;">The {app_name} Security Team</strong>
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#f8fafc;padding:20px 40px;border-top:1px solid #e2e8f0;text-align:center;">
              <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.5;">
                Sent by {from_name} &nbsp;•&nbsp; Automated security notification<br/>
                Please do not reply to this email.
              </p>
            </td>
          </tr>

        </table>
        <!-- /Card -->

      </td>
    </tr>
  </table>

</body>
</html>"""


def _build_otp_text(otp: str, expire_minutes: int = 10) -> str:
    """
    Build the plain-text fallback body for OTP emails.
    """
    app_name = settings.APP_NAME or "MailSentry"
    return f"""Password Reset — {app_name}
{"=" * 40}

We received a request to reset your {app_name} password.

Your one-time code:

    {otp}

This code expires in {expire_minutes} minutes.

If you did not request a password reset, ignore this email.
Your account remains secure.

– The {app_name} Team
"""


# ── Public API ─────────────────────────────────────────────────────────────────


def send_reset_otp_email(email: str, otp: str, expire_minutes: int = 10) -> None:
    """
    Synchronously send a password-reset OTP email to the given address.

    Args:
        email          (str): Recipient email address.
        otp            (str): Plain-text 6-digit OTP.
        expire_minutes (int): Validity window to display in the email body.
    """
    app_name = settings.APP_NAME or "MailSentry"
    subject = f"Your {app_name} password reset code"

    html_body = _build_otp_html(otp, expire_minutes)
    text_body = _build_otp_text(otp, expire_minutes)

    _send_email(
        to_email=email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )


async def send_reset_otp_email_async(email: str, otp: str, expire_minutes: int = 10) -> None:
    """
    Asynchronously send a password-reset OTP email via thread pool so that
    it never blocks the FastAPI event loop.
    """
    await asyncio.to_thread(
        send_reset_otp_email,
        email=email,
        otp=otp,
        expire_minutes=expire_minutes,
    )


def send_reset_otp_email_background(email: str, otp: str, expire_minutes: int = 10) -> None:
    """
    Fire-and-forget background OTP email dispatch using the worker thread pool.
    Enables API endpoints to respond immediately (<30ms) to the user while
    dispatching the email concurrently.
    """
    def _worker():
        try:
            send_reset_otp_email(email=email, otp=otp, expire_minutes=expire_minutes)
        except Exception as e:
            logger.error(
                f"[EmailService] Background OTP delivery failed for {email}: {e!s}",
                exc_info=True,
            )

    _EMAIL_EXECUTOR.submit(_worker)
