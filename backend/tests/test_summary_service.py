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

from app.services.summary_service import SummaryService


@pytest.fixture
def summary_service():
    return SummaryService(api_key="test_gemini_api_key", model_name="gemini-1.5-flash")


@pytest.mark.anyio
async def test_generate_summary_success(summary_service):
    """
    Test successful summary generation with structured prompt and Gemini API response.
    """
    email_body = (
        "Dear Team, Please submit your project reports by Friday, August 10th. "
        "We need to review the Q3 budget requirements."
    )
    expected_summary = (
        "Purpose: Q3 report submission.\n"
        "Important dates: Friday, August 10th.\n"
        "Required actions: Submit project reports.\n"
        "Deadlines: Aug 10.\n"
        "Tone: Professional and urgent."
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": expected_summary}]
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        summary = await summary_service.generate_summary(email_body)

        assert summary == expected_summary
        mock_post.assert_called_once()

        # Check payload contents
        call_kwargs = mock_post.call_args.kwargs
        payload = call_kwargs["json"]
        sent_text = payload["contents"][0]["parts"][0]["text"]

        assert "You are an intelligent email assistant." in sent_text
        assert "Purpose" in sent_text
        assert "Important dates" in sent_text
        assert "Required actions" in sent_text
        assert "Deadlines" in sent_text
        assert "Tone" in sent_text
        assert "Return the summary in under 100 words." in sent_text
        assert email_body in sent_text


@pytest.mark.anyio
async def test_generate_summary_retry_on_timeout_success(summary_service):
    """
    Test that generate_summary retries once on TimeoutException and succeeds on attempt 2.
    """
    email_body = "Weekly sync call scheduled for tomorrow at 10 AM."
    expected_summary = "Purpose: Weekly sync meeting tomorrow at 10 AM."

    mock_success_response = MagicMock()
    mock_success_response.status_code = 200
    mock_success_response.json.return_value = {
        "candidates": [
            {"content": {"parts": [{"text": expected_summary}]}}
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # 1st call raises TimeoutException, 2nd call returns success response
        mock_post.side_effect = [
            httpx.TimeoutException("Connection timed out"),
            mock_success_response,
        ]

        summary = await summary_service.generate_summary(email_body)

        assert summary == expected_summary
        assert mock_post.call_count == 2


@pytest.mark.anyio
async def test_generate_summary_retry_fails_raises_504(summary_service):
    """
    Test that generate_summary raises HTTP 504 after retrying twice on persistent timeout.
    """
    email_body = "Urgent server maintenance tonight at 11 PM."

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")

        with pytest.raises(HTTPException) as exc_info:
            await summary_service.generate_summary(email_body)

        assert exc_info.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT
        assert mock_post.call_count == 2


@pytest.mark.anyio
async def test_generate_summary_empty_response_raises_502(summary_service):
    """
    Test that empty response candidate set from Gemini raises 502 Bad Gateway.
    """
    email_body = "Meeting invite: Project kickoff."

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"candidates": []}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            await summary_service.generate_summary(email_body)

        assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY
        assert mock_post.call_count == 2


@pytest.mark.anyio
async def test_generate_summary_missing_api_key_raises_500():
    """
    Test that missing API key raises HTTP 500.
    """
    service = SummaryService(api_key="")

    with pytest.raises(HTTPException) as exc_info:
        await service.generate_summary("Some body content")

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.anyio
async def test_generate_summary_empty_body_raises_400(summary_service):
    """
    Test that empty body raises HTTP 400.
    """
    with pytest.raises(HTTPException) as exc_info:
        await summary_service.generate_summary("   ")

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
