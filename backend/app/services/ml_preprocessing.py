"""
MLPreprocessing — Standalone Backend Text Preprocessing Pipeline
================================================────────────────
Replicates the text cleaning and feature engineering steps from ml-service
so the backend can execute predictions standalone without relying on ml-service code at runtime.

Preprocessing Steps (matching ml-service/src/components/data_transformation.py):
  1. Combine Subject and Body/Snippet.
  2. Clean text: convert to lowercase, strip HTML tags, remove punctuation, collapse whitespace.
  3. Extract URL features: parse schemes, domain names, and query indicators and append tokens.
"""

import logging
import re
import string
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class MLPreprocessing:
    """
    Standalone text preprocessing pipeline for MailSentry backend.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Cleans text: converts to lowercase, removes HTML tags, removes punctuation,
        and normalizes extra whitespace.
        """
        if not text:
            return ""
        try:
            # 1. Lowercase
            cleaned = text.lower()
            # 2. Strip HTML tags
            cleaned = re.sub(r"<.*?>", "", cleaned)
            # 3. Remove punctuation
            cleaned = cleaned.translate(str.maketrans("", "", string.punctuation))
            # 4. Collapse extra whitespace
            cleaned = re.sub(r"\s+", " ", cleaned)
            return cleaned.strip()
        except Exception as err:
            logger.warning(f"MLPreprocessing: Error in clean_text: {err}")
            return text or ""

    @staticmethod
    def extract_url_features(text: str) -> str:
        """
        Extracts URL tokens (schemes, domain parts, query indicators) and appends
        them to the text for feature extraction matching ml-service pipeline.
        """
        if not text:
            return ""
        try:
            extracted_tokens: list[str] = []
            url_pattern = r"https?://[^\s]+"
            urls = re.findall(url_pattern, text)

            for url in urls:
                parsed = urlparse(url)
                if parsed.scheme:
                    extracted_tokens.append(parsed.scheme.lower())

                domain_parts = parsed.netloc.lower().replace("www.", "").split(".")
                if len(domain_parts) >= 2:
                    extracted_tokens.append(domain_parts[-2])

                if parsed.query:
                    extracted_tokens.append("has_query")

            if extracted_tokens:
                return text + " " + " ".join(extracted_tokens)
            return text
        except Exception as err:
            logger.warning(f"MLPreprocessing: Error extracting URL features: {err}")
            return text or ""

    @classmethod
    def preprocess_email_text(cls, subject: str, body: str) -> str:
        """
        Full email preprocessing pipeline:
        Combines subject + body, extracts URL features, and applies text cleaning.
        """
        subject_str = (subject or "").strip()
        body_str = (body or "").strip()
        combined_text = f"{subject_str} {body_str}".strip()

        # Step 1: Extract URL tokens prior to stripping punctuation
        with_url_features = cls.extract_url_features(combined_text)

        # Step 2: Apply standard text cleaning
        cleaned_text = cls.clean_text(with_url_features)

        return cleaned_text
