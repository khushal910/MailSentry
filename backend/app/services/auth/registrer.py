from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from app.core.config import settings
from app.db.mongodb import get_database
from app.utils.main_utile import (validate_email, validate_password_strength, hash_password, create_access_token, return_response)
from app.schemas.user import UserRegisterSchema

async def register_user(user_data: UserRegisterSchema) -> Dict[str, Any]:
    """
    Registers a new user in the system using environment‑based configuration.

    Args:
        user_data (dict): Must contain 'username', 'email', and 'password'.

    Returns:
        dict: Registered user info (without password hash) and an access token.

    Raises:
        ValueError: If validation fails or user already exists.
    """
    
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

    print(users_col)
    
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

    # Generate JWT access token
    access_token = create_access_token(user_id, username)

    # Prepare response (exclude password_hash)
    response_user = {
        "id": user_id,
        "username": username,
        "email": email,
    }

    return {
        "user": response_user,
    }
