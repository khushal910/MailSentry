"""
Utility functions for configuring and logging MLflow experiments.

This module centralizes all MLflow operations so that ModelTrainer
only focuses on model training.
"""

from __future__ import annotations

import sys
from typing import Any, Dict

import mlflow
import mlflow.sklearn
import mlflow.xgboost
import mlflow.catboost

from src.exception import MyException
from src.logger import logger

import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier


# ============================================================================
# Log Model
# ============================================================================

def log_model_to_mlflow(
    model_name: str,
    model: Any,
    params: Dict[str, Any],
    metrics: Dict[str, float],
) -> None:
    """
    Log one trained model into MLflow.

    Parameters
    ----------
    model_name : str
        Name of the model.

    model : Any
        Trained sklearn compatible model.

    params : Dict
        Hyperparameters.

    metrics : Dict
        Evaluation metrics.
    """

    try:

        with mlflow.start_run(run_name=model_name):

            # ----------------------------------------------------
            # Parameters
            # ----------------------------------------------------

            if params:

                mlflow.log_params(params)

            # ----------------------------------------------------
            # Metrics
            # ----------------------------------------------------

            if metrics:

                mlflow.log_metrics(metrics)

            # ----------------------------------------------------
            # Model
            # ----------------------------------------------------

            if isinstance(model, xgb.XGBClassifier):

                mlflow.xgboost.log_model(
                    xgb_model=model,
                    name="model",
                )

            elif isinstance(model, CatBoostClassifier):

                mlflow.catboost.log_model(
                    cb_model=model,
                    name="model",
                )

            elif isinstance(model, lgb.LGBMClassifier):

                mlflow.lightgbm.log_model(
                    lgb_model=model,
                    name="model",
                )

            else:

                mlflow.sklearn.log_model(
                    sk_model=model,
                    name="model",
                )

            logger.info(f"{model_name} logged to MLflow successfully.")

    except Exception as e:

        logger.exception(e)

        raise MyException(e, sys) from e    