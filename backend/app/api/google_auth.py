import logging
from fastapi import APIRouter, Request, Response, Query, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.dependencies.google_auth_deps import get_google_oauth_service
from app.services.auth.google_oauth_service import GoogleOAuthService
from app.utils.main_utile import return_response, create_access_token

logger = logging.getLogger("mailsentry.google_oauth.router")

google_auth_router = APIRouter()


@google_auth_router.get("/login")
async def google_login(
    response: Response,
    service: GoogleOAuthService = Depends(get_google_oauth_service)
):
    """
    GET /auth/google/login
    Initiates Google OAuth 2.0 Authorization Code Flow via injected GoogleOAuthService.
    Generates a secure state parameter, sets an HTTP-only cookie,
    and redirects the user to Google's consent screen.
    """
    try:
        temp_resp = Response()
        auth_url = service.generate_auth_url(temp_resp)

        redirect = RedirectResponse(url=auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        for key, value in temp_resp.headers.raw:
            if key.lower() == b"set-cookie":
                redirect.headers.append(key.decode("latin1"), value.decode("latin1"))

        return redirect
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating Google OAuth login: {str(e)}")
        return return_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error initiating Google OAuth login: {str(e)}"
        )


@google_auth_router.get("/callback")
async def google_callback(
    request: Request,
    response: Response,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    """
    GET /auth/google/callback
    Handles the Google OAuth 2.0 redirect callback using injected GoogleOAuthService.
    Validates CSRF state, exchanges code for tokens, verifies ID token,
    matches/auto-creates MailSentry user, persists Google account details,
    and issues standard HTTP-only JWT access token cookie.
    """
    if error:
        logger.warning(f"Google OAuth authorization cancelled or failed: {error}")
        return return_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Google OAuth authorization failed or was cancelled: {error}"
        )

    if not code:
        return return_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Authorization code missing from Google callback"
        )

    try:
        # 1. Validate CSRF state parameter against HTTP-only cookie
        service.validate_csrf_state(request, state)

        # 2. Exchange authorization code for tokens
        token_data = await service.exchange_code_for_tokens(code)

        # 3. Verify ID Token and extract user profile information
        id_token_str = token_data["id_token"]
        user_info = service.verify_id_token(id_token_str)

        # 4. Match existing MailSentry user or auto-create a new user profile
        user_doc = service.find_or_create_user(user_info)
        user_id = str(user_doc["_id"])
        username = user_doc["username"]

        # 5. Persist/update Google Account in MongoDB
        service.persist_google_account(
            google_email=user_info["email"],
            google_user_id=user_info.get("google_id"),
            user_id=user_id,
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in"),
        )

        # 6. Issue standard MailSentry JWT access token and set HTTP-only cookie
        jwt_token = create_access_token(user_id=user_id, username=username)

        response.set_cookie(
            key="access_token",
            value=jwt_token,
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite="lax",
            max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        # 7. Return standard authentication response payload
        return return_response(
            status_code=status.HTTP_200_OK,
            message="Google login successful",
            data={
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": user_info["email"],
                    "role": user_doc.get("role", "user"),
                    "google_connected": True,
                }
            }
        )

    except HTTPException as he:
        return return_response(
            status_code=he.status_code,
            message=he.detail
        )
    except Exception as e:
        logger.error(f"Unexpected error in Google OAuth callback: {str(e)}")
        return return_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error processing Google OAuth callback: {str(e)}"
        )
