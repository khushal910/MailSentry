from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import Response
from app.core.config import settings
from app.db.mongodb import get_database
from app.utils.main_utile import (validate_email, validate_password_strength, hash_password, create_access_token, return_response)
from app.schemas.user import UserRegisterSchema

async def register_user(user_data: UserRegisterSchema, response: Response) -> Dict[str, Any]:
    """
    Registers a new user in the system using environment‑based configuration.
    On success, generates an access token and stores it in an HTTP-only cookie
    (same behaviour as login).

    Args:
        user_data (dict): Must contain 'username', 'email', and 'password'.
        response (Response): FastAPI Response object used to set the cookie.

    Returns:
        dict: Standardised response with success, status_code, and message.

    Raises:
        ValueError: If validation fails or user already exists.
    """
    try:
        
        user_data = user_data.model_dump()
        username = user_data['username'].strip()
        email = user_data['email'].strip().lower()
        password = user_data['password']

        # Validate email format
        if not validate_email(email):
            return return_response(
                status_code=400,
                message="Invalid email format"
            )
            
            
        # Validate password strength
        if not validate_password_strength(password):
            return return_response(
                status_code=400,
                message="Password must be at least 8 characters, with uppercase, lowercase, and a digit"
            )

        # Check for duplicate user (username or email)
        db = get_database()
        users_col = db[settings.USER_COLLECTION_NAME]
        existing = users_col.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing:
            return return_response(
                status_code=400,
                message="Username or email already exists"
            )

        # Hash the password (using bcrypt)
        hashed_password = hash_password(password)

        # Create user document
        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now(timezone.utc),
            "is_active": True,
            "updated_at": datetime.now(timezone.utc)
        }

        # Insert into MongoDB
        result = users_col.insert_one(new_user)
        user_id = str(result.inserted_id)

        # Generate access token and store in HTTP-only cookie (same as login)
        access_token = create_access_token(
            user_id=user_id,
            username=username
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite="lax",
            max_age=60 * 30
        )

        return return_response(
            status_code=201,
            message="User registered successfully"
        )

    except Exception as e:
        return return_response(
            status_code=500,
            message=f"Error during registration: {str(e)}"
        )