#!/usr/bin/env python
"""Generate the additional diagrams, analyses and console screenshots used by the
expanded project report.

Produces into report/figures/:
    shot_*.png              console screenshots of real program output
    fig_kfold.png           stratified k-fold cross-validation schematic
    fig_split_flow.png      train/test split and where SMOTE is applied
    fig_schema.png          dataset schema (entity-relationship style)
    fig_package.png         package / class structure of the sdp package
    fig_sequence.png        sequence diagram of one training run
    fig_imbalance_all.png   defect ratio across the four datasets
    fig_learning_curve.png  real learning curves (KC1)
    fig_threshold.png       real precision/recall/F1 against decision threshold (KC1)
    fig_confmatrix_expl.png confusion-matrix terminology
    plus EDA and evaluation figures for JM1, PC1 and CM1

Usage:  python scripts/make_extra_figures.py
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import _bootstrap  # noqa: F401
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

from sdp.config import load_config  # noqa: E402
from sdp.data_loader import load_dataset, split_features_target  # noqa: E402
from sdp.evaluate import get_scores  # noqa: E402
from sdp.models import get_model  # noqa: E402
from sdp.preprocessing import build_model_pipeline, clean_dataframe, stratified_split  # noqa: E402
from sdp.utils import PROJECT_ROOT, ensure_dir, set_seed  # noqa: E402

OUT = ensure_dir(PROJECT_ROOT / "report" / "figures")
CAP = PROJECT_ROOT / "report" / "captures"
RESULTS = PROJECT_ROOT / "results"
FONT = "Helvetica"
MONO = "DejaVu Sans Mono"


def dot(name: str, source: str) -> None:
    subprocess.run(["dot", "-Tpng", "-Gdpi=170", "-o", str(OUT / f"{name}.png")],
                   input=source.encode("utf-8"), check=True)
    print("wrote", name + ".png")


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(OUT / f"{name}.png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name + ".png")


# --------------------------------------------------------------------------- #
# Console screenshots
# --------------------------------------------------------------------------- #
def screenshot(name: str, command: str, text: str, max_lines: int = 40) -> None:
    """Render captured console output as a terminal-style image."""
    lines = [ln.rstrip() for ln in text.strip("\n").split("\n")][:max_lines]
    body = [f"$ {command}", ""] + lines
    width = max(len(ln) for ln in body) + 2

    char_w, line_h = 0.088, 0.205
    fig_w = max(6.5, width * char_w)
    fig_h = (len(body) + 2) * line_h + 0.45

    fig = plt.figure(figsize=(fig_w, fig_h), facecolor="#1E1E2E")
    ax = fig.add_axes((0, 0, 1, 1)); ax.set_axis_off()
    ax.set_xlim(0, fig_w); ax.set_ylim(0, fig_h)

    # title bar with the three window buttons
    ax.add_patch(Rectangle((0, fig_h - 0.42), fig_w, 0.42, facecolor="#313244"))
    for i, c in enumerate(("#F38BA8", "#F9E2AF", "#A6E3A1")):
        ax.add_patch(plt.Circle((0.28 + i * 0.26, fig_h - 0.21), 0.075, facecolor=c))
    ax.text(fig_w / 2, fig_h - 0.21, "Command Prompt  —  software-defect-prediction",
            color="#CDD6F4", fontsize=8.5, ha="center", va="center", family=MONO)

    y = fig_h - 0.72
    for ln in body:
        if ln.startswith("$ "):
            ax.text(0.22, y, "$", color="#A6E3A1", fontsize=9, va="center", family=MONO)
            ax.text(0.42, y, ln[2:], color="#89B4FA", fontsize=9, va="center", family=MONO)
        else:
            colour = "#CDD6F4"
            if "INFO" in ln:
                colour = "#9399B2"
            elif "passed" in ln or "Best model" in ln:
                colour = "#A6E3A1"
            elif ln.startswith("|") or ln.startswith("+") or ln.startswith("==="):
                colour = "#F9E2AF"
            ax.text(0.22, y, ln, color=colour, fontsize=9, va="center", family=MONO)
        y -= line_h

    save(fig, name)


def all_screenshots() -> None:
    jobs = [
        ("shot_download", "python scripts/download_data.py", "download.txt", 14),
        ("shot_eda", "python scripts/run_eda.py --dataset KC1", "eda_kc1.txt", 24),
        ("shot_pipeline", "python scripts/run_pipeline.py --dataset KC1", "pipeline_kc1.txt", 16),
        ("shot_pytest", "python -m pytest -q", "pytest.txt", 6),
        ("shot_predict", "python scripts/predict.py --dataset KC1 --model gradient_boosting "
                         "--input data/sample_modules.csv", "predict.txt", 6),
    ]
    for name, cmd, fname, n in jobs:
        path = CAP / fname
        if path.exists():
            screenshot(name, cmd, path.read_text(encoding="utf-8", errors="ignore"), n)
        else:
            print("WARNING - missing capture", path)

    tree = """software-defect-prediction/
