from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.services.auth.google_status import get_google_status_service
from app.schemas.google_auth import (
    GoogleStatusConnectedResponse,
    GoogleStatusNotConnectedResponse,
)

google_status_router = APIRouter()


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
