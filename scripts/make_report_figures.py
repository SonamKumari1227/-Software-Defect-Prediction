#!/usr/bin/env python
"""Generate the hand-drawn-style diagrams for the report and collect every
figure referenced in report/Minor_Project_Report.md into report/figures/.

Diagrams (Graphviz + matplotlib):
    fig4_1_methodology.png      overall pipeline flowchart
    fig4_2_smote.png            SMOTE working principle
    fig5_1_architecture.png     layered architecture of the sdp package
    fig5_2_dfd.png              level-1 data-flow diagram
    fig5_3_usecase.png          use-case diagram
    fig6_1_pipeline.png         composition of the scikit-learn/imblearn pipeline

Result figures are copied from results/ (run scripts/run_pipeline.py --all first).

Usage:  python scripts/make_report_figures.py
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
from matplotlib.patches import Ellipse, FancyArrowPatch  # noqa: E402

from sdp.utils import PROJECT_ROOT, ensure_dir  # noqa: E402

OUT = ensure_dir(PROJECT_ROOT / "report" / "figures")
RESULTS = PROJECT_ROOT / "results"
FONT = "Helvetica"


def dot(name: str, source: str) -> Path:
    """Render a DOT graph to PNG with Graphviz."""
    path = OUT / f"{name}.png"
    subprocess.run(["dot", "-Tpng", "-Gdpi=170", "-o", str(path)], input=source.encode("utf-8"), check=True)
    print("wrote", path.name)
    return path


# --------------------------------------------------------------------------- #
# Figure 4.1 - methodology flowchart
# --------------------------------------------------------------------------- #
def fig4_1() -> None:
    dot("fig4_1_methodology", f"""
digraph G {{
  rankdir=TB; nodesep=0.35; ranksep=0.35;
  node [shape=box, style="rounded,filled", fillcolor="#EAF2FB", color="#2F5597", fontname="{FONT}", fontsize=11, margin="0.18,0.08"];
  edge [color="#2F5597", arrowsize=0.8];

  data   [label="NASA MDP datasets (ARFF)\\nKC1, JM1, PC1, CM1 – cleaned D'' versions", fillcolor="#FFF2CC", color="#BF9000"];
  clean  [label="Data cleaning\\nremove duplicate rows and constant features"];
  split  [label="Stratified hold-out split\\n80 % training / 20 % test (seed 42)"];
  train  [label="Training set", shape=note, fillcolor="#E2F0D9", color="#548235"];
  test   [label="Test set", shape=note, fillcolor="#FBE5D6", color="#C55A11"];
  pre    [label="Preprocessing pipeline\\nmedian imputation → log(1+x) → standardisation"];
  smote  [label="SMOTE\\n(applied inside training folds only)"];
  models [label="Eight classifiers\\nLR, DT, RF, GB, SVM, k-NN, NB, MLP"];
  cv     [label="Stratified 5-fold cross-validation\\nmean ± std of every metric"];
  fit    [label="Refit on the full training set"];
  eval   [label="Hold-out evaluation\\nAccuracy, Precision, Recall, F1, ROC-AUC, MCC, PF"];
  out    [label="Result tables, figures and saved models", fillcolor="#FFF2CC", color="#BF9000"];

  data -> clean -> split;
  split -> train; split -> test;
  train -> pre -> smote -> models -> cv -> fit -> eval -> out;
  test -> eval;
  {{ rank=same; train; test; }}
}}
""")


# --------------------------------------------------------------------------- #
# Figure 4.2 - SMOTE principle (matplotlib)
# --------------------------------------------------------------------------- #
def fig4_2() -> None:
    rng = np.random.default_rng(11)
    maj = rng.normal([-0.8, -0.3], [1.2, 1.0], size=(70, 2))
    mino = rng.normal([2.4, 1.6], [1.0, 0.9], size=(9, 2))

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.scatter(maj[:, 0], maj[:, 1], s=28, c="#4C72B0", alpha=0.75, label="Majority class (non-defective)")
    ax.scatter(mino[:, 0], mino[:, 1], s=70, c="#C44E52", edgecolor="k", zorder=3, label="Minority class (defective)")

    synth = []
    drawn = set()
    for i in range(len(mino)):
        d = np.linalg.norm(mino - mino[i], axis=1)
        for j in np.argsort(d)[1:3]:  # two nearest minority neighbours
            lam = rng.uniform(0.25, 0.75)
            synth.append(mino[i] + lam * (mino[j] - mino[i]))
            if (j, i) not in drawn:
                ax.plot([mino[i, 0], mino[j, 0]], [mino[i, 1], mino[j, 1]], color="grey", lw=0.9, ls="--", zorder=1)
                drawn.add((i, j))
    synth = np.array(synth)
    ax.scatter(synth[:, 0], synth[:, 1], s=60, facecolor="white", edgecolor="#C44E52", lw=1.7, zorder=4,
               label="Synthetic minority sample")

    ax.text(0.98, 0.03, r"$x_{new} = x_i + \lambda\,(x_j - x_i),\;\lambda \in [0, 1]$", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=10.5, bbox=dict(boxstyle="round", fc="white", ec="#BFBFBF"))
    ax.set_xlabel("Feature 1 (standardised)")
    ax.set_ylabel("Feature 2 (standardised)")
    ax.set_title("Synthetic Minority Over-sampling Technique (SMOTE)")
    ax.legend(loc="upper left", fontsize=8.5, frameon=True)
    ax.set_xticks([]); ax.set_yticks([])
    ax.margins(0.08)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_2_smote.png", dpi=170)
    plt.close(fig)
    print("wrote fig4_2_smote.png")


# --------------------------------------------------------------------------- #
# Figure 5.1 - layered architecture
# --------------------------------------------------------------------------- #
def fig5_1() -> None:
    dot("fig5_1_architecture", f"""
