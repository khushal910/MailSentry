import sys
import os
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Tuple
from pandas import DataFrame

from src.logger import logger
from src.exception import MyException
from src.entity.config_entity import DataIngestionConfig
from src.data_access.fetch_data import FetchRealUserMail


class RealUserIngestion:
    """
    Component for incremental ingestion, normalization, validation,
    and persistent curation of real user email data from MongoDB 2 using _id checkpointing.
    """

    def __init__(self, config: Optional[DataIngestionConfig] = None):
        try:
            self.config = config or DataIngestionConfig()
        except Exception as e:
            raise MyException(e, sys)

    @staticmethod
    def resolve_gmail_label(doc: dict) -> Optional[str]:
        """
        Resolves Gmail classification into 'spam' or 'ham'.
        Returns None if classification is ambiguous or missing.
        """
        gmail_cls = doc.get("gmail_classification")
        label_ids = doc.get("label_ids")

        # Priority 1: Explicit boolean flag
        if isinstance(gmail_cls, dict) and "is_spam" in gmail_cls and gmail_cls["is_spam"] is not None:
            return "spam" if bool(gmail_cls["is_spam"]) else "ham"

        # Priority 2: Explicit status string
        if isinstance(gmail_cls, dict) and "status" in gmail_cls and gmail_cls["status"]:
            status = str(gmail_cls["status"]).strip().lower()
            if status in ("spam", "phishing", "fraud"):
                return "spam"
            if status in ("not_spam", "ham", "inbox", "legitimate"):
                return "ham"

        # Priority 3: Label IDs list
        labels = label_ids or (gmail_cls.get("label_ids") if isinstance(gmail_cls, dict) else [])
        if labels and isinstance(labels, list):
            upper_labels = [str(l).upper() for l in labels]
            if "SPAM" in upper_labels or "TRASH" in upper_labels:
                return "spam"
            if "INBOX" in upper_labels or "IMPORTANT" in upper_labels:
                return "ham"

        return None

    @staticmethod
    def extract_text_and_subject(doc: dict) -> Tuple[str, str]:
        """
        Extracts subject and message text from real user document.
        Prefers body over snippet.
        """
        subject = str(doc.get("subject") or "").strip()
        body = doc.get("body")
        snippet = doc.get("snippet")

        message = ""
        if body and isinstance(body, str) and body.strip():
            message = body.strip()
        elif snippet and isinstance(snippet, str) and snippet.strip():
            message = snippet.strip()

        return subject, message

    def ingest_incremental_real_user_data(self) -> DataFrame:
        """
        Performs incremental fetch of new records (_id > last_processed_id) from MongoDB 2,
        normalizes fields, validates records, appends NEW records to real_user_curated.csv,
        and updates the checkpoint state ONLY AFTER successful file persistence.

        Returns full accumulated real-user DataFrame matching 5-column schema:
        ["Message ID", "Subject", "Message", "Spam/Ham", "Date"]
        """
        try:
            logger.info("Starting incremental real-user email data ingestion from MongoDB 2 via _id checkpointing.")

            curated_path = self.config.real_user_curated_file_path
            state_file_path = self.config.ingestion_state_file_path
            schema_cols = ["Message ID", "Subject", "Message", "Spam/Ham", "Date"]

            # Load existing curated real-user dataset if present
            existing_curated_df = DataFrame(columns=schema_cols)

            if os.path.exists(curated_path):
                try:
                    existing_curated_df = pd.read_csv(curated_path)
                    existing_curated_df = existing_curated_df[[c for c in schema_cols if c in existing_curated_df.columns]].copy()
                    logger.info(f"Loaded existing accumulated real-user dataset from {curated_path} with {len(existing_curated_df)} records.")
                except Exception as load_err:
                    logger.warning(f"Could not load existing accumulated dataset file ({load_err}). Starting fresh.")
                    existing_curated_df = DataFrame(columns=schema_cols)

            # Initialize MongoDB 2 client
            fetch_mail = FetchRealUserMail(
                database_name=self.config.real_user_db_name,
                collection_name=self.config.real_user_collection_name,
            )

            last_processed_id = fetch_mail.get_last_processed_id(state_file_path=state_file_path)
            logger.info(f"Last processed MongoDB _id checkpoint before fetch: {last_processed_id}")

            # Fetch ONLY newer documents (_id > last_processed_id) from MongoDB 2
            raw_docs = fetch_mail.fetch_new_user_emails(last_processed_id=last_processed_id)

            if not raw_docs:
                logger.info("No new real-user email documents found in MongoDB 2 (_id > checkpoint).")
                return existing_curated_df

            fetched_count = len(raw_docs)
            valid_new_records = []
            ambiguous_count = 0
            empty_count = 0
            highest_processed_id = last_processed_id

            for doc in raw_docs:
                mongo_id = str(doc.get("_id"))
                msg_id = str(doc.get("message_id") or doc.get("gmail_message_id") or mongo_id).strip()

                if mongo_id:
                    highest_processed_id = mongo_id

                subject, message = self.extract_text_and_subject(doc)

                # Skip only if BOTH subject and message are empty
                if not subject and not message:
                    empty_count += 1
                    continue

                # Skip if label is ambiguous or missing
                label = self.resolve_gmail_label(doc)
                if not label:
                    ambiguous_count += 1
                    continue

                date_val = str(doc.get("sent_at") or doc.get("received_at") or pd.Timestamp.now().isoformat())

                record = {
                    "Message ID": msg_id,  # Store the actual Gmail message ID string directly
                    "Subject": subject,
                    "Message": message,
                    "Spam/Ham": label,
                    "Date": date_val,
                }
                valid_new_records.append(record)

            new_appended_count = len(valid_new_records)
            logger.info(
                f"Ingestion Statistics: Fetched={fetched_count} | Valid New={new_appended_count} | "
                f"Ambiguous Skipped={ambiguous_count} | Empty Skipped={empty_count}"
            )

            if new_appended_count > 0:
                new_df = DataFrame(valid_new_records)[schema_cols]
                if not existing_curated_df.empty:
                    combined_curated = pd.concat([existing_curated_df, new_df], ignore_index=True)
                else:
                    combined_curated = new_df

                # Ensure directory exists and write accumulated dataset to disk (5 schema columns only)
                os.makedirs(os.path.dirname(curated_path), exist_ok=True)
                combined_curated[schema_cols].to_csv(curated_path, index=False, header=True)
                logger.info(f"Successfully appended {new_appended_count} new records and saved accumulated dataset ({len(combined_curated)} total records) to {curated_path}")

                # FAIL-SAFE CHECKPOINT UPDATE: Update state ONLY AFTER successful file persistence
                if highest_processed_id:
                    fetch_mail.update_last_processed_id(highest_processed_id, state_file_path=state_file_path)
                    logger.info(f"Fail-safe checkpoint successfully updated to: {highest_processed_id}")

                existing_curated_df = combined_curated[schema_cols]

            elif highest_processed_id and highest_processed_id != last_processed_id:
                # Even if no valid records were added (all empty/ambiguous), update checkpoint to avoid re-scanning
                fetch_mail.update_last_processed_id(highest_processed_id, state_file_path=state_file_path)

            return existing_curated_df[schema_cols]

        except Exception as e:
            logger.error(f"Error in ingest_incremental_real_user_data: {e}")
            raise MyException(e, sys)
