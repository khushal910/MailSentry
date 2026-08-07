"""
Re-export SummaryService for backward compatibility with existing imports across the application.
Delegates implementation to app.services.llm.summary_service.
"""

from app.services.llm.base import LLMProvider
from app.services.llm.factory import LLMFactory
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.summary_service import SummaryService

__all__ = [
    "SummaryService",
    "LLMProvider",
    "LLMFactory",
    "GroqProvider",
    "GeminiProvider",
]
