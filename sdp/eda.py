"""Exploratory data analysis driver.

Produces, for one dataset:
    results/<dataset>/eda/summary_statistics.csv
    results/<dataset>/eda/dataset_overview.json
    results/<dataset>/eda/*.png
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from sdp.data_loader import TARGET, load_dataset
from sdp.preprocessing import clean_dataframe
from sdp.utils import ensure_dir, get_logger, resolve_path, save_json
from sdp.visualization import (
    plot_class_distribution,
    plot_correlation_heatmap,
    plot_feature_distributions,
    plot_target_correlation,
)

log = get_logger(__name__)


def run_eda(dataset: str, cfg: dict[str, Any]) -> dict[str, Any]:
    out_dir = ensure_dir(resolve_path(cfg["results_dir"]) / dataset / "eda")

    raw = load_dataset(dataset, cfg)
    df = clean_dataframe(raw, cfg)
    X = df.drop(columns=[TARGET])

    overview = {
        "dataset": dataset,
        "rows_raw": int(len(raw)),
        "rows_after_cleaning": int(len(df)),
        "duplicates_removed": int(len(raw) - len(df)),
        "n_features": int(X.shape[1]),
        "missing_values_total": int(X.isna().sum().sum()),
        "features_with_missing": X.columns[X.isna().any()].tolist(),
        "defective_count": int(df[TARGET].sum()),
        "defective_ratio": float(df[TARGET].mean()),
        "imbalance_ratio": float((df[TARGET] == 0).sum() / max(1, df[TARGET].sum())),
        "feature_names": X.columns.tolist(),
    }
    save_json(overview, out_dir / "dataset_overview.json")

    stats = X.describe().T
    stats["skewness"] = X.skew()
    stats["missing"] = X.isna().sum()
    stats["corr_with_target"] = X.apply(lambda s: s.corr(df[TARGET]))
    stats.to_csv(out_dir / "summary_statistics.csv")

    figures = [
        plot_class_distribution(df, dataset, out_dir),
        plot_correlation_heatmap(df, dataset, out_dir),
        plot_feature_distributions(df, dataset, out_dir),
        plot_target_correlation(df, dataset, out_dir),
    ]
    log.info("EDA for %s complete -> %s (%d figures)", dataset, out_dir, len(figures))
    overview["figures"] = [str(Path(f).name) for f in figures]
    return overview