digraph G {{
  rankdir=TB; compound=true; nodesep=0.25; ranksep=0.45;
  node [shape=box, style="rounded,filled", fillcolor="white", fontname="{FONT}", fontsize=10, margin="0.14,0.06"];
  edge [color="#555555", arrowsize=0.7];
  graph [fontname="{FONT}", fontsize=11, style="rounded,filled", color="#BFBFBF"];

  subgraph cluster_p {{ label="Presentation layer – command-line scripts"; fillcolor="#EAF2FB";
    dl [label="download_data.py"]; eda [label="run_eda.py"]; rp [label="run_pipeline.py"]; pr [label="predict.py"]; }}
  subgraph cluster_a {{ label="Application layer – workflows"; fillcolor="#E2F0D9";
    seda [label="sdp.eda"]; sev [label="sdp.evaluate"]; }}
  subgraph cluster_d {{ label="Domain layer – machine-learning logic"; fillcolor="#FFF2CC";
    spre [label="sdp.preprocessing"]; smod [label="sdp.models"]; svis [label="sdp.visualization"]; }}
  subgraph cluster_data {{ label="Data layer"; fillcolor="#FBE5D6";
    sdl [label="sdp.data_loader"]; cfg [label="config.yaml", shape=note]; raw [label="data/raw/*.arff", shape=cylinder]; }}
  subgraph cluster_x {{ label="Cross-cutting"; fillcolor="#EDEDED";
    util [label="sdp.utils\\nlogging · seeding · paths"]; tests [label="tests/"]; }}

  dl -> sdl; eda -> seda; rp -> sev; rp -> spre; rp -> smod; rp -> svis; pr -> sdl;
  seda -> sdl; seda -> spre; seda -> svis; sev -> smod;
  spre -> sdl; sdl -> raw; sdl -> cfg [style=dashed];
  tests -> spre [style=dotted]; tests -> sev [style=dotted]; util -> sdl [style=dotted];
}}
""")


# --------------------------------------------------------------------------- #
# Figure 5.2 - level-1 data-flow diagram
# --------------------------------------------------------------------------- #
def fig5_2() -> None:
    dot("fig5_2_dfd", f"""
