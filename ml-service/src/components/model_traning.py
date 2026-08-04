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
import shutil
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
from datetime import datetime, timezone
from typing import Any, Dict, Tuple
import pandas as pd
from src.components.hyperparameter_tuner import HyperparameterTuner
from src.components.models import ModelList
from src.constants import *
from src.entity.artifact_entity import ModelTrainerArtifact
from src.entity.config_entity import TrainModelConfig, DataTransformationConfig
from src.entity.model_metadata import ModelMetadata
from src.services.model_registry import ModelRegistry
from src.services.model_saver import ModelSaverFactory, ModelLoaderFactory
from src.components.benchmark import Benchmark
from src.components.checkpoint_manager import CheckpointManager
from src.components.training_state_manager import TrainingStateManager
from src.config.hyperparameter_config import PARAM_SEARCH_SPACES
from src.exception import MyException 
from src.logger import logger
from src.services.storage_service import LocalStorageService
from src.utils.main_utils import (
    evaluate_classification_model,
    read_yaml_file,
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
            n_jobs=1,
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
        Compare the best new model with the existing production champion in ModelRegistry.
        """
        try:
            registry = ModelRegistry(self.train_model_config.model_registry_dir)

            if not registry.has_champion():
                logger.info("No production champion found in ModelRegistry. New model will be saved.")
                return candidate_model, True

            logger.info("Loading existing champion model from ModelRegistry: %s", registry.champion_path)
            meta = registry.load_champion_metadata()
            loader = ModelLoaderFactory.create(meta)
            production_model = loader.load(registry.champion_path, meta)

            production_pred = production_model.predict(x_test.to_numpy())
            production_score = self._get_model_scores(production_model, x_test.to_numpy())

            production_metrics = evaluate_classification_model(
                y_true=y_test,
                y_pred=production_pred,
                y_score=production_score,
            )

            candidate_score = candidate_model.metrics[self.model_evaluate_metric]
            production_score_val = production_metrics[self.model_evaluate_metric]

            logger.info("==================================================================")
            logger.info("  PRODUCTION MODEL EVALUATION & COMPARISON LOG")
            logger.info("  Best Newly Trained Model in Current Run: %s (%s: %.6f)", candidate_model.name, self.model_evaluate_metric, candidate_score)
            logger.info("  Active Production Champion Model:       %s (%s: %.6f)", meta.model_name, self.model_evaluate_metric, production_score_val)

            if candidate_score > production_score_val:
                logger.info("  RESULT: Candidate '%s' OUTPERFORMS current production '%s' (%.6f > %.6f)!", candidate_model.name, meta.model_name, candidate_score, production_score_val)
                logger.info("  ACTION: Promoting '%s' as the NEW Production Model!", candidate_model.name)
                logger.info("==================================================================")
                return candidate_model, True

            logger.info("  RESULT: Existing production model '%s' (%.6f) is STILL BETTER than candidate '%s' (%.6f).", meta.model_name, production_score_val, candidate_model.name, candidate_score)
            logger.info("  ACTION: Production model '%s' retained. Newly trained '%s' will NOT replace production.", meta.model_name, candidate_model.name)
            logger.info("==================================================================")
            return _ModelEvaluation(
                name=meta.model_name,
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

    def save_best_model(
        self,
        winner: _ModelEvaluation,
        should_save: bool,
        x_test: pd.DataFrame
    ) -> None:
        """
        Save the best model using ModelSaverFactory, Benchmark, and ModelRegistry.
        Eliminates all framework-specific conditionals.
        """
        try:
            # Always save the finalized winning model object to artifact/model_trainer/model.pkl
            os.makedirs(os.path.dirname(self.train_model_config.trained_model_file_path), exist_ok=True)
            import joblib
            joblib.dump(winner.model, self.train_model_config.trained_model_file_path)
            logger.info("Saved finalized champion model '%s' to pipeline artifact: %s", winner.name, self.train_model_config.trained_model_file_path)

            if should_save:
                logger.info("Promoting & saving new best model '%s' to ModelRegistry & Backend Storage.", winner.name)

                is_transformer = (
                    winner.name.lower().startswith("distilbert")
                    or hasattr(winner.model, "save_pretrained")
                )

                framework = "transformers" if is_transformer else "sklearn"
                serialization = "huggingface" if is_transformer else "joblib"
                input_type = "raw_text" if is_transformer else "tfidf"
                preprocessor_name = "distilbert-tokenizer" if is_transformer else "tfidf"

                # 1. Run Benchmark Stage
                benchmark_results = Benchmark().run(
                    model=winner.model,
                    x_test=x_test.to_numpy(),
                    serialization=serialization
                )

                # 2. Build Rich Metadata
                metadata = ModelMetadata(
                    model_name=winner.name,
                    framework=framework,
                    serialization=serialization,
                    task="binary_classification",
                    input_type=input_type,
                    output_type="probability",
                    preprocessor=preprocessor_name,
                    metric=self.model_evaluate_metric,
                    score=float(winner.metrics.get(self.model_evaluate_metric, 0.0)),
                    metrics=winner.metrics,
                    trained_at=datetime.now(timezone.utc).isoformat(),
                    training_time_sec=benchmark_results["training_time_sec"],
                    inference_time_ms=benchmark_results["inference_time_ms"],
                    model_size_mb=benchmark_results["model_size_mb"],
                    memory_usage_mb=benchmark_results["memory_usage_mb"],
                )

                # 3. Create staging directory for SaverFactory
                registry = ModelRegistry(self.train_model_config.model_registry_dir)
                staging_dir = os.path.join(self.train_model_config.model_registry_dir, "_staging_tmp")
                os.makedirs(staging_dir, exist_ok=True)

                try:
                    # Save preprocessor artifacts if present (for sklearn models)
                    staging_prep_dir = os.path.join(staging_dir, "preprocessor")
                    os.makedirs(staging_prep_dir, exist_ok=True)
                    if os.path.exists(self.transform_config.preprocessor_file):
                        shutil.copy2(
                            self.transform_config.preprocessor_file,
                            os.path.join(staging_prep_dir, "preprocessing.pkl")
                        )
                    if os.path.exists(self.transform_config.label_encoder_file_path):
                        shutil.copy2(
                            self.transform_config.label_encoder_file_path,
                            os.path.join(staging_prep_dir, "label_encoder.pkl")
                        )

                    # Save model using SaverFactory strategy
                    saver = ModelSaverFactory.create(metadata)
                    saver.save(model=winner.model, target_dir=staging_dir, metadata=metadata)

                    # 4. Promote to Champion in ModelRegistry
                    registry.promote_champion(staging_dir=staging_dir, metadata=metadata)

                finally:
                    if os.path.exists(staging_dir):
                        shutil.rmtree(staging_dir)

                    logger.info("Successfully persisted winning model '%s' to ModelRegistry.", winner.name)
            else:
                logger.info("Keeping existing production model '%s' in backend storage unchanged.", winner.name)
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def _save_checkpoint(self, model_eval: _ModelEvaluation) -> str:
        """
        Immediately save a trained & evaluated model checkpoint into checkpoints/<model_name>/.

        Parameters
        ----------
        model_eval : _ModelEvaluation
            Model evaluation container with trained model object and metrics.

        Returns
        -------
        str
            Path to the saved checkpoint directory.
        """
        try:
            checkpoint_dir = os.path.join(
                self.train_model_config.checkpoints_dir, model_eval.name
            )
            os.makedirs(checkpoint_dir, exist_ok=True)

            is_transformer = (
                model_eval.name.lower().startswith("distilbert")
                or hasattr(model_eval.model, "save_pretrained")
            )

            framework = "transformers" if is_transformer else "sklearn"
            serialization = "huggingface" if is_transformer else "joblib"
            input_type = "raw_text" if is_transformer else "tfidf"
            preprocessor_name = "distilbert-tokenizer" if is_transformer else "tfidf"

            metadata = ModelMetadata(
                model_name=model_eval.name,
                framework=framework,
                serialization=serialization,
                task="binary_classification",
                input_type=input_type,
                output_type="probability",
                preprocessor=preprocessor_name,
                metric=self.model_evaluate_metric,
                score=float(model_eval.metrics.get(self.model_evaluate_metric, 0.0)),
                metrics=model_eval.metrics,
                trained_at=datetime.now(timezone.utc).isoformat(),
            )

            saver = ModelSaverFactory.create(metadata)
            saver.save(model=model_eval.model, target_dir=checkpoint_dir, metadata=metadata)

            write_yaml_file(
                os.path.join(checkpoint_dir, "metrics.yaml"), model_eval.metrics
            )
            write_yaml_file(
                os.path.join(checkpoint_dir, "params.yaml"), model_eval.params or {}
            )
            LocalStorageService().write_json(
                os.path.join(checkpoint_dir, "metadata.json"), metadata.to_dict()
            )

            logger.info(
                "Successfully saved checkpoint for model '%s' at: %s",
                model_eval.name,
                checkpoint_dir,
            )
            return checkpoint_dir
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def _load_checkpoint(self, model_name: str) -> _ModelEvaluation:
        """
        Load model checkpoint and reconstruct a complete _ModelEvaluation object.

        Parameters
        ----------
        model_name : str
            Name of the model to load from checkpoints/.

        Returns
        -------
        _ModelEvaluation
            Reconstructed evaluation object containing loaded model and metrics.
        """
        try:
            checkpoint_dir = os.path.join(
                self.train_model_config.checkpoints_dir, model_name
            )
            if not os.path.exists(checkpoint_dir):
                raise FileNotFoundError(
                    f"Checkpoint directory not found for model '{model_name}': {checkpoint_dir}"
                )

            metrics_path = os.path.join(checkpoint_dir, "metrics.yaml")
            if not os.path.exists(metrics_path):
                raise FileNotFoundError(
                    f"Checkpoint metrics.yaml not found at: {metrics_path}"
                )
            metrics = read_yaml_file(metrics_path)

            params_path = os.path.join(checkpoint_dir, "params.yaml")
            params = read_yaml_file(params_path) if os.path.exists(params_path) else {}

            meta_path = os.path.join(checkpoint_dir, "metadata.json")
            if os.path.exists(meta_path):
                meta_dict = LocalStorageService().read_json(meta_path)
                metadata = ModelMetadata.from_dict(meta_dict)
            else:
                is_transformer = model_name.lower().startswith("distilbert")
                serialization = "huggingface" if is_transformer else "joblib"
                framework = "transformers" if is_transformer else "sklearn"
                metadata = ModelMetadata(
                    model_name=model_name,
                    framework=framework,
                    serialization=serialization,
                    task="binary_classification",
                    input_type="raw_text" if is_transformer else "tfidf",
                    output_type="probability",
                    preprocessor="distilbert-tokenizer" if is_transformer else "tfidf",
                    metric=self.model_evaluate_metric,
                    score=float(metrics.get(self.model_evaluate_metric, 0.0)),
                    metrics=metrics,
                    trained_at=datetime.now(timezone.utc).isoformat(),
                )

            loader = ModelLoaderFactory.create(metadata)
            loaded_model = loader.load(checkpoint_dir, metadata)

            logger.info("Successfully loaded checkpoint for model '%s'.", model_name)
            return _ModelEvaluation(
                name=model_name,
                model=loaded_model,
                params=params,
                metrics=metrics,
            )
        except Exception as exc:
            raise MyException(exc, sys) from exc

    def _train_and_checkpoint_distilbert(
        self,
        state: TrainingStateManager,
        checkpoint_mgr: CheckpointManager,
        config_hash: str,
        evaluated_models: Dict[str, _ModelEvaluation],
        evaluation_errors: Dict[str, str],
    ) -> None:
        """
        Train, evaluate, save temporary staging checkpoint, verify, promote, and update state for DistilBERT.
        """
        distilbert_name = "DistilBERT"
        logger.info("Training %s...", distilbert_name)
        checkpoint_mgr.cleanup_temporary_checkpoint(distilbert_name)
        try:
            from src.components.transformer_trainer import TransformerTrainer

            transformer_trainer = TransformerTrainer()
            distilbert_eval = transformer_trainer.train_and_evaluate()
            if distilbert_eval is not None:
                tmp_chk_dir = checkpoint_mgr.save_temporary_checkpoint(
                    distilbert_eval, config_hash=config_hash
                )
                if checkpoint_mgr.verify_checkpoint(tmp_chk_dir, expected_config_hash=config_hash):
                    final_chk_dir = checkpoint_mgr.promote_checkpoint(distilbert_name)
                    state.mark_completed(
                        distilbert_name,
                        checkpoint=final_chk_dir,
                        config_hash=config_hash,
                    )
                    evaluated_models[distilbert_name] = distilbert_eval
                    logger.info(
                        "DistilBERT evaluated successfully, verified, and promoted to candidate list."
                    )
                else:
                    err_msg = "DistilBERT temporary staging checkpoint verification failed."
                    logger.error(err_msg)
                    checkpoint_mgr.cleanup_temporary_checkpoint(distilbert_name)
                    evaluation_errors[distilbert_name] = err_msg
                    state.mark_failed(distilbert_name, reason=err_msg)
            else:
                err_msg = "DistilBERT training returned None."
                checkpoint_mgr.cleanup_temporary_checkpoint(distilbert_name)
                evaluation_errors[distilbert_name] = err_msg
                state.mark_failed(distilbert_name, reason=err_msg)
        except Exception as trans_err:
            error_msg = str(trans_err)
            checkpoint_mgr.cleanup_temporary_checkpoint(distilbert_name)
            logger.error("DistilBERT training failed: %s", error_msg)
            evaluation_errors[distilbert_name] = error_msg
            state.mark_failed(distilbert_name, reason=error_msg)

    def initiate_model_training(self) -> ModelTrainerArtifact:
        """
        Execute the full training pipeline with atomic checkpoint replacement, per-model SHA-256
        config_hash validation, incremental retraining, fail-fast verification, and reporting.
        """
        try:
            logger.info("Starting model training pipeline.")
            setup_mlflow()

            state = TrainingStateManager(
                self.train_model_config.training_state_file_path
            )
            checkpoint_mgr = CheckpointManager(
                checkpoints_dir=self.train_model_config.checkpoints_dir,
                default_metric=self.model_evaluate_metric,
            )

            state.update_last_updated()
            logger.info("Loading previous training session state...")

            train_df, test_df = self.load_data()
            x_train, y_train = self._split_features_target(train_df)
            x_test, y_test = self._split_features_target(test_df)

            models = self.get_model_list  # Dict[str, _ModelBundle]

            evaluated_models: Dict[str, _ModelEvaluation] = {}
            training_errors: Dict[str, str] = {}
            evaluation_errors: Dict[str, str] = {}

            tuner = HyperparameterTuner(
                n_iter=20,
                cv=5,
                scoring=self.model_evaluate_metric,
                random_state=42,
                n_jobs=1,
                enable_fine_tuning=self.train_model_config.enable_fine_tuning,
            )

            # Compute SHA-256 hashes for dataset & preprocessor files
            train_file_hash = checkpoint_mgr.compute_file_checksum(
                self.transformed_train_file_path
            )
            test_file_hash = checkpoint_mgr.compute_file_checksum(
                self.transformed_test_file_path
            )
            prep_file_hashes = {
                "preprocessor": checkpoint_mgr.compute_file_checksum(
                    self.transform_config.preprocessor_file
                ),
                "label_encoder": checkpoint_mgr.compute_file_checksum(
                    self.transform_config.label_encoder_file_path
                ),
            }
            tuner_config = {
                "n_iter": tuner.n_iter,
                "cv": tuner.cv,
                "random_state": tuner.random_state,
                "enable_fine_tuning": self.train_model_config.enable_fine_tuning,
            }

            # 1. Process candidate classical models
            for model_name, bundle in models.items():
                current_config_hash = checkpoint_mgr.compute_config_hash(
                    model_name=model_name,
                    train_file_hash=train_file_hash,
                    test_file_hash=test_file_hash,
                    prep_file_hashes=prep_file_hashes,
                    params=bundle.params,
                    search_space=PARAM_SEARCH_SPACES.get(model_name, {}),
                    tuner_config=tuner_config,
                    framework="sklearn",
                    serialization="joblib",
                )

                if state.is_completed(model_name):
                    if checkpoint_mgr.validate_checkpoint(model_name, current_config_hash):
                        logger.info("Checkpoint validated for %s. Skipping...", model_name)
                        try:
                            loaded_eval = checkpoint_mgr.load_checkpoint(model_name)
                            evaluated_models[model_name] = loaded_eval
                            continue
                        except Exception as load_err:
                            logger.warning(
                                "Recovered from corrupted checkpoint for %s (%s). Retraining...",
                                model_name,
                                load_err,
                            )

                # Clean up any lingering temporary staging directory before retraining
                checkpoint_mgr.cleanup_temporary_checkpoint(model_name)

                # Update state to pending BEFORE retraining starts
                state.mark_pending(model_name)
                logger.info("Training %s...", model_name)

                try:
                    is_tabpfn = (
                        model_name.lower().startswith("tabpfn")
                        or type(bundle.model).__name__ == "TabPFNClassifier"
                    )

                    if is_tabpfn:
                        logger.info(
                            "Fitting TabPFN directly without RandomizedSearchCV: %s",
                            model_name,
                        )
                        bundle.model.fit(x_train.to_numpy(), y_train.to_numpy())
                        model_params = (
                            getattr(bundle.model, "get_params", lambda: {})()
                            or bundle.params
                        )
                        trained_model = bundle.model
                        best_params = model_params
                        best_cv_score = 0.0
                    else:
                        best_estimator, best_params, best_cv_score = tuner.tune(
                            model_name=model_name,
                            estimator=bundle.model,
                            x_train=x_train,
                            y_train=y_train,
                        )
                        trained_model = best_estimator

                    # Evaluate model immediately
                    logger.info("Evaluating model: %s", model_name)
                    y_pred = trained_model.predict(x_test.to_numpy())
                    y_score = self._get_model_scores(trained_model, x_test.to_numpy())

                    metrics = evaluate_classification_model(
                        y_true=y_test,
                        y_pred=y_pred,
                        y_score=y_score,
                    )
                    metrics["best_cv_score"] = float(best_cv_score)

                    log_model_to_mlflow(
                        model_name=model_name,
                        model=trained_model,
                        params=best_params,
                        metrics=metrics,
                    )

                    eval_obj = _ModelEvaluation(
                        name=model_name,
                        model=trained_model,
                        params=best_params,
                        metrics=metrics,
                    )

                    # Atomic Checkpoint Replacement: Save to _tmp, verify, and promote
                    tmp_chk_dir = checkpoint_mgr.save_temporary_checkpoint(
                        eval_obj, config_hash=current_config_hash
                    )
                    if checkpoint_mgr.verify_checkpoint(tmp_chk_dir, expected_config_hash=current_config_hash):
                        final_chk_dir = checkpoint_mgr.promote_checkpoint(model_name)
                        state.mark_completed(
                            model_name, checkpoint=final_chk_dir, config_hash=current_config_hash
                        )
                        evaluated_models[model_name] = eval_obj
                    else:
                        err_msg = f"Temporary checkpoint verification failed for model {model_name}"
                        logger.error(err_msg)
                        checkpoint_mgr.cleanup_temporary_checkpoint(model_name)
                        training_errors[model_name] = err_msg
                        state.mark_failed(model_name, reason=err_msg)

                except Exception as e:
                    error_msg = str(e)
                    logger.error(
                        f"Model {model_name} training/evaluation failed: {error_msg}"
                    )
                    checkpoint_mgr.cleanup_temporary_checkpoint(model_name)
                    training_errors[model_name] = error_msg
                    state.mark_failed(model_name, reason=error_msg)

            # 2. Process DistilBERT Transformer model
            distilbert_name = "DistilBERT"
            raw_train_hash = checkpoint_mgr.compute_file_checksum(
                self.transform_config.transform_train_raw_file
            )
            raw_test_hash = checkpoint_mgr.compute_file_checksum(
                self.transform_config.transform_test_raw_file
            )
            distilbert_config_hash = checkpoint_mgr.compute_config_hash(
                model_name=distilbert_name,
                train_file_hash=raw_train_hash,
                test_file_hash=raw_test_hash,
                prep_file_hashes={},
                params={
                    "model_name": "distilbert-base-uncased",
                    "epochs": 3,
                    "batch_size": 16,
                    "learning_rate": 2e-5,
                },
                search_space={},
                tuner_config={},
                framework="transformers",
                serialization="huggingface",
            )

            if not self.train_model_config.enable_distilbert:
                logger.info("DistilBERT fine-tuning disabled via ENABLE_DISTILBERT=false.")
                if state.is_completed(distilbert_name) and checkpoint_mgr.validate_checkpoint(distilbert_name, distilbert_config_hash):
                    try:
                        distilbert_eval = checkpoint_mgr.load_checkpoint(distilbert_name)
                        evaluated_models[distilbert_name] = distilbert_eval
                        logger.info("Loaded pre-existing validated checkpoint for disabled DistilBERT.")
                    except Exception as load_err:
                        logger.warning("DistilBERT disabled and checkpoint unreadable: %s", load_err)
            elif state.is_completed(distilbert_name):
                if checkpoint_mgr.validate_checkpoint(distilbert_name, distilbert_config_hash):
                    logger.info("Checkpoint validated for %s. Skipping...", distilbert_name)
                    try:
                        distilbert_eval = checkpoint_mgr.load_checkpoint(distilbert_name)
                        evaluated_models[distilbert_name] = distilbert_eval
                    except Exception as load_err:
                        logger.warning(
                            "Recovered from corrupted checkpoint for %s (%s). Retraining...",
                            distilbert_name,
                            load_err,
                        )
                        state.mark_pending(distilbert_name)
                        self._train_and_checkpoint_distilbert(
                            state, checkpoint_mgr, distilbert_config_hash, evaluated_models, evaluation_errors
                        )
                else:
                    state.mark_pending(distilbert_name)
                    self._train_and_checkpoint_distilbert(
                        state, checkpoint_mgr, distilbert_config_hash, evaluated_models, evaluation_errors
                    )
            else:
                state.mark_pending(distilbert_name)
                self._train_and_checkpoint_distilbert(
                    state, checkpoint_mgr, distilbert_config_hash, evaluated_models, evaluation_errors
                )

            # 3. Select best candidate model
            if not evaluated_models:
                raise ValueError(
                    "No models were successfully evaluated across all runs. Cannot select best model."
                )

            best_candidate = self.select_best_model(evaluated_models)

            # 4. Compare with production champion & persist winner
            winner, is_new_model_winner = self.compare_with_production_model(
                candidate_model=best_candidate,
                x_test=x_test,
                y_test=y_test,
            )

            self.save_best_model(
                winner=winner,
                should_save=is_new_model_winner,
                x_test=x_test,
            )

            # 5. Build comprehensive status report across all runs
            training_timestamp = datetime.now(timezone.utc).isoformat()

            all_model_names = set(self.get_model_list.keys()) | {"DistilBERT"}
            model_status = {}
            for name in all_model_names:
                if name in evaluated_models:
                    model_status[name] = {"status": "completed"}
                elif name in training_errors:
                    model_status[name] = {"status": "failed", "reason": training_errors[name]}
                elif name in evaluation_errors:
                    model_status[name] = {"status": "failed", "reason": evaluation_errors[name]}
                else:
                    status_in_state = state.get_model_status(name)
                    if status_in_state:
                        info = state.get_model_info(name)
                        model_status[name] = info
                    else:
                        model_status[name] = {"status": "pending"}

            report = {
                "best_model_name": winner.name,
                "best_model_metric": self.model_evaluate_metric,
                "winner_metrics": winner.metrics,
                "model_status": model_status,
                "metrics_of_successful_models": {
                    name: result.metrics for name, result in evaluated_models.items()
                },
                "training_timestamp": training_timestamp,
            }
            write_yaml_file(self.train_model_config.model_report_file_path, report)

            logger.info("Model training pipeline completed successfully.")
            logger.info(
                f"Report saved at {self.train_model_config.model_report_file_path}"
            )

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