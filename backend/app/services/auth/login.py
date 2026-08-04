from fastapi import Response

from app.core.config import settings
from app.db.mongodb import get_database
from app.schemas.user import UserLoginSchema
from app.utils.main_utile import (
    create_access_token,
    return_response,
    set_auth_cookie,
    verify_password,
)


async def login_user(user: UserLoginSchema, response: Response):
    """
    Authenticate user with email and password.
    Returns: success response and sets access_token cookie.
    """
    try:
        db = get_database()
        user_col = db[settings.USER_COLLECTION_NAME]
        db_user = user_col.find_one({"email": user.email})

        if not db_user:
            return return_response(status_code=401, message="Invalid email or password")

        if not verify_password(user.password, db_user["password"]):
            return return_response(status_code=401, message="Invalid email or password")

        access_token = create_access_token(
            user_id=str(db_user["_id"]), username=db_user["username"]
        )

        set_auth_cookie(response, access_token)

        return return_response(status_code=200, message="Login successful")

    except Exception as e:
        return return_response(status_code=500, message=f"Error during login: {e!s}")