├── config.yaml
├── requirements.txt
├── README.md
├── sdp/
│   ├── __init__.py       ├── models.py
│   ├── config.py         ├── evaluate.py
│   ├── utils.py          ├── visualization.py
│   ├── data_loader.py    └── eda.py
│   └── preprocessing.py
├── scripts/
│   ├── download_data.py  ├── run_pipeline.py
│   ├── run_eda.py        └── predict.py
├── tests/test_pipeline.py
├── data/raw/cleaned/     KC1.arff JM1.arff PC1.arff CM1.arff
├── results/              KC1/ JM1/ PC1/ CM1/ summary_all_datasets.csv
└── report/"""
    screenshot("shot_tree", "tree /F", tree, 30)


# --------------------------------------------------------------------------- #
# Conceptual diagrams
# --------------------------------------------------------------------------- #
def fig_kfold() -> None:
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    k, n = 5, 10
    for fold in range(k):
        y = k - fold - 1
        for blk in range(n):
            val = (blk // 2) == fold
            ax.add_patch(Rectangle((blk, y), 0.94, 0.8,
                                   facecolor="#C44E52" if val else "#4C72B0", alpha=0.9))
        ax.text(-0.25, y + 0.4, f"Fold {fold + 1}", ha="right", va="center", fontsize=10)
        ax.text(n + 0.25, y + 0.4, "train 80 % / validate 20 %", ha="left", va="center", fontsize=8.5, color="#555")
    ax.add_patch(Rectangle((0, -1.15), 0.94, 0.55, facecolor="#4C72B0"))
    ax.text(1.15, -0.88, "Training partition of the fold", va="center", fontsize=9)
    ax.add_patch(Rectangle((5.0, -1.15), 0.94, 0.55, facecolor="#C44E52"))
    ax.text(6.15, -0.88, "Validation partition of the fold", va="center", fontsize=9)
    ax.set_xlim(-2.2, n + 3.4); ax.set_ylim(-1.5, k + 0.3); ax.axis("off")
    ax.set_title("Stratified 5-fold cross-validation: each block keeps the 25 % / 75 % class ratio", fontsize=10.5)
    save(fig, "fig_kfold")


def fig_split_flow() -> None:
    dot("fig_split_flow", f"""
digraph G {{
  rankdir=LR; nodesep=0.35; ranksep=0.5;
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=10, margin="0.16,0.08"];
  edge [color="#2F5597", arrowsize=0.8, fontname="{FONT}", fontsize=9];

  all  [label="Cleaned dataset\\n1,162 modules\\n294 defective (25.3 %)", fillcolor="#FFF2CC"];
  tr   [label="Training set\\n929 modules\\n235 defective", fillcolor="#E2F0D9"];
  te   [label="Test set\\n233 modules\\n59 defective", fillcolor="#FBE5D6"];
  sm   [label="After SMOTE\\n1,388 modules\\n694 defective (50 %)", fillcolor="#E2F0D9", color="#C55A11", penwidth=1.6];
  fit  [label="Model fitting", fillcolor="#EAF2FB"];
  ev   [label="Final evaluation\\n(never resampled)", fillcolor="#EAF2FB"];

  all -> tr [label="80 %, stratified"];
  all -> te [label="20 %, stratified"];
  tr -> sm [label="oversample\\nminority only"];
  sm -> fit; fit -> ev; te -> ev [style=dashed];
}}
""")


def fig_schema() -> None:
    dot("fig_schema", f"""
