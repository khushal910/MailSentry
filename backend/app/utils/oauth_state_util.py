import hmac
import hashlib
import logging
import secrets
import time
from fastapi import HTTPException, status

logger = logging.getLogger("mailsentry.google_oauth.state")

# Maximum age of a state token in seconds (10 minutes)
_STATE_MAX_AGE = 600

def _get_secret() -> bytes:
    """Lazily imports the app SECRET_KEY to avoid circular import at module level."""
    from app.core.config import settings
    return settings.SECRET_KEY.encode("utf-8")


def generate_oauth_state() -> str:
    """
    Generates a stateless, HMAC-signed OAuth state token.

    Format: {nonce}|{timestamp}|{signature}

    Why stateless instead of cookie-based:
    Cookie-based state validation fails when the browser does not send the
    oauth_state cookie back to the callback endpoint.  This happens when:
      - The cookie was set on a 302 redirect and some browsers drop it before
        following the redirect to Google.
      - Third-party / cross-site cookie restrictions interfere with the
        google → backend redirect chain.
    A signed state token stores all the information needed for validation
    inside the token itself, so no server-side session or cookie is required.
    """
    nonce = secrets.token_urlsafe(24)
    timestamp = str(int(time.time()))
    message = f"{nonce}|{timestamp}"
    sig = hmac.new(_get_secret(), message.encode(), hashlib.sha256).hexdigest()
    state = f"{message}|{sig}"
    logger.debug("Generated HMAC-signed OAuth state token.")
    return state


def validate_oauth_state(cookie_state: str | None, param_state: str | None) -> None:
    """
    Validates the HMAC-signed state token returned by Google.

    The cookie_state argument is accepted for backwards-compatibility but is
    ignored — validation is performed entirely against param_state.

    Raises HTTPException 400 if the token is missing, malformed, expired, or
    its HMAC signature does not match.
    """
    if not param_state:
        logger.warning("CSRF validation failed: state parameter is missing.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter: state parameter or cookie missing."
        )

    parts = param_state.split("|")
    if len(parts) != 3:
        logger.warning("CSRF validation failed: malformed state token.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter: state parameter or cookie missing."
        )

    nonce, timestamp_str, received_sig = parts

    # Verify HMAC signature
    message = f"{nonce}|{timestamp_str}"
    expected_sig = hmac.new(_get_secret(), message.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_sig, expected_sig):
        logger.warning("CSRF validation failed: HMAC signature mismatch.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter: state mismatch. Potential CSRF attack."
        )

    # Verify the token has not expired
    try:
        token_age = int(time.time()) - int(timestamp_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter: state parameter or cookie missing."
        )

    if token_age > _STATE_MAX_AGE:
        logger.warning("CSRF validation failed: state token has expired (age=%ds).", token_age)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth state token has expired. Please try signing in again."
        )

    logger.debug("HMAC state validation successful (token age=%ds).", token_age)
