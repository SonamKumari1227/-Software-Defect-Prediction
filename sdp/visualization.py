"""Every figure used in the report, produced with a consistent style.

All functions save a PNG to *out_dir* and return the path. Nothing is shown
interactively so the pipeline can run headless (servers, CI, notebooks).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # headless backend - must precede pyplot import

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    ConfusionMatrixDisplay,
    PrecisionRecallDisplay,
    RocCurveDisplay,
)

from sdp.data_loader import TARGET  # noqa: E402
from sdp.models import DISPLAY_NAMES  # noqa: E402
from sdp.utils import ensure_dir  # noqa: E402

sns.set_theme(style="whitegrid", context="paper", font_scale=1.1)
DPI = 150


def _save(fig: plt.Figure, out_dir: Path, name: str) -> Path:
    path = ensure_dir(out_dir) / f"{name}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# EDA figures
# --------------------------------------------------------------------------- #
def plot_class_distribution(df: pd.DataFrame, dataset: str, out_dir: Path) -> Path:
    counts = df[TARGET].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    bars = ax.bar(["Non-defective (0)", "Defective (1)"], counts.values, color=["#4C72B0", "#C44E52"])
    for b, v in zip(bars, counts.values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v}\n({100*v/len(df):.1f}%)", ha="center", va="bottom")
    ax.set_ylabel("Number of modules")
    ax.set_title(f"{dataset}: class distribution")
    return _save(fig, out_dir, "class_distribution")


def plot_correlation_heatmap(df: pd.DataFrame, dataset: str, out_dir: Path) -> Path:
    corr = df.drop(columns=[TARGET]).corr(method="spearman")
    n = len(corr)
    fig, ax = plt.subplots(figsize=(max(7, 0.35 * n), max(6, 0.32 * n)))
    sns.heatmap(corr, cmap="coolwarm", center=0, vmin=-1, vmax=1, square=True,
                cbar_kws={"shrink": 0.7}, ax=ax, xticklabels=True, yticklabels=True)
    ax.tick_params(axis="both", labelsize=7)
    ax.set_title(f"{dataset}: Spearman correlation between metrics")
    return _save(fig, out_dir, "correlation_heatmap")


def plot_feature_distributions(df: pd.DataFrame, dataset: str, out_dir: Path, top_n: int = 12) -> Path:
    """Box plots (log scale) of the features most associated with defects."""
    X = df.drop(columns=[TARGET])
    # Rank features by absolute point-biserial correlation with the target.
    corr = X.apply(lambda s: s.corr(df[TARGET])).abs().sort_values(ascending=False)
    feats = corr.index[:top_n].tolist()

    ncols = 4
    nrows = int(np.ceil(len(feats) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.6 * ncols, 2.8 * nrows))
    for ax, feat in zip(axes.ravel(), feats):
        sns.boxplot(data=df, x=TARGET, y=feat, hue=TARGET, palette=["#4C72B0", "#C44E52"],
                    legend=False, ax=ax, fliersize=1.5)
        ax.set_yscale("symlog")
        ax.set_ylim(bottom=0)  # metrics are non-negative; hide the mirrored negative ticks
        ax.set_xlabel("")
        ax.set_xticks([0, 1], ["Non-def.", "Defective"])
        ax.set_title(feat, fontsize=9)
    for ax in axes.ravel()[len(feats):]:
        ax.axis("off")
    fig.suptitle(f"{dataset}: metric distributions by class (top {len(feats)} by correlation)")
    return _save(fig, out_dir, "feature_distributions")


def plot_target_correlation(df: pd.DataFrame, dataset: str, out_dir: Path) -> Path:
    X = df.drop(columns=[TARGET])
    corr = X.apply(lambda s: s.corr(df[TARGET])).sort_values()
    fig, ax = plt.subplots(figsize=(6, max(4, 0.25 * len(corr))))
    colors = ["#C44E52" if v > 0 else "#4C72B0" for v in corr.values]
    ax.barh(corr.index, corr.values, color=colors)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("Point-biserial correlation with 'defective'")
    ax.set_title(f"{dataset}: feature-target correlation")
    ax.tick_params(axis="y", labelsize=7)
    return _save(fig, out_dir, "target_correlation")


# --------------------------------------------------------------------------- #
# Model-evaluation figures
# --------------------------------------------------------------------------- #
def plot_roc_curves(fitted: dict[str, Any], X_test: pd.DataFrame, y_test: pd.Series,
                    dataset: str, out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6, 5))
    for name, pipe in fitted.items():
        RocCurveDisplay.from_estimator(pipe, X_test, y_test, name=DISPLAY_NAMES.get(name, name), ax=ax)
    ax.plot([0, 1], [0, 1], "k--", lw=0.8, label="Chance")
    ax.set_title(f"{dataset}: ROC curves (hold-out test set)")
    ax.legend(fontsize=7, loc="lower right")
    return _save(fig, out_dir, "roc_curves")


def plot_pr_curves(fitted: dict[str, Any], X_test: pd.DataFrame, y_test: pd.Series,
                   dataset: str, out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6, 5))
    for name, pipe in fitted.items():
        PrecisionRecallDisplay.from_estimator(pipe, X_test, y_test, name=DISPLAY_NAMES.get(name, name), ax=ax)
    ax.axhline(y_test.mean(), color="k", ls="--", lw=0.8, label=f"Baseline ({y_test.mean():.2f})")
    ax.set_title(f"{dataset}: precision-recall curves (hold-out test set)")
    ax.legend(fontsize=7, loc="upper right")
    return _save(fig, out_dir, "pr_curves")


def plot_confusion_matrices(fitted: dict[str, Any], X_test: pd.DataFrame, y_test: pd.Series,
                            dataset: str, out_dir: Path) -> Path:
    n = len(fitted)
    ncols = 4
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.4 * ncols, 3.2 * nrows))
    for ax, (name, pipe) in zip(np.ravel(axes), fitted.items()):
        ConfusionMatrixDisplay.from_estimator(pipe, X_test, y_test, ax=ax, colorbar=False,
                                              cmap="Blues", display_labels=["Non-def.", "Defective"])
        ax.set_title(DISPLAY_NAMES.get(name, name), fontsize=9)
    for ax in np.ravel(axes)[n:]:
        ax.axis("off")
    fig.suptitle(f"{dataset}: confusion matrices (hold-out test set)")
    return _save(fig, out_dir, "confusion_matrices")


def plot_model_comparison(table: pd.DataFrame, dataset: str, out_dir: Path,
                          metrics: tuple[str, ...] = ("accuracy", "precision", "recall", "f1", "roc_auc")) -> Path:
    melted = table.melt(id_vars="model", value_vars=list(metrics), var_name="metric", value_name="score")
    melted["model"] = melted["model"].map(lambda m: DISPLAY_NAMES.get(m, m))
    fig, ax = plt.subplots(figsize=(10, 4.5))
    sns.barplot(data=melted, x="model", y="score", hue="metric", ax=ax, palette="viridis")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("")
    ax.set_ylabel("Score")
    ax.set_title(f"{dataset}: model comparison on hold-out test set")
    ax.tick_params(axis="x", rotation=25)
    ax.legend(ncol=len(metrics), fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.25))
    return _save(fig, out_dir, "model_comparison")


def plot_cv_boxplot(cv_scores: dict[str, np.ndarray], dataset: str, out_dir: Path, metric: str = "f1") -> Path:
    data = pd.DataFrame({DISPLAY_NAMES.get(k, k): v for k, v in cv_scores.items()})
    fig, ax = plt.subplots(figsize=(9, 4))
    sns.boxplot(data=data, ax=ax, palette="Set2")
    ax.set_ylabel(metric.upper())
    ax.set_title(f"{dataset}: cross-validated {metric.upper()} per model")
    ax.tick_params(axis="x", rotation=25)
    return _save(fig, out_dir, f"cv_{metric}_boxplot")


def plot_feature_importance(pipe: Any, feature_names: list[str], dataset: str, out_dir: Path,
                            model_name: str = "random_forest", top_n: int = 15) -> Path | None:
    model = pipe.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        return None
    imp = pd.Series(model.feature_importances_, index=feature_names).sort_values(ascending=True).tail(top_n)
    fig, ax = plt.subplots(figsize=(6, 0.3 * top_n + 1.5))
    ax.barh(imp.index, imp.values, color="#55A868")
    ax.set_xlabel("Mean decrease in impurity")
    ax.set_title(f"{dataset}: top-{top_n} features ({DISPLAY_NAMES.get(model_name, model_name)})")
    ax.tick_params(axis="y", labelsize=8)
    return _save(fig, out_dir, "feature_importance")


def plot_cross_dataset_summary(summary: pd.DataFrame, out_dir: Path, metric: str = "f1") -> Path:
    """Heatmap of *metric* for every (dataset, model) pair."""
    pivot = summary.pivot(index="model", columns="dataset", values=metric)
    pivot.index = [DISPLAY_NAMES.get(m, m) for m in pivot.index]
    fig, ax = plt.subplots(figsize=(1.6 * len(pivot.columns) + 3, 0.5 * len(pivot) + 1.5))
    sns.heatmap(pivot, annot=True, fmt=".3f", cmap="YlGnBu", vmin=0, vmax=1, ax=ax)
    ax.set_title(f"{metric.upper()} across datasets and models (hold-out test set)")
    ax.set_xlabel("")
    ax.set_ylabel("")
    return _save(fig, out_dir, f"cross_dataset_{metric}")
