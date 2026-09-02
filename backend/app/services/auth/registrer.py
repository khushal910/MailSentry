from datetime import datetime, timezone

from fastapi import Response

from app.core.config import settings
from app.db.mongodb import get_database
from app.schemas.user import UserRegisterSchema
from app.utils.main_utile import (
    create_access_token,
    hash_password,
    return_response,
    set_auth_cookie,
    validate_email,
    validate_password_strength,
)


async def register_user(user: UserRegisterSchema, response: Response):
    """
    Registers a new user into MongoDB after performing validation checks.
    """
    try:
        username, email, password = user.username, user.email, user.password

        if not validate_email(email):
            return return_response(status_code=400, message="Invalid email address format")

        if not validate_password_strength(password):
            pwd_msg = (
                f"Password must be at least {settings.PASSWORD_LENGTH} characters long and include at least one uppercase letter, one lowercase letter, and one number"
                if settings.PASSWORD_RULE_APPLY
                else f"Password must be at least {settings.PASSWORD_LENGTH} characters long"
            )
            return return_response(status_code=400, message=pwd_msg)

        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]

        if users_col.find_one({"email": email}):
            return return_response(status_code=400, message="Email already registered")

        if users_col.find_one({"username": username}):
            return return_response(status_code=400, message="Username already taken")

        hashed_password = hash_password(password)

        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": "user",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = users_col.insert_one(new_user)
        user_id = str(result.inserted_id)

        # Generate token and set HTTP-only cookie — identical to login
        access_token = create_access_token(user_id=user_id, username=username)

        set_auth_cookie(response, access_token)

        return return_response(
            status_code=201,
            message="User registered successfully",
            data={"access_token": access_token},
        )

    except Exception as e:
        return return_response(
            status_code=500, message=f"Error during registration: {e!s}"
        )
