"""General-purpose helpers: paths, logging, seeding and JSON persistence."""

from __future__ import annotations

import json
import logging
import os
import random
from pathlib import Path
from typing import Any

import numpy as np

# The project root is the directory that contains ``config.yaml``
# (one level above this package).
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]


def get_logger(name: str = "sdp", level: int = logging.INFO) -> logging.Logger:
    """Return a console logger with a compact, timestamped format."""
    logger = logging.getLogger(name)
    if not logger.handlers:  # avoid duplicate handlers on repeated calls
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S")
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def set_seed(seed: int) -> None:
    """Seed every random number generator we rely on for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def ensure_dir(path: str | Path) -> Path:
    """Create *path* (and parents) if missing and return it as a ``Path``."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def resolve_path(path: str | Path) -> Path:
    """Resolve a path from ``config.yaml`` relative to the project root."""
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def save_json(obj: Any, path: str | Path) -> None:
    """Write *obj* to *path* as indented JSON (numpy types are converted)."""

    def _default(o: Any) -> Any:
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serialisable")

    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=_default)


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
