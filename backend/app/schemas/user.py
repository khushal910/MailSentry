from pydantic import BaseModel, EmailStr

class UserRegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    """Request payload for POST /forgot-password"""
    email: EmailStr

class VerifyResetOtpRequest(BaseModel):
    """Request payload for POST /verify-reset-otp"""
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    """Request payload for POST /reset-password"""
    reset_token: str
    new_password: str