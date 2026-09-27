#!/usr/bin/env python
"""Score new modules with a trained model.

The input CSV must contain the same metric columns the model was trained on
(see results/<dataset>/run_summary.json -> "features").

Usage
-----
    python scripts/predict.py --dataset KC1 --model random_forest --input new_modules.csv
    python scripts/predict.py --dataset KC1 --model random_forest --input new_modules.csv --output scored.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
import joblib
import pandas as pd

from sdp.config import load_config
from sdp.evaluate import get_scores
from sdp.utils import load_json, resolve_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True, help="Dataset the model was trained on (e.g. KC1)")
    parser.add_argument("--model", default="random_forest", help="Model name (see config.yaml)")
    parser.add_argument("--input", required=True, type=Path, help="CSV file of module metrics")
    parser.add_argument("--output", type=Path, help="Where to write the scored CSV (default: stdout)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Probability threshold for 'defective'")
    args = parser.parse_args()

    cfg = load_config()
    run_dir = resolve_path(cfg["results_dir"]) / args.dataset
    features = load_json(run_dir / "run_summary.json")["features"]
    pipe = joblib.load(run_dir / "models" / f"{args.model}.joblib")

    df = pd.read_csv(args.input)
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise SystemExit(f"Input is missing required columns: {missing}")

    proba = get_scores(pipe, df[features])
    out = df.copy()
    out["defect_probability"] = proba.round(4)
    out["predicted_defective"] = (proba >= args.threshold).astype(int)

    if args.output:
        out.to_csv(args.output, index=False)
        print(f"Wrote {len(out)} predictions to {args.output}")
    else:
        print(out[["defect_probability", "predicted_defective"]].to_string())


if __name__ == "__main__":
    main()