digraph G {{
  rankdir=LR; nodesep=0.4; ranksep=0.7;
  node [shape=plaintext, fontname="{FONT}", fontsize=10];
  edge [color="#2F5597", fontname="{FONT}", fontsize=9];

  ds [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="4">
      <tr><td bgcolor="#2F5597"><font color="white"><b>DATASET</b></font></td></tr>
      <tr><td align="left"><u>dataset_id</u> : text (PK)</td></tr>
      <tr><td align="left">name : KC1 | JM1 | PC1 | CM1</td></tr>
      <tr><td align="left">language : C | C++</td></tr>
      <tr><td align="left">n_modules : integer</td></tr>
      <tr><td align="left">n_features : integer</td></tr>
      <tr><td align="left">defect_ratio : real</td></tr></table>>];

  mod [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="4">
      <tr><td bgcolor="#2F5597"><font color="white"><b>MODULE  (one row of the ARFF file)</b></font></td></tr>
      <tr><td align="left"><u>module_id</u> : integer (PK)</td></tr>
      <tr><td align="left">dataset_id : text (FK)</td></tr>
      <tr><td align="left">loc_total, loc_executable, loc_comments : integer</td></tr>
      <tr><td align="left">cyclomatic_complexity, design_complexity : integer</td></tr>
      <tr><td align="left">essential_complexity, branch_count : integer</td></tr>
      <tr><td align="left">num_operators, num_operands : integer</td></tr>
      <tr><td align="left">halstead_volume, halstead_difficulty, halstead_effort : real</td></tr>
      <tr><td align="left"><b>defective</b> : {{0, 1}}  &#8592; target</td></tr></table>>];

  mdl [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="4">
      <tr><td bgcolor="#548235"><font color="white"><b>MODEL</b></font></td></tr>
      <tr><td align="left"><u>model_id</u> : text (PK)</td></tr>
      <tr><td align="left">algorithm : text</td></tr>
      <tr><td align="left">balance_mode : none | smote | class_weight</td></tr>
      <tr><td align="left">random_seed : integer</td></tr></table>>];

  pred [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="4">
      <tr><td bgcolor="#C55A11"><font color="white"><b>PREDICTION</b></font></td></tr>
      <tr><td align="left">module_id : integer (FK)</td></tr>
      <tr><td align="left">model_id : text (FK)</td></tr>
      <tr><td align="left">defect_probability : real</td></tr>
      <tr><td align="left">predicted_defective : {{0, 1}}</td></tr></table>>];

  ds -> mod [label="1 : N  contains"];
  mod -> pred [label="1 : N  receives"];
  mdl -> pred [label="1 : N  produces"];
  ds -> mdl [label="1 : N  trains", style=dashed];
}}
""")


def fig_package() -> None:
    dot("fig_package", f"""
digraph G {{
  rankdir=TB; nodesep=0.3; ranksep=0.45;
  node [shape=plaintext, fontname="{FONT}", fontsize=9.5];
  edge [color="#555555", arrowsize=0.7, style=dashed];

  loader [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="3">
    <tr><td bgcolor="#EAF2FB"><b>data_loader</b></td></tr>
    <tr><td align="left">download_dataset(name, cfg)</td></tr>
    <tr><td align="left">read_arff(path)</td></tr>
    <tr><td align="left">load_dataset(name, cfg)</td></tr>
    <tr><td align="left">split_features_target(df)</td></tr></table>>];

  prep [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="3">
    <tr><td bgcolor="#E2F0D9"><b>preprocessing</b></td></tr>
    <tr><td align="left">clean_dataframe(df, cfg)</td></tr>
    <tr><td align="left">stratified_split(X, y, cfg)</td></tr>
    <tr><td align="left">preprocessing_steps(cfg)</td></tr>
    <tr><td align="left">build_model_pipeline(model, cfg)</td></tr></table>>];

  models [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="3">
    <tr><td bgcolor="#FFF2CC"><b>models</b></td></tr>
    <tr><td align="left">MODEL_REGISTRY : dict</td></tr>
    <tr><td align="left">PARAM_DISTRIBUTIONS : dict</td></tr>
    <tr><td align="left">get_model(name, seed, balance)</td></tr>
    <tr><td align="left">get_models(cfg)</td></tr></table>>];

  ev [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="3">
    <tr><td bgcolor="#FBE5D6"><b>evaluate</b></td></tr>
    <tr><td align="left">compute_metrics(y, yhat, score)</td></tr>
    <tr><td align="left">cross_validate_pipeline(...)</td></tr>
    <tr><td align="left">evaluate_on_test(...)</td></tr>
    <tr><td align="left">results_table(records)</td></tr></table>>];

  vis [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="3">
    <tr><td bgcolor="#EDEDED"><b>visualization</b></td></tr>
    <tr><td align="left">plot_class_distribution(...)</td></tr>
    <tr><td align="left">plot_roc_curves(...)</td></tr>
    <tr><td align="left">plot_confusion_matrices(...)</td></tr>
    <tr><td align="left">plot_feature_importance(...)</td></tr></table>>];

  utils [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="3">
    <tr><td bgcolor="#EDEDED"><b>utils / config</b></td></tr>
    <tr><td align="left">get_logger(name)</td></tr>
    <tr><td align="left">set_seed(seed)</td></tr>
    <tr><td align="left">load_config(path)</td></tr></table>>];

  prep -> loader; ev -> models; vis -> models; loader -> utils; prep -> utils; ev -> utils;
}}
""")


def fig_sequence() -> None:
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    actors = ["run_pipeline", "data_loader", "preprocessing", "models", "evaluate", "visualization"]
    xs = np.linspace(0.8, 9.2, len(actors))
    top, bottom = 9.0, 0.6
    for x, a in zip(xs, actors):
        ax.add_patch(Rectangle((x - 0.62, top), 1.24, 0.5, facecolor="#EAF2FB", edgecolor="#2F5597"))
        ax.text(x, top + 0.25, a, ha="center", va="center", fontsize=8.5)
        ax.plot([x, x], [bottom, top], color="#999", lw=0.9, ls="--", zorder=0)

    msgs = [
        (0, 1, "load_dataset(name)", 8.4),
        (1, 0, "DataFrame", 7.9),
        (0, 2, "clean_dataframe(df)", 7.4),
        (0, 2, "stratified_split(X, y)", 6.9),
        (2, 0, "X_train, X_test, y_train, y_test", 6.4),
        (0, 3, "get_models(cfg)", 5.9),
        (0, 2, "build_model_pipeline(model)", 5.4),
        (0, 4, "cross_validate_pipeline(...)", 4.9),
        (4, 0, "mean ± std per metric", 4.4),
        (0, 4, "evaluate_on_test(pipe, X_test)", 3.9),
        (4, 0, "Accuracy, F1, ROC-AUC, MCC, PF", 3.4),
        (0, 5, "plot_roc_curves / confusion / importance", 2.9),
        (5, 0, "PNG files written", 2.4),
        (0, 0, "joblib.dump(pipeline) and CSV/JSON export", 1.7),
    ]
    for src, dst, label, y in msgs:
        x1, x2 = xs[src], xs[dst]
        if src == dst:
            ax.add_patch(FancyArrowPatch((x1, y + 0.16), (x1, y - 0.16), arrowstyle="-|>",
                                         connectionstyle="arc3,rad=2.6", color="#2F5597", mutation_scale=9))
            ax.text(x1 + 0.55, y, label, fontsize=8, va="center")
        else:
            style = "-|>" if src < dst else "-|>"
            colour = "#2F5597" if src < dst else "#777777"
            ls = "-" if src < dst else "--"
            ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle=style, color=colour,
                                         linestyle=ls, mutation_scale=10, lw=1.0))
            ax.text((x1 + x2) / 2, y + 0.13, label, fontsize=8, ha="center")
    ax.set_xlim(0, 10.5); ax.set_ylim(0.2, 9.9); ax.axis("off")
    ax.set_title("Sequence of calls during one execution of run_pipeline.py", fontsize=10.5)
    save(fig, "fig_sequence")


def fig_confmatrix_expl() -> None:
    fig, ax = plt.subplots(figsize=(6.6, 4.3))
    cells = [((0, 1), "True Positive (TP)\ndefective module\ncorrectly flagged", "#A9D08E"),
             ((1, 1), "False Negative (FN)\ndefect missed\n(costly escape)", "#F4B183"),
             ((0, 0), "False Positive (FP)\nclean module flagged\n(wasted review)", "#FFE699"),
             ((1, 0), "True Negative (TN)\nclean module\ncorrectly passed", "#A9D08E")]
    for (cx, cy), text, colour in cells:
        ax.add_patch(Rectangle((cx, cy), 1, 1, facecolor=colour, edgecolor="k", lw=1.1))
        ax.text(cx + 0.5, cy + 0.5, text, ha="center", va="center", fontsize=9)
    ax.text(0.5, 2.12, "Predicted: defective", ha="center", fontsize=10, weight="bold")
    ax.text(1.5, 2.12, "Predicted: non-defective", ha="center", fontsize=10, weight="bold")
    ax.text(-0.09, 1.5, "Actually\ndefective", ha="right", va="center", fontsize=10, weight="bold")
    ax.text(-0.09, 0.5, "Actually\nnon-defective", ha="right", va="center", fontsize=10, weight="bold")
    ax.text(1.0, -0.42, "Recall = TP / (TP + FN)      Precision = TP / (TP + FP)      PF = FP / (FP + TN)",
            ha="center", fontsize=9.5)
    ax.set_xlim(-1.05, 2.15); ax.set_ylim(-0.7, 2.4); ax.axis("off")
    save(fig, "fig_confmatrix_expl")


# --------------------------------------------------------------------------- #
# Real analyses
# --------------------------------------------------------------------------- #
def fig_imbalance_all(cfg) -> None:
    rows = []
    for name in ["KC1", "JM1", "PC1", "CM1"]:
        df = clean_dataframe(load_dataset(name, cfg), cfg)
        rows.append((name, len(df), int(df["defective"].sum())))
    df = pd.DataFrame(rows, columns=["dataset", "total", "defective"])
    df["clean"] = df.total - df.defective
    df["pct"] = 100 * df.defective / df.total

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.2, 4.0))
    idx = np.arange(len(df))
    a1.bar(idx, df.clean, label="Non-defective", color="#4C72B0")
    a1.bar(idx, df.defective, bottom=df.clean, label="Defective", color="#C44E52")
    a1.set_xticks(idx, df.dataset); a1.set_ylabel("Number of modules")
    a1.set_title("Composition of each dataset"); a1.legend(fontsize=8.5)
    for i, r in df.iterrows():
        a1.text(i, r.total, f"{r.total:,}", ha="center", va="bottom", fontsize=8.5)

    bars = a2.bar(idx, df.pct, color="#C44E52")
    a2.set_xticks(idx, df.dataset); a2.set_ylabel("Defective modules (%)")
    a2.set_title("Class imbalance across datasets"); a2.set_ylim(0, 30)
    for b, v in zip(bars, df.pct):
        a2.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f} %", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    save(fig, "fig_imbalance_all")


def fig_learning_curve(cfg) -> None:
    from sklearn.model_selection import learning_curve

    df = clean_dataframe(load_dataset("KC1", cfg), cfg)
    X, y = split_features_target(df)
    X_train, _, y_train, _ = stratified_split(X, y, cfg)

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.1), sharey=True)
    for ax, name in zip(axes, ["gradient_boosting", "random_forest"]):
        pipe = build_model_pipeline(get_model(name, cfg["random_seed"], "smote"), cfg)
        sizes, train_sc, val_sc = learning_curve(
            pipe, X_train, y_train, cv=5, scoring="f1", n_jobs=1,
            train_sizes=np.linspace(0.15, 1.0, 8), random_state=cfg["random_seed"])
        ax.plot(sizes, train_sc.mean(1), "o-", color="#4C72B0", label="Training F1")
        ax.fill_between(sizes, train_sc.mean(1) - train_sc.std(1), train_sc.mean(1) + train_sc.std(1),
                        alpha=0.15, color="#4C72B0")
        ax.plot(sizes, val_sc.mean(1), "s-", color="#C44E52", label="Cross-validated F1")
        ax.fill_between(sizes, val_sc.mean(1) - val_sc.std(1), val_sc.mean(1) + val_sc.std(1),
                        alpha=0.15, color="#C44E52")
        ax.set_xlabel("Number of training modules")
        ax.set_title({"gradient_boosting": "Gradient Boosting", "random_forest": "Random Forest"}[name])
        ax.legend(fontsize=8.5); ax.grid(alpha=0.3)
    axes[0].set_ylabel("F1-score")
    fig.suptitle("Learning curves on KC1: the gap indicates variance, the plateau indicates data sufficiency",
                 fontsize=10.5)
    fig.tight_layout()
    save(fig, "fig_learning_curve")


def fig_threshold(cfg) -> None:
    from sklearn.metrics import f1_score, precision_score, recall_score

    df = clean_dataframe(load_dataset("KC1", cfg), cfg)
    X, y = split_features_target(df)
    X_train, X_test, y_train, y_test = stratified_split(X, y, cfg)
    pipe = build_model_pipeline(get_model("gradient_boosting", cfg["random_seed"], "smote"), cfg)
    pipe.fit(X_train, y_train)
    proba = get_scores(pipe, X_test)

    ts = np.linspace(0.05, 0.95, 91)
    pr = [precision_score(y_test, proba >= t, zero_division=0) for t in ts]
    rc = [recall_score(y_test, proba >= t, zero_division=0) for t in ts]
    f1 = [f1_score(y_test, proba >= t, zero_division=0) for t in ts]
    best = ts[int(np.argmax(f1))]

    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.plot(ts, pr, label="Precision", color="#4C72B0")
    ax.plot(ts, rc, label="Recall", color="#C44E52")
    ax.plot(ts, f1, label="F1-score", color="#55A868", lw=2.2)
    ax.axvline(0.5, ls="--", color="grey", lw=1, label="Default threshold (0.50)")
    ax.axvline(best, ls=":", color="#55A868", lw=1.6, label=f"F1-optimal threshold ({best:.2f})")
    ax.set_xlabel("Decision threshold on the predicted defect probability")
    ax.set_ylabel("Score")
    ax.set_title("KC1, Gradient Boosting: the threshold trades recall against precision")
    ax.legend(fontsize=8.5); ax.grid(alpha=0.3)
    fig.tight_layout()
    save(fig, "fig_threshold")
    print(f"  (F1-optimal threshold = {best:.2f}, F1 = {max(f1):.3f})")


# --------------------------------------------------------------------------- #
# Copy per-dataset result figures
# --------------------------------------------------------------------------- #
def copy_more_results() -> None:
    mapping = {}
    for ds in ["JM1", "PC1", "CM1"]:
        low = ds.lower()
        mapping.update({
            f"fig_{low}_class_distribution.png": f"{ds}/eda/class_distribution.png",
            f"fig_{low}_target_correlation.png": f"{ds}/eda/target_correlation.png",
            f"fig_{low}_roc_curves.png": f"{ds}/figures/roc_curves.png",
            f"fig_{low}_confusion_matrices.png": f"{ds}/figures/confusion_matrices.png",
            f"fig_{low}_feature_importance.png": f"{ds}/figures/feature_importance.png",
        })
    mapping["fig_ablation_kc1.png"] = "ablation_no_balance/KC1/figures/model_comparison.png"
    for dst, src in mapping.items():
        s = RESULTS / src
        if s.exists():
            shutil.copy(s, OUT / dst)
            print("copied", dst)
        else:
            print("WARNING - missing", s)


if __name__ == "__main__":
    cfg = load_config()
    set_seed(cfg["random_seed"])
    all_screenshots()
    fig_kfold(); fig_split_flow(); fig_schema(); fig_package(); fig_sequence(); fig_confmatrix_expl()
    fig_imbalance_all(cfg)
    fig_learning_curve(cfg)
    fig_threshold(cfg)
    copy_more_results()
