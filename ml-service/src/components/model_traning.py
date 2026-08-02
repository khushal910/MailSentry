"""
Model training pipeline for classification models.
Steps: 
  1. loads transformed datasets
  2. trains multiple classifiers (skips any that fail)
  3. evaluates them using standard metrics (skips any that fail)
  4. tracks each successful run with MLflow
  5. selects the best model by the given metric from those that succeeded
  6. compares it against the existing production model
  7. persists the winning production model
  8. writes a YAML training report with detailed model status
"""

from __future__ import annotations
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Tuple
import pandas as pd
from src.components.hyperparameter_tuner import HyperparameterTuner
from src.components.models import ModelList
from src.constants import *
from src.entity.artifact_entity import ModelTrainerArtifact
from src.entity.config_entity import TrainModelConfig, DataTransformationConfig
from src.exception import MyException 
from src.logger import logger
from src.utils.main_utils import (
    evaluate_classification_model,
    load_object,
    save_object,
    write_yaml_file,
)
from src.utils.mlflow_utils import log_model_to_mlflow
from src.configuration.mlflow_connection import setup_mlflow
from src.entity.config_entity import _ModelBundle, _ModelEvaluation


class ModelTrainer:
    """
    Train, evaluate, compare, and persist classification models.
    Now with error‑tolerance per model and a full status report.
    """

    def __init__(self) -> None:
        """
        Initialize the model trainer.
        """
        try:
            self.transform_config = DataTransformationConfig()
            self.train_model_config = TrainModelConfig()
                        
            self.transformed_train_file_path = self.transform_config.transform_train_file
            self.transformed_test_file_path = self.transform_config.transform_test_file
            self.target_column_name = TARGET_COLUMN
            self.get_model_list = ModelList().get_models()
            self.model_evaluate_metric = self.train_model_config.model_evaluate_metric
        
        except Exception as exc:
            raise MyException(exc, sys) 

    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load transformed train and test datasets from disk.
        """
        try:
            logger.info("Loading transformed training and testing datasets.")
            train_df = pd.read_csv(self.transformed_train_file_path)
            test_df = pd.read_csv(self.transformed_test_file_path)

            if train_df.empty:
                logger.error("Transformed training dataset is empty.")
                raise ValueError("Transformed training dataset is empty.")
            if test_df.empty:
                logger.error("Transformed testing dataset is empty.")
                raise ValueError("Transformed testing dataset is empty.")

            logger.info(
                "Loaded train data shape: %s, test data shape: %s",
                train_df.shape,
                test_df.shape,
            )
            return train_df, test_df
        except Exception as exc:
            raise MyException(exc, sys) 

    def _split_features_target(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Split a dataframe into features and target.
        """
        try:
            target_column = self.target_column_name
            if target_column not in data.columns:
                raise ValueError(f"Target column '{target_column}' not found in dataset.")

            x = data.drop(columns=[target_column])
            y = data[target_column]
            return x, y
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def train_models(
        self,
        models: Dict[str, _ModelBundle],
        x_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> Tuple[Dict[str, _ModelBundle], Dict[str, str]]:
        """
        Tune every candidate model using RandomizedSearchCV. If a model fails, its error is captured.
        Returns:
            - Dictionary of successfully trained & tuned model bundles.
            - Dictionary mapping failed model names to error messages.
        """
        trained_models: Dict[str, _ModelBundle] = {}
        training_errors: Dict[str, str] = {}

        tuner = HyperparameterTuner(
            n_iter=20,
            cv=5,
            scoring=self.model_evaluate_metric,
            random_state=42,
            n_jobs=-1,
        )

        for model_name, bundle in models.items():
            logger.info("Processing model: %s", model_name)
            try:
                is_tabpfn = (
                    model_name.lower().startswith("tabpfn")
                    or type(bundle.model).__name__ == "TabPFNClassifier"
                )

                if is_tabpfn:
                    logger.info("Fitting TabPFN directly without RandomizedSearchCV: %s", model_name)
                    bundle.model.fit(x_train.to_numpy(), y_train.to_numpy())
                    model_params = (
                        getattr(bundle.model, "get_params", lambda: {})() or bundle.params
                    )
                    trained_bundle = _ModelBundle(
                        name=bundle.name,
                        model=bundle.model,
                        params=model_params,
                        best_cv_score=0.0,
                    )
                else:
                    best_estimator, best_params, best_cv_score = tuner.tune(
                        model_name=model_name,
                        estimator=bundle.model,
                        x_train=x_train,
                        y_train=y_train,
                    )
                    trained_bundle = _ModelBundle(
                        name=bundle.name,
                        model=best_estimator,
                        params=best_params,
                        best_cv_score=best_cv_score,
                    )
                trained_models[model_name] = trained_bundle
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Model {model_name} training failed: {error_msg}")
                training_errors[model_name] = error_msg

        return trained_models, training_errors



    def _get_model_scores(self, model: Any, x_test: pd.DataFrame) -> Any:
        """
        Compute score outputs required for ROC-AUC.
        """
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(x_test)
            if hasattr(probabilities, "ndim") and probabilities.ndim == 2 and probabilities.shape[1] > 1:
                return probabilities[:, 1]
            return probabilities

        if hasattr(model, "decision_function"):
            return model.decision_function(x_test)

        return model.predict(x_test)

    def evaluate_models(
        self,
        trained_models: Dict[str, _ModelBundle],
        x_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> Tuple[Dict[str, _ModelEvaluation], Dict[str, str]]:
        """
        Evaluate every successfully trained model. If evaluation fails, capture error.
        Returns:
            - Dictionary of successfully evaluated model results.
            - Dictionary mapping failed model names to error messages.
        """
        logger.info("Evaluating trained models.")
        evaluated_models: Dict[str, _ModelEvaluation] = {}
        evaluation_errors: Dict[str, str] = {}

        for model_name, bundle in trained_models.items():
            logger.info("Evaluating model: %s", model_name)
            try:
                y_pred = bundle.model.predict(x_test.to_numpy())
                y_score = self._get_model_scores(bundle.model, x_test.to_numpy())

                metrics = evaluate_classification_model(
                    y_true=y_test,
                    y_pred=y_pred,
                    y_score=y_score,
                )
                metrics["best_cv_score"] = getattr(bundle, "best_cv_score", 0.0)

                log_model_to_mlflow(
                    model_name=model_name,
                    model=bundle.model,
                    params=bundle.params,
                    metrics=metrics,
                )

                evaluated_models[model_name] = _ModelEvaluation(
                    name=model_name,
                    model=bundle.model,
                    params=bundle.params,
                    metrics=metrics,
                )
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Model {model_name} evaluation failed: {error_msg}")
                evaluation_errors[model_name] = error_msg

        return evaluated_models, evaluation_errors

    def select_best_model(
        self,
        evaluated_models: Dict[str, _ModelEvaluation],
    ) -> _ModelEvaluation:
        """
        Select the best model among those that were successfully evaluated.
        Raises an exception if no model succeeded.
        """
        if not evaluated_models:
            raise ValueError("No models were successfully evaluated. Cannot select a best model.")

        best_model_name = max(
            evaluated_models,
            key=lambda name: evaluated_models[name].metrics[self.model_evaluate_metric],
        )
        best_model = evaluated_models[best_model_name]
        logger.info(
            "Best trained model: %s with %s: %.6f",
            best_model.name,
            self.model_evaluate_metric,
            best_model.metrics[self.model_evaluate_metric],
        )
        return best_model

    def compare_with_production_model(
        self,
        candidate_model: _ModelEvaluation,
        x_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> Tuple[_ModelEvaluation, bool]:
        """
        Compare the best new model with the existing production model.
        """
        try:
            production_model_path = self.train_model_config.trained_model_file_path  

            if not os.path.exists(production_model_path):
                logger.info("No production model found. New model will be saved.")
                return candidate_model, True

            logger.info("Loading existing production model from: %s", production_model_path)
            production_model = load_object(production_model_path)
            production_pred = production_model.predict(
                x_test.to_numpy()
            )
            production_score = self._get_model_scores(
                production_model,
                x_test.to_numpy()
            )

            production_metrics = evaluate_classification_model(
                y_true=y_test,
                y_pred=production_pred,
                y_score=production_score,
            )

            # Compare using the configured best metric
            candidate_score = candidate_model.metrics[self.model_evaluate_metric]
            production_score_val = production_metrics[self.model_evaluate_metric]

            logger.info(
                "Production model %s: %.6f | Candidate model %s: %.6f",
                self.model_evaluate_metric,
                production_score_val,
                self.model_evaluate_metric,
                candidate_score,
            )

            if candidate_score > production_score_val:
                logger.info("Candidate model outperforms production model.")
                return candidate_model, True

            logger.info("Production model retained.")
            return _ModelEvaluation(
                name="production_model",
                model=production_model,
                params={},
                metrics=production_metrics,
            ), False
        except Exception as exc:
            logger.warning(
                "Production model comparison failed. Falling back to new candidate model. Reason: %s",
                exc,
            )
            return candidate_model, True

    def save_best_model(self, winner: _ModelEvaluation, should_save: bool) -> None:
        """
        Save the best model to the configured production model path,
        registering version in DB, running test mode verification, and cleaning up old versions.
        """
        try:
            if should_save:
                logger.info("Saving best model to: %s", self.train_model_config.trained_model_file_path)
                save_object(self.train_model_config.trained_model_file_path, winner.model)
                save_object(self.train_model_config.trained_model_backend_path, winner.model)

                # Attempt to register via MLModelService
                try:
                    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
                    if backend_path not in sys.path:
                        sys.path.insert(0, backend_path)
                    from app.services.ml_model_service import MLModelService
                    service = MLModelService()
                    service.save_and_register_model(
                        model_obj=winner.model,
                        model_name=winner.name or "spam_classifier",
                        metrics=winner.metrics
                    )
                    logger.info("Successfully registered model via MLModelService.")
                except Exception as ml_err:
                    logger.warning(f"Could not register model via MLModelService: {ml_err}")
            else:
                logger.info("Keeping existing production model unchanged.")
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def initiate_model_training(self) -> ModelTrainerArtifact:
        """
        Execute the full training pipeline with error‑tolerance and detailed reporting.
        """
        try:
            logger.info("Starting model training pipeline.")
            setup_mlflow()

            train_df, test_df = self.load_data()
            x_train, y_train = self._split_features_target(train_df)
            x_test, y_test = self._split_features_target(test_df)

            models = self.get_model_list

            # 1. Train models (capture failures)
            trained_models, training_errors = self.train_models(
                models=models, x_train=x_train, y_train=y_train
            )

            # 2. Evaluate models (capture failures)
            evaluated_models, evaluation_errors = self.evaluate_models(
                trained_models=trained_models,
                x_test=x_test,
                y_test=y_test,
            )

            # 3. Select best from successful ones
            best_candidate = self.select_best_model(evaluated_models)

            # 4. Compare with production & save
            winner, is_new_model_winner = self.compare_with_production_model(
                candidate_model=best_candidate,
                x_test=x_test,
                y_test=y_test,
            )

            self.save_best_model(winner=winner, should_save=is_new_model_winner)

            # 5. Build comprehensive status report
            training_timestamp = datetime.now(timezone.utc).isoformat()

            # Collect status for ALL models (including those that failed)
            all_model_names = set(self.get_model_list.keys())
            model_status = {}
            for name in all_model_names:
                if name in evaluated_models:
                    model_status[name] = {"status": "success"}
                elif name in training_errors:
                    model_status[name] = {"status": "failed", "reason": training_errors[name]}
                elif name in evaluation_errors:
                    model_status[name] = {"status": "failed", "reason": evaluation_errors[name]}
                else:
                    # Should not happen, but keep as safeguard
                    model_status[name] = {"status": "unknown"}

            report = {
                "best_model_name": winner.name,
                "best_model_metric": self.model_evaluate_metric,
                "winner_metrics": winner.metrics,
                "model_status": model_status,                      # NEW: detailed status
                "metrics_of_successful_models": {
                    name: result.metrics for name, result in evaluated_models.items()
                },
                "training_timestamp": training_timestamp,
            }
            write_yaml_file(self.train_model_config.model_report_file_path, report)

            logger.info("Model training pipeline completed successfully.")
            logger.info(f"Report saved at {self.train_model_config.model_report_file_path}")

            return ModelTrainerArtifact(
                trained_model_file_path=self.train_model_config.trained_model_file_path,
                best_model_name=winner.name,
                best_model_score=winner.metrics[self.model_evaluate_metric],
            )
        except Exception as exc:
            raise MyException(exc, sys) from exc


if __name__ == "__main__":
    model_trainer = ModelTrainer()
    model_trainer.initiate_model_training()