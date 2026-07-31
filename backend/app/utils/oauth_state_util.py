import hmac
import logging
import secrets
from fastapi import HTTPException, status

logger = logging.getLogger("mailsentry.google_oauth.state")

def generate_oauth_state() -> str:
    """
    Generates a cryptographically secure 32-byte URL-safe state parameter for CSRF protection.
    """
    state = secrets.token_urlsafe(32)
    logger.debug("Generated secure OAuth state parameter.")
    return state

def validate_oauth_state(cookie_state: str | None, param_state: str | None) -> None:
    """
    Validates that the state parameter received from Google matches the HTTP-only cookie state.
    Uses constant-time comparison to protect against timing attacks.
    """
    if not param_state or not cookie_state:
        logger.warning("CSRF validation failed: missing state parameter or state cookie.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter: state parameter or cookie missing."
        )

    if not hmac.compare_digest(param_state, cookie_state):
        logger.warning("CSRF validation failed: state mismatch.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter: state mismatch. Potential CSRF attack."
        )

    logger.debug("CSRF state validation successful.")
