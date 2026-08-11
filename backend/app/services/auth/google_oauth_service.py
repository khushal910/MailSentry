import logging
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException, Request, Response, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings
from app.repositories.google_account_repository import GoogleAccountRepository
from app.utils.encryption_util import encrypt_token
from app.utils.oauth_state_util import generate_oauth_state
from app.utils.oauth_state_util import validate_oauth_state as validate_oauth_state_util

logger = logging.getLogger("mailsentry.google_oauth.service")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.readonly",
]


class GoogleOAuthService:
    """
    Service layer for handling Google OAuth 2.0 flow, token exchange,
    ID token verification, user account auto-creation, and MongoDB persistence.
    """

    def __init__(self, repo: GoogleAccountRepository | None = None):
        self.repo = repo if repo is not None else GoogleAccountRepository()

    def generate_auth_url_with_state(
        self, user_id: str | None = None, google_email: str | None = None
    ) -> tuple[str, str]:
        """
        Generates a secure OAuth state parameter and the Google authorization URL.
        Distinguishes between First Login vs Returning Login:
        - First Login (no valid refresh token in DB): uses prompt="consent", access_type="offline"
        - Returning Login (valid refresh token exists): uses access_type="offline", include_granted_scopes="true" (omits prompt="consent")
        """
        if not settings.GOOGLE_CLIENT_ID:
            logger.error("GOOGLE_CLIENT_ID environment variable is missing.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Client ID is not configured on the server.",
            )

        # 1. Check if user already has a valid stored refresh token in MongoDB
        returning_user = self.repo.has_valid_refresh_token(
            user_id=user_id, google_email=google_email
        )

        # 2. Generate cryptographically secure CSRF state
        state = generate_oauth_state()

        # 3. Build Google authorization URL
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "state": state,
        }

        if returning_user:
            params["include_granted_scopes"] = "true"
            logger.info(
                "Generated Google OAuth authorization URL for RETURNING user (prompt=consent omitted)."
            )
        else:
            params["prompt"] = "consent"
            logger.info(
                "Generated Google OAuth authorization URL for FIRST-TIME user (prompt=consent included)."
            )

        auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return state, auth_url

    def generate_connect_url_with_state(
        self, user_id: str | None = None, google_email: str | None = None
    ) -> tuple[str, str]:
        """
        Generates OAuth authorization URL specifically for connecting/reconnecting Gmail.
        Forces access_type="offline" and prompt="consent".
        Makes NO database changes.
        """
        if not settings.GOOGLE_CLIENT_ID:
            logger.error("GOOGLE_CLIENT_ID environment variable is missing.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Client ID is not configured on the server.",
            )

        state = generate_oauth_state()

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
        logger.info(
            "Generated Google OAuth connect URL with access_type=offline and prompt=consent."
        )
        return state, auth_url

    def generate_auth_url(
        self,
        response: Response,
        user_id: str | None = None,
        google_email: str | None = None,
    ) -> str:
        """
        Legacy wrapper kept for backward compatibility.
        """
        state, auth_url = self.generate_auth_url_with_state(
            user_id=user_id, google_email=google_email
        )
        return auth_url

    def validate_csrf_state(self, request: Request, state_param: str | None) -> None:
        """
        Validates the incoming CSRF state against the HTTP-only cookie.
        """
        cookie_state = request.cookies.get("oauth_state")
        validate_oauth_state_util(cookie_state=cookie_state, param_state=state_param)

    async def exchange_code_for_tokens(self, code: str) -> dict:
        """
        Exchanges the authorization code for tokens (access_token, refresh_token, id_token, expires_in).
        - No code / Invalid code -> 400 Bad Request
        - Google server error -> 500 Internal Server Error
        """
        if not code or not code.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is missing or empty.",
            )

        if not settings.GOOGLE_CLIENT_SECRET:
            logger.error("GOOGLE_CLIENT_SECRET environment variable is missing.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Client Secret is not configured on the server.",
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

            if resp.status_code >= 500:
                logger.error(
                    f"Google OAuth server returned 5xx error: {resp.status_code}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Google server error while exchanging authorization code.",
                )

            if resp.status_code != 200 or "error" in data:
                error_msg = (
                    data.get("error_description")
                    or data.get("error")
                    or "Invalid authorization code"
                )
                logger.error(f"Failed to exchange authorization code: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid authorization code: {error_msg}",
                )

            # Validate expected fields in token payload
            if "id_token" not in data or "access_token" not in data:
                logger.error(
                    "Required tokens missing from Google OAuth token response."
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token response from Google: id_token or access_token missing.",
                )

            return data
        except HTTPException:
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error connecting to Google token endpoint: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Google server error: {e!s}",
            )
        except Exception as e:
            logger.error(f"Unexpected error during code exchange: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Google server error: {e!s}",
            )

    def verify_id_token(self, id_token_str: str) -> dict:
        """
        Verifies Google's ID Token authenticity and extracts user profile data.
        - Invalid ID Token -> 401 Unauthorized
        - Email missing -> 400 Bad Request
        """
        try:
            req = google_requests.Request()
            user_info = google_id_token.verify_oauth2_token(
                id_token_str,
                req,
                settings.GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=10,
            )
        except Exception as e:
            logger.error(f"Invalid Google ID Token: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google ID Token: {e!s}",
            )

        email = user_info.get("email")
        if not email:
            logger.error("Email missing from Google ID token payload.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email missing from Google ID token payload.",
            )

        google_user_id = user_info.get("sub")
        if not google_user_id:
            logger.error("Google user ID (sub) missing from ID token.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google user ID missing from ID token.",
            )

        return {
            "google_id": google_user_id,
            "email": email,
            "email_verified": user_info.get("email_verified", False),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "given_name": user_info.get("given_name"),
            "family_name": user_info.get("family_name"),
        }

    def find_or_create_user(
        self, user_info: dict, current_user_id: str | None = None
    ) -> dict:
        """
        Matches the authenticated Google email or current_user_id with an existing MailSentry user.
        - If current_user_id provided: links Google account & updates google_connected=True for that user.
        - Else if user exists by email: links Google account & updates google_connected=True.
        - Else: auto-creates a new MailSentry account using Google profile.
        """
        from bson import ObjectId

        from app.db.mongodb import get_database

        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]

        email = user_info["email"].strip().lower()
        now = datetime.now(timezone.utc)

        existing_user = None
        if current_user_id:
            try:
                if ObjectId.is_valid(current_user_id):
                    existing_user = users_col.find_one(
                        {"_id": ObjectId(current_user_id)}
                    )
                else:
                    existing_user = users_col.find_one({"_id": current_user_id})
            except Exception:
                pass

        # If current_user_id was not provided or invalid/stale, fall back to email lookup
        if not existing_user:
            existing_user = users_col.find_one({"email": email})

        if existing_user:
            users_col.update_one(
                {"_id": existing_user["_id"]},
                {
                    "$set": {
                        "google_connected": True,
                        "updated_at": now,
                        "last_login_at": now,
                    },
                    "$addToSet": {"providers": "google"},
                },
            )
            existing_user["google_connected"] = True
            existing_user["last_login_at"] = now
            logger.info(
                f"Linked Google account ({email}) to user: {existing_user.get('_id')}"
            )
            return existing_user

        # User does not exist — auto-create new MailSentry account
        raw_name = (
            user_info.get("given_name") or user_info.get("name") or email.split("@")[0]
        )
        base_username = (
            "".join(c for c in raw_name if c.isalnum() or c in ("_", "-")).strip()
            or "user"
        )
        username = base_username

        counter = 1
        while users_col.find_one({"username": username}):
            username = f"{base_username}{counter}"
            counter += 1

        new_user = {
            "username": username,
            "email": email,
            "password": None,  # OAuth login
            "providers": ["google"],
            "role": "user",
            "is_active": True,
            "google_connected": True,
            "created_at": now,
            "updated_at": now,
            "last_login_at": now,
        }

        try:
            result = users_col.insert_one(new_user)
            new_user["_id"] = result.inserted_id
            logger.info(
                f"Auto-created new MailSentry user via Google OAuth: {email} (username: {username})"
            )
            return new_user
        except Exception:
            # Fallback check if user was inserted concurrently
            existing_user = users_col.find_one({"email": email})
            if existing_user:
                users_col.update_one(
                    {"_id": existing_user["_id"]},
                    {
                        "$set": {
                            "google_connected": True,
                            "updated_at": now,
                            "last_login_at": now,
                        },
                        "$addToSet": {"providers": "google"},
                    },
                )
                existing_user["google_connected"] = True
                existing_user["last_login_at"] = now
                return existing_user
            raise

    def persist_google_account(
        self,
        google_email: str,
        google_user_id: str | None = None,
        user_id: str | None = None,
        refresh_token: str | None = None,
        expires_in: int | None = None,
    ) -> dict:
        """
        Encrypts refresh_token (if present), calculates access token expiry,
        and delegates persistence to GoogleAccountRepository.
        Never stores plain access_token in MongoDB.
        If refresh_token is None, existing encrypted refresh token in MongoDB is preserved.
        """
        self.repo.ensure_indexes()

        if refresh_token:
            logger.info(
                "New refresh token received from Google. Encrypting and updating MongoDB."
            )
            encrypted_refresh_token = encrypt_token(refresh_token)
        else:
            logger.info(
                "No new refresh token in Google response (returning user). Preserving existing refresh token."
            )
            encrypted_refresh_token = None

        access_token_expiry = None
        if expires_in is not None:
            access_token_expiry = datetime.now(timezone.utc) + timedelta(
                seconds=expires_in
            )

        saved_doc = self.repo.upsert_account(
            google_email=google_email,
            google_user_id=google_user_id,
            user_id=user_id,
            encrypted_refresh_token=encrypted_refresh_token,
            access_token_expiry=access_token_expiry,
        )

        return saved_doc

    async def refresh_google_access_token(self, google_email: str) -> str:
        """
        Refreshes Google OAuth access token automatically using stored encrypted refresh token.
        1. Reads and decrypts refresh_token from MongoDB.
        2. Calls Google Token endpoint with grant_type=refresh_token.
        3. Updates access_token_expiry in MongoDB.
        4. Returns fresh access_token.
        """
        decrypted_rt = self.repo.get_decrypted_refresh_token(google_email)
        if not decrypted_rt:
            logger.error(
                f"Cannot refresh access token: No refresh token found for email {google_email}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No refresh token available. User must re-authenticate with Google.",
            )

        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            logger.error("Google Client ID or Client Secret missing in settings.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth server configuration missing.",
            )

        payload = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": decrypted_rt,
            "grant_type": "refresh_token",
        }

        try:
            logger.info(f"Refreshing Google access token for {google_email}...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
                data = resp.json()

            if resp.status_code != 200 or "error" in data:
                error_msg = (
                    data.get("error_description")
                    or data.get("error")
                    or "Unknown refresh error"
                )
                logger.error(
                    f"Google token refresh failed for {google_email}: {error_msg}"
                )
                # Automatically mark account as disconnected in MongoDB if token is invalid/revoked/expired
                account_doc = self.repo.find_by_email(google_email)
                if account_doc:
                    target_u_id = account_doc.get("user_id")
                    if target_u_id:
                        self.repo.disconnect_account(str(target_u_id))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Gmail access revoked or refresh token expired: {error_msg}. Please reconnect your account.",
                )

            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)

            if not access_token:
                logger.error("No access_token returned in Google refresh response.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid response from Google token refresh endpoint.",
                )

            # Calculate and store updated expiry
            new_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            self.repo.update_access_token_expiry(google_email, new_expiry)

            # Check if Google optionally rotated the refresh_token
            new_rt = data.get("refresh_token")
            if new_rt:
                logger.info(
                    f"Google issued a rotated refresh token for {google_email}. Updating MongoDB."
                )
                encrypted_new_rt = encrypt_token(new_rt)
                self.repo.upsert_account(
                    google_email=google_email,
                    encrypted_refresh_token=encrypted_new_rt,
                    access_token_expiry=new_expiry,
                )

            logger.info(
                f"Successfully refreshed Google access token for {google_email}. Expires in {expires_in}s."
            )
            return access_token

        except httpx.HTTPError as e:
            logger.error(
                f"HTTP error during Google token refresh for {google_email}: {e!s}"
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to connect to Google token endpoint: {e!s}",
            )

    def get_user_google_credentials(self, google_email: str) -> dict:
        """
        Retrieves decrypted refresh_token and account details for a Google user.
        """
        decrypted_rt = self.repo.get_decrypted_refresh_token(google_email)
        account_doc = self.repo.find_by_email(google_email)
        return {
            "google_email": google_email,
            "refresh_token": decrypted_rt,
            "google_connected": (
                account_doc.get("google_connected", False) if account_doc else False
            ),
            "access_token_expiry": (
                account_doc.get("access_token_expiry") if account_doc else None
            ),
        }


# Standalone function wrappers for backwards compatibility
def generate_google_auth_url(response: Response) -> str:
    return GoogleOAuthService().generate_auth_url(response)


def validate_oauth_state(request: Request, state_param: str | None) -> None:
    GoogleOAuthService().validate_csrf_state(request, state_param)


async def exchange_code_for_tokens(code: str) -> dict:
    return await GoogleOAuthService().exchange_code_for_tokens(code)


def verify_id_token_and_extract_user(id_token_str: str) -> dict:
    return GoogleOAuthService().verify_id_token(id_token_str)


def find_or_create_user_from_google_profile(user_info: dict) -> dict:
    return GoogleOAuthService().find_or_create_user(user_info)


def save_or_update_google_account(
    google_email: str,
    google_user_id: str | None = None,
    user_id: str | None = None,
    refresh_token: str | None = None,
    expires_in: int | None = None,
) -> dict:
    return GoogleOAuthService().persist_google_account(
        google_email=google_email,
        google_user_id=google_user_id,
        user_id=user_id,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )
