"""
Transformer trainer component for fine-tuning DistilBERT on raw email text.

Responsibilities:
  1. Load raw text datasets (transformed_train_raw.csv, transformed_test_raw.csv)
  2. Perform robust validation checks (shape, non-emptiness, required columns, valid labels, text length)
  3. Load distilbert-base-uncased tokenizer & sequence classification model
  4. Build robust custom PyTorch Dataset & DataLoader with length assertions and early failure
  5. Fine-tune DistilBERT
  6. Evaluate using standard classification metrics
  7. Return _ModelEvaluation object compatible with existing pipeline
  8. Log parameters, metrics, tokenizer, and model checkpoint to MLflow
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.entity.config_entity import DataTransformationConfig, TrainModelConfig, _ModelEvaluation
from src.exception import MyException
from src.logger import logger
from src.utils.main_utils import evaluate_classification_model
from src.utils.mlflow_utils import log_model_to_mlflow


class DistilBERTModelWrapper:
    """
    Duck-typed scikit-learn compatible wrapper around a fine-tuned DistilBERT model and tokenizer.
    Supports predict(), predict_proba(), and save_pretrained().
    """

    def __init__(self, model: Any, tokenizer: Any, device: str = "cpu") -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.model_type = "transformer"

    def predict_proba(self, X: Any) -> np.ndarray:
        import torch

        self.model.eval()
        self.model.to(self.device)
        texts = [str(x) for x in X]

        if not texts or len(texts) == 0:
            logger.warning("predict_proba received an empty list of inputs.")
            return np.empty((0, 2))

        all_probs = []
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()
                all_probs.append(probs)

        if all_probs:
            return np.vstack(all_probs)
        return np.empty((0, 2))

    def predict(self, X: Any) -> np.ndarray:
        probs = self.predict_proba(X)
        if probs.shape[0] == 0:
            return np.array([])
        return np.argmax(probs, axis=1)

    def save_pretrained(self, save_directory: str) -> None:
        """
        Save HuggingFace transformer model weights and tokenizer configuration.
        """
        os.makedirs(save_directory, exist_ok=True)
        self.model.save_pretrained(save_directory)
        self.tokenizer.save_pretrained(save_directory)


class TransformerTrainer:
    """
    Dedicated trainer for DistilBERT transformer classification model.
    Includes rigorous data validation, assertions, detailed step-by-step logging,
    and early failure mechanisms to guarantee dataset non-emptiness.
    """

    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5,
    ) -> None:
        self.model_name = model_name
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.transform_config = DataTransformationConfig()
        self.train_config = TrainModelConfig()

    def _validate_raw_dataframe(self, df: pd.DataFrame, file_path: str, dataset_name: str) -> pd.DataFrame:
        """
        Validate raw text dataset DataFrame loaded from CSV disk.

        Checks:
          - File path exists
          - DataFrame is non-empty (shape[0] > 0)
          - Required columns ("email_text", "target") exist
          - "email_text" column contains non-empty text strings
          - "target" column contains valid binary labels without NaNs
        """
        logger.info("--- Validating %s raw text dataset ---", dataset_name)
        logger.info("%s file path: %s", dataset_name, file_path)

        if df.empty or df.shape[0] == 0:
            raise ValueError(
                f"[{dataset_name}] Dataframe loaded from '{file_path}' is EMPTY! Shape={df.shape}"
            )

        logger.info("%s dataframe shape: %s", dataset_name, df.shape)
        logger.info("%s dataframe columns: %s", dataset_name, df.columns.tolist())
        logger.info("%s first 3 rows:\n%s", dataset_name, df.head(3))

        required_cols = ["email_text", "target"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(
                f"[{dataset_name}] Missing required columns {missing_cols} in '{file_path}'. Found: {df.columns.tolist()}"
            )

        # Handle NAs and type conversions
        df["email_text"] = df["email_text"].fillna("").astype(str)

        # Check for non-empty text strings
        non_empty_mask = df["email_text"].str.strip().str.len() > 0
        non_empty_count = non_empty_mask.sum()
        logger.info(
            "%s non-empty text count: %d / %d (%.2f%%)",
            dataset_name,
            non_empty_count,
            len(df),
            (non_empty_count / max(1, len(df))) * 100,
        )

        if non_empty_count == 0:
            raise ValueError(
                f"[{dataset_name}] Every row in '{file_path}' contains empty/whitespace email text!"
            )

        # Filter empty text rows if any
        if non_empty_count < len(df):
            logger.warning(
                "[%s] Dropping %d empty text rows from dataset.",
                dataset_name,
                len(df) - non_empty_count,
            )
            df = df[non_empty_mask].copy()

        # Validate target column
        if df["target"].isna().any():
            raise ValueError(f"[{dataset_name}] Target column contains NaN values!")

        unique_labels = df["target"].unique()
        label_counts = df["target"].value_counts().to_dict()

        logger.info("%s total text samples: %d", dataset_name, len(df["email_text"]))
        logger.info("%s total label count: %d", dataset_name, len(df["target"]))
        logger.info("%s unique labels: %s", dataset_name, unique_labels.tolist())
        logger.info("%s label distribution: %s", dataset_name, label_counts)

        if len(unique_labels) < 2 and dataset_name.lower().startswith("train"):
            raise ValueError(
                f"[{dataset_name}] Training set must contain at least 2 unique target classes, but got: {unique_labels}"
            )

        assert df.shape[0] > 0, f"[{dataset_name}] DataFrame shape[0] must be > 0 after validation"
        return df

    def load_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load raw text train and test CSV datasets from disk with complete verification.
        """
        train_path = self.transform_config.transform_train_raw_file
        test_path = self.transform_config.transform_test_raw_file

        if not os.path.exists(train_path):
            raise FileNotFoundError(
                f"Raw text transformed training file not found at '{train_path}'."
            )
        if not os.path.exists(test_path):
            raise FileNotFoundError(
                f"Raw text transformed testing file not found at '{test_path}'."
            )

        logger.info("Loading raw text datasets for DistilBERT fine-tuning.")
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)

        train_df = self._validate_raw_dataframe(train_df, train_path, "Training")
        test_df = self._validate_raw_dataframe(test_df, test_path, "Testing")

        return train_df, test_df

    def train_and_evaluate(self) -> Optional[_ModelEvaluation]:
        """
        Tokenize, fine-tune DistilBERT, evaluate performance, and log to MLflow.

        Returns
        -------
        Optional[_ModelEvaluation]
            Evaluation artifact for DistilBERT if successful, or None if training failed.
        """
        try:
            logger.info("Starting DistilBERT transformer training module.")

            try:
                import torch
                from torch.utils.data import DataLoader, Dataset
                from transformers import (
                    AutoModelForSequenceClassification,
                    AutoTokenizer,
                )
            except ImportError as imp_err:
                logger.error("HuggingFace transformers or PyTorch missing: %s", imp_err)
                raise imp_err

            train_df, test_df = self.load_raw_data()
            x_train = train_df["email_text"].values
            y_train = train_df["target"].values
            x_test = test_df["email_text"].values
            y_test = test_df["target"].values

            # Verify arrays
            logger.info("x_train count: %d, y_train count: %d", len(x_train), len(y_train))
            logger.info("x_test count: %d, y_test count: %d", len(x_test), len(y_test))

            if len(x_train) == 0:
                raise ValueError(
                    f"Training text array is empty (len=0). Shape={train_df.shape}"
                )
            if len(y_train) == 0:
                raise ValueError(
                    f"Training label array is empty (len=0). Shape={train_df.shape}"
                )
            if len(x_train) != len(y_train):
                raise ValueError(
                    f"Mismatch between training text size ({len(x_train)}) and label size ({len(y_train)})"
                )

            if len(x_test) == 0:
                raise ValueError(
                    f"Testing text array is empty (len=0). Shape={test_df.shape}"
                )

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Selected device for DistilBERT training: %s", device)

            logger.info("Loading tokenizer and pretrained model: %s", self.model_name)
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name, num_labels=2
            )
            model.to(device)

            # Define dataset class for PyTorch dataloader with robust checks
            class TextDataset(Dataset):
                def __init__(self, texts, labels):
                    self.texts = list(texts)
                    self.labels = list(labels)
                    if len(self.texts) == 0:
                        raise ValueError(
                            "TextDataset initialized with num_samples=0! Texts array is empty."
                        )
                    if len(self.labels) == 0:
                        raise ValueError(
                            "TextDataset initialized with 0 labels! Labels array is empty."
                        )
                    if len(self.texts) != len(self.labels):
                        raise ValueError(
                            f"TextDataset texts len ({len(self.texts)}) != labels len ({len(self.labels)})"
                        )
                    logger.info("TextDataset initialized with %d items.", len(self.texts))

                def __len__(self):
                    length = len(self.texts)
                    assert length > 0, f"TextDataset.__len__() returned invalid non-positive length={length}"
                    return length

                def __getitem__(self, idx):
                    return self.texts[idx], self.labels[idx]

            train_dataset = TextDataset(x_train, y_train)
            dataset_length = len(train_dataset)
            logger.info("Created PyTorch train_dataset with length: %d", dataset_length)
            assert dataset_length > 0, f"train_dataset length must be > 0, got {dataset_length}"

            train_loader = DataLoader(
                train_dataset, batch_size=self.batch_size, shuffle=True
            )
            dataloader_batch_count = len(train_loader)
            logger.info(
                "Created PyTorch DataLoader: batch_count=%d, batch_size=%d",
                dataloader_batch_count,
                self.batch_size,
            )
            if dataloader_batch_count == 0:
                raise ValueError(
                    f"DataLoader contains 0 batches for dataset of size {dataset_length}."
                )

            optimizer = torch.optim.AdamW(model.parameters(), lr=self.learning_rate)

            logger.info(
                "Fine-tuning DistilBERT for %d epochs with batch size %d and LR %e",
                self.epochs,
                self.batch_size,
                self.learning_rate,
            )

            model.train()
            for epoch in range(1, self.epochs + 1):
                total_loss = 0.0
                step_count = 0
                for batch_texts, batch_labels in train_loader:
                    inputs = tokenizer(
                        list(batch_texts),
                        padding=True,
                        truncation=True,
                        max_length=512,
                        return_tensors="pt",
                    )
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                    labels_tensor = torch.tensor(batch_labels, dtype=torch.long).to(device)

                    optimizer.zero_grad()
                    outputs = model(labels=labels_tensor, **inputs)
                    loss = outputs.loss
                    loss.backward()
                    optimizer.step()
                    total_loss += loss.item()
                    step_count += 1

                avg_loss = total_loss / max(1, step_count)
                logger.info("Epoch %d/%d completed (%d steps) - Average Loss: %.4f", epoch, self.epochs, step_count, avg_loss)

            wrapper = DistilBERTModelWrapper(model=model, tokenizer=tokenizer, device=device)

            logger.info("Evaluating DistilBERT model on test dataset (%d samples).", len(x_test))
            y_pred = wrapper.predict(x_test)
            y_proba = wrapper.predict_proba(x_test)
            y_score = y_proba[:, 1] if y_proba.ndim == 2 and y_proba.shape[1] > 1 else y_proba

            metrics = evaluate_classification_model(
                y_true=y_test,
                y_pred=y_pred,
                y_score=y_score,
            )
            metrics["best_cv_score"] = 0.0  # Transformers use validation epoch loss

            training_params = {
                "model_name": self.model_name,
                "epochs": self.epochs,
                "batch_size": self.batch_size,
                "learning_rate": self.learning_rate,
                "device": device,
            }

            log_model_to_mlflow(
                model_name="DistilBERT",
                model=model,
                params=training_params,
                metrics=metrics,
            )

            logger.info("DistilBERT evaluation completed. Metrics: %s", metrics)

            return _ModelEvaluation(
                name="DistilBERT",
                model=wrapper,
                params=training_params,
                metrics=metrics,
            )

        except Exception as exc:
            logger.error("DistilBERT transformer training failed: %s", str(exc), exc_info=True)
            return None

