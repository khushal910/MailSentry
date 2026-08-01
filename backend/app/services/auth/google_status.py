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
    Disconnects Google Account for the given user_id.
    """
    if repo is None:
        repo = GoogleAccountRepository()

    repo.disconnect_account(user_id)

    from app.db.mongodb import get_database
    from app.core.config import settings
    from bson import ObjectId

    db = get_database()
    users_col = db[settings.USER_COLLECTION_NAME]
    if ObjectId.is_valid(user_id):
        users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"google_connected": False, "updated_at": datetime.now(timezone.utc)}}
        )
    else:
        users_col.update_one(
            {"_id": user_id},
            {"$set": {"google_connected": False, "updated_at": datetime.now(timezone.utc)}}
        )

    return {
        "success": True,
        "message": "Gmail account disconnected successfully"
    }
