import logging

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardStatsResponse
from app.utils.cache_util import dashboard_stats_cache

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service layer for retrieving and preparing dashboard statistics for authenticated users with in-memory caching.
    """

    def __init__(self, repo: DashboardRepository | None = None):
        self.repo = repo if repo is not None else DashboardRepository()

    def get_dashboard_stats(self, user_id: str) -> DashboardStatsResponse:
        """
        Retrieves real aggregated dashboard statistics for the specified user_id with in-memory caching.
        """
        cache_key = f"stats:{user_id}"
        cached = dashboard_stats_cache.get(cache_key)
        if cached is not None and isinstance(cached, dict):
            return DashboardStatsResponse(**cached)

        raw_stats = self.repo.get_user_stats(user_id)
        stats_obj = DashboardStatsResponse(**raw_stats)
        dashboard_stats_cache.set(cache_key, stats_obj.model_dump(), ttl_seconds=30)
        return stats_obj

