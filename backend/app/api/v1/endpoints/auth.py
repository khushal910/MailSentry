from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse,
    TokenRefresh, MessageResponse, UserOut
)
from app.services.auth import register_user, authenticate_user, logout_user, refresh_access_token
from app.core.dependencies import get_current_user, oauth2_scheme
from app.db.mongodb import mongodb

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    user = await register_user(user_data)
    return UserOut(id=user["id"], email=user["email"], full_name=user.get("full_name"), is_active=user["is_active"])

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm uses 'username' for email
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    tokens = await authenticate_user(login_data)
    return tokens

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    tokens = await refresh_access_token(token_data.refresh_token)
    return tokens

@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: dict = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    # Optionally accept refresh_token from request body
    refresh_token: str | None = None
):
    # Invalidate current access token (and refresh if provided)
    message = await logout_user(token, refresh_token)
    return message

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        id=str(current_user["_id"]),
        email=current_user["email"],
        full_name=current_user.get("full_name"),
        is_active=current_user["is_active"]
    )