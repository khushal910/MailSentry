"""
Transformer trainer component for fine-tuning DistilBERT on raw email text.

Responsibilities:
  1. Load raw text datasets (train_raw.csv, test_raw.csv)
  2. Load distilbert-base-uncased tokenizer & sequence classification model
  3. Tokenize emails (combining subject and body)
  4. Fine-tune DistilBERT on CPU
  5. Evaluate using standard classification metrics
  6. Return _ModelEvaluation object compatible with existing pipeline
  7. Log parameters, metrics, tokenizer, and model checkpoint to MLflow
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

    def load_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load raw text train and test CSV datasets from disk.
        """
        train_path = self.transform_config.transform_train_raw_file
        test_path = self.transform_config.transform_test_raw_file

        if not os.path.exists(train_path) or not os.path.exists(test_path):
            raise FileNotFoundError(
                f"Raw text transformed files not found at '{train_path}' or '{test_path}'."
            )

        logger.info("Loading raw text datasets for DistilBERT fine-tuning.")
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)

        train_df["email_text"] = train_df["email_text"].fillna("").astype(str)
        test_df["email_text"] = test_df["email_text"].fillna("").astype(str)

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

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Selected device for DistilBERT training: %s", device)

            logger.info("Loading tokenizer and pretrained model: %s", self.model_name)
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name, num_labels=2
            )
            model.to(device)

            # Define dataset class for PyTorch dataloader
            class TextDataset(Dataset):
                def __init__(self, texts, labels):
                    self.texts = list(texts)
                    self.labels = list(labels)

                def __len__(self):
                    return len(self.texts)

                def __getitem__(self, idx):
                    return self.texts[idx], self.labels[idx]

            train_dataset = TextDataset(x_train, y_train)
            train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)

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

                avg_loss = total_loss / max(1, len(train_loader))
                logger.info("Epoch %d/%d - Average Loss: %.4f", epoch, self.epochs, avg_loss)

            wrapper = DistilBERTModelWrapper(model=model, tokenizer=tokenizer, device=device)

            logger.info("Evaluating DistilBERT model on test dataset.")
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
            logger.error("DistilBERT transformer training failed: %s", str(exc))
            return None
