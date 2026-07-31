from fastapi import Depends
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
