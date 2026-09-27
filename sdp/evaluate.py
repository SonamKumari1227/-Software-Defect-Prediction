"""Metrics, cross-validation and hold-out evaluation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate

from sdp.utils import get_logger

log = get_logger(__name__)

# Order in which metrics appear in tables.
METRIC_ORDER = ["accuracy", "precision", "recall", "f1", "roc_auc", "mcc", "balanced_accuracy"]


def compute_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, y_score: np.ndarray | None = None
) -> dict[str, float]:
    """Standard binary-classification metrics (positive class = defective)."""
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "mcc": matthews_corrcoef(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
    }
    if y_score is not None and len(np.unique(y_true)) == 2:
        metrics["roc_auc"] = roc_auc_score(y_true, y_score)
    else:
        metrics["roc_auc"] = float("nan")

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    metrics.update({"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)})
    # Probability of false alarm - commonly reported in defect-prediction papers.
    metrics["pf"] = fp / (fp + tn) if (fp + tn) else 0.0
    return metrics


def get_scores(estimator: BaseEstimator, X: pd.DataFrame) -> np.ndarray:
    """Continuous score for ROC-AUC: predict_proba if available, else decision_function."""
    if hasattr(estimator, "predict_proba"):
        return estimator.predict_proba(X)[:, 1]
    if hasattr(estimator, "decision_function"):
        return estimator.decision_function(X)
    return estimator.predict(X)


def make_cv(cfg: dict[str, Any]) -> RepeatedStratifiedKFold:
    cv_cfg = cfg["cross_validation"]
    return RepeatedStratifiedKFold(
        n_splits=cv_cfg["n_splits"],
        n_repeats=cv_cfg.get("n_repeats", 1),
        random_state=cfg["random_seed"],
    )


def cross_validate_pipeline(
    pipeline: BaseEstimator, X: pd.DataFrame, y: pd.Series, cfg: dict[str, Any]
) -> tuple[dict[str, float], dict[str, np.ndarray]]:
    """Repeated stratified k-fold CV on the *training* data.

    Returns
    -------
    summary : ``{cv_<metric>_mean, cv_<metric>_std, ...}`` for every metric in the config.
    raw     : ``{metric: per-fold scores}`` for box plots.

    ``n_jobs`` defaults to 1: libsvm is known to crash inside forked/spawned
    worker processes on some Windows builds, and sequential execution keeps
    the run fully deterministic.
    """
    cv_cfg = cfg["cross_validation"]
    res = cross_validate(pipeline, X, y, cv=make_cv(cfg), scoring=cv_cfg["scoring"],
                         n_jobs=cv_cfg.get("n_jobs", 1))
    summary: dict[str, float] = {}
    raw: dict[str, np.ndarray] = {}
    for metric in cv_cfg["scoring"]:
        scores = res[f"test_{metric}"]
        raw[metric] = scores
        summary[f"cv_{metric}_mean"] = float(np.mean(scores))
        summary[f"cv_{metric}_std"] = float(np.std(scores))
    return summary, raw


def evaluate_on_test(
    pipeline: BaseEstimator, X_test: pd.DataFrame, y_test: pd.Series
) -> tuple[dict[str, float], np.ndarray, np.ndarray]:
    """Evaluate a *fitted* pipeline on the hold-out set."""
    y_pred = pipeline.predict(X_test)
    y_score = get_scores(pipeline, X_test)
    return compute_metrics(np.asarray(y_test), y_pred, y_score), y_pred, y_score


def results_table(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Turn a list of per-model result dicts into a tidy, sorted DataFrame."""
    df = pd.DataFrame(records)
    cols = ["model"] + [c for c in METRIC_ORDER if c in df.columns]
    extra = [c for c in df.columns if c not in cols]
    df = df[cols + extra]
    return df.sort_values("f1", ascending=False).reset_index(drop=True)
