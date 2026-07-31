import logging
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status, Depends
from app.repositories.google_account_repository import GoogleAccountRepository
from app.services.auth.google_oauth_service import GoogleOAuthService
from app.dependencies.google_auth_deps import get_google_oauth_service, get_google_account_repository

logger = logging.getLogger("mailsentry.gmail_token_manager")

# Safety buffer in seconds before token expiration to trigger automatic refresh (5 minutes)
EXPIRATION_BUFFER_SECONDS = 300


class GmailTokenManager:
    """
    Service for transparently managing Google OAuth access tokens for Gmail API requests.
    Ensures that a valid, unexpired access token is available before making any Gmail API calls.
    """

    def __init__(
        self,
        repo: GoogleAccountRepository | None = None,
        oauth_service: GoogleOAuthService | None = None,
    ):
        self.repo = repo if repo is not None else GoogleAccountRepository()
        self.oauth_service = oauth_service if oauth_service is not None else GoogleOAuthService(repo=self.repo)

    async def get_valid_access_token(self, google_email: str) -> str:
        """
        Retrieves a valid, unexpired Google access token for the given google_email.
        If the access token is expired or about to expire (within 5 minutes),
        it automatically calls refresh_google_access_token() to obtain and store a fresh access token.

        Returns:
            str: Fresh Google OAuth access_token suitable for Bearer authorization headers.
        """
        email = google_email.strip().lower()
        account_doc = self.repo.find_by_email(email)

        if not account_doc:
            logger.error(f"GmailTokenManager: No Google account found for email {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Google account for {email} is not linked to MailSentry."
            )

        access_token_expiry = account_doc.get("access_token_expiry")
        now = datetime.now(timezone.utc)

        # Ensure datetime is timezone-aware
        if access_token_expiry and access_token_expiry.tzinfo is None:
            access_token_expiry = access_token_expiry.replace(tzinfo=timezone.utc)

        # Check if token is missing, expired, or expiring within the buffer window (5 min)
        needs_refresh = (
            not access_token_expiry
            or (access_token_expiry - now).total_seconds() < EXPIRATION_BUFFER_SECONDS
        )

        if needs_refresh:
            logger.info(
                f"GmailTokenManager: Access token for {email} is expired or near expiry "
                f"(expiry={access_token_expiry}). Triggering automatic refresh."
            )
            fresh_token = await self.oauth_service.refresh_google_access_token(email)
            return fresh_token

        logger.debug(f"GmailTokenManager: Access token for {email} is valid until {access_token_expiry}.")
        # To strictly comply with Database Rules ("Never store plaintext access tokens permanently"),
        # a fresh token is requested from Google whenever a caller asks for an active access_token.
        fresh_token = await self.oauth_service.refresh_google_access_token(email)
        return fresh_token


def get_gmail_token_manager(
    repo: GoogleAccountRepository = Depends(get_google_account_repository),
    oauth_service: GoogleOAuthService = Depends(get_google_oauth_service),
) -> GmailTokenManager:
    """
    FastAPI Dependency Provider for GmailTokenManager.
    """
    return GmailTokenManager(repo=repo, oauth_service=oauth_service)
