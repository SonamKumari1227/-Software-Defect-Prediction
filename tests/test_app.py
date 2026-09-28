"""Tests for the logic behind the web interface.

The Streamlit layout itself is exercised manually; what is tested here is the
computation the form depends on, namely the derivation of the Halstead
measures from the four basic operator and operand counts, and the ability of
the saved pipelines to score a single hand-entered module.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import joblib
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

from sdp.evaluate import get_scores  # noqa: E402
from sdp.utils import load_json  # noqa: E402


def derive(n1: float, n2: float, big_n1: float, big_n2: float) -> dict[str, float]:
    n, length = n1 + n2, big_n1 + big_n2
    volume = length * math.log2(n) if n > 1 else 0.0
    difficulty = (n1 / 2) * (big_n2 / n2) if n2 else 0.0
    effort = difficulty * volume
    return {"length": length, "volume": volume, "difficulty": difficulty,
            "effort": effort, "level": 1 / difficulty if difficulty else 0.0,
            "time": effort / 18, "bugs": volume / 3000}


def test_halstead_length_is_the_sum_of_the_token_counts():
    assert derive(10, 11, 28, 17)["length"] == 45


def test_halstead_volume_matches_the_definition():
    d = derive(10, 11, 28, 17)
    assert d["volume"] == pytest.approx(45 * math.log2(21), rel=1e-9)


def test_halstead_difficulty_and_level_are_reciprocal():
    d = derive(10, 11, 28, 17)
    assert d["difficulty"] == pytest.approx((10 / 2) * (17 / 11), rel=1e-9)
    assert d["level"] == pytest.approx(1 / d["difficulty"], rel=1e-9)


def test_halstead_effort_time_and_bugs_follow_from_volume_and_difficulty():
    d = derive(18, 33, 124, 75)
    assert d["effort"] == pytest.approx(d["difficulty"] * d["volume"], rel=1e-9)
    assert d["time"] == pytest.approx(d["effort"] / 18, rel=1e-9)
    assert d["bugs"] == pytest.approx(d["volume"] / 3000, rel=1e-9)


def test_degenerate_counts_do_not_raise():
    d = derive(0, 0, 0, 0)
    assert d["volume"] == 0 and d["difficulty"] == 0 and d["level"] == 0


def _presets():
    """The two starting points the form offers, taken from the training data.

    Percentiles of the real dataset are used rather than an arbitrary constant
    vector, because the metrics are not independent: a module cannot have a
    Halstead level of 100, and feeding a physically impossible combination to
    the model tests nothing.
    """
    from sdp.config import load_config
    from sdp.data_loader import TARGET, load_dataset
    from sdp.preprocessing import clean_dataframe

    cfg = load_config()
    ref = clean_dataframe(load_dataset("KC1", cfg), cfg)
    feats = [c for c in ref.columns if c != TARGET]
    small = pd.DataFrame([ref[feats].quantile(0.10)], columns=feats)
    large = pd.DataFrame([ref[feats].quantile(0.90)], columns=feats)
    return feats, small, large


@pytest.mark.parametrize("model_name", ["gradient_boosting", "random_forest"])
def test_saved_pipeline_scores_a_single_manually_entered_module(model_name):
    """The form submits exactly one row; the pipeline must accept that."""
    run = ROOT / "results" / "KC1"
    if not (run / "models" / f"{model_name}.joblib").exists():
        pytest.skip("models not built; run scripts/run_pipeline.py --dataset KC1")

    features = load_json(run / "run_summary.json")["features"]
    pipe = joblib.load(run / "models" / f"{model_name}.joblib")
    feats, small, large = _presets()
    assert feats == features

    for frame in (small, large):
        score = float(get_scores(pipe, frame)[0])
        assert 0.0 <= score <= 1.0

    # a large, complex module must score higher than a small, simple one
    assert float(get_scores(pipe, large)[0]) > float(get_scores(pipe, small)[0])
