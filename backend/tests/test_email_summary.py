from unittest.mock import AsyncMock, MagicMock, patch

from bson import ObjectId
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.repositories.email_repository import EmailRepository
from app.services.email_summary_service import EmailSummaryService
from app.utils.main_utile import create_access_token
from main import app


@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=EmailRepository)
    return repo


@pytest.fixture
def summary_service(mock_repo):
    return EmailSummaryService(repository=mock_repo)


@pytest.mark.anyio
async def test_returns_cached_summary_without_calling_gemini(summary_service, mock_repo):
    """
    Test Requirement 4: If summary exists in DB, return it immediately and NEVER call Gemini API.
    """
    email_id = str(ObjectId())
    cached_text = "This is a previously cached summary of the email."

    mock_repo.find_by_id.return_value = {
        "_id": ObjectId(email_id),
        "user_id": "user123",
        "subject": "Project Status Update",
        "body": "Hi team, here is the weekly project update. All tasks are on schedule.",
        "summary": cached_text,
    }

    with patch.object(summary_service, "_call_gemini_api", new_callable=AsyncMock) as mock_gemini:
        result = await summary_service.get_or_generate_summary(email_id=email_id)

        assert result["email_id"] == email_id
        assert result["summary"] == cached_text
        assert result["cached"] is True

        # CRITICAL VERIFICATION: Gemini API was NEVER called
        mock_gemini.assert_not_called()
        mock_repo.update_summary.assert_not_called()


@pytest.mark.anyio
async def test_generates_and_stores_summary_when_not_cached(summary_service, mock_repo):
    """
    Test Requirement 5: If summary does not exist, send body to Gemini, generate summary, store in DB, and return it.
    """
    email_id = str(ObjectId())
    email_body = "Important security alert: Please update your password immediately."
    generated_text = "Action required: Password reset requested due to security alert."

    mock_repo.find_by_id.return_value = {
        "_id": ObjectId(email_id),
        "user_id": "user123",
        "subject": "Security Notice",
        "body": email_body,
        "summary": None,  # No summary present
    }
    mock_repo.update_summary.return_value = True

    with patch.object(summary_service, "_call_gemini_api", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = generated_text

        result = await summary_service.get_or_generate_summary(email_id=email_id)

        assert result["email_id"] == email_id
        assert result["summary"] == generated_text
        assert result["summary_model"] == summary_service.summary_service.model_name
        assert result["summary_created_at"] is not None
        assert result["cached"] is False

        # Verify Gemini API was called with the body text
        mock_gemini.assert_called_once_with(email_body)
        # Verify MongoDB was updated with summary, summary_model, and summary_created_at
        mock_repo.update_summary.assert_called_once()
        call_kwargs = mock_repo.update_summary.call_args.kwargs
        assert call_kwargs["email_id"] == email_id
        assert call_kwargs["summary"] == generated_text
        assert call_kwargs["summary_model"] == summary_service.summary_service.model_name
        assert call_kwargs["summary_created_at"] is not None


@pytest.mark.anyio
async def test_raises_404_when_email_not_found(summary_service, mock_repo):
    """
    Test Requirement 2 & 7: Return 404 Not Found if email_id does not exist.
    """
    email_id = str(ObjectId())
    mock_repo.find_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await summary_service.get_or_generate_summary(email_id=email_id)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_raises_400_when_email_id_is_empty(summary_service):
    """
    Test Requirement 6 & 7: Return 400 Bad Request when email_id is invalid/empty.
    """
    with pytest.raises(HTTPException) as exc_info:
        await summary_service.get_or_generate_summary(email_id="")

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.anyio
async def test_raises_400_when_email_body_is_empty(summary_service, mock_repo):
    """
    Test Requirement 6 & 7: Return 400 Bad Request when email body is empty.
    """
    email_id = str(ObjectId())
    mock_repo.find_by_id.return_value = {
        "_id": ObjectId(email_id),
        "user_id": "user123",
        "subject": "",
        "body": "",  # Empty body
        "summary": None,
    }

    with pytest.raises(HTTPException) as exc_info:
        await summary_service.get_or_generate_summary(email_id=email_id)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_endpoint_get_email_summary_cached():
    """
    Test GET /emails/{email_id}/summary endpoint with cached summary.
    """
    user_id = str(ObjectId())
    email_id = str(ObjectId())
    mock_user = {"_id": user_id, "username": "testuser"}
    app.dependency_overrides[get_current_user] = lambda: mock_user

    token = create_access_token(user_id=user_id, username="testuser")

    with patch("app.api.emails.EmailRepository") as mock_repo_cls:
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.find_by_id.return_value = {
            "_id": ObjectId(email_id),
            "user_id": user_id,
            "subject": "Test Email",
            "body": "Test body content",
            "summary": "Existing cached summary text",
        }

        client = TestClient(app)
        response = client.get(
            f"/api/emails/{email_id}/summary",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status_code"] == 200
        assert json_data["data"]["summary"] == "Existing cached summary text"
        assert json_data["data"]["cached"] is True

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_gmail_message_id_lookup_success(summary_service, mock_repo):
    """
    Test lookup when email_id is a 16-character Gmail message_id string (e.g. '19fcdab11a9f0ff7').
    """
    gmail_msg_id = "19fcdab11a9f0ff7"
    email_doc_id = str(ObjectId())

    mock_repo.find_by_id.return_value = {
        "_id": ObjectId(email_doc_id),
        "message_id": gmail_msg_id,
        "user_id": "user123",
        "subject": "Gmail Message Test",
        "body": "Body content of Gmail message.",
        "summary": "Cached summary for Gmail message ID.",
    }

    result = await summary_service.get_or_generate_summary(email_id=gmail_msg_id)

    assert result["summary"] == "Cached summary for Gmail message ID."
    assert result["cached"] is True
    mock_repo.find_by_id.assert_called_with(gmail_msg_id)


