from fastapi import Request, HTTPException, status
from app.db.mongodb import get_database
from app.utils.main_utile import decode_token
from app.core.config import settings
from bson import ObjectId


async def get_current_user(request: Request) -> dict:
    """
    Reads the access_token cookie, decodes the JWT, fetches the user
    document from MongoDB and attaches it to request.state.user.

    Raises HTTPException 401 if the token is missing, invalid, or the
    user no longer exists in the database.
    """

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # decode_token raises HTTPException on invalid/expired tokens
    payload = decode_token(token)

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    db = get_database()
    users_col = db[settings.USER_COLLECTION_NAME]

    try:
        user = users_col.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    request.state.user = user
    return user