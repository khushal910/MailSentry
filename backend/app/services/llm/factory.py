import logging
import os
from typing import Type

from app.core.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.groq_provider import GroqProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    Factory Pattern & Strategy Pattern registry for LLM providers.

    Reads `LLM_PROVIDER` from configuration / environment variables.
    Returns configured provider instance (defaults to GroqProvider).
    Supports dynamic registration of future LLM providers without modifying codebase.
    """

    _registry: dict[str, Type[LLMProvider]] = {
        "groq": GroqProvider,
        "gemini": GeminiProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[LLMProvider]) -> None:
        """
        Registers a new LLM provider class into the factory registry.
        Example: LLMFactory.register_provider("openai", OpenAIProvider)
        """
        clean_name = name.lower().strip()
        cls._registry[clean_name] = provider_cls
        logger.info(f"[LLMFactory] Successfully registered LLM provider '{clean_name}'.")

    @classmethod
    def get_provider(
        cls,
        provider_name: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> LLMProvider:
        """
        Instantiates and returns the configured LLMProvider.

        Args:
            provider_name: Optional explicit provider name (e.g. 'groq' or 'gemini').
            api_key: Optional override API key for the provider.
            model_name: Optional override model identifier.

        Returns:
            An instance of LLMProvider (GroqProvider or GeminiProvider).
            Defaults to GroqProvider if provider_name is invalid or missing.
        """
        target_name = provider_name
        if not target_name:
            if model_name and "gemini" in str(model_name).lower():
                target_name = "gemini"
            elif model_name and "llama" in str(model_name).lower():
                target_name = "groq"
            else:
                target_name = (
                    getattr(settings, "LLM_PROVIDER", "groq")
                    or os.getenv("LLM_PROVIDER", "groq")
                )

        clean_name = str(target_name).lower().strip()

        provider_cls = cls._registry.get(clean_name)
        if not provider_cls:
            logger.warning(
                f"[LLMFactory] Unknown LLM_PROVIDER '{clean_name}'. "
                f"Defaulting to 'groq' (GroqProvider)."
            )
            provider_cls = GroqProvider

        logger.info(f"[LLMFactory] Instantiating LLM Provider: '{clean_name}'")
        try:
            return provider_cls(api_key=api_key, model_name=model_name)
        except TypeError:
            return provider_cls()
