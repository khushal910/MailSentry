import logging
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status

from app.core.config import settings
from app.dependencies.auth import get_current_user
from app.schemas.profile_schema import (
    ProfileResponse,
    UpdateUsernameRequest,
    RequestEmailChangeRequest,
    VerifyEmailOtpRequest,
    ChangePasswordRequest,
)
from app.services.profile_service import ProfileService
from app.utils.main_utile import return_response, create_access_token

logger = logging.getLogger("mailsentry.profile_api")

profile_router = APIRouter()
profile_service = ProfileService()


def _get_client_ip(request: Request) -> str:
    """Extracts client IP address for audit logging."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _set_jwt_cookie(response: Response, user_id: str, username: str) -> str:
    """Generates a fresh JWT access token and sets it as an HttpOnly cookie."""
    new_jwt = create_access_token(user_id=user_id, username=username)
    response.set_cookie(
        key="access_token",
        value=new_jwt,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="lax",
        path="/",
        max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return new_jwt


@profile_router.get(
    "/profile",
    summary="Get authenticated user profile details",
    response_model=None
)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    GET /api/profile
    Returns current user profile information including role, providers, creation date,
    and linked Google account email/status.
    """
    user_id = str(current_user["_id"])
    profile = profile_service.get_profile(user_id)
    return return_response(
        status_code=status.HTTP_200_OK,
        message="Profile details retrieved successfully",
        data=profile,
    )


@profile_router.patch(
    "/profile/username",
    summary="Update username",
    response_model=None
)
async def update_username(
    payload: UpdateUsernameRequest,
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    """
    PATCH /api/profile/username
    Updates username, regenerates JWT access token, and sets updated HttpOnly cookie.
    """
    user_id = str(current_user["_id"])
    client_ip = _get_client_ip(request)

    updated_profile = profile_service.update_username(
        user_id=user_id,
        new_username=payload.username,
        client_ip=client_ip,
    )

    # Regenerate JWT and set cookie
    new_jwt = _set_jwt_cookie(response, user_id=user_id, username=updated_profile["username"])

    return return_response(
        status_code=status.HTTP_200_OK,
        message="Username updated successfully",
        data={
            "profile": updated_profile,
            "token": new_jwt,
        },
    )


@profile_router.post(
    "/profile/request-email-change",
    summary="Request email change (sends OTP)",
    response_model=None
)
async def request_email_change(
    payload: RequestEmailChangeRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/profile/request-email-change
    Checks email availability, generates a 6-digit OTP, stores expiry (5 min),
    and sends OTP to the new email address.
    """
    user_id = str(current_user["_id"])
    client_ip = _get_client_ip(request)

    res = await profile_service.request_email_change(
        user_id=user_id,
        new_email=payload.new_email,
        client_ip=client_ip,
    )

    return return_response(
        status_code=status.HTTP_200_OK,
        message=res["message"],
        data=res,
    )


@profile_router.post(
    "/profile/verify-email-otp",
    summary="Verify OTP and complete email change",
    response_model=None
)
async def verify_email_otp(
    payload: VerifyEmailOtpRequest,
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/profile/verify-email-otp
    Verifies 6-digit OTP, updates email in MongoDB, synchronizes Google accounts,
    regenerates JWT access token, and updates HttpOnly cookie.
    """
    user_id = str(current_user["_id"])
    client_ip = _get_client_ip(request)

    updated_profile = profile_service.verify_email_change_otp(
        user_id=user_id,
        otp=payload.otp,
        client_ip=client_ip,
    )

    # Regenerate JWT and set cookie
    new_jwt = _set_jwt_cookie(response, user_id=user_id, username=updated_profile["username"])

    msg = "Email address updated successfully"
    if "notice" in updated_profile:
        msg = f"Email updated successfully. {updated_profile['notice']}"

    return return_response(
        status_code=status.HTTP_200_OK,
        message=msg,
        data={
            "profile": updated_profile,
            "token": new_jwt,
        },
    )


@profile_router.post(
    "/profile/password",
    summary="Change password for local accounts",
    response_model=None
)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/profile/password
    Changes password for local accounts after verifying current password.
    Regenerates JWT access token and updates HttpOnly cookie.
    """
    user_id = str(current_user["_id"])
    client_ip = _get_client_ip(request)

    res = profile_service.change_password(
        user_id=user_id,
        current_pw=payload.current_password,
        new_pw=payload.new_password,
        confirm_pw=payload.confirm_password,
        client_ip=client_ip,
    )

    # Regenerate JWT and set cookie
    new_jwt = _set_jwt_cookie(response, user_id=user_id, username=current_user["username"])

    return return_response(
        status_code=status.HTTP_200_OK,
        message=res["message"],
        data={
            "token": new_jwt,
        },
    )
