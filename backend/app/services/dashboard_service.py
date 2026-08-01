import logging
from typing import Optional
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardStatsResponse

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service layer for retrieving and preparing dashboard statistics for authenticated users.
    """

    def __init__(self, repo: Optional[DashboardRepository] = None):
        self.repo = repo if repo is not None else DashboardRepository()

    def get_dashboard_stats(self, user_id: str) -> DashboardStatsResponse:
        """
        Retrieves real aggregated dashboard statistics for the specified user_id.
        """
        raw_stats = self.repo.get_user_stats(user_id)
        return DashboardStatsResponse(**raw_stats)
