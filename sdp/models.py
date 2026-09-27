"""Registry of baseline classifiers and their (optional) search spaces.

Adding a new model is a two-line change: register a factory in
``MODEL_REGISTRY`` and, optionally, a parameter distribution in
``PARAM_DISTRIBUTIONS``. Every factory receives the random seed and the
class-balancing mode so that ``class_weight`` can be applied uniformly.
"""

from __future__ import annotations

from typing import Any, Callable

from scipy.stats import randint, uniform
from sklearn.base import BaseEstimator
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

# Human-readable names used in tables and figure legends.
DISPLAY_NAMES: dict[str, str] = {
    "logistic_regression": "Logistic Regression",
    "decision_tree": "Decision Tree",
    "random_forest": "Random Forest",
    "gradient_boosting": "Gradient Boosting",
    "svm": "SVM (RBF)",
    "knn": "k-Nearest Neighbours",
    "naive_bayes": "Gaussian Naive Bayes",
    "mlp": "MLP (Neural Network)",
}


def _cw(balance: str) -> str | None:
    """Return ``'balanced'`` when class weighting is the chosen balancing mode."""
    return "balanced" if balance == "class_weight" else None


MODEL_REGISTRY: dict[str, Callable[[int, str], BaseEstimator]] = {
    "logistic_regression": lambda seed, bal: LogisticRegression(
        max_iter=2000, class_weight=_cw(bal), random_state=seed
    ),
    "decision_tree": lambda seed, bal: DecisionTreeClassifier(
        max_depth=8, min_samples_leaf=5, class_weight=_cw(bal), random_state=seed
    ),
    "random_forest": lambda seed, bal: RandomForestClassifier(
        n_estimators=300, min_samples_leaf=2, class_weight=_cw(bal), n_jobs=-1, random_state=seed
    ),
    "gradient_boosting": lambda seed, bal: GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.05, max_depth=3, random_state=seed
    ),
    # SVC has no native probabilities; wrap it in Platt scaling so ROC-AUC and
    # PR curves can be computed like the other models.
    "svm": lambda seed, bal: CalibratedClassifierCV(
        SVC(C=1.0, kernel="rbf", gamma="scale", cache_size=1000, class_weight=_cw(bal), random_state=seed),
        method="sigmoid", cv=3, ensemble=False,
    ),
    "knn": lambda seed, bal: KNeighborsClassifier(n_neighbors=7, weights="distance"),
    "naive_bayes": lambda seed, bal: GaussianNB(),
    "mlp": lambda seed, bal: MLPClassifier(
        hidden_layer_sizes=(64, 32), alpha=1e-3, max_iter=600, early_stopping=True, random_state=seed
    ),
}

# Search spaces for RandomizedSearchCV (keys are prefixed with ``model__``
# because the estimator sits at the end of a pipeline).
PARAM_DISTRIBUTIONS: dict[str, dict[str, Any]] = {
    "random_forest": {
        "model__n_estimators": randint(100, 600),
        "model__max_depth": [None, 6, 10, 16],
        "model__min_samples_leaf": randint(1, 6),
        "model__max_features": ["sqrt", "log2", 0.5],
    },
    "gradient_boosting": {
        "model__n_estimators": randint(100, 400),
        "model__learning_rate": uniform(0.02, 0.18),
        "model__max_depth": randint(2, 5),
        "model__subsample": uniform(0.6, 0.4),
    },
    "svm": {  # SVC sits inside CalibratedClassifierCV -> one more level of nesting
        "model__estimator__C": uniform(0.1, 10),
        "model__estimator__gamma": ["scale", 0.01, 0.05, 0.1],
    },
    "logistic_regression": {
        "model__C": uniform(0.01, 5),
    },
    "knn": {
        "model__n_neighbors": randint(3, 21),
        "model__weights": ["uniform", "distance"],
    },
}


def get_model(name: str, seed: int, balance: str = "none") -> BaseEstimator:
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model '{name}'. Available: {sorted(MODEL_REGISTRY)}")
    return MODEL_REGISTRY[name](seed, balance)


def get_models(cfg: dict[str, Any]) -> dict[str, BaseEstimator]:
    """Instantiate every model listed in ``config.yaml``."""
    seed = cfg["random_seed"]
    balance = cfg["preprocessing"].get("balance", "none")
    return {name: get_model(name, seed, balance) for name in cfg["models"]}
