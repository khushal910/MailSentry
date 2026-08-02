import sys
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.ensemble import AdaBoostClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from src.entity.config_entity import _ModelBundle
from xgboost import XGBClassifier
from typing import Dict
from src.logger import logger
from src.exception import MyException


class ModelList:
  def get_models(self) -> Dict[str, _ModelBundle]:
        """
        Create all candidate classification models with fixed random states.

        Returns:
            Dictionary mapping model names to model bundles.

        Raises:
            MyException: If model creation fails.
        """
        try:
            logger.info("Creating candidate models.")
            models: Dict[str, _ModelBundle] = {
                "LogisticRegression": _ModelBundle(
                    name="LogisticRegression",
                    model=LogisticRegression(
                        solver="liblinear",
                        max_iter=1000,
                        random_state=42,
                    ),
                    params={
                        "solver": "liblinear",
                        "max_iter": 1000,
                        "random_state": 42,
                    },
                ),
                "RandomForest": _ModelBundle(
                    name="RandomForest",
                    model=RandomForestClassifier(
                        n_estimators=300,
                        random_state=42,
                        n_jobs=-1,
                    ),
                    params={
                        "n_estimators": 300,
                        "random_state": 42,
                        "n_jobs": -1,
                    },
                ),
                "XGBClassifier": _ModelBundle(
                    name="XGBClassifier",
                    model=XGBClassifier(
                        n_estimators=300,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        objective="binary:logistic",
                        eval_metric="logloss",
                        random_state=42,
                        n_jobs=-1,
                    ),
                    params={
                        "n_estimators": 300,
                        "max_depth": 6,
                        "learning_rate": 0.1,
                        "subsample": 0.8,
                        "colsample_bytree": 0.8,
                        "objective": "binary:logistic",
                        "eval_metric": "logloss",
                        "random_state": 42,
                        "n_jobs": -1,
                    },
                ),
                "CatBoostClassifier": _ModelBundle(
                    name="CatBoostClassifier",
                    model=CatBoostClassifier(
                        iterations=500,  
                        learning_rate=0.1,
                        depth=6,
                        loss_function="Logloss",
                        random_seed=42,
                        verbose=False,
                        allow_writing_files=False,
                    ),
                    params={
                        "iterations": 500,
                        "learning_rate": 0.1,
                        "depth": 6,
                        "loss_function": "Logloss",
                        "random_seed": 42,
                        "verbose": False,
                        "allow_writing_files": False,
                    },
                ),
                "LinearSVC": _ModelBundle(
                    name="LinearSVC",
                    model=LinearSVC(
                        C=1.0,
                        random_state=42,
                    ),
                    params={
                        "C": 1.0,
                        "random_state": 42,
                    },
                ),
                "ExtraTrees": _ModelBundle(
                    name="ExtraTrees",
                    model=ExtraTreesClassifier(
                        n_estimators=300,
                        random_state=42,
                        n_jobs=-1,
                    ),
                    params={
                        "n_estimators": 300,
                        "random_state": 42,
                        "n_jobs": -1,
                    },
                ),
                
                
                "LightGBM": _ModelBundle(
                    name="LightGBM",
                    model=LGBMClassifier(
                        n_estimators=300,
                        learning_rate=0.1,
                        random_state=42,
                        n_jobs=-1,
                    ),
                    params={
                        "n_estimators": 300,
                        "learning_rate": 0.1,
                        "random_state": 42,
                        "n_jobs": -1,
                    },
                )
            }

            try:
                from tabpfn import TabPFNClassifier
                models["TabPFN"] = _ModelBundle(
                    name="TabPFN",
                    model=TabPFNClassifier(device="auto"),
                    params={"device": "auto"},
                )
            except Exception as tabpfn_err:
                logger.warning("Could not initialize TabPFNClassifier: %s", tabpfn_err)

            return models

        except Exception as exc:
            raise MyException(exc, sys) from exc