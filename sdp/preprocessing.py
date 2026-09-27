"""Data cleaning and the scikit-learn preprocessing pipeline.

Design principle: every *learned* transformation (imputation statistics,
scaling parameters, SMOTE synthetic samples) is placed inside a pipeline so
that it is fitted on the training folds only. This prevents data leakage,
which is a common flaw in published defect-prediction experiments.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.base import BaseEstimator
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler, StandardScaler

from sdp.data_loader import TARGET
from sdp.utils import get_logger

log = get_logger(__name__)


# --------------------------------------------------------------------------- #
# Frame-level cleaning (applied once, before the split - no leakage risk
# because these steps do not learn statistics from the data).
# --------------------------------------------------------------------------- #
def clean_dataframe(df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    """Remove duplicates and constant columns according to the config."""
    pp = cfg["preprocessing"]
    before = len(df)

    if pp.get("remove_duplicates", True):
        df = df.drop_duplicates().reset_index(drop=True)
        log.info("Removed %d duplicate rows", before - len(df))

    if pp.get("drop_constant_features", True):
        feature_cols = [c for c in df.columns if c != TARGET]
        constant = [c for c in feature_cols if df[c].nunique(dropna=True) <= 1]
        if constant:
            df = df.drop(columns=constant)
            log.info("Dropped %d constant feature(s): %s", len(constant), constant)

    return df


def stratified_split(
    X: pd.DataFrame, y: pd.Series, cfg: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Stratified hold-out split so that both sets keep the defect ratio."""
    return train_test_split(
        X,
        y,
        test_size=cfg["preprocessing"]["test_size"],
        stratify=y,
        random_state=cfg["random_seed"],
    )


# --------------------------------------------------------------------------- #
# Pipeline construction
# --------------------------------------------------------------------------- #
def _log1p_safe(X: np.ndarray) -> np.ndarray:
    """log1p that tolerates the occasional negative value produced by imputation."""
    return np.log1p(np.clip(X, a_min=0, a_max=None))


def preprocessing_steps(cfg: dict[str, Any]) -> list[tuple[str, Any]]:
    """Imputation -> optional log transform -> scaling, as a list of named steps."""
    pp = cfg["preprocessing"]
    steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy=pp.get("impute_strategy", "median")))
    ]

    if pp.get("log_transform", True):
        steps.append(("log1p", FunctionTransformer(_log1p_safe, feature_names_out="one-to-one")))

    scaler = pp.get("scaler", "standard")
    if scaler == "standard":
        steps.append(("scaler", StandardScaler()))
    elif scaler == "minmax":
        steps.append(("scaler", MinMaxScaler()))
    elif scaler not in ("none", None):
        raise ValueError(f"Unknown scaler '{scaler}'")

    return steps


def build_preprocessor(cfg: dict[str, Any]) -> Pipeline:
    """Stand-alone preprocessing pipeline (useful for EDA / inspection)."""
    return Pipeline(preprocessing_steps(cfg))


def build_model_pipeline(model: BaseEstimator, cfg: dict[str, Any]) -> Pipeline:
    """Wrap *model* with preprocessing (and SMOTE if configured).

    When ``balance == 'smote'`` an ``imblearn`` pipeline is returned so that
    resampling happens *inside* each CV fold and only on training data.
    Steps are kept flat (imblearn forbids nested pipelines); the estimator is
    always the final step named ``"model"``.
    """
    balance = cfg["preprocessing"].get("balance", "none")
    steps = preprocessing_steps(cfg)

    if balance == "smote":
        steps.append(("smote", SMOTE(random_state=cfg["random_seed"])))
        steps.append(("model", model))
        return ImbPipeline(steps)

    steps.append(("model", model))
    return Pipeline(steps)
