"""Load and lightly validate the YAML configuration file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sdp.utils import PROJECT_ROOT

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"

_REQUIRED_TOP_LEVEL = ("random_seed", "datasets", "preprocessing", "cross_validation", "models")


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Read ``config.yaml`` and return it as a nested dictionary.

    Parameters
    ----------
    path:
        Optional alternative config file. Defaults to ``<project_root>/config.yaml``.

    Raises
    ------
    FileNotFoundError, KeyError
        If the file is missing or a mandatory section is absent.
    """
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {cfg_path}")

    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    missing = [k for k in _REQUIRED_TOP_LEVEL if k not in cfg]
    if missing:
        raise KeyError(f"config.yaml is missing required section(s): {missing}")

    # Sensible defaults for optional keys so the rest of the code can rely on them.
    cfg.setdefault("results_dir", "results")
    cfg.setdefault("tuning", {"enabled": False, "n_iter": 10})
    cfg["preprocessing"].setdefault("balance", "none")
    cfg["preprocessing"].setdefault("scaler", "standard")
    cfg["preprocessing"].setdefault("log_transform", True)
    return cfg
