#!/usr/bin/env python
"""Download the NASA MDP defect datasets listed in config.yaml.

Usage
-----
    python scripts/download_data.py            # all datasets in config
    python scripts/download_data.py KC1 PC1    # specific datasets
    python scripts/download_data.py --force    # re-download even if present
"""

import argparse

import _bootstrap  # noqa: F401  (adds project root to sys.path)

from sdp.config import load_config
from sdp.data_loader import download_dataset, load_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("datasets", nargs="*", help="Dataset names (default: all in config.yaml)")
    parser.add_argument("--force", action="store_true", help="Re-download even if the file exists")
    args = parser.parse_args()

    cfg = load_config()
    names = args.datasets or cfg["datasets"]["names"]
    for name in names:
        download_dataset(name, cfg, force=args.force)
        load_dataset(name, cfg)  # parse once to validate the file and print a summary


if __name__ == "__main__":
    main()
