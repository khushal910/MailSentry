import logging
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.dependencies.google_auth_deps import get_google_oauth_service
from app.services.auth.google_oauth_service import GoogleOAuthService
from app.utils.main_utile import create_access_token, return_response, set_auth_cookie

logger = logging.getLogger("mailsentry.google_oauth.router")

google_auth_router = APIRouter()


def _get_frontend_base(request: Request) -> str:
    """
    Returns the canonical frontend base URL from settings.FRONTEND_URL.

    Why settings.FRONTEND_URL instead of sniffing headers:
    When Google redirects back to /auth/google/callback, the browser issues a
    plain GET with no Origin or Referer header (browsers strip Referer on
    cross-site navigations and never send Origin on GET redirects). Sniffing
    those headers therefore always falls through to reading the *backend* Host
    header, producing the wrong redirect target.

    The FRONTEND_URL env var is the authoritative source for where the frontend
    lives and is controlled by the server admin.
    """
    frontend_base = settings.FRONTEND_URL.rstrip("/")
    logger.debug(f"Frontend base URL resolved to: {frontend_base}")
    return frontend_base


@google_auth_router.get("/login")
async def google_login(
    request: Request,
    user_id: str | None = Query(None),
    google_email: str | None = Query(None),
    service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    """
    GET /auth/google/login

    Initiates Google OAuth 2.0 Authorization Code Flow.
    Differentiates First Login vs Returning Login:
    - If user is already authenticated or has a stored refresh token in MongoDB,
      omits prompt="consent" so Google signs them in without showing the consent screen.
    - Otherwise, includes prompt="consent" to request offline access and refresh_token.
    """
    try:
        # Check if user is logged in via access_token cookie
        if not user_id:
            token = request.cookies.get("access_token")
            if token:
                try:
                    from app.utils.main_utile import decode_token

                    payload = decode_token(token)
                    user_id = payload.get("user_id") or payload.get("sub")
                except Exception:
                    pass

        # 1. Build the Google authorization URL (also returns the raw state string)
        state, auth_url = service.generate_auth_url_with_state(
            user_id=user_id, google_email=google_email
        )

        # 2. Redirect the browser to Google's consent screen / sign-in screen
        redirect = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)

        logger.info("Google OAuth login initiated — redirecting to Google.")
        return redirect
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating Google OAuth login: {e!s}", exc_info=True)
        return return_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error initiating Google OAuth login: {e!s}",
        )