digraph G {{
  rankdir=TB; nodesep=0.45; ranksep=0.45;
  node [fontname="{FONT}", fontsize=10];
  edge [fontname="{FONT}", fontsize=9, color="#555555", arrowsize=0.7];

  ext  [label="PROMISE / GitHub\\nmirror", shape=box, style=filled, fillcolor="#EDEDED"];
  user [label="Researcher", shape=box, style=filled, fillcolor="#EDEDED"];
  p1 [label="1.0\\nDownload", shape=circle, style=filled, fillcolor="#EAF2FB", fixedsize=true, width=1.05];
  p2 [label="2.0\\nParse &\\nclean", shape=circle, style=filled, fillcolor="#EAF2FB", fixedsize=true, width=1.05];
  p3 [label="3.0\\nSplit", shape=circle, style=filled, fillcolor="#EAF2FB", fixedsize=true, width=1.05];
  p4 [label="4.0\\nTrain &\\ncross-validate", shape=circle, style=filled, fillcolor="#EAF2FB", fixedsize=true, width=1.15];
  p5 [label="5.0\\nEvaluate", shape=circle, style=filled, fillcolor="#EAF2FB", fixedsize=true, width=1.05];
  p6 [label="6.0\\nVisualise", shape=circle, style=filled, fillcolor="#EAF2FB", fixedsize=true, width=1.05];
  d1 [label="D1  data/raw", shape=cylinder, style=filled, fillcolor="#FFF2CC"];
  d2 [label="D2  results/<ds>/models", shape=cylinder, style=filled, fillcolor="#FFF2CC"];
  d3 [label="D3  results/<ds>/test_metrics.csv", shape=cylinder, style=filled, fillcolor="#FFF2CC"];
  d4 [label="D4  results/<ds>/figures", shape=cylinder, style=filled, fillcolor="#FFF2CC"];
  cfg [label="config.yaml", shape=note, style=filled, fillcolor="#FBE5D6"];

  ext -> p1 [label="ARFF file"]; p1 -> d1 [label="cached file"]; d1 -> p2 [label="raw rows"];
  p2 -> p3 [label="clean frame"]; p3 -> p4 [label="training set"]; p3 -> p5 [label="test set"];
  p4 -> d2 [label="fitted pipelines"]; p4 -> p5 [label="CV scores"]; d2 -> p5;
  p5 -> d3 [label="metrics"]; d3 -> p6; p6 -> d4 [label="PNG figures"];
  cfg -> p3 [style=dashed]; cfg -> p4 [style=dashed];
  user -> p1 [label="dataset name"]; d3 -> user [label="summary table"];
  {{ rank=same; ext; user; }}
  {{ rank=same; p3; cfg; }}
  {{ rank=same; d2; p5; }}
}}
""")


# --------------------------------------------------------------------------- #
# Figure 5.3 - use-case diagram (matplotlib)
# --------------------------------------------------------------------------- #
def fig5_3() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.set_xlim(0, 10); ax.set_ylim(0.4, 6.3); ax.axis("off")

    # system boundary
    ax.add_patch(plt.Rectangle((3.2, 0.8), 6.4, 5.2, fill=False, lw=1.2, color="#2F5597"))
    ax.text(6.4, 5.72, "Software Defect Prediction System", ha="center", fontsize=10.5, weight="bold", color="#2F5597")

    # actor (stick figure)
    ax.add_patch(plt.Circle((1.3, 4.2), 0.28, fill=False, lw=1.5))
    ax.plot([1.3, 1.3], [3.92, 3.1], "k", lw=1.5)
    ax.plot([0.85, 1.75], [3.65, 3.65], "k", lw=1.5)
    ax.plot([1.3, 0.9], [3.1, 2.4], "k", lw=1.5); ax.plot([1.3, 1.7], [3.1, 2.4], "k", lw=1.5)
    ax.text(1.3, 2.05, "Researcher /\nDeveloper", ha="center", va="top", fontsize=9.5)

    # one column of use cases: every association ends on an ellipse's left edge, so no line crosses another ellipse
    names = ["Download datasets", "Explore data (EDA)", "Train and compare classifiers", "Predict on new modules", "Run automated tests"]
    ys = [5.05, 4.15, 3.25, 2.35, 1.45]
    x, w, h = 5.3, 3.3, 0.72
    for name, y in zip(names, ys):
        ax.add_patch(Ellipse((x, y), w, h, facecolor="#EAF2FB", edgecolor="#2F5597", lw=1.2, zorder=2))
        ax.text(x, y, name, ha="center", va="center", fontsize=9, zorder=3)
        ax.add_line(plt.Line2D([1.75, x - w / 2], [3.5, y], color="k", lw=0.9, zorder=1))

    # include relationships: Train includes Download; Predict includes Train
    for (sy, dy, lx) in [(3.25, 5.05, 7.85), (2.35, 3.25, 7.45)]:
        ax.add_patch(FancyArrowPatch((x + w / 2 - 0.05, sy + 0.12), (x + w / 2 - 0.05, dy - 0.3), arrowstyle="-|>",
                                     linestyle="--", color="#7F7F7F", mutation_scale=12, connectionstyle="arc3,rad=-0.5", zorder=4))
        ax.text(lx, (sy + dy) / 2, "«include»", fontsize=8, color="#7F7F7F", rotation=90, va="center", ha="center")

    fig.tight_layout()
    fig.savefig(OUT / "fig5_3_usecase.png", dpi=170)
    plt.close(fig)
    print("wrote fig5_3_usecase.png")


# --------------------------------------------------------------------------- #
# Figure 6.1 - pipeline composition
# --------------------------------------------------------------------------- #
def fig6_1() -> None:
    dot("fig6_1_pipeline", f"""
