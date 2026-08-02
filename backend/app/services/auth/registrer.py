from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import Response
from app.core.config import settings
from app.db.mongodb import get_database
from app.utils.main_utile import (
    validate_email,
    validate_password_strength,
    hash_password,
    create_access_token,
    return_response,
    set_auth_cookie,
)
from app.schemas.user import UserRegisterSchema


async def register_user(user: UserRegisterSchema, response: Response):
    """
    Registers a new user into MongoDB after performing validation checks.
    """
    try:
        username, email, password = user.username, user.email, user.password

        val = validate_email(email)
        if not val["is_valid"]:
            return return_response(status_code=400, message=val["message"])

        val_pw = validate_password_strength(password)
        if not val_pw["is_valid"]:
            return return_response(status_code=400, message=val_pw["message"])

        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]

        if users_col.find_one({"email": email}):
            return return_response(status_code=400, message="Email already registered")

        if users_col.find_one({"username": username}):
            return return_response(status_code=400, message="Username already taken")

        hashed_password = hash_password(password)

        new_user = {
            "username":   username,
            "email":      email,
            "password":   hashed_password,
            "role":       "user",
            "is_active":  True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result  = users_col.insert_one(new_user)
        user_id = str(result.inserted_id)

        # Generate token and set HTTP-only cookie — identical to login
        access_token = create_access_token(user_id=user_id, username=username)

        set_auth_cookie(response, access_token)

        return return_response(status_code=201, message="User registered successfully")

    except Exception as e:
        return return_response(status_code=500, message=f"Error during registration: {str(e)}")