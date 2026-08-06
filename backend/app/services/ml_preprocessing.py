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

import ipaddress
import logging
import re
import string
from typing import Any, Dict, List
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

logger = logging.getLogger(__name__)

SUSPICIOUS_TLDS = {
    "xyz", "top", "zip", "work", "click", "link", "info", "online",
    "site", "icu", "buzz", "cc", "tk", "ml", "ga", "cf", "gq", "download",
    "racing", "rest", "fit", "surf", "casa", "ren", "monster"
}


class URLFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Scikit-learn compatible transformer that extracts 15 structured numerical URL features
    from text inputs. Returns a 2D numpy array compatible with ColumnTransformer & FeatureUnion.
    """

    def fit(self, X: Any, y: Any = None) -> "URLFeatureExtractor":
        return self

    @staticmethod
    def extract_structured_url_features(text: str) -> Dict[str, Any]:
        """
        Extracts 15 structured numerical features from URLs embedded in email text.
        Returns zeros if no URLs exist or text is empty.
        """
        empty_features: Dict[str, Any] = {
            "url_count": 0,
            "total_url_length": 0,
            "average_url_length": 0.0,
            "max_url_length": 0,
            "uses_https_count": 0,
            "uses_http_count": 0,
            "contains_ip_address": 0,
            "query_count": 0,
            "total_digit_count": 0,
            "total_hyphen_count": 0,
            "average_domain_length": 0.0,
            "average_path_length": 0.0,
            "average_query_length": 0.0,
            "suspicious_tld_count": 0,
            "unique_domain_count": 0,
        }

        if not text or not isinstance(text, str):
            return empty_features

        url_pattern = r"https?://[^\s]+"
        urls = re.findall(url_pattern, text)

        if not urls:
            return empty_features

        url_count = len(urls)
        lengths = [len(u) for u in urls]
        total_url_length = sum(lengths)
        average_url_length = float(total_url_length / url_count)
        max_url_length = max(lengths)

        uses_https_count = 0
        uses_http_count = 0
        contains_ip_address = 0
        query_count = 0
        total_digit_count = 0
        total_hyphen_count = 0
        suspicious_tld_count = 0

        domains: List[str] = []
        domain_lengths: List[int] = []
        path_lengths: List[int] = []
        query_lengths: List[int] = []

        for u in urls:
            try:
                parsed = urlparse(u)
                scheme = (parsed.scheme or "").lower()
                if scheme == "https":
                    uses_https_count += 1
                elif scheme == "http":
                    uses_http_count += 1

                netloc = parsed.netloc.lower()
                hostname = netloc.split(":")[0] if ":" in netloc else netloc
                hostname_clean = hostname.replace("www.", "")

                # Detect IPv4 or IPv6 addresses
                try:
                    ipaddress.ip_address(hostname_clean)
                    contains_ip_address = 1
                except ValueError:
                    pass

                if hostname_clean:
                    domains.append(hostname_clean)
                    domain_lengths.append(len(hostname_clean))

                    # Check TLD
                    parts = hostname_clean.split(".")
                    if len(parts) >= 2:
                        tld = parts[-1]
                        if tld in SUSPICIOUS_TLDS:
                            suspicious_tld_count += 1

                path = parsed.path or ""
                path_lengths.append(len(path))

                query = parsed.query or ""
                if query:
                    query_count += 1
                    query_lengths.append(len(query))

                total_digit_count += sum(c.isdigit() for c in u)
                total_hyphen_count += u.count("-")

            except Exception:
                continue

        avg_domain_len = (
            float(sum(domain_lengths) / len(domain_lengths)) if domain_lengths else 0.0
        )
        avg_path_len = (
            float(sum(path_lengths) / len(path_lengths)) if path_lengths else 0.0
        )
        avg_query_len = (
            float(sum(query_lengths) / len(query_lengths)) if query_lengths else 0.0
        )
        unique_domain_count = len(set(domains))

        return {
            "url_count": url_count,
            "total_url_length": total_url_length,
            "average_url_length": average_url_length,
            "max_url_length": max_url_length,
            "uses_https_count": uses_https_count,
            "uses_http_count": uses_http_count,
            "contains_ip_address": contains_ip_address,
            "query_count": query_count,
            "total_digit_count": total_digit_count,
            "total_hyphen_count": total_hyphen_count,
            "average_domain_length": avg_domain_len,
            "average_path_length": avg_path_len,
            "average_query_length": avg_query_len,
            "suspicious_tld_count": suspicious_tld_count,
            "unique_domain_count": unique_domain_count,
        }

    def transform(self, X: Any) -> np.ndarray:
        if isinstance(X, pd.Series):
            texts = X.tolist()
        elif isinstance(X, pd.DataFrame):
            texts = X.iloc[:, 0].tolist()
        elif isinstance(X, (list, tuple, np.ndarray)):
            texts = [str(x) for x in X]
        else:
            texts = [str(X)]

        feature_dicts = [
            self.extract_structured_url_features(t) for t in texts
        ]
        matrix = np.array(
            [[d[k] for k in d] for d in feature_dicts], dtype=np.float64
        )
        return matrix


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
            cleaned = text.lower()
            cleaned = re.sub(r"<.*?>", "", cleaned)
            cleaned = cleaned.translate(str.maketrans("", "", string.punctuation))
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

    @staticmethod
    def extract_structured_url_features(text: str) -> Dict[str, Any]:
        """
        Exposes structured numerical URL feature extraction via MLPreprocessing.
        """
        return URLFeatureExtractor.extract_structured_url_features(text)

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