digraph G {{
  rankdir=TB; nodesep=0.5; ranksep=0.3;
  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=10, margin="0.16,0.08", width=2.6];
  edge [color="#2F5597", arrowsize=0.8];

  x   [label="Raw feature matrix X\\n(21–37 code metrics)", fillcolor="#FFF2CC"];
  imp [label="SimpleImputer\\nstrategy = median", fillcolor="#EAF2FB"];
  log [label="FunctionTransformer\\nlog(1 + x)", fillcolor="#EAF2FB"];
  sc  [label="StandardScaler\\nzero mean, unit variance", fillcolor="#EAF2FB"];
  sm  [label="SMOTE\\nk = 5, balanced classes", fillcolor="#FBE5D6", color="#C55A11", penwidth=1.6];
  clf [label="Classifier\\n(one of eight estimators)", fillcolor="#E2F0D9"];
  y   [label="Prediction ŷ and\\ndefect probability", fillcolor="#FFF2CC"];
  note [label="Executed during fit() only —\\nskipped at predict() time, so the\\ntest set is never resampled", shape=note, fillcolor="#FFFFFF", fontsize=9, color="#C55A11"];

  x -> imp -> log -> sc -> sm -> clf -> y;
  note -> sm [style=dashed, color="#C55A11", arrowhead=none];
  {{ rank=same; sm; note; }}
}}
""")


# --------------------------------------------------------------------------- #
# Copy generated result figures with report numbering
# --------------------------------------------------------------------------- #
COPY_MAP = {
    "fig7_01_kc1_class_distribution.png": "KC1/eda/class_distribution.png",
    "fig7_02_kc1_correlation_heatmap.png": "KC1/eda/correlation_heatmap.png",
    "fig7_03_kc1_feature_distributions.png": "KC1/eda/feature_distributions.png",
    "fig7_04_kc1_target_correlation.png": "KC1/eda/target_correlation.png",
    "fig7_05_kc1_model_comparison.png": "KC1/figures/model_comparison.png",
    "fig7_06_kc1_roc_curves.png": "KC1/figures/roc_curves.png",
    "fig7_07_kc1_pr_curves.png": "KC1/figures/pr_curves.png",
    "fig7_08_kc1_confusion_matrices.png": "KC1/figures/confusion_matrices.png",
    "fig7_09_kc1_cv_f1_boxplot.png": "KC1/figures/cv_f1_boxplot.png",
    "fig7_10_kc1_feature_importance.png": "KC1/figures/feature_importance.png",
    "fig7_11_cross_dataset_f1.png": "cross_dataset_f1.png",
    "fig7_12_cross_dataset_roc_auc.png": "cross_dataset_roc_auc.png",
    "figB_1_jm1_model_comparison.png": "JM1/figures/model_comparison.png",
    "figB_2_pc1_model_comparison.png": "PC1/figures/model_comparison.png",
    "figB_3_cm1_model_comparison.png": "CM1/figures/model_comparison.png",
}


def copy_results() -> None:
    missing = []
    for dst, src in COPY_MAP.items():
        s = RESULTS / src
        if s.exists():
            shutil.copy(s, OUT / dst)
            print("copied", dst)
        else:
            missing.append(str(s))
    if missing:
        print("WARNING - missing result figures (run scripts/run_pipeline.py --all):\n  " + "\n  ".join(missing))


if __name__ == "__main__":
    fig4_1(); fig4_2(); fig5_1(); fig5_2(); fig5_3(); fig6_1()
    copy_results()
