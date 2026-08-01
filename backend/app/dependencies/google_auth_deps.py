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
    repo: GoogleAccountRepository = Depends(get_google_account_repository)
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
    FastAPI Dependency for Gmail APIs.
    Enforces that user has an active connected Google Account document in MongoDB.
    If disconnected or account deleted -> returns 403 Forbidden ("Please connect Gmail.").
    """
    user_id = str(current_user["_id"])
    account = repo.find_by_user_id(user_id)
    if not current_user.get("google_connected") or not account or not account.get("google_connected", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please connect Gmail."
        )
    return account
