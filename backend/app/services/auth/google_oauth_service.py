import hmac
import logging
import secrets
import urllib.parse
import httpx
from fastapi import Request, Response, HTTPException, status
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
]

def generate_google_auth_url(response: Response) -> str:
    """
    Generates a secure OAuth state parameter, sets it in an HTTP-only cookie,
    and constructs the Google OAuth 2.0 authorization URL.
    """
    if not settings.GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID environment variable is missing.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Client ID is not configured on the server."
        )

    # 1. Generate secure random CSRF state
    state = secrets.token_urlsafe(32)

    # 2. Store state parameter in HTTP-only cookie (valid for 10 minutes)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="lax",
        max_age=600  # 10 minutes
    )

    # 3. Construct query parameters for Authorization Code Flow
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    logger.info("Generated Google OAuth login URL with state parameter.")
    return auth_url


def validate_oauth_state(request: Request, state_param: str | None) -> None:
    """
    Validates that the incoming state parameter matches the state stored in the HTTP-only cookie.
    Prevents CSRF attacks.
    """
    cookie_state = request.cookies.get("oauth_state")

    if not state_param or not cookie_state:
        logger.warning("CSRF validation failed: missing state parameter or cookie.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter: state parameter or cookie missing."
        )

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(state_param, cookie_state):
        logger.warning("CSRF validation failed: state mismatch.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter: state mismatch. Potential CSRF attack."
        )


async def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchanges the Google authorization code for tokens (access_token, refresh_token, id_token, expires_in).
    Handles errors gracefully if the code is invalid or expired.
    """
    if not settings.GOOGLE_CLIENT_SECRET:
        logger.error("GOOGLE_CLIENT_SECRET environment variable is missing.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Client Secret is not configured on the server."
        )

    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
            data = resp.json()

        if resp.status_code != 200 or "error" in data:
            error_msg = data.get("error_description") or data.get("error") or "Unknown error"
            logger.error(f"Failed to exchange authorization code: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or expired authorization code: {error_msg}"
            )

        return data
    except httpx.HTTPError as e:
        logger.error(f"HTTP error connecting to Google token endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Google OAuth service: {str(e)}"
        )


def verify_id_token_and_extract_user(id_token_str: str) -> dict:
    """
    Verifies the authenticity of Google's ID Token and extracts the user's profile information.
    """
    try:
        req = google_requests.Request()
        # Verify ID Token against Google's public keys and check client_id audience
        user_info = google_id_token.verify_oauth2_token(
            id_token_str, req, settings.GOOGLE_CLIENT_ID
        )

        return {
            "google_id": user_info.get("sub"),
            "email": user_info.get("email"),
            "email_verified": user_info.get("email_verified", False),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "given_name": user_info.get("given_name"),
            "family_name": user_info.get("family_name"),
        }
    except ValueError as e:
        logger.error(f"Invalid Google ID Token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to verify Google ID Token: {str(e)}"
        )


from datetime import datetime, timezone, timedelta
from app.utils.encryption_util import encrypt_token
from app.repositories.google_account_repository import GoogleAccountRepository



def find_or_create_user_from_google_profile(user_info: dict) -> dict:
    """
    Matches the authenticated Google email with an existing MailSentry user.
    - If user exists: links Google account & updates google_connected=True.
    - If user does not exist: creates a new MailSentry account using Google profile data.
    """
    from app.db.mongodb import get_database
    db = get_database()
    users_col = db[settings.USER_COLLECTION_NAME]

    email = user_info["email"].strip().lower()
    now = datetime.now(timezone.utc)
    existing_user = users_col.find_one({"email": email})

    if existing_user:
        # Update google_connected=True on existing user
        users_col.update_one(
            {"_id": existing_user["_id"]},
            {"$set": {"google_connected": True, "updated_at": now}}
        )
        existing_user["google_connected"] = True
        logger.info(f"Linked Google account to existing MailSentry user: {email}")
        return existing_user

    # User does not exist — auto-create new MailSentry account
    raw_name = user_info.get("given_name") or user_info.get("name") or email.split("@")[0]
    # Clean username string
    base_username = "".join(c for c in raw_name if c.isalnum() or c in ("_", "-")).strip() or "user"
    username = base_username

    # Ensure username uniqueness
    counter = 1
    while users_col.find_one({"username": username}):
        username = f"{base_username}{counter}"
        counter += 1

    new_user = {
        "username": username,
        "email": email,
        "password": None,  # Authenticated via OAuth
        "role": "user",
        "is_active": True,
        "google_connected": True,
        "created_at": now,
        "updated_at": now,
    }

    result = users_col.insert_one(new_user)
    new_user["_id"] = result.inserted_id
    logger.info(f"Auto-created new MailSentry user via Google OAuth: {email} (username: {username})")
    return new_user


def save_or_update_google_account(
    google_email: str,
    google_user_id: str | None = None,
    user_id: str | None = None,
    refresh_token: str | None = None,
    expires_in: int | None = None,
) -> dict:
    """
    Encrypts the refresh_token (if present), calculates access token expiry,
    and delegates persistence/upsert to GoogleAccountRepository.
    Never stores plain access_token in MongoDB.
    """
    repo = GoogleAccountRepository()
    repo.ensure_indexes()

    encrypted_refresh_token = encrypt_token(refresh_token) if refresh_token else None
    
    access_token_expiry = None
    if expires_in is not None:
        access_token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    saved_doc = repo.upsert_account(
        google_email=google_email,
        google_user_id=google_user_id,
        user_id=user_id,
        encrypted_refresh_token=encrypted_refresh_token,
        access_token_expiry=access_token_expiry,
    )

    return saved_doc


