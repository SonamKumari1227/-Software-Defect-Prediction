"""Unit and smoke tests. Run with:  pytest -q"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sdp.config import load_config  # noqa: E402
from sdp.data_loader import TARGET, _normalise_target, read_arff  # noqa: E402
from sdp.evaluate import compute_metrics, evaluate_on_test  # noqa: E402
from sdp.models import MODEL_REGISTRY, get_models  # noqa: E402
from sdp.preprocessing import build_model_pipeline, clean_dataframe, stratified_split  # noqa: E402

_ARFF = """
% comment line
@relation 'toy'
@attribute LOC numeric
@attribute COMPLEXITY numeric
@attribute Defective {Y,N}
@data
10,1,N
20,?,Y
30,3,N
"""


@pytest.fixture(scope="module")
def cfg():
    c = load_config()
    c["cross_validation"]["n_splits"] = 3
    c["cross_validation"]["n_repeats"] = 1
    c["models"] = ["logistic_regression", "decision_tree", "naive_bayes"]
    return c


@pytest.fixture(scope="module")
def toy_frame(cfg):
    """Synthetic but realistic imbalanced dataset with skewed metric columns."""
    rng = np.random.default_rng(cfg["random_seed"])
    n = 400
    loc = rng.lognormal(3, 1, n)
    cc = np.clip(loc / 8 + rng.normal(0, 2, n), 1, None)
    halstead = loc * rng.uniform(5, 15, n)
    logit = -3.5 + 0.02 * loc + 0.15 * cc
    y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    df = pd.DataFrame({"LOC": loc, "CC": cc, "HALSTEAD": halstead, "CONST": 1.0, TARGET: y})
    return pd.concat([df, df.iloc[:5]], ignore_index=True)  # add duplicates on purpose


def test_read_arff_parses_names_and_missing(tmp_path):
    p = tmp_path / "toy.arff"
    p.write_text(_ARFF)
    df = read_arff(p)
    assert list(df.columns) == ["LOC", "COMPLEXITY", "Defective"]
    assert df.shape == (3, 3)
    assert df["COMPLEXITY"].isna().sum() == 1


def test_normalise_target_encodes_binary(tmp_path):
    p = tmp_path / "toy.arff"
    p.write_text(_ARFF)
    df = _normalise_target(read_arff(p))
    assert TARGET in df.columns
    assert df[TARGET].tolist() == [0, 1, 0]


def test_clean_dataframe_removes_duplicates_and_constants(cfg, toy_frame):
    cleaned = clean_dataframe(toy_frame, cfg)
    assert len(cleaned) == len(toy_frame) - 5
    assert "CONST" not in cleaned.columns


def test_stratified_split_preserves_ratio(cfg, toy_frame):
    df = clean_dataframe(toy_frame, cfg)
    X, y = df.drop(columns=[TARGET]), df[TARGET]
    X_tr, X_te, y_tr, y_te = stratified_split(X, y, cfg)
    assert len(X_tr) + len(X_te) == len(X)
    assert abs(y_tr.mean() - y_te.mean()) < 0.05


def test_compute_metrics_perfect_prediction():
    y = np.array([0, 1, 0, 1])
    m = compute_metrics(y, y, y.astype(float))
    assert m["accuracy"] == m["f1"] == m["roc_auc"] == 1.0
    assert m["fp"] == m["fn"] == 0


@pytest.mark.parametrize("balance", ["none", "smote", "class_weight"])
def test_every_registered_model_trains_end_to_end(cfg, toy_frame, balance):
    cfg = {**cfg, "preprocessing": {**cfg["preprocessing"], "balance": balance}}
    df = clean_dataframe(toy_frame, cfg)
    X, y = df.drop(columns=[TARGET]), df[TARGET]
    X_tr, X_te, y_tr, y_te = stratified_split(X, y, cfg)
    for name in MODEL_REGISTRY:
        cfg["models"] = [name]
        pipe = build_model_pipeline(get_models(cfg)[name], cfg)
        pipe.fit(X_tr, y_tr)
        metrics, y_pred, y_score = evaluate_on_test(pipe, X_te, y_te)
        assert set(y_pred) <= {0, 1}
        assert 0.0 <= metrics["f1"] <= 1.0
        assert 0.0 <= metrics["roc_auc"] <= 1.0, name


def test_pipeline_is_deterministic(cfg, toy_frame):
    df = clean_dataframe(toy_frame, cfg)
    X, y = df.drop(columns=[TARGET]), df[TARGET]
    X_tr, X_te, y_tr, y_te = stratified_split(X, y, cfg)
    results = []
    for _ in range(2):
        pipe = build_model_pipeline(get_models(cfg)["logistic_regression"], cfg)
        pipe.fit(X_tr, y_tr)
        results.append(evaluate_on_test(pipe, X_te, y_te)[0]["f1"])
    assert results[0] == pytest.approx(results[1])
