from typing import Optional
from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    """
    Pydantic response schema for user dashboard statistics.
    All fields are calculated per-user from MongoDB predictions.
    """
    total_predictions: int = Field(0, description="Total predictions belonging to current user")
    spam_emails: int = Field(0, description="Total spam emails count")
    safe_emails: int = Field(0, description="Total safe emails count")
    accuracy: Optional[float] = Field(None, description="Accuracy score if ground truth exists, else null")
    average_confidence: float = Field(0.0, description="Average model confidence score percentage (0-100)")
    today_predictions: int = Field(0, description="Predictions count for today (UTC)")
    last_week_predictions: int = Field(0, description="Predictions count for previous week")
    this_week_predictions: int = Field(0, description="Predictions count for current week")
    spam_percentage: float = Field(0.0, description="Percentage of spam predictions (0-100)")
    safe_percentage: float = Field(0.0, description="Percentage of safe predictions (0-100)")
    growth_percentage: Optional[float] = Field(None, description="Growth percentage vs last week (None if lastWeek == 0)")
