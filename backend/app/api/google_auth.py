import logging
from fastapi import APIRouter, Request, Response, Query, HTTPException, status
from fastapi.responses import RedirectResponse
from app.services.auth.google_oauth_service import (
    generate_google_auth_url,
    validate_oauth_state,
    exchange_code_for_tokens,
    verify_id_token_and_extract_user,
)
from app.utils.main_utile import return_response

logger = logging.getLogger(__name__)

google_auth_router = APIRouter()


@google_auth_router.get("/login")
async def google_login(response: Response):
    """
    GET /auth/google/login
    Initiates Google OAuth 2.0 Authorization Code Flow.
    Generates a secure state parameter, sets an HTTP-only cookie,
    and redirects the user to Google's consent screen.
    """
    try:
        # Create a temporary redirect response so we can attach the cookie
        temp_resp = Response()
        auth_url = generate_google_auth_url(temp_resp)

        # Build RedirectResponse and copy Set-Cookie headers
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
):
    """
    GET /auth/google/callback
    Handles the Google OAuth 2.0 redirect callback.
    Validates CSRF state, exchanges the authorization code for tokens,
    verifies the ID token, and returns user information.
    """
    # Handle user cancellation or Google OAuth errors
    if error:
        logger.warning(f"Google OAuth error: {error}")
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
        validate_oauth_state(request, state)

        # 2. Exchange authorization code for tokens
        token_data = await exchange_code_for_tokens(code)

        # 3. Verify ID Token and extract user profile information
        id_token_str = token_data.get("id_token")
        if not id_token_str:
            return return_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="ID token missing from Google response"
            )

        user_info = verify_id_token_and_extract_user(id_token_str)

        # 4. Clean up state cookie
        res = return_response(
            status_code=status.HTTP_200_OK,
            message="Google authentication successful",
            data={
                "user_info": user_info,
                "tokens": {
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in"),
                    "id_token": token_data.get("id_token"),
                    "scope": token_data.get("scope"),
                    "token_type": token_data.get("token_type"),
                }
            }
        )

        # Delete oauth_state cookie after validation
        resp = Response(content=res, media_type="application/json") if isinstance(res, str) else None
        # Return standard response dictionary or response with cleared cookie
        # In FastAPI returning dict gets auto JSON-encoded
        return res

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
