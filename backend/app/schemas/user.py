from pydantic import BaseModel, EmailStr


class VerifyResetOtpRequest(BaseModel):
    """Request payload for POST /verify-reset-otp"""
    email: EmailStr
    otp: str