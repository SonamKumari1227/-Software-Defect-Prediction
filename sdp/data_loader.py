"""Download and parse NASA MDP / PROMISE defect datasets.

The datasets are distributed in ARFF (Attribute-Relation File Format). A small,
dependency-free ARFF reader is implemented here because the files are simple
(numeric attributes + one nominal class attribute) and it avoids the
``bytes``-typed nominal columns returned by ``scipy.io.arff``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from sdp.utils import ensure_dir, get_logger, resolve_path

log = get_logger(__name__)

# Column name used for the binary target throughout the project.
TARGET = "defective"

# The class attribute is named differently across the MDP files
# (e.g. ``Defective`` in KC1 and ``label`` in JM1); these are all normalised.
_KNOWN_TARGET_NAMES = {"defective", "label", "defects", "class", "problems", "c"}


# --------------------------------------------------------------------------- #
# Download
# --------------------------------------------------------------------------- #
def download_dataset(name: str, cfg: dict[str, Any], force: bool = False) -> Path:
    """Download ``<name>.arff`` into ``data/raw`` and return the local path.

    Tries the GitHub mirror first and falls back to OpenML.
    """
    ds_cfg = cfg["datasets"]
    variant = ds_cfg.get("variant", "cleaned")
    raw_dir = ensure_dir(resolve_path(ds_cfg["raw_dir"]) / variant)
    dest = raw_dir / f"{name}.arff"

    if dest.exists() and not force:
        log.info("Dataset %s (%s) already present at %s (skip download)", name, variant, dest)
        return dest

    url = f"{ds_cfg['github_base_urls'][variant]}/{name}.arff"
    log.info("Downloading %s from %s", name, url)
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        log.info("Saved %s (%d bytes)", dest, len(resp.content))
        return dest
    except Exception as exc:  # noqa: BLE001 - we want to fall back on any failure
        log.warning("GitHub download failed (%s). Trying OpenML fallback...", exc)

    return _download_from_openml(name, dest, ds_cfg)


def _download_from_openml(name: str, dest: Path, ds_cfg: dict[str, Any]) -> Path:
    """Fallback loader using scikit-learn's OpenML client; writes a CSV instead of ARFF."""
    from sklearn.datasets import fetch_openml  # local import: optional path

    openml_name = ds_cfg.get("openml_names", {}).get(name, name.lower())
    bunch = fetch_openml(name=openml_name, version=1, as_frame=True, parser="auto")
    frame: pd.DataFrame = bunch.frame
    dest = dest.with_suffix(".csv")
    frame.to_csv(dest, index=False)
    log.info("Saved OpenML copy of %s to %s", name, dest)
    return dest


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
_ATTR_RE = re.compile(r"^@attribute\s+'?([^'\s]+)'?\s+(.+)$", re.IGNORECASE)


def read_arff(path: str | Path) -> pd.DataFrame:
    """Parse an ARFF file into a DataFrame. ``?`` is treated as missing."""
    columns: list[str] = []
    data_lines: list[str] = []
    in_data = False

    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("%"):
                continue
            if in_data:
                data_lines.append(line)
                continue
            if line.lower().startswith("@attribute"):
                match = _ATTR_RE.match(line)
                if not match:
                    raise ValueError(f"Cannot parse attribute line: {line}")
                columns.append(match.group(1))
            elif line.lower().startswith("@data"):
                in_data = True

    from io import StringIO

    df = pd.read_csv(StringIO("\n".join(data_lines)), header=None, names=columns, na_values="?")
    return df


def _normalise_target(df: pd.DataFrame) -> pd.DataFrame:
    """Rename the class column to ``TARGET`` and encode it as 0/1 integers."""
    target_col = None
    for col in df.columns:
        if col.lower() in _KNOWN_TARGET_NAMES:
            target_col = col
            break
    if target_col is None:  # assume last column (ARFF convention)
        target_col = df.columns[-1]

    values = df[target_col].astype(str).str.strip().str.upper()
    positive = {"Y", "YES", "TRUE", "1", "B'Y'"}
    df = df.rename(columns={target_col: TARGET})
    df[TARGET] = values.isin(positive).astype(int)
    return df


def load_dataset(name: str, cfg: dict[str, Any]) -> pd.DataFrame:
    """Return the full dataset (features + ``defective`` target) as a DataFrame."""
    path = download_dataset(name, cfg)
    if path.suffix == ".arff":
        df = read_arff(path)
    else:
        df = pd.read_csv(path)
    df = _normalise_target(df)

    # Everything except the target must be numeric for the MDP metric sets.
    feature_cols = [c for c in df.columns if c != TARGET]
    df[feature_cols] = df[feature_cols].apply(pd.to_numeric, errors="coerce")

    log.info(
        "Loaded %s [%s]: %d rows x %d features | defective = %d (%.1f%%)",
        name,
        cfg["datasets"].get("variant", "cleaned"),
        len(df),
        len(feature_cols),
        int(df[TARGET].sum()),
        100 * df[TARGET].mean(),
    )
    return df


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    X = df.drop(columns=[TARGET])
    y = df[TARGET].astype(int)
    return X, y
