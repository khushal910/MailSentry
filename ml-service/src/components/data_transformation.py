"""
Data Transformation Steps:

    1. Drop unwanted columns: ["Message ID", "Date"]
    2. Fill missing values with empty strings for "Subject" and "Message" columns.
    3. Label encode the target column: ["Spam/Ham"]
    4. Clean text in "Subject" and "Message" columns by:
        - Converting to lowercase
        - Removing HTML tags
        - Removing punctuation
        - Removing extra whitespace
    5. Combine "Subject" and "Message" columns into a new column "combined_text".
    6. Extract URL features from "combined_text" column by:
        - Extracting scheme, domain, and query parameters from URLs
        - Appending extracted features to the cleaned text
    7. Remove the original "Subject" and "Message" columns. (The new data has only two columns: "combined_text" and the target column["Spam/Ham"])
    8. Split the data into features (X) and target (y) for both train and test datasets.
    9. Apply TF-IDF vectorization on the "combined_text" column with the following parameters:
    10. Save the transformed train and test datasets as CSV files and the preprocessor and label encoder as pickle files.
"""

import sys
import joblib
from src.logger import logger
from src.exception import MyException
from pandas import DataFrame
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from src.utils.main_utils import read_csv, read_yaml_file
from src.entity.config_entity import (
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    TrainModelConfig,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.base import BaseEstimator, TransformerMixin
import ipaddress
import numpy as np
import os
import pandas as pd
import re
import string

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

    def fit(self, X, y=None):
        return self

    @staticmethod
    def extract_structured_url_features(text: str) -> dict:
        """
        Extracts 15 structured numerical features from URLs embedded in email text.
        Returns zeros if no URLs exist or text is empty.
        """
        empty_features = {
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

        domains = []
        domain_lengths = []
        path_lengths = []
        query_lengths = []

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

    def transform(self, X):
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
from urllib.parse import urlparse


class DataTransformation:

    def __init__(self):
        """
        Initialize the DataTransformation class with configurations and load data.
        """
        try:
            logger.info("Entered __init__ method of DataTransformation class")

            self.data_ingestion_config = DataIngestionConfig()
            self.data_transformation_config = DataTransformationConfig()
            self.train_model_config = TrainModelConfig()
            self.schema_file_path = DataValidationConfig().schema_file_path

            self.train_file_path = self.data_ingestion_config.training_file_path
            self.test_file_path = self.data_ingestion_config.testing_file_path

            self.train_dataframe = read_csv(self.train_file_path)
            self.test_dataframe = read_csv(self.test_file_path)

            self.schema_file_content = read_yaml_file(self.schema_file_path)

            logger.info(
                f"Loaded train data of shape {self.train_dataframe.shape} "
                f"and test data of shape {self.test_dataframe.shape}"
            )
            logger.info("Exited __init__ method of DataTransformation class")

        except Exception as e:
            logger.error(f"Exception in __init__: {e}")
            raise MyException(e, sys)

    def apply_preprocessing(self, train_df: DataFrame, test_df: DataFrame):
        """
        Fit preprocessing on train dataset and transform train/test.
        """
        try:
            logger.info("Entered apply_preprocessing method")

            schema = self.schema_file_content
            target_column = schema["target_column"]

            # ----------------------------------------------
            # Drop unwanted columns
            # ----------------------------------------------
            drop_columns = schema["drop_columns"]
            logger.info(f"Dropping columns: {drop_columns}")
            train_df = train_df.drop(columns=drop_columns)
            test_df = test_df.drop(columns=drop_columns)
            logger.info(
                f"After dropping, train shape: {train_df.shape}, test shape: {test_df.shape}"
            )

            # ----------------------------------------------
            # Fill Missing Values
            # ----------------------------------------------
            fill_missing_columns = schema.get("fill_missing_columns", {})
            fill_missing_values = schema.get("fill_missing_values", {})
            logger.info("Filling missing values in columns: %s", fill_missing_columns)
            for col in fill_missing_columns:
                train_df[col] = train_df[col].fillna(fill_missing_values.get(col, ""))
            for col in fill_missing_columns:
                test_df[col] = test_df[col].fillna(fill_missing_values.get(col, ""))

            # ----------------------------------------------
            # Label Encoding
            # ----------------------------------------------
            logger.info("Label encoding target column: %s", target_column)
            label_encoder = LabelEncoder()
            train_df[target_column] = label_encoder.fit_transform(
                train_df[target_column]
            )
            test_df[target_column] = label_encoder.transform(test_df[target_column])
            logger.info(
                "Target classes: %s", label_encoder.classes_.tolist()
            )  # e.g., ['ham', 'spam']

            # ----------------------------------------------
            # Clean Text
            # ----------------------------------------------
            logger.info("Cleaning text in Subject and Message columns")
            train_df["Subject"] = train_df["Subject"].apply(self.clean_text)
            train_df["Message"] = train_df["Message"].apply(self.clean_text)
            test_df["Subject"] = test_df["Subject"].apply(self.clean_text)
            test_df["Message"] = test_df["Message"].apply(self.clean_text)

            # ----------------------------------------------
            # Combine Text
            # ----------------------------------------------
            logger.info("Combining Subject and Message into combined_text")
            train_df["combined_text"] = (
                train_df["Subject"] + " " + train_df["Message"]
            )
            test_df["combined_text"] = test_df["Subject"] + " " + test_df["Message"]

            # ----------------------------------------------
            # URL Feature Extraction
            # ----------------------------------------------
            logger.info("Extracting URL features from combined_text")
            train_df["combined_text"] = train_df["combined_text"].apply(
                self.extract_url_features
            )
            test_df["combined_text"] = test_df["combined_text"].apply(
                self.extract_url_features
            )

            # ----------------------------------------------
            # Remove old columns
            # ----------------------------------------------
            logger.info("Removing original Subject and Message columns")
            train_df.drop(columns=["Subject", "Message"], inplace=True)
            test_df.drop(columns=["Subject", "Message"], inplace=True)
            logger.info(
                f"After removal, train shape: {train_df.shape}, test shape: {test_df.shape}"
            )

            # ----------------------------------------------
            # Split X & y
            # ----------------------------------------------
            logger.info("Splitting into features and target")
            X_train = train_df["combined_text"]
            y_train = train_df[target_column]
            X_test = test_df["combined_text"]
            y_test = test_df[target_column]

            # ----------------------------------------------
            # Combined Word TF-IDF + Char TF-IDF + Engineered URL Features Pipeline
            # ----------------------------------------------
            logger.info(
                "Initializing Word TF-IDF, Character TF-IDF, and Engineered URL Features FeatureUnion"
            )
            word_vectorizer = TfidfVectorizer(
                analyzer="word",
                max_features=7000,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                sublinear_tf=True,
            )

            char_vectorizer = TfidfVectorizer(
                analyzer="char",
                max_features=5000,
                ngram_range=(2, 5),
                min_df=2,
                sublinear_tf=True,
            )

            url_numerical_pipeline = Pipeline(
                [
                    ("url_extractor", URLFeatureExtractor()),
                    ("scaler", StandardScaler(with_mean=False)),
                ]
            )

            combined_features = FeatureUnion(
                [
                    ("word_tfidf", word_vectorizer),
                    ("char_tfidf", char_vectorizer),
                    ("url_numerical_features", url_numerical_pipeline),
                ]
            )

            preprocessor = Pipeline([("features", combined_features)])

            logger.info("Fitting combined Word + Char TF-IDF + URL Features FeatureUnion on training data")
            X_train = preprocessor.fit_transform(X_train)
            logger.info(
                f"FeatureUnion fitted. Training matrix shape: {X_train.shape} "
                f"(Sparse matrix with {X_train.shape[1]} total features)"
            )

            logger.info("Transforming test data with FeatureUnion")
            X_test = preprocessor.transform(X_test)
            logger.info(f"Test matrix shape: {X_test.shape}")

            logger.info("Exited apply_preprocessing method")
            return (
                X_train,
                y_train,
                X_test,
                y_test,
                train_df["combined_text"],
                test_df["combined_text"],
                preprocessor,
                label_encoder,
            )

        except Exception as e:
            logger.error(f"Exception in apply_preprocessing: {e}")
            raise MyException(e, sys)

    def clean_text(self, text):
        """
        Clean text by lowercasing, removing HTML tags, punctuation, and extra whitespace.
        """
        try:
            text = text.lower()
            text = re.sub(r"<.*?>", "", text)
            text = text.translate(str.maketrans("", "", string.punctuation))
            text = re.sub(r"\s+", " ", text)
            return text.strip()
        except Exception as e:
            logger.error(f"Error in clean_text: {e}")
            raise MyException(e, sys)

    def extract_url_features(self, text):
        """
        Extract URL components (scheme, domain parts, query presence) and append to cleaned text.
        """
        try:
            extracted_tokens = []
            pattern = r"https?://[^\s]+"
            urls = re.findall(pattern, text)

            for url in urls:
                parsed = urlparse(url)
                if parsed.scheme:
                    extracted_tokens.append(parsed.scheme.lower())

                domain_parts = (
                    parsed.netloc.lower().replace("www.", "").split(".")
                )
                if len(domain_parts) >= 2:
                    extracted_tokens.append(domain_parts[-2])
                    extracted_tokens.append(domain_parts[-1])
                elif len(domain_parts) == 1:
                    extracted_tokens.append(domain_parts[0])

                if parsed.query:
                    extracted_tokens.append("query")

            cleaned_text = re.sub(pattern, "", text)
            if extracted_tokens:
                cleaned_text += " " + " ".join(extracted_tokens)

            return " ".join(cleaned_text.split())
        except Exception as e:
            logger.error(f"Error in extract_url_features: {e}")
            raise MyException(e, sys)

    def store_transformed_data(
        self,
        X_train,
        y_train,
        X_test,
        y_test,
        raw_train_text,
        raw_test_text,
        preprocessor,
        label_encoder,
    ):
        """
        Store transformed TF-IDF train/test CSVs, raw text train/test CSVs, preprocessor, and label encoder.
        """
        try:
            logger.info("Entered store_transformed_data method")

            # Convert sparse matrices to dense DataFrames for TF-IDF
            logger.info("Converting sparse matrices to TF-IDF DataFrames")
            train_tfidf_df = pd.DataFrame(X_train.toarray())
            train_tfidf_df["target"] = y_train.values

            test_tfidf_df = pd.DataFrame(X_test.toarray())
            test_tfidf_df["target"] = y_test.values

            # Create Raw Text DataFrames
            logger.info("Creating Raw Text DataFrames (email_text, target)")
            train_raw_df = pd.DataFrame({
                "email_text": raw_train_text.values,
                "target": y_train.values,
            })
            test_raw_df = pd.DataFrame({
                "email_text": raw_test_text.values,
                "target": y_test.values,
            })

            # Create directories
            os.makedirs(
                os.path.dirname(self.data_transformation_config.transform_train_file),
                exist_ok=True,
            )
            os.makedirs(
                os.path.dirname(self.data_transformation_config.preprocessor_file),
                exist_ok=True,
            )
            os.makedirs(
                os.path.dirname(
                    self.data_transformation_config.label_encoder_file_path
                ),
                exist_ok=True,
            )

            # Save Raw Text CSV files to transform_train_file & transform_test_file (Fast I/O)
            logger.info(
                f"Saving text train data to {self.data_transformation_config.transform_train_file}"
            )
            train_raw_df.to_csv(
                self.data_transformation_config.transform_train_file, index=False
            )
            logger.info(
                f"Saving text test data to {self.data_transformation_config.transform_test_file}"
            )
            test_raw_df.to_csv(
                self.data_transformation_config.transform_test_file, index=False
            )

            # Validate and Save Raw Text CSV files for transformer models
            if train_raw_df.empty or train_raw_df.shape[0] == 0:
                raise ValueError(
                    f"train_raw_df is empty before saving to {self.data_transformation_config.transform_train_raw_file}. Shape={train_raw_df.shape}"
                )
            if test_raw_df.empty or test_raw_df.shape[0] == 0:
                raise ValueError(
                    f"test_raw_df is empty before saving to {self.data_transformation_config.transform_test_raw_file}. Shape={test_raw_df.shape}"
                )

            logger.info(
                f"Saving raw text train data (Shape={train_raw_df.shape}) to {self.data_transformation_config.transform_train_raw_file}"
            )
            train_raw_df.to_csv(
                self.data_transformation_config.transform_train_raw_file, index=False
            )

            logger.info(
                f"Saving raw text test data (Shape={test_raw_df.shape}) to {self.data_transformation_config.transform_test_raw_file}"
            )
            test_raw_df.to_csv(
                self.data_transformation_config.transform_test_raw_file, index=False
            )

            # Save preprocessor and label encoder locally to ml-service artifact directory
            logger.info(
                f"Saving preprocessor to {self.data_transformation_config.preprocessor_file}"
            )
            joblib.dump(
                preprocessor, self.data_transformation_config.preprocessor_file
            )

            logger.info(
                f"Saving label encoder to {self.data_transformation_config.label_encoder_file_path}"
            )
            joblib.dump(
                label_encoder,
                self.data_transformation_config.label_encoder_file_path,
            )

            # Copy/Save preprocessor and label encoder into backend/models for standalone backend deployment
            try:
                backend_models_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "models")
                )
                os.makedirs(backend_models_dir, exist_ok=True)
                
                backend_preprocessor_path = os.path.join(backend_models_dir, "preprocessing.pkl")
                backend_label_encoder_path = os.path.join(backend_models_dir, "label_encoder.pkl")

                joblib.dump(preprocessor, backend_preprocessor_path)
                joblib.dump(label_encoder, backend_label_encoder_path)
                logger.info(f"Successfully copied preprocessor and label encoder to backend: {backend_models_dir}")
            except Exception as copy_err:
                logger.warning(f"Could not copy preprocessor/label_encoder to backend: {copy_err}")

            logger.info("All transformed files stored successfully.")
            logger.info("Exited store_transformed_data method")

        except Exception as e:
            logger.error(f"Exception in store_transformed_data: {e}")
            raise MyException(e, sys)

    def init_transformation_pipeline(self):
        """
        Initialize the data transformation pipeline.
        """
        try:
            logger.info("Entered init_transformation_pipeline method")

            (
                X_train,
                y_train,
                X_test,
                y_test,
                raw_train_text,
                raw_test_text,
                preprocessor,
                label_encoder,
            ) = self.apply_preprocessing(
                train_df=self.train_dataframe, test_df=self.test_dataframe
            )

            self.store_transformed_data(
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                raw_train_text=raw_train_text,
                raw_test_text=raw_test_text,
                preprocessor=preprocessor,
                label_encoder=label_encoder,
            )

            logger.info("Exited init_transformation_pipeline method")

        except Exception as e:
            logger.error(f"Exception in init_transformation_pipeline: {e}")
            raise MyException(e, sys)



if __name__ == "__main__":
    try:
        logger.info("Starting data transformation pipeline")
        data_transformation = DataTransformation()
        data_transformation.init_transformation_pipeline()
        logger.info("Data transformation pipeline completed successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise MyException(e, sys)