"""
CryptoScope Tree and Classical ML Models
Implements Random Forest, Support Vector Machine (SVM), and XGBoost classifiers.
Supports Optuna hyperparameter optimization.
"""

from typing import Dict, Any, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
import optuna

# Disable optuna verbose logging
optuna.logging.set_verbosity(optuna.logging.WARNING)

def create_model(model_type: str, params: Optional[Dict[str, Any]] = None, random_state: int = 42) -> Any:
    params = params or {}
    m = model_type.lower()

    if m in ["rf", "random_forest", "randomforest"]:
        default_params = {
            "n_estimators": 100,
            "max_depth": 15,
            "min_samples_split": 2,
            "n_jobs": -1,
            "random_state": random_state
        }
        default_params.update(params)
        return RandomForestClassifier(**default_params)

    elif m in ["svm", "svc"]:
        default_params = {
            "C": 1.0,
            "kernel": "rbf",
            "probability": True,
            "random_state": random_state
        }
        default_params.update(params)
        return SVC(**default_params)

    elif m in ["xgb", "xgboost"]:
        default_params = {
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "eval_metric": "logloss",
            "random_state": random_state,
            "n_jobs": -1
        }
        default_params.update(params)
        return XGBClassifier(**default_params)

    else:
        raise ValueError(f"Unsupported model type: {model_type}")

def tune_hyperparameters(model_type: str, 
                         x_train: np.ndarray, 
                         y_train: np.ndarray, 
                         n_trials: int = 15,
                         random_state: int = 42) -> Dict[str, Any]:
    """
    Optuna hyperparameter tuning with configurable search budget.
    """
    m = model_type.lower()

    def objective(trial: optuna.Trial) -> float:
        if m in ["rf", "random_forest"]:
            n_estimators = trial.suggest_int("n_estimators", 50, 200, step=25)
            max_depth = trial.suggest_int("max_depth", 5, 25)
            min_samples_split = trial.suggest_int("min_samples_split", 2, 8)
            clf = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_split=min_samples_split,
                random_state=random_state,
                n_jobs=-1
            )
        elif m in ["svm", "svc"]:
            c_val = trial.suggest_float("C", 0.1, 10.0, log=True)
            kernel = trial.suggest_categorical("kernel", ["rbf", "linear"])
            clf = SVC(C=c_val, kernel=kernel, probability=True, random_state=random_state)
        elif m in ["xgb", "xgboost"]:
            n_estimators = trial.suggest_int("n_estimators", 50, 150, step=25)
            max_depth = trial.suggest_int("max_depth", 3, 10)
            lr = trial.suggest_float("learning_rate", 0.01, 0.3, log=True)
            clf = XGBClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=lr,
                eval_metric="logloss",
                random_state=random_state,
                n_jobs=-1
            )
        else:
            return 0.0

        # Simple 3-fold cross validation score
        from sklearn.model_selection import cross_val_score
        scores = cross_val_score(clf, x_train, y_train, cv=3, scoring="f1_macro")
        return float(scores.mean())

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    return study.best_params
