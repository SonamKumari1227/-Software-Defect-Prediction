#!/usr/bin/env python
"""End-to-end training and evaluation pipeline.

For each selected dataset:
    1. load + clean the data
    2. stratified train/test split
    3. for every model in config.yaml:
         a. repeated stratified k-fold CV on the training set
         b. (optional) randomised hyper-parameter search
         c. fit on the full training set, evaluate on the hold-out test set
    4. save metrics (CSV + JSON), figures and the best model (joblib)

Usage
-----
    python scripts/run_pipeline.py                    # default dataset (KC1)
    python scripts/run_pipeline.py --dataset PC1
    python scripts/run_pipeline.py --all              # all four datasets + summary
    python scripts/run_pipeline.py --balance none     # override config
    python scripts/run_pipeline.py --tune             # enable RandomizedSearchCV
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV
from tabulate import tabulate

from sdp.config import load_config
from sdp.data_loader import load_dataset, split_features_target
from sdp.evaluate import (
    cross_validate_pipeline,
    evaluate_on_test,
    make_cv,
    results_table,
)
from sdp.models import DISPLAY_NAMES, PARAM_DISTRIBUTIONS, get_models
from sdp.preprocessing import build_model_pipeline, clean_dataframe, stratified_split
from sdp.utils import ensure_dir, get_logger, resolve_path, save_json, set_seed
from sdp.visualization import (
    plot_confusion_matrices,
    plot_cross_dataset_summary,
    plot_cv_boxplot,
    plot_feature_importance,
    plot_model_comparison,
    plot_pr_curves,
    plot_roc_curves,
)

log = get_logger("sdp.pipeline")


def run_dataset(dataset: str, cfg: dict[str, Any]) -> pd.DataFrame:
    """Train and evaluate every configured model on one dataset."""
    out_dir = ensure_dir(resolve_path(cfg["results_dir"]) / dataset)
    fig_dir = ensure_dir(out_dir / "figures")
    model_dir = ensure_dir(out_dir / "models")

    # ---- 1. data -----------------------------------------------------------
    df = clean_dataframe(load_dataset(dataset, cfg), cfg)
    X, y = split_features_target(df)
    X_train, X_test, y_train, y_test = stratified_split(X, y, cfg)
    log.info("Split %s: train=%d  test=%d  (defect ratio train=%.3f, test=%.3f)",
             dataset, len(X_train), len(X_test), y_train.mean(), y_test.mean())

    # ---- 2. models ---------------------------------------------------------
    records: list[dict[str, Any]] = []
    fitted: dict[str, Any] = {}
    cv_f1_scores: dict[str, np.ndarray] = {}
    tuning = cfg.get("tuning", {})

    for name, model in get_models(cfg).items():
        t0 = time.perf_counter()
        pipe = build_model_pipeline(model, cfg)

        # 2a. cross-validation on the training portion only
        cv_summary, cv_raw = cross_validate_pipeline(pipe, X_train, y_train, cfg)
        cv_f1_scores[name] = cv_raw["f1"]

        # 2b. optional hyper-parameter search
        best_params: dict[str, Any] = {}
        if tuning.get("enabled") and name in PARAM_DISTRIBUTIONS:
            search = RandomizedSearchCV(
                pipe, PARAM_DISTRIBUTIONS[name], n_iter=tuning.get("n_iter", 10), scoring="f1",
                cv=make_cv(cfg), random_state=cfg["random_seed"],
                n_jobs=cfg["cross_validation"].get("n_jobs", 1), refit=True,
            )
            search.fit(X_train, y_train)
            pipe = search.best_estimator_
            best_params = {k.replace("model__", ""): v for k, v in search.best_params_.items()}
            log.info("  tuned %s -> %s", name, best_params)
        else:
            pipe.fit(X_train, y_train)

        # 2c. hold-out evaluation
        test_metrics, _, _ = evaluate_on_test(pipe, X_test, y_test)
        elapsed = time.perf_counter() - t0

        records.append({"model": name, **test_metrics, **cv_summary,
                        "train_time_s": round(elapsed, 2), "best_params": best_params})
        fitted[name] = pipe
        joblib.dump(pipe, model_dir / f"{name}.joblib")
        log.info("  %-22s F1=%.3f  AUC=%.3f  Acc=%.3f  (%.1fs)",
                 DISPLAY_NAMES.get(name, name), test_metrics["f1"], test_metrics["roc_auc"],
                 test_metrics["accuracy"], elapsed)

    # ---- 3. results --------------------------------------------------------
    table = results_table(records)
    table.insert(0, "dataset", dataset)
    table.to_csv(out_dir / "test_metrics.csv", index=False)
    save_json(records, out_dir / "test_metrics.json")

    best = table.iloc[0]
    save_json(
        {"dataset": dataset, "best_model": best["model"], "f1": best["f1"], "roc_auc": best["roc_auc"],
         "n_train": int(len(X_train)), "n_test": int(len(X_test)), "features": X.columns.tolist(),
         "balance": cfg["preprocessing"]["balance"], "seed": cfg["random_seed"]},
        out_dir / "run_summary.json",
    )

    # ---- 4. figures --------------------------------------------------------
    plot_roc_curves(fitted, X_test, y_test, dataset, fig_dir)
    plot_pr_curves(fitted, X_test, y_test, dataset, fig_dir)
    plot_confusion_matrices(fitted, X_test, y_test, dataset, fig_dir)
    plot_model_comparison(table, dataset, fig_dir)
    plot_cv_boxplot(cv_f1_scores, dataset, fig_dir, metric="f1")
    if "random_forest" in fitted:
        plot_feature_importance(fitted["random_forest"], X.columns.tolist(), dataset, fig_dir)

    # ---- 5. console summary ------------------------------------------------
    show = table[["model", "accuracy", "precision", "recall", "f1", "roc_auc", "mcc", "pf"]].copy()
    show["model"] = show["model"].map(lambda m: DISPLAY_NAMES.get(m, m))
    print(f"\n=== {dataset}: hold-out test results (sorted by F1) ===")
    print(tabulate(show, headers="keys", floatfmt=".4f", showindex=False, tablefmt="github"))
    print(f"Best model: {DISPLAY_NAMES.get(best['model'], best['model'])}  "
          f"(F1={best['f1']:.4f}, ROC-AUC={best['roc_auc']:.4f})\n")
    return table


def summarise_all(tables: list[pd.DataFrame], cfg: dict[str, Any]) -> None:
    """Combine per-dataset tables into one CSV plus cross-dataset heatmaps."""
    results_dir = resolve_path(cfg["results_dir"])
    summary = pd.concat(tables, ignore_index=True)
    summary.to_csv(results_dir / "summary_all_datasets.csv", index=False)
    for metric in ("f1", "roc_auc"):
        plot_cross_dataset_summary(summary, results_dir, metric=metric)

    mean_rank = (
        summary.groupby("dataset")["f1"].rank(ascending=False)
        .groupby(summary["model"]).mean().sort_values()
    )
    print("=== Mean F1 rank across datasets (lower is better) ===")
    print(tabulate(mean_rank.reset_index().rename(columns={"f1": "mean_rank"}),
                   headers="keys", floatfmt=".2f", showindex=False, tablefmt="github"))
    log.info("Cross-dataset summary written to %s", results_dir / "summary_all_datasets.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", help="Dataset name (default from config.yaml)")
    parser.add_argument("--all", action="store_true", help="Run every dataset in config.yaml")
    parser.add_argument("--balance", choices=["none", "smote", "class_weight"], help="Override balancing mode")
    parser.add_argument("--tune", action="store_true", help="Enable RandomizedSearchCV hyper-parameter tuning")
    parser.add_argument("--config", type=Path, help="Alternative config file")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.balance:
        cfg["preprocessing"]["balance"] = args.balance
    if args.tune:
        cfg["tuning"]["enabled"] = True
    set_seed(cfg["random_seed"])

    names = cfg["datasets"]["names"] if args.all else [args.dataset or cfg["datasets"]["default"]]
    tables = [run_dataset(name, cfg) for name in names]
    if len(tables) > 1:
        summarise_all(tables, cfg)


if __name__ == "__main__":
    main()
