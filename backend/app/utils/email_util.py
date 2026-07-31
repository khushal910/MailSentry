"""
email_util.py
-------------
Reusable email delivery service built on Python's stdlib smtplib.

Design decisions
----------------
* stdlib only — no extra dependencies (fastapi-mail, sendgrid, etc.).
  The SMTP protocol support built into Python's smtplib is sufficient
  and keeps the dependency footprint small.

* Every public function accepts (to_email, subject, html_body, text_body).
  send_reset_otp_email() is a thin wrapper that builds the content and
  delegates to _send_email(), making it trivial to add future email types
  (email verification, welcome email, etc.) by following the same pattern.

* STARTTLS (port 587) is used by default instead of SMTP_SSL (port 465).
  STARTTLS is the modern recommended approach: the connection starts in
  plain text, then upgrades to TLS before credentials are transmitted.
  SMTP_SSL is supported via SMTP_USE_TLS=False in .env if needed.

* The plain-text fallback is included in every email as a MIME multipart
  alternative. Mail clients that cannot render HTML (CLI tools, screen
  readers, old clients) will show the text part automatically.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from app.core.config import settings


# ── Internal sender ────────────────────────────────────────────────────────────

def _send_email(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    """
    Low-level helper that opens an SMTP connection, authenticates, and
    delivers a multipart/alternative email (HTML + plain-text fallback).

    This function is intentionally private (_prefix). All public functions
    in this module call it after building their specific content, keeping
    the SMTP logic in one place.

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
    # 'alternative' means the client picks the best part it can render.
    # Parts are added from least-preferred to most-preferred (text first, HTML last).
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = formataddr((settings.EMAIL_FROM_NAME, settings.EMAIL_FROM))
    msg["To"]      = to_email

    # Attach plain-text first (lower priority — fallback)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))

    # Attach HTML second (higher priority — preferred rendering)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if settings.SMTP_USE_TLS:
        # STARTTLS: connect on port 587, upgrade the connection to TLS,
        # then authenticate. This is the modern recommended method.
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
    else:
        # SMTP_SSL: entire connection is wrapped in TLS from the start.
        # Used for port 465. Set SMTP_USE_TLS=False in .env to use this path.
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())


# ── HTML template builder ──────────────────────────────────────────────────────

def _build_otp_html(otp: str, expire_minutes: int = 10) -> str:
    """
    Build a clean, branded HTML email body for OTP delivery.

    Why a function and not a file?
        For a single template, an inline f-string keeps the project
        self-contained without a template directory or Jinja2 dependency.
        If the number of templates grows, migrate to Jinja2.

    Args:
        otp            (str): The 6-digit OTP to display.
        expire_minutes (int): How long the OTP is valid (shown to the user).

    Returns:
        str: Complete HTML document as a string.
    """
    app_name   = settings.APP_NAME or "MailSentry"
    from_name  = settings.EMAIL_FROM_NAME or app_name

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Password Reset — {app_name}</title>
</head>
<body style="margin:0;padding:0;background-color:#0f0f13;font-family:'Helvetica Neue',Arial,sans-serif;">

  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#0f0f13;padding:40px 16px;">
    <tr>
      <td align="center">

        <!-- Card -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="max-width:520px;background-color:#18181f;border-radius:16px;
                      border:1px solid #2a2a38;overflow:hidden;">

          <!-- Header bar -->
          <tr>
            <td style="background:linear-gradient(135deg,#6d28d9 0%,#4f46e5 100%);
                       padding:28px 40px;">
              <p style="margin:0;font-size:22px;font-weight:700;color:#ffffff;
                        letter-spacing:-0.3px;">
                🛡️ {app_name}
              </p>
              <p style="margin:4px 0 0;font-size:13px;color:rgba(255,255,255,0.75);">
                AI-powered email protection
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 40px;">
              <h1 style="margin:0 0 8px;font-size:20px;font-weight:600;color:#f4f4f8;">
                Password Reset Request
              </h1>
              <p style="margin:0 0 28px;font-size:14px;color:#9090a8;line-height:1.6;">
                We received a request to reset your {app_name} password.
                Use the one-time code below — it expires in
                <strong style="color:#c4b5fd;">{expire_minutes} minutes</strong>.
              </p>

              <!-- OTP box -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center">
                    <div style="display:inline-block;background-color:#1e1e2e;
                                border:2px solid #6d28d9;border-radius:12px;
                                padding:20px 40px;margin-bottom:28px;">
                      <p style="margin:0;font-size:11px;font-weight:600;
                                color:#9090a8;letter-spacing:2px;text-transform:uppercase;">
                        Your OTP code
                      </p>
                      <p style="margin:8px 0 0;font-size:42px;font-weight:800;
                                color:#a78bfa;letter-spacing:12px;font-variant-numeric:tabular-nums;">
                        {otp}
                      </p>
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Warning -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="background-color:#1e1a2e;border-left:3px solid #7c3aed;
                            border-radius:6px;margin-bottom:24px;">
                <tr>
                  <td style="padding:14px 16px;">
                    <p style="margin:0;font-size:13px;color:#c4b5fd;line-height:1.5;">
                      ⚠️ If you did not request this, you can safely ignore this email.
                      Your account remains secure.
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin:0;font-size:13px;color:#6060788;">
                For security, never share this code with anyone.
                {app_name} will never ask for your OTP.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color:#111118;padding:20px 40px;
                       border-top:1px solid #2a2a38;">
              <p style="margin:0;font-size:12px;color:#5a5a72;text-align:center;">
                Sent by {from_name} &nbsp;·&nbsp;
                This is an automated message, please do not reply.
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

    Plain text is always included alongside HTML so the email renders
    correctly in environments that strip or block HTML (CLI mail clients,
    accessibility tools, strict corporate mail filters).

    Args:
        otp            (str): The 6-digit OTP.
        expire_minutes (int): Validity window shown to the user.

    Returns:
        str: Plain-text email body.
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
    Send a password-reset OTP email to the given address.

    This is the only function callers need to use for the password-reset
    flow. It builds both the HTML and plain-text bodies and hands off to
    the internal _send_email() sender.

    How to add future email types:
        Follow the same pattern:
          1. Add _build_<type>_html() and _build_<type>_text() builders.
          2. Add a send_<type>_email() public function that calls _send_email().
        The SMTP transport layer does not need to change.

    Args:
        email          (str): Recipient email address.
        otp            (str): Plain-text 6-digit OTP (from generate_otp()).
                              Only the hash is stored in the DB; the plain
                              OTP is only ever transmitted by email.
        expire_minutes (int): Validity window to display in the email body.
                              Must match the value stored in reset_otp_expire_at.

    Raises:
        RuntimeError: When SMTP credentials are missing from .env.
        smtplib.SMTPException: On network or authentication failure.

    Example:
        from app.utils.otp_util   import generate_otp, hash_otp
        from app.utils.email_util import send_reset_otp_email

        otp = generate_otp()
        send_reset_otp_email(user["email"], otp)
        # After sending, persist hash_otp(otp) → reset_otp_hash in MongoDB
    """
    app_name = settings.APP_NAME or "MailSentry"
    subject  = f"Your {app_name} password reset code"

    html_body = _build_otp_html(otp, expire_minutes)
    text_body = _build_otp_text(otp, expire_minutes)

    _send_email(
        to_email  = email,
        subject   = subject,
        html_body = html_body,
        text_body = text_body,
    )
