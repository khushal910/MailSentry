from datetime import datetime, timezone
from app.repositories.google_account_repository import GoogleAccountRepository


def _format_datetime(dt) -> str:
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    elif isinstance(dt, str):
        return dt
    return datetime.now(timezone.utc).isoformat()


def get_google_status_service(
    user_id: str, repo: GoogleAccountRepository | None = None
) -> dict:
    """
    Checks if a google_account exists for the given user_id.

    Returns:
      If google_account exists and is connected:
        {
            "connected": True,
            "google_email": "...",
            "connected_at": "...",
            "last_updated": "..."
        }
      If google_account does not exist:
        {
            "connected": False
        }
    """
    if repo is None:
        repo = GoogleAccountRepository()

    account = repo.find_by_user_id(user_id)

    if not account or not account.get("google_connected", True):
        return {"connected": False}

    created_at = account.get("created_at")
    updated_at = account.get("updated_at")

    return {
        "connected": True,
        "google_email": account.get("google_email", ""),
        "connected_at": _format_datetime(created_at),
        "last_updated": _format_datetime(updated_at),
    }


def disconnect_google_service(
    user_id: str, repo: GoogleAccountRepository | None = None
) -> dict:
    """
    Disconnects Google Account for the given user_id:
    1. Verify account status. If already disconnected, return success.
    2. Delete document from google_accounts collection.
    3. Update user document in users collection: google_connected=false.
    4. On database error, rollback state and return 500 error.
    """
    import logging
    from fastapi import HTTPException, status

    logger = logging.getLogger(__name__)

    if repo is None:
        repo = GoogleAccountRepository()

    account = repo.find_by_user_id(user_id)

    now = datetime.now(timezone.utc)

    # Validation: Already disconnected -> return success
    if not account or not account.get("google_connected", True):
        repo.update_user_google_connected(user_id, False, now)
        return {
            "success": True,
            "connected": False,
            "message": "Gmail account already disconnected"
        }

    try:
        # Delete document from google_accounts collection
        repo.delete_account(user_id)

        # Update user document in users collection: google_connected=false
        repo.update_user_google_connected(user_id, False, now)

        return {
            "success": True,
            "connected": False,
            "message": "Gmail account disconnected successfully"
        }
    except HTTPException:
        # Rollback: restore user.google_connected=True on error
        repo.update_user_google_connected(user_id, True, now)
        raise
    except Exception as e:
        logger.error(f"Database error disconnecting Google account for user_id={user_id}: {str(e)}")
        # Rollback: restore user.google_connected=True on error
        repo.update_user_google_connected(user_id, True, now)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error disconnecting Google account: {str(e)}"
        )
