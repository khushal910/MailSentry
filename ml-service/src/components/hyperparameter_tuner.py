"""
Hyperparameter tuner component using RandomizedSearchCV.

Responsibilities:
  - Accept model name, sklearn estimator, X_train, y_train
  - Run RandomizedSearchCV using centralized parameter search spaces
  - Return best_estimator, best_params, best_cv_score
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV

from src.config.hyperparameter_config import PARAM_SEARCH_SPACES
from src.exception import MyException
from src.logger import logger


class HyperparameterTuner:
    """
    Executes RandomizedSearchCV hyperparameter optimization for candidate models.
    """

    def __init__(
        self,
        n_iter: int = 20,
        cv: int = 5,
        scoring: str = "f1",
        random_state: int = 42,
        n_jobs: int = 1,

    ) -> None:
        """
        Initialize HyperparameterTuner settings.
        """
        self.n_iter = n_iter
        self.cv = cv
        self.scoring = scoring
        self.random_state = random_state
        self.n_jobs = n_jobs

    def tune(
        self,
        model_name: str,
        estimator: Any,
        x_train: pd.DataFrame | np.ndarray,
        y_train: pd.Series | np.ndarray,
    ) -> Tuple[Any, Dict[str, Any], float]:
        """
        Run RandomizedSearchCV on the estimator using the model's search space.

        Parameters
        ----------
        model_name : str
            Name identifier for candidate model.
        estimator : Any
            Sklearn-compatible estimator instance.
        x_train : pd.DataFrame | np.ndarray
            Training feature matrix.
        y_train : pd.Series | np.ndarray
            Training target vector.

        Returns
        -------
        Tuple[Any, Dict[str, Any], float]
            best_estimator, best_params, best_cv_score
        """
        try:
            logger.info("Initiating hyperparameter search for: %s", model_name)

            param_dist = PARAM_SEARCH_SPACES.get(model_name, {})

            if not param_dist:
                logger.warning(
                    "No search space defined for '%s'. Fitting estimator with default parameters.",
                    model_name,
                )
                x_data = x_train.to_numpy() if isinstance(x_train, pd.DataFrame) else x_train
                y_data = y_train.to_numpy() if isinstance(y_train, pd.Series) else y_train
                estimator.fit(x_data, y_data)
                default_params = getattr(estimator, "get_params", lambda: {})()
                return estimator, default_params, 0.0

            # Calculate actual n_iter to avoid exceeding total discrete combinations
            total_combinations = 1
            for param_vals in param_dist.values():
                if isinstance(param_vals, (list, tuple)):
                    total_combinations *= len(param_vals)
                else:
                    total_combinations = 0
                    break

            n_iter_to_use = (
                min(self.n_iter, total_combinations)
                if total_combinations > 0
                else self.n_iter
            )

            random_search = RandomizedSearchCV(
                estimator=estimator,
                param_distributions=param_dist,
                n_iter=n_iter_to_use,
                cv=self.cv,
                scoring=self.scoring,
                random_state=self.random_state,
                n_jobs=self.n_jobs,
                error_score="raise",
            )

            x_data = x_train.to_numpy() if isinstance(x_train, pd.DataFrame) else x_train
            y_data = y_train.to_numpy() if isinstance(y_train, pd.Series) else y_train

            random_search.fit(x_data, y_data)

            best_estimator = random_search.best_estimator_
            best_params = random_search.best_params_
            best_cv_score = float(random_search.best_score_)

            logger.info(
                "Completed hyperparameter search for %s. Best CV (%s) Score: %.6f",
                model_name,
                self.scoring,
                best_cv_score,
            )

            return best_estimator, best_params, best_cv_score

        except Exception as exc:
            logger.error("Hyperparameter search failed for model %s: %s", model_name, str(exc))
            raise MyException(exc, sys) from exc
