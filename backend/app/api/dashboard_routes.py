from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.services.dashboard_service import DashboardService
from app.utils.main_utile import return_response

dashboard_router = APIRouter()


@dashboard_router.get(
    "/dashboard/stats",
    summary="Get dashboard statistics for authenticated user",
    response_description="User dashboard statistics calculated from stored email predictions",
)
async def get_dashboard_stats_endpoint(current_user: dict = Depends(get_current_user)):
    """
    GET /api/dashboard/stats
    Returns aggregated real stats for the logged-in user:
    - total_predictions
    - spam_emails & safe_emails
    - spam_percentage & safe_percentage
    - average_confidence
    - weekly change and growth percentage
    """
    user_id = str(current_user["_id"])
    service = DashboardService()
    stats = service.get_dashboard_stats(user_id)

    return return_response(
        status_code=status.HTTP_200_OK,
        message="Dashboard statistics retrieved successfully",
        data=stats.model_dump(),
    )
