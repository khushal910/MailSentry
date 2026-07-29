from __future__ import annotations
import os
import pickle
from typing import Any, Dict, Optional
import numpy as np
import yaml
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from src.exception import MyException
import yaml
from pathlib import Path

def read_yaml_file(file_path: str | Path) -> dict:
    """
    Reads a YAML file and returns its contents as a dictionary.

    Args:
        file_path (str | Path): Path to the YAML file.

    Returns:
        dict: Parsed YAML content.
    """

    file_path = Path(file_path)

    with open(file_path, "r", encoding="utf-8") as yaml_file:
        content = yaml.safe_load(yaml_file)

    return content


def read_csv(file_path: str | Path):
    """
    Reads a CSV file and returns its contents as a DataFrame.

    Args:
        file_path (str | Path): Path to the CSV file.
        
    Returns:
        DataFrame: Parsed CSV content.
    """
    import pandas as pd

    file_path = Path(file_path)

    dataframe = pd.read_csv(file_path)

    return dataframe


def save_object(file_path: str, obj: Any) -> None:
    """
    Serialize a Python object to disk using pickle.

    Args:
        file_path: Destination file path.
        obj: Serializable Python object.

    Raises:
        MyException: If persistence fails.
    """
    try:
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        with open(file_path, "wb") as file_obj:
            pickle.dump(obj, file_obj)
    except Exception as exc:
        raise MyException(exc, os.sys) from exc


def load_object(file_path: str) -> Any:
    """
    Load a pickled Python object from disk.

    Args:
        file_path: Source file path.

    Returns:
        The deserialized Python object.

    Raises:
        MyException: If loading fails.
    """
    try:
        with open(file_path, "rb") as file_obj:
            return pickle.load(file_obj)
    except Exception as exc:
        raise MyException(exc, os.sys) from exc


def write_yaml_file(file_path: str, content: Dict[str, Any]) -> None:
    """
    Write a dictionary to a YAML file.

    Args:
        file_path: Destination YAML file path.
        content: YAML-serializable dictionary.

    Raises:
        MyException: If file writing fails.
    """
    try:
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as file_obj:
            yaml.safe_dump(content, file_obj, sort_keys=False, default_flow_style=False)
    except Exception as exc:
        raise MyException(exc, os.sys) from exc


def evaluate_classification_model(
    y_true: Any,
    y_pred: Any,
    y_score: Optional[Any] = None,
) -> Dict[str, float]:
    """
    Evaluate a classification model using standard metrics.

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted class labels.
        y_score: Optional probability scores or decision scores for ROC-AUC.

    Returns:
        Dictionary containing accuracy, precision, recall, f1, and roc_auc.

    Raises:
        MyException: If metric computation fails.
    """
    try:
        y_true_arr = np.asarray(y_true)
        y_pred_arr = np.asarray(y_pred)

        metrics: Dict[str, float] = {
            "accuracy": float(accuracy_score(y_true_arr, y_pred_arr)),
            "precision": float(
                precision_score(y_true_arr, y_pred_arr, average="binary", zero_division=0)
            ),
            "recall": float(
                recall_score(y_true_arr, y_pred_arr, average="binary", zero_division=0)
            ),
            "f1": float(f1_score(y_true_arr, y_pred_arr, average="binary", zero_division=0)),
        }

        score_source = y_score if y_score is not None else y_pred_arr
        score_arr = np.asarray(score_source)

        if score_arr.ndim > 1 and score_arr.shape[1] > 1:
            score_arr = score_arr[:, 1]

        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true_arr, score_arr))
        except Exception:
            metrics["roc_auc"] = 0.0

        return metrics
    except Exception as exc:
        raise MyException(exc, os.sys) from exc