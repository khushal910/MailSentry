import re

from pydantic import BaseModel, EmailStr, Field, validator


class ProfileResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: str = "user"
    providers: list[str] = ["local"]
    is_active: bool = True
    google_connected: bool = False
    google_email: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


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
    current_password: str = Field(...)
    new_password: str = Field(...)
    confirm_password: str = Field(...)

    @validator("current_password", "new_password", "confirm_password")
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password fields cannot be empty or whitespace only.")
        return v

    @validator("new_password")
    def validate_new_password_length(cls, v: str) -> str:
        if len(v.strip()) < 8:
            raise ValueError("New password must be at least 8 characters long.")
        return v

    @validator("confirm_password")
    def validate_passwords_match(cls, v: str, values: dict) -> str:
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("New password and confirm password do not match.")
        return v
