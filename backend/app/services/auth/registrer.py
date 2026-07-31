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
)
from app.schemas.user import UserRegisterSchema


async def register_user(user_data: UserRegisterSchema, response: Response) -> Dict[str, Any]:
    """
    Registers a new user and sets an HTTP-only access_token cookie on success,
    exactly like login_user does.
    """
    try:
        data     = user_data.model_dump()
        username = data["username"].strip()
        email    = data["email"].strip().lower()
        password = data["password"]

        # Validate email
        if not validate_email(email):
            return return_response(status_code=400, message="Invalid email format")

        # Validate password strength
        if not validate_password_strength(password):
            return return_response(
                status_code=400,
                message="Password must be at least 8 characters, with uppercase, lowercase, and a digit",
            )

        # Check for duplicate username or email
        db        = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]
        existing  = users_col.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing:
            return return_response(status_code=400, message="Username or email already exists")

        # Hash password and insert user
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

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite="lax",
            max_age=60 * 30,
        )

        return return_response(status_code=201, message="User registered successfully")

    except Exception as e:
        return return_response(status_code=500, message=f"Error during registration: {str(e)}")