from app.core.config import settings
import bcrypt
import jwt
import re
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with a salt round of 12."""
    
    salt = bcrypt.gensalt(rounds=12)
    
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(user_id: str, username: str) -> str:
    """Generate a JWT access token."""

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.
    Returns the payload if valid.
    """

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing"
        )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        user_id = payload.get("sub")
        username = payload.get("username")

        if user_id is None or username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired"
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )

def validate_email(email: str) -> bool:
    """Simple email format validation."""
    
    return re.match(r'^[^@]+@[^@]+\.[^@]+$', email) is not None


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength.
    At least 8 characters, one uppercase, one lowercase, one digit.
    """
    
    if settings.PASSWORD_RULE_APPLY:
        if len(password) < settings.PASSWORD_LENGTH:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
    return True

def return_response(status_code: int, message: str, data: dict = None):
    """
    Return a standardized response dictionary.

    Args:
        status_code (int): The HTTP status code.
        message (str): A message describing the response.
        data (dict, optional): Additional data to include in the response.

    Returns:
        dict: A dictionary containing the response details.
    """
    response = {
        "success": 200 <= status_code < 300,
        "status_code": status_code,
        "message": message,
    }
    if data is not None:
        response["data"] = data

    return response