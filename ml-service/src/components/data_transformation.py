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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from src.utils.main_utils import read_csv, read_yaml_file
from src.entity.config_entity import (
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    TrainModelConfig,
)
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import pandas as pd
import re
import string
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
            # TF-IDF Pipeline
            # ----------------------------------------------
            logger.info(
                "Initializing TF-IDF vectorizer with parameters: "
                "max_features=7000, stop_words=english, ngram_range=(1,2), "
                "min_df=2, max_df=0.95, sublinear_tf=True"
            )
            preprocessor = Pipeline(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(
                            max_features=7000,
                            stop_words="english",
                            ngram_range=(1, 2),
                            min_df=2,
                            max_df=0.95,
                            sublinear_tf=True,
                        ),
                    )
                ]
            )

            logger.info("Fitting TF-IDF on training data")
            X_train = preprocessor.fit_transform(X_train)
            logger.info(
                f"TF-IDF fitted. Training matrix shape: {X_train.shape}, "
                f"vocabulary size: {len(preprocessor.named_steps['tfidf'].vocabulary_)}"
            )

            logger.info("Transforming test data with TF-IDF")
            X_test = preprocessor.transform(X_test)
            logger.info(f"Test matrix shape: {X_test.shape}")

            logger.info("Exited apply_preprocessing method")
            return (
                X_train,
                y_train,
                X_test,
                y_test,
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
        self, X_train, y_train, X_test, y_test, preprocessor, label_encoder
    ):
        """
        Store transformed train and test datasets as CSV, and save preprocessor and label encoder as pickle.
        """
        try:
            logger.info("Entered store_transformed_data method")

            # Convert sparse matrices to dense DataFrames
            logger.info("Converting sparse matrices to DataFrames")
            train_df = pd.DataFrame(X_train.toarray())
            train_df["target"] = y_train.values

            test_df = pd.DataFrame(X_test.toarray())
            test_df["target"] = y_test.values

            # Create directories
            os.makedirs(
                os.path.dirname(self.data_transformation_config.transform_train_file),
                exist_ok=True,
            )
            os.makedirs(
                os.path.dirname(self.data_transformation_config.transform_test_file),
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

            # Save CSV files
            logger.info(
                f"Saving transformed train data to {self.data_transformation_config.transform_train_file}"
            )
            train_df.to_csv(
                self.data_transformation_config.transform_train_file, index=False
            )

            logger.info(
                f"Saving transformed test data to {self.data_transformation_config.transform_test_file}"
            )
            test_df.to_csv(
                self.data_transformation_config.transform_test_file, index=False
            )

            # Save preprocessor and label encoder
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

            logger.info("All transformed files stored successfully.")
            logger.info("Exited store_transformed_data method")

        except Exception as e:
            logger.error(f"Exception in store_transformed_data: {e}")
            raise MyException(e, sys)

    def init_transformation_pipeline(self):
        """
        Method Name :   init_transformation_pipeline
        Description :   This method initializes the data transformation pipeline
                        by calling the methods in the correct order.
        Output      :   None (files saved)
        On Failure  :   Write an exception log and then raise an exception
        """
        try:
            logger.info("Entered init_transformation_pipeline method")

            (
                X_train,
                y_train,
                X_test,
                y_test,
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