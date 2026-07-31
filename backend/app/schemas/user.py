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