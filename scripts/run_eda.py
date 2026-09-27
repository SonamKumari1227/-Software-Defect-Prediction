#!/usr/bin/env python
"""Run exploratory data analysis and write figures/tables to results/<dataset>/eda.

Usage
-----
    python scripts/run_eda.py                 # default dataset from config.yaml
    python scripts/run_eda.py --dataset JM1
    python scripts/run_eda.py --all
"""

import argparse
import json

import _bootstrap  # noqa: F401

from sdp.config import load_config
from sdp.eda import run_eda
from sdp.utils import set_seed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", help="Dataset name (default from config.yaml)")
    parser.add_argument("--all", action="store_true", help="Run for every dataset in config.yaml")
    args = parser.parse_args()

    cfg = load_config()
    set_seed(cfg["random_seed"])
    names = cfg["datasets"]["names"] if args.all else [args.dataset or cfg["datasets"]["default"]]

    for name in names:
        overview = run_eda(name, cfg)
        print(json.dumps({k: v for k, v in overview.items() if k != "feature_names"}, indent=2))


if __name__ == "__main__":
    main()
