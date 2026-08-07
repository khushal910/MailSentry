from unittest.mock import AsyncMock, MagicMock, patch

import httpx
try:
    import pytest
except ImportError:
    class DummyPytestMark:
        def __getattr__(self, name):
            return lambda fn: fn
    class DummyPytest:
        def fixture(self, *args, **kwargs):
            return lambda fn: fn
        mark = DummyPytestMark()
    pytest = DummyPytest()
from fastapi import HTTPException, status

from app.services.llm.base import LLMProvider
from app.services.llm.factory import LLMFactory
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.groq_provider import GroqProvider
from app.services.llm.summary_service import SummaryService


def test_factory_returns_groq_by_default():
    """
    Test that LLMFactory defaults to GroqProvider when LLM_PROVIDER is unset or 'groq'.
    """
    provider = LLMFactory.get_provider("groq")
    assert isinstance(provider, GroqProvider)
    assert provider.provider_name == "groq"
    assert "llama" in provider.model_name.lower()

    # Invalid provider falls back to GroqProvider
    invalid_provider = LLMFactory.get_provider("invalid_provider_name")
    assert isinstance(invalid_provider, GroqProvider)


def test_factory_returns_gemini():
    """
    Test that LLMFactory returns GeminiProvider when provider_name is 'gemini'.
    """
    provider = LLMFactory.get_provider("gemini")
    assert isinstance(provider, GeminiProvider)
    assert provider.provider_name == "gemini"
    assert "gemini" in provider.model_name.lower()


def test_factory_register_new_provider():
    """
    Test that future providers (e.g. OpenAI, Anthropic, Ollama) can be registered dynamically.
    """
    class MockOpenAIProvider(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "openai"

        @property
        def model_name(self) -> str:
            return "gpt-4o"

        async def generate_summary(self, email_body: str) -> str:
            return "Mock OpenAI Summary"

    LLMFactory.register_provider("openai", MockOpenAIProvider)
    provider = LLMFactory.get_provider("openai")

    assert isinstance(provider, MockOpenAIProvider)
    assert provider.provider_name == "openai"
    assert provider.model_name == "gpt-4o"


@pytest.mark.anyio
async def test_groq_provider_summary_success():
    """
    Test successful summary generation using GroqProvider.
    """
    provider = GroqProvider(api_key="mock_groq_api_key", model_name="llama-3.3-70b-versatile")
    email_body = "Project update meeting scheduled for Monday at 10 AM."
    expected_summary = "Purpose: Project update meeting.\nDate: Monday 10 AM.\nActions: Attend meeting."

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": expected_summary
                }
            }
        ],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 30,
            "total_tokens": 150,
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        summary = await provider.generate_summary(email_body)

        assert summary == expected_summary
        mock_post.assert_called_once()

        # Verify endpoint and Authorization header
        call_kwargs = mock_post.call_args.kwargs
        headers = call_kwargs["headers"]
        assert headers["Authorization"] == "Bearer mock_groq_api_key"

        payload = call_kwargs["json"]
        assert payload["model"] == "llama-3.3-70b-versatile"
        assert payload["messages"][1]["content"] == f"Email Body:\n{email_body}"


@pytest.mark.anyio
async def test_groq_provider_missing_api_key_raises_500():
    """
    Test that GroqProvider raises HTTP 500 when GROQ_API_KEY is missing.
    """
    provider = GroqProvider(api_key="")
    with pytest.raises(HTTPException) as exc_info:
        await provider.generate_summary("Body content")

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.anyio
async def test_groq_provider_timeout_retries_and_raises_504():
    """
    Test that GroqProvider retries twice on timeout before raising 504 Gateway Timeout.
    """
    provider = GroqProvider(api_key="mock_key")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")

        with pytest.raises(HTTPException) as exc_info:
            await provider.generate_summary("Email body text")

        assert exc_info.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT
        assert mock_post.call_count == 2


@pytest.mark.anyio
async def test_gemini_provider_summary_success():
    """
    Test successful summary generation using GeminiProvider.
    """
    provider = GeminiProvider(api_key="mock_gemini_key", model_name="gemini-2.5-flash")
    email_body = "Server deployment complete."
    expected_summary = "Purpose: Deployment confirmation.\nTone: Informational."

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": expected_summary}]
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 20,
            "totalTokenCount": 120,
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        summary = await provider.generate_summary(email_body)

        assert summary == expected_summary
        mock_post.assert_called_once()


@pytest.mark.anyio
async def test_summary_service_dependency_injection():
    """
    Test that SummaryService executes via injected LLMProvider abstraction.
    """
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.provider_name = "mock_provider"
    mock_provider.model_name = "mock_model_v1"
    mock_provider.generate_summary = AsyncMock(return_value="Summary from Mock Provider")

    service = SummaryService(provider=mock_provider)

    result = await service.generate_summary("Test body")

    assert result == "Summary from Mock Provider"
    assert service.provider_name == "mock_provider"
    assert service.model_name == "mock_model_v1"
    mock_provider.generate_summary.assert_called_once_with("Test body")
