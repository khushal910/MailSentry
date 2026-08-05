from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract base interface for LLM summarization providers.
    Follows SOLID principles (Interface Segregation & Dependency Inversion).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the canonical provider name (e.g., 'groq', 'gemini')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the specific LLM model identifier used by the provider."""
        pass

    @abstractmethod
    async def generate_summary(self, email_body: str) -> str:
        """
        Generates a concise summary for the provided email body string.

        Args:
            email_body: Raw email body text to summarize.

        Returns:
            Concise summary string (under 100 words).

        Raises:
            fastapi.HTTPException: On API timeouts, missing keys, or rate limits.
        """
        pass
