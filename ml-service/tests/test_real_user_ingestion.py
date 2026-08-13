import os
import sys
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from src.components.real_user_ingestion import RealUserIngestion
from src.entity.config_entity import DataIngestionConfig
from src.data_access.fetch_data import FetchRealUserMail


def test_resolve_gmail_label():
    """Test Gmail label resolution priority."""
    # Priority 1: is_spam boolean flag
    assert RealUserIngestion.resolve_gmail_label({"gmail_classification": {"is_spam": True}}) == "spam"
    assert RealUserIngestion.resolve_gmail_label({"gmail_classification": {"is_spam": False}}) == "ham"

    # Priority 2: status string
    assert RealUserIngestion.resolve_gmail_label({"gmail_classification": {"status": "spam"}}) == "spam"
    assert RealUserIngestion.resolve_gmail_label({"gmail_classification": {"status": "not_spam"}}) == "ham"

    # Priority 3: label_ids
    assert RealUserIngestion.resolve_gmail_label({"label_ids": ["SPAM", "UNREAD"]}) == "spam"
    assert RealUserIngestion.resolve_gmail_label({"label_ids": ["INBOX"]}) == "ham"

    # Ambiguous
    assert RealUserIngestion.resolve_gmail_label({}) is None
    assert RealUserIngestion.resolve_gmail_label({"gmail_classification": {}}) is None


def test_extract_text_and_subject():
    """Test message and subject extraction rules."""
    # Body present -> prefers body
    subj, msg = RealUserIngestion.extract_text_and_subject({"subject": "Hello", "body": "Full body text", "snippet": "Snippet text"})
    assert subj == "Hello"
    assert msg == "Full body text"

    # Body missing -> falls back to snippet
    subj, msg = RealUserIngestion.extract_text_and_subject({"subject": "Hello", "snippet": "Snippet text"})
    assert subj == "Hello"
    assert msg == "Snippet text"

    # Subject empty, Message present -> Accept
    subj, msg = RealUserIngestion.extract_text_and_subject({"subject": "", "snippet": "Snippet text"})
    assert subj == ""
    assert msg == "Snippet text"

    # Message empty, Subject present -> Accept
    subj, msg = RealUserIngestion.extract_text_and_subject({"subject": "Hello", "body": ""})
    assert subj == "Hello"
    assert msg == ""

    # Both empty -> Empty strings
    subj, msg = RealUserIngestion.extract_text_and_subject({"subject": "", "body": ""})
    assert subj == ""
    assert msg == ""


def test_incremental_ingestion_and_checkpoint_advancement(tmp_path):
    """
    Test incremental fetching via MongoDB _id checkpoint.
    Run 1: 2 new docs -> 2 appended -> checkpoint advances to doc 2.
    Run 2: 0 new docs -> 0 appended -> dataset stays size 2.
    Run 3: 1 new doc -> 1 appended -> dataset becomes size 3 -> checkpoint advances to doc 3.
    """
    curated_file = str(tmp_path / "real_user_curated.csv")
    state_file = str(tmp_path / "ingestion_state.json")

    config = DataIngestionConfig()
    config.real_user_curated_file_path = curated_file
    config.ingestion_state_file_path = state_file

    mock_docs_batch1 = [
        {"_id": "651a2f000000000000000001", "message_id": "msg_001", "subject": "Spam 1", "body": "Click here", "gmail_classification": {"is_spam": True}},
        {"_id": "651a2f000000000000000002", "message_id": "msg_002", "subject": "Ham 1", "body": "Meeting tomorrow", "gmail_classification": {"is_spam": False}},
    ]

    with patch("src.components.real_user_ingestion.FetchRealUserMail") as MockFetch:
        mock_fetch_instance = MagicMock()
        MockFetch.return_value = mock_fetch_instance

        # Run 1 Setup
        mock_fetch_instance.get_last_processed_id.return_value = None
        mock_fetch_instance.fetch_new_user_emails.return_value = mock_docs_batch1

        ingestion = RealUserIngestion(config=config)
        df_run1 = ingestion.ingest_incremental_real_user_data()

        assert len(df_run1) == 2
        assert list(df_run1.columns) == ["Message ID", "Subject", "Message", "Spam/Ham", "Date"]
        assert list(df_run1["Message ID"]) == ["msg_001", "msg_002"]
        assert set(df_run1["Spam/Ham"]) == {"spam", "ham"}
        assert os.path.exists(curated_file)
        # Verify checkpoint update was called with highest _id
        mock_fetch_instance.update_last_processed_id.assert_called_with("651a2f000000000000000002", state_file_path=state_file)

        # Run 2 Setup (No new documents _id > doc 2)
        mock_fetch_instance.reset_mock()
        mock_fetch_instance.get_last_processed_id.return_value = "651a2f000000000000000002"
        mock_fetch_instance.fetch_new_user_emails.return_value = []

        df_run2 = ingestion.ingest_incremental_real_user_data()
        assert len(df_run2) == 2  # Count remains 2
        mock_fetch_instance.update_last_processed_id.assert_not_called()

        # Run 3 Setup (1 new document _id > doc 2)
        mock_docs_batch2 = [
            {"_id": "651a2f000000000000000003", "message_id": "msg_003", "subject": "Ham 2", "body": "Invoice attached", "gmail_classification": {"is_spam": False}},
        ]
        mock_fetch_instance.reset_mock()
        mock_fetch_instance.get_last_processed_id.return_value = "651a2f000000000000000002"
        mock_fetch_instance.fetch_new_user_emails.return_value = mock_docs_batch2

        df_run3 = ingestion.ingest_incremental_real_user_data()
        assert len(df_run3) == 3  # Count becomes 3
        mock_fetch_instance.update_last_processed_id.assert_called_with("651a2f000000000000000003", state_file_path=state_file)


def test_fail_safe_checkpoint_protection(tmp_path):
    """
    Test that if a failure occurs before file persistence, last_processed_id is NOT updated.
    """
    curated_file = str(tmp_path / "invalid_dir" / "read_only" / "real_user_curated.csv")
    state_file = str(tmp_path / "ingestion_state.json")

    config = DataIngestionConfig()
    config.real_user_curated_file_path = curated_file
    config.ingestion_state_file_path = state_file

    mock_docs = [
        {"_id": "651a2f000000000000000001", "message_id": "msg_001", "subject": "Spam 1", "body": "Click here", "gmail_classification": {"is_spam": True}},
    ]

    with patch("src.components.real_user_ingestion.FetchRealUserMail") as MockFetch:
        mock_fetch_instance = MagicMock()
        MockFetch.return_value = mock_fetch_instance
        mock_fetch_instance.get_last_processed_id.return_value = None
        mock_fetch_instance.fetch_new_user_emails.return_value = mock_docs

        # Mock to_csv to raise Exception (simulating save crash)
        with patch.object(pd.DataFrame, "to_csv", side_effect=IOError("Disk write error")):
            ingestion = RealUserIngestion(config=config)
            with pytest.raises(Exception):
                ingestion.ingest_incremental_real_user_data()

            # Verify checkpoint was NEVER updated due to crash
            mock_fetch_instance.update_last_processed_id.assert_not_called()
