from app.repositories.email_repository import EmailRepository


def get_email_repository() -> EmailRepository:
    """
    FastAPI Dependency Provider for EmailRepository.
    """
    return EmailRepository()
