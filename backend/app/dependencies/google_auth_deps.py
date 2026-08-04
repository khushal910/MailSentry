from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.repositories.google_account_repository import GoogleAccountRepository
from app.services.auth.google_oauth_service import GoogleOAuthService


def get_google_account_repository() -> GoogleAccountRepository:
    """
    FastAPI Dependency Provider for GoogleAccountRepository.
    """
    return GoogleAccountRepository()


def get_google_oauth_service(
    repo: GoogleAccountRepository = Depends(get_google_account_repository),
) -> GoogleOAuthService:
    """
    FastAPI Dependency Provider for GoogleOAuthService.
    Injects GoogleAccountRepository.
    """
    return GoogleOAuthService(repo=repo)


def require_google_connected(
    current_user: dict = Depends(get_current_user),
    repo: GoogleAccountRepository = Depends(get_google_account_repository),
) -> dict:
    """
    FastAPI Dependency for all Gmail endpoints (Fetch Emails, Classify Emails, Summarize Emails, Schedule Meeting).
    Verifies Gmail connection status prior to executing any operation.

    Rules:
    1. Find google_account for logged in user.
    2. If google_account missing:
       - Automatically fix user.google_connected = False if user.google_connected was True.
       - Return 403 Forbidden: "Please connect Gmail."
    3. If google_account exists but refresh_token is missing or empty:
       - Return 403 Forbidden: "Reconnect Gmail."
    4. If google_account exists but google_connected is False:
       - Return 403 Forbidden: "Please connect Gmail."
    5. Returns valid google_account document.
    """
    from datetime import datetime, timezone

    user_id = str(current_user["_id"])
    account = repo.find_by_user_id(user_id)

    if not account:
        # Rule 4: If user.google_connected = true but google_account missing -> automatically fix to false
        if current_user.get("google_connected") is True:
            repo.update_user_google_connected(
                user_id, False, datetime.now(timezone.utc)
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Please connect Gmail."
        )

    if not account.get("google_connected", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Please connect Gmail."
        )

    # Rule 3: Refresh token missing or empty -> Reconnect Gmail
    refresh_token = account.get("refresh_token")
    if not refresh_token or not str(refresh_token).strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Reconnect Gmail."
        )

    return account
