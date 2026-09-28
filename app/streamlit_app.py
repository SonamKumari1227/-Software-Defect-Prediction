"""Software Defect Prediction - interactive web interface.

A Streamlit front end for the trained models. The user enters the static code
metrics of a software module through a form and the application returns the
predicted defect probability together with the resulting classification.

Run with:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdp.config import load_config  # noqa: E402
from sdp.data_loader import TARGET, load_dataset  # noqa: E402
from sdp.evaluate import get_scores  # noqa: E402
from sdp.models import DISPLAY_NAMES  # noqa: E402
from sdp.preprocessing import clean_dataframe  # noqa: E402

st.set_page_config(page_title="Software Defect Prediction",
                   page_icon="🛡", layout="wide")

# --------------------------------------------------------------------------- #
# Metric grouping and help text
# --------------------------------------------------------------------------- #
GROUPS = {
    "Size metrics (lines of code)": [
        "LOC_TOTAL", "LOC_EXECUTABLE", "LOC_COMMENTS", "LOC_BLANK", "LOC_CODE_AND_COMMENT"],
    "McCabe complexity metrics": [
        "CYCLOMATIC_COMPLEXITY", "DESIGN_COMPLEXITY", "ESSENTIAL_COMPLEXITY", "BRANCH_COUNT",
        "CYCLOMATIC_DENSITY", "DECISION_COUNT", "DECISION_DENSITY", "CONDITION_COUNT",
        "EDGE_COUNT", "NODE_COUNT", "MAINTENANCE_SEVERITY", "DESIGN_DENSITY",
        "ESSENTIAL_DENSITY", "GLOBAL_DATA_COMPLEXITY", "GLOBAL_DATA_DENSITY"],
    "Halstead vocabulary counts": [
        "NUM_UNIQUE_OPERATORS", "NUM_UNIQUE_OPERANDS", "NUM_OPERATORS", "NUM_OPERANDS"],
    "Halstead derived measures": [
        "HALSTEAD_LENGTH", "HALSTEAD_VOLUME", "HALSTEAD_DIFFICULTY", "HALSTEAD_LEVEL",
        "HALSTEAD_EFFORT", "HALSTEAD_CONTENT", "HALSTEAD_PROG_TIME", "HALSTEAD_ERROR_EST"],
}

HELP = {
    "LOC_TOTAL": "Total lines of code in the module.",
    "LOC_EXECUTABLE": "Lines containing executable statements.",
    "LOC_COMMENTS": "Lines containing only comments.",
    "LOC_BLANK": "Blank lines.",
    "LOC_CODE_AND_COMMENT": "Lines holding both code and a comment.",
    "CYCLOMATIC_COMPLEXITY": "McCabe v(G): independent paths through the control-flow graph.",
    "DESIGN_COMPLEXITY": "Complexity of the module's calls to other modules.",
    "ESSENTIAL_COMPLEXITY": "Degree of unstructured control flow.",
    "BRANCH_COUNT": "Number of branches in the flow graph.",
    "NUM_UNIQUE_OPERATORS": "n1: distinct operators.",
    "NUM_UNIQUE_OPERANDS": "n2: distinct operands.",
    "NUM_OPERATORS": "N1: total operator occurrences.",
    "NUM_OPERANDS": "N2: total operand occurrences.",
    "HALSTEAD_LENGTH": "N = N1 + N2.",
    "HALSTEAD_VOLUME": "V = N x log2(n1 + n2).",
    "HALSTEAD_DIFFICULTY": "D = (n1 / 2) x (N2 / n2).",
    "HALSTEAD_LEVEL": "L = 1 / D.",
    "HALSTEAD_EFFORT": "E = D x V.",
    "HALSTEAD_CONTENT": "Intelligence content, I = V / D.",
    "HALSTEAD_PROG_TIME": "T = E / 18 seconds.",
    "HALSTEAD_ERROR_EST": "Estimated delivered bugs, B = V / 3000.",
}

DERIVED = ["HALSTEAD_LENGTH", "HALSTEAD_VOLUME", "HALSTEAD_DIFFICULTY", "HALSTEAD_LEVEL",
           "HALSTEAD_EFFORT", "HALSTEAD_CONTENT", "HALSTEAD_PROG_TIME", "HALSTEAD_ERROR_EST"]


# --------------------------------------------------------------------------- #
# Cached loaders
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def load_reference(dataset: str) -> pd.DataFrame:
    """Cleaned training data, used for defaults and for context in the output."""
    cfg = load_config()
    return clean_dataframe(load_dataset(dataset, cfg), cfg)


@st.cache_resource(show_spinner=False)
def load_model(dataset: str, model_name: str):
    path = ROOT / "results" / dataset / "models" / f"{model_name}.joblib"
    return joblib.load(path)


@st.cache_data(show_spinner=False)
def load_metrics(dataset: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / "results" / dataset / "test_metrics.csv")


def available(dataset: str) -> list[str]:
    d = ROOT / "results" / dataset / "models"
    return sorted(p.stem for p in d.glob("*.joblib")) if d.exists() else []


def halstead_from_counts(n1: float, n2: float, big_n1: float, big_n2: float) -> dict[str, float]:
    """Recompute the derived Halstead measures from the four basic counts."""
    n, length = n1 + n2, big_n1 + big_n2
    volume = length * math.log2(n) if n > 1 else 0.0
    difficulty = (n1 / 2) * (big_n2 / n2) if n2 else 0.0
    effort = difficulty * volume
    return {
        "HALSTEAD_LENGTH": length,
        "HALSTEAD_VOLUME": round(volume, 2),
        "HALSTEAD_DIFFICULTY": round(difficulty, 2),
        "HALSTEAD_LEVEL": round(1 / difficulty, 4) if difficulty else 0.0,
        "HALSTEAD_EFFORT": round(effort, 2),
        "HALSTEAD_CONTENT": round(volume / difficulty, 2) if difficulty else 0.0,
        "HALSTEAD_PROG_TIME": round(effort / 18, 2),
        "HALSTEAD_ERROR_EST": round(volume / 3000, 3),
    }


def gauge(probability: float, threshold: float):
    """Horizontal risk gauge showing the predicted probability."""
    fig, ax = plt.subplots(figsize=(7.4, 1.15))
    for lo, hi, colour in ((0, .25, "#4C9F70"), (.25, .5, "#F0C808"),
                           (.5, .75, "#E8871E"), (.75, 1, "#C44E52")):
        ax.barh([0], hi - lo, left=lo, height=.5, color=colour, alpha=.85)
    ax.plot([probability, probability], [-.42, .42], color="#111", lw=3.2, solid_capstyle="round")
    ax.plot([threshold, threshold], [-.35, .35], color="#111", lw=1.3, ls="--")
    ax.text(probability, .55, f"{probability:.1%}", ha="center", fontsize=12, weight="bold")
    ax.text(threshold, -.78, f"threshold {threshold:.2f}", ha="center", fontsize=8, color="#444")
    for x, lab in ((.125, "Low"), (.375, "Moderate"), (.625, "High"), (.875, "Very high")):
        ax.text(x, 0, lab, ha="center", va="center", fontsize=8.5, color="white", weight="bold")
    ax.set_xlim(0, 1); ax.set_ylim(-.9, .9); ax.axis("off")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
st.sidebar.title("Configuration")
dataset = st.sidebar.selectbox(
    "Training dataset", ["KC1", "JM1", "PC1", "CM1"], index=0,
    help="The NASA MDP dataset the model was trained on.")

models = available(dataset)
if not models:
    st.error(f"No trained model found for {dataset}. "
             f"Run  python scripts/run_pipeline.py --dataset {dataset}  first.")
    st.stop()

default_model = models.index("gradient_boosting") if "gradient_boosting" in models else 0
model_name = st.sidebar.selectbox(
    "Classifier", models, index=default_model,
    format_func=lambda m: DISPLAY_NAMES.get(m, m),
    help="All eight classifiers compared in the study are available.")

threshold = st.sidebar.slider(
    "Decision threshold", 0.05, 0.95, 0.50, 0.01,
    help="Probability above which a module is flagged as defective. "
         "Lower it to favour recall, raise it to favour precision.")

ref = load_reference(dataset)
features = [c for c in ref.columns if c != TARGET]
model = load_model(dataset, model_name)
metrics = load_metrics(dataset)
row = metrics[metrics.model == model_name].iloc[0]

st.sidebar.divider()
st.sidebar.subheader("Model performance")
st.sidebar.caption("Measured on the held-out test set.")
c1, c2 = st.sidebar.columns(2)
c1.metric("F1-score", f"{row.f1:.3f}")
c2.metric("ROC-AUC", f"{row.roc_auc:.3f}")
c3, c4 = st.sidebar.columns(2)
c3.metric("Recall", f"{row.recall:.3f}")
c4.metric("Precision", f"{row.precision:.3f}")
st.sidebar.caption(
    f"Trained on {len(ref):,} modules, {int(ref[TARGET].sum())} of them defective "
    f"({ref[TARGET].mean():.1%}).")

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("Software Defect Prediction")
st.caption("Enter the static code metrics of a software module to estimate whether it is "
           "defect-prone. Models were trained on the cleaned NASA MDP benchmark datasets.")

preset = st.radio(
    "Starting values", ["Typical module (dataset median)", "Small, simple module",
                        "Large, complex module"],
    horizontal=True,
    help="A starting point for the form. Every field remains editable.")

med = ref[features].median()
if preset == "Small, simple module":
    base = ref[features].quantile(0.10)
elif preset == "Large, complex module":
    base = ref[features].quantile(0.90)
else:
    base = med

# A number_input keeps whatever the user last typed, so changing the preset or
# the dataset has to push the new starting values into the widget state
# explicitly, before the widgets themselves are created.
if st.session_state.get("_context") != (dataset, preset):
    st.session_state["_context"] = (dataset, preset)
    for feat in features:
        st.session_state[f"in_{feat}"] = float(base[feat])

auto = st.checkbox(
    "Derive the Halstead measures automatically from the operator and operand counts",
    value=True,
    help="Volume, difficulty, effort and the rest are algebraic functions of n1, n2, N1 and N2. "
         "Leaving this ticked keeps the entered values mutually consistent.")

# --------------------------------------------------------------------------- #
# Input form
# --------------------------------------------------------------------------- #
values: dict[str, float] = {}
grouped = [f for g in GROUPS.values() for f in g]
groups = {**GROUPS, "Other metrics": [f for f in features if f not in grouped]}

with st.form("metrics"):
    for title, names in groups.items():
        present = [f for f in names if f in features]
        if not present:
            continue
        if auto and title == "Halstead derived measures":
            st.markdown(f"**{title}** — computed automatically from the counts above")
            continue
        st.markdown(f"**{title}**")
        cols = st.columns(min(4, len(present)))
        for i, feat in enumerate(present):
            lo, hi = float(ref[feat].min()), float(ref[feat].max())
            step = 1.0 if float(ref[feat].round().eq(ref[feat]).all()) else 0.01
            values[feat] = cols[i % len(cols)].number_input(
                feat.replace("_", " ").title(), min_value=lo, max_value=max(hi, lo + 1),
                step=step, help=HELP.get(feat), key=f"in_{feat}")
    submitted = st.form_submit_button("Predict", type="primary", use_container_width=True)

if auto:
    counts = {k: values.get(k, float(base.get(k, 0)))
              for k in ("NUM_UNIQUE_OPERATORS", "NUM_UNIQUE_OPERANDS",
                        "NUM_OPERATORS", "NUM_OPERANDS")}
    derived = halstead_from_counts(counts["NUM_UNIQUE_OPERATORS"], counts["NUM_UNIQUE_OPERANDS"],
                                   counts["NUM_OPERATORS"], counts["NUM_OPERANDS"])
    for k, v in derived.items():
        if k in features:
            values[k] = v

for feat in features:                      # anything not shown keeps its default
    values.setdefault(feat, float(base[feat]))

# --------------------------------------------------------------------------- #
# Prediction
# --------------------------------------------------------------------------- #
if submitted:
    X = pd.DataFrame([[values[f] for f in features]], columns=features)
    probability = float(get_scores(model, X)[0])
    defective = probability >= threshold

    st.divider()
    st.subheader("Prediction")

    left, right = st.columns([3, 2])
    with left:
        if defective:
            st.error(f"### Defective\nThis module is predicted to be **defect-prone** and is "
                     f"recommended for inspection.")
        else:
            st.success(f"### Non-defective\nThis module is **not** predicted to be defect-prone.")
        st.pyplot(gauge(probability, threshold))

    with right:
        st.metric("Defect probability", f"{probability:.1%}")
        st.metric("Decision", "Defective" if defective else "Non-defective")
        band = ("Very high" if probability >= .75 else "High" if probability >= .5
                else "Moderate" if probability >= .25 else "Low")
        st.metric("Risk band", band)
        st.caption(f"{DISPLAY_NAMES.get(model_name, model_name)} trained on {dataset}, "
                   f"threshold {threshold:.2f}.")

    st.markdown("**How this module compares with the training data**")
    comp = pd.DataFrame({
        "Metric": features,
        "Entered value": [round(values[f], 2) for f in features],
        "Dataset median": [round(float(med[f]), 2) for f in features],
        "Ratio to median": [round(values[f] / med[f], 2) if med[f] else float("nan")
                            for f in features],
    })
    comp["Percentile in dataset"] = [
        f"{(ref[f] <= values[f]).mean():.0%}" for f in features]
    st.dataframe(comp, use_container_width=True, hide_index=True, height=300)

    st.caption(
        "The prediction ranks a module for review; it does not prove the presence or absence of "
        "a defect. On this dataset the selected model attains an F1-score of "
        f"{row.f1:.3f} and a false-alarm rate of {row.pf:.3f}.")
else:
    st.info("Set the metric values above and press **Predict**.")
