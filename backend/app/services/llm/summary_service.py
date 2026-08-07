import logging
from typing import Any

from app.services.llm.base import LLMProvider
from app.services.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class SummaryService:
    """
    High-level business service for Email Summarization.

    Follows Clean Architecture & Dependency Inversion Principle (DIP):
    - SummaryService depends ONLY on the abstract `LLMProvider` interface.
    - NEVER contains provider-specific branching logic or hardcoded provider details.
    - Accepts an `LLMProvider` via dependency injection (or fetches configured provider from LLMFactory).
    """

    def __init__(
        self,
        provider: LLMProvider | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
        provider_name: str | None = None,
    ):
        if provider is not None:
            self.provider = provider
        else:
            self.provider = LLMFactory.get_provider(
                provider_name=provider_name,
                api_key=api_key,
                model_name=model_name,
            )

    @property
    def provider_name(self) -> str:
        return self.provider.provider_name

    @property
    def model_name(self) -> str:
        return self.provider.model_name

    async def generate_summary(self, email_body: str) -> str:
        """
        Delegates email summarization to the injected LLMProvider.

        Args:
            email_body: Email body content text.

        Returns:
            Generated summary string.
        """
        logger.info(
            f"[SummaryService] Initiating email summary request using provider='{self.provider_name}' (model='{self.model_name}')"
        )
        return await self.provider.generate_summary(email_body)
