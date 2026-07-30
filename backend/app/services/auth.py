from datetime import datetime
from app.db.mongodb import mongodb
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.schemas.user import UserRegister, UserLogin
from app.core.config import settings
from fastapi import HTTPException, status

async def register_user(user_data: UserRegister):
    db = mongodb.db
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user_dict = {
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
        "full_name": user_data.full_name,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user_dict)
    
    # Return the user (without password)
    new_user = await db.users.find_one({"_id": result.inserted_id})
    new_user["id"] = str(new_user.pop("_id"))
    return new_user

async def authenticate_user(user_data: UserLogin):
    db = mongodb.db
    user = await db.users.find_one({"email": user_data.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user["_id"]), "email": user["email"]})
    refresh_token = create_refresh_token(data={"sub": str(user["_id"])})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

async def logout_user(access_token: str, refresh_token: str | None = None):
    """
    Blacklist the access token so it can't be reused.
    Optionally blacklist the refresh token as well.
    """
    db = mongodb.db
    now = datetime.utcnow()
    # Decode to get expiration
    payload = decode_token(access_token)
    expires_at = datetime.utcfromtimestamp(payload.get("exp")) if payload.get("exp") else now
    await db.revoked_tokens.insert_one({
        "token": access_token,
        "type": "access",
        "revoked_at": now,
        "expires_at": expires_at
    })
    if refresh_token:
        payload_ref = decode_token(refresh_token)
        ref_exp = datetime.utcfromtimestamp(payload_ref.get("exp")) if payload_ref.get("exp") else now
        await db.revoked_tokens.insert_one({
            "token": refresh_token,
            "type": "refresh",
            "revoked_at": now,
            "expires_at": ref_exp
        })
    # Optionally clear from client side; we just return a message
    return {"message": "Successfully logged out"}

async def refresh_access_token(refresh_token: str):
    db = mongodb.db
    # Check if refresh token is blacklisted
    revoked = await db.revoked_tokens.find_one({"token": refresh_token, "type": "refresh"})
    if revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked"
        )
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    user_id = payload.get("sub")
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    # Generate new access token (and optionally rotate refresh token)
    new_access = create_access_token(data={"sub": user_id, "email": user["email"]})
    new_refresh = create_refresh_token(data={"sub": user_id})
    # Revoke old refresh token
    await db.revoked_tokens.insert_one({
        "token": refresh_token,
        "type": "refresh",
        "revoked_at": datetime.utcnow(),
        "expires_at": datetime.utcfromtimestamp(payload["exp"])
    })
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }