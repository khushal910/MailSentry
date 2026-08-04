from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse

from app.dependencies.auth import get_current_user
from app.dependencies.google_auth_deps import get_google_oauth_service
from app.schemas.google_auth import (
    GoogleStatusConnectedResponse,
    GoogleStatusNotConnectedResponse,
)
from app.services.auth.google_oauth_service import GoogleOAuthService
from app.services.auth.google_status import (
    disconnect_google_service,
    get_google_status_service,
)
from app.utils.main_utile import return_response

google_status_router = APIRouter()


@google_status_router.get(
    "/connect",
    summary="Generate Google OAuth URL with prompt=consent and access_type=offline and redirect",
)
async def connect_google(
    request: Request,
    user_id: str | None = Query(None),
    google_email: str | None = Query(None),
    format: str | None = Query(None),
    service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    """
    GET /api/google/connect

    Initiates Google OAuth flow to connect or reconnect Gmail.
    - Uses access_type=offline and prompt=consent.
    - Performs zero database changes.
    - If format=json, returns {"url": auth_url}.
    - Otherwise redirects (302) to Google.
    """
    if not user_id:
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()

        if token:
            try:
                from app.utils.main_utile import decode_token

                payload = decode_token(token)
                user_id = payload.get("user_id") or payload.get("sub")
            except Exception:
                pass

    state, auth_url = service.generate_connect_url_with_state(
        user_id=user_id, google_email=google_email
    )

    if format == "json":
        return return_response(
            status_code=status.HTTP_200_OK,
            message="Google connect URL generated successfully",
            data={"url": auth_url, "state": state},
        )

    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@google_status_router.get(
    "/status",
    response_model=GoogleStatusConnectedResponse | GoogleStatusNotConnectedResponse,
    summary="Get Google Account connection status for currently logged-in user",
)
async def get_google_status(current_user: dict = Depends(get_current_user)):
    """
    GET /api/google/status

    Requires valid JWT token. Returns Google account connection status for the user.
    """
    user_id = str(current_user["_id"])
    return get_google_status_service(user_id)


@google_status_router.post(
    "/disconnect",
    summary="Disconnect Google Account for current user",
)
async def disconnect_google(current_user: dict = Depends(get_current_user)):
    """
    POST /api/google/disconnect

    Disconnects the Google account for the authenticated user.
    """
    user_id = str(current_user["_id"])
    return disconnect_google_service(user_id)
