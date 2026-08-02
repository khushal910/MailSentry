"""
Centralized hyperparameter search spaces for candidate classification models.
Used by HyperparameterTuner for RandomizedSearchCV.
"""

from typing import Any, Dict, List

PARAM_SEARCH_SPACES: Dict[str, Dict[str, List[Any]]] = {
    "RandomForest": {
        "n_estimators": [100, 200, 300, 400],
        "max_depth": [None, 10, 20, 30],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "bootstrap": [True, False],
    },
    "LightGBM": {
        "learning_rate": [0.01, 0.05, 0.1, 0.2],
        "n_estimators": [100, 200, 300],
        "max_depth": [-1, 5, 10, 15],
        "num_leaves": [20, 31, 50, 70],
        "subsample": [0.6, 0.8, 1.0],
        "colsample_bytree": [0.6, 0.8, 1.0],
    },
    "XGBClassifier": {
        "learning_rate": [0.01, 0.05, 0.1, 0.2],
        "max_depth": [3, 5, 7, 9],
        "n_estimators": [100, 200, 300],
        "subsample": [0.6, 0.8, 1.0],
        "colsample_bytree": [0.6, 0.8, 1.0],
        "gamma": [0, 0.1, 0.2, 0.3],
    },
    "LogisticRegression": {
        "C": [0.01, 0.1, 1.0, 10.0, 100.0],
        "penalty": ["l1", "l2"],
    },
    "LinearSVC": {
        "C": [0.01, 0.1, 1.0, 10.0, 100.0],
    },
    "ExtraTrees": {
        "n_estimators": [100, 200, 300, 400],
        "max_depth": [None, 10, 20, 30],
    },
    "CatBoostClassifier": {
        "iterations": [100, 200, 300, 500],
        "learning_rate": [0.01, 0.05, 0.1, 0.2],
        "depth": [4, 6, 8, 10],
    },
}

# Aliases matching alternative naming conventions
PARAM_SEARCH_SPACES["XGBoost"] = PARAM_SEARCH_SPACES["XGBClassifier"]
PARAM_SEARCH_SPACES["CatBoost"] = PARAM_SEARCH_SPACES["CatBoostClassifier"]