@google_auth_router.get("/callback")
async def google_callback(
    request: Request,
    response: Response,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    format: str | None = Query(None),
    service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    """
    GET /auth/google/callback

    Handles the Google OAuth 2.0 redirect. Instead of setting an HTTP-only cookie here
    (which fails across 127.0.0.1 vs localhost), we redirect the browser to the
    frontend /auth/callback page and pass the JWT as a short-lived URL query parameter.

    The frontend /auth/callback page calls POST /auth/google/set-token to convert that
    URL token into a proper HttpOnly cookie on the correct origin, then navigates to
    /dashboard. This is the industry-standard approach for OAuth code flows with SPAs.
    """
    frontend_base = _get_frontend_base(request)

    if error:
        logger.warning(f"Google OAuth authorization cancelled or failed: {error}")
        if format == "json":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google authorization failed: {error}",
            )
        error_url = (
            f"{frontend_base}/login?oauth_error={urllib.parse.quote(str(error))}"
        )
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)

    if not code or not code.strip():
        logger.warning("Google callback invoked without authorization code.")
        if format == "json":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is missing",
            )
        error_url = f"{frontend_base}/login?oauth_error=missing_code"
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)

    try:
        # Step 1 — Validate CSRF state cookie against query param
        logger.debug("Step 1: Validating CSRF state parameter.")
        service.validate_csrf_state(request, state)
        logger.debug("Step 1 OK: CSRF state is valid.")

        # Step 2 — Exchange authorization code for tokens from Google
        logger.debug("Step 2: Exchanging authorization code for tokens.")
        token_data = await service.exchange_code_for_tokens(code)
        logger.debug("Step 2 OK: Received token_data keys: %s", list(token_data.keys()))

        # Step 3 — Verify ID Token and extract user profile
        logger.debug("Step 3: Verifying Google ID Token.")
        id_token_str = token_data["id_token"]
        user_info = service.verify_id_token(id_token_str)
        logger.info("Step 3 OK: Verified Google user email=%s", user_info.get("email"))

        # Step 4 — Find logged in user or match existing MailSentry user
        logger.debug("Step 4: Finding or creating MailSentry user.")
        logged_in_user_id = None
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()

        if token:
            try:
                from app.utils.main_utile import decode_token

                payload = decode_token(token)
                logged_in_user_id = payload.get("user_id") or payload.get("sub")
            except Exception:
                pass

        user_doc = service.find_or_create_user(
            user_info, current_user_id=logged_in_user_id
        )
        user_id = str(user_doc["_id"])
        username = user_doc["username"]
        logger.info("Step 4 OK: user_id=%s username=%s", user_id, username)

        # Step 5 — Persist / update Google account record in MongoDB
        logger.debug("Step 5: Persisting Google account to MongoDB.")
        service.persist_google_account(
            google_email=user_info["email"],
            google_user_id=user_info.get("google_id"),
            user_id=user_id,
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in"),
        )
        logger.debug("Step 5 OK: Google account persisted.")

        # Step 6 — Issue MailSentry JWT access token
        logger.debug("Step 6: Issuing MailSentry JWT access token.")
        jwt_token = create_access_token(user_id=user_id, username=username)
        logger.debug("Step 6 OK: JWT token created.")

        # 7. If JSON format is explicitly requested (for testing), return JSON + cookie
        if format == "json":
            res = return_response(
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
                },
            )
            set_auth_cookie(response, jwt_token)
            return res

        # 8. Redirect to frontend /auth/callback with token as URL param.
        encoded_token = urllib.parse.quote(jwt_token, safe="")
        redirect_url = f"{frontend_base}/auth/callback?token={encoded_token}"

        redirect_resp = RedirectResponse(
            url=redirect_url, status_code=status.HTTP_302_FOUND
        )
        logger.info(
            f"Google OAuth successful for user_id={user_id}. "
            f"Redirecting to frontend callback at {frontend_base}/auth/callback"
        )
        return redirect_resp

    except HTTPException as he:
        if format == "json":
            raise he
        logger.warning(
            "HTTPException in Google OAuth callback: status=%s detail=%s",
            he.status_code,
            he.detail,
        )
        error_url = (
            f"{frontend_base}/login?oauth_error={urllib.parse.quote(str(he.detail))}"
        )
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)
    except Exception as e:
        if format == "json":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Google server error: {e!s}",
            )
        logger.error(
            "Unexpected error in Google OAuth callback: %s", str(e), exc_info=True
        )
        error_url = f"{frontend_base}/login?oauth_error=server_error"
        return RedirectResponse(url=error_url, status_code=status.HTTP_302_FOUND)


@google_auth_router.post("/set-token")
async def set_token(
    request: Request,
    response: Response,
):
    """
    POST /auth/google/set-token

    Called by the frontend /auth/callback page immediately after receiving the
    JWT from the URL query parameter. Validates the token and sets it as a proper
    HttpOnly cookie on this origin, then returns success.

    The frontend immediately removes the token from the URL and navigates to /dashboard.

    Request body: { "token": "<jwt>" }
    """
    try:
        body = await request.json()
        token = body.get("token", "").strip()

        if not token:
            return return_response(status_code=400, message="Token is required")

        # Validate the token is a real, unexpired JWT before setting it as a cookie
        from app.utils.main_utile import decode_token

        decode_token(token)  # raises HTTPException 401 if invalid/expired

        set_auth_cookie(response, token)
        logger.info("Access token cookie set successfully via /auth/google/set-token")
        return return_response(status_code=200, message="Token set successfully")

    except HTTPException as he:
        return return_response(status_code=he.status_code, message=he.detail)
    except Exception as e:
        logger.error(f"Error in /auth/google/set-token: {e!s}")
        return return_response(status_code=500, message="Failed to set token")


@google_auth_router.post("/refresh-token")
async def refresh_google_token(
    request: Request,
    google_email: str | None = Query(None),
    service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    """
    POST /auth/google/refresh-token

    Triggers an automatic refresh of the Google OAuth access token using the stored
    encrypted refresh token in MongoDB.
    Accepts google_email in body or query param.
    """
    try:
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass

        email = google_email or body.get("google_email")
        if not email:
            return return_response(status_code=400, message="google_email is required")

        fresh_access_token = await service.refresh_google_access_token(email)
        return return_response(
            status_code=200,
            message="Google access token refreshed successfully",
            data={"access_token": fresh_access_token, "google_email": email},
        )
    except HTTPException as he:
        return return_response(status_code=he.status_code, message=he.detail)
    except Exception as e:
        logger.error(f"Error in /auth/google/refresh-token: {e!s}")
        return return_response(
            status_code=500, message="Failed to refresh Google access token"
        )
