from app.core.config import settings
import bcrypt
import jwt
import re
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with a salt round of 12."""
    try:
        salt = bcrypt.gensalt(rounds=12)
    
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    except Exception as e:
        return return_response(
            status_code=500,
            message=f"Error hashing password: {str(e)}"
        )


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        return return_response(
            status_code=500,
            message=f"Error verifying password: {str(e)}"
        )


def create_access_token(user_id: str, username: str) -> str:
    """Generate a JWT access token."""

    try:
        
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

    except Exception as e:
        return return_response(
            status_code=500,
            message=f"Error creating access token: {str(e)}"
        )

# Password‑reset JWT helpers
def create_password_reset_token(email: str) -> str:
    """Create a short‑lived JWT for password‑reset flows.
    Payload includes email, purpose='password_reset', exp (10 min), iat.
    """
    try:
        expire = datetime.now(timezone.utc) + timedelta(minutes=10)
        payload = {
            "email": email,
            "purpose": "password_reset",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    except Exception as e:
        raise RuntimeError(f"Error creating password reset token: {str(e)}")

def verify_password_reset_token(token: str) -> dict:
    """Validate a password‑reset token and return its payload.
    Raises HTTPException(401) for missing, expired, invalid, or wrong‑purpose tokens.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token purpose")
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password reset token has expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password reset token")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error verifying token: {str(e)}")
    
def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.
    Returns the payload if valid.
    """
    
    try:

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

            user_id = payload.get("user_id") or payload.get("sub")

            if user_id is None:
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error decoding token: {str(e)}"
        )

def validate_email(email: str) -> bool:
    """Simple email format validation."""
    
    try:
        return re.match(r'^[^@]+@[^@]+\.[^@]+$', email) is not None
    except Exception as e:
        return return_response(
            status_code=500,
            message=f"Error validating email: {str(e)}"
        )


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength.
    At least {settings.PASSWORD_LENGTH} characters, one uppercase, one lowercase, one digit.
    """
    try:
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
    except Exception as e:
        return return_response(
            status_code=500,
            message=f"Error validating password strength: {str(e)}"
        )

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
    
    try:
        response = {
            "success": 200 <= status_code < 300,
            "status_code": status_code,
            "message": message,
        }
        if data is not None:
            response["data"] = data

        return response
    except Exception as e:
        return {
            "success": False,
            "status_code": 500,
            "message": f"Error generating response: {str(e)}"
        }