from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
import re

class ProfileResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: str = "user"
    providers: List[str] = ["local"]
    is_active: bool = True
    google_connected: bool = False
    google_email: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UpdateUsernameRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

    @validator("username")
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(v) > 50:
            raise ValueError("Username must be at most 50 characters long")
        # Allowed chars: letters, numbers, underscores, hyphens, single spaces between words
        if not re.match(r"^[a-zA-Z0-9_\-]+( [a-zA-Z0-9_\-]+)*$", v):
            raise ValueError("Username contains invalid characters")
        return v


class RequestEmailChangeRequest(BaseModel):
    new_email: EmailStr


class VerifyEmailOtpRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6)

    @validator("otp")
    def validate_otp(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 6:
            raise ValueError("OTP must be a 6-digit number")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @validator("confirm_password")
    def validate_passwords_match(cls, v: str, values: dict) -> str:
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v
