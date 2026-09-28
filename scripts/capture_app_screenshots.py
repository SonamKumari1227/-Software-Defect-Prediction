#!/usr/bin/env python
"""Capture screenshots of the running Streamlit application for the report.

The application must already be serving, for example:

    python -m streamlit run app/streamlit_app.py --server.headless true

Then:

    python scripts/capture_app_screenshots.py

Writes into report/figures/:
    shot_app_form.png       the metric-entry form as first presented
    shot_app_sidebar.png    the configuration sidebar and model performance panel
    shot_app_clean.png      the prediction for a small, simple module
    shot_app_defective.png  the prediction for a large, complex module
    shot_app_compare.png    the comparison table against the training data
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import _bootstrap  # noqa: F401
from playwright.sync_api import sync_playwright

from sdp.utils import PROJECT_ROOT, ensure_dir

URL = "http://localhost:8501"
OUT = ensure_dir(PROJECT_ROOT / "report" / "figures")


def settle(page, seconds: float = 2.5) -> None:
    """Wait for Streamlit to finish its websocket-driven rerender."""
    page.wait_for_load_state("networkidle")
    time.sleep(seconds)


def choose_preset(page, label: str) -> None:
    page.get_by_text(label, exact=True).first.click()
    settle(page)


def predict(page) -> None:
    page.get_by_role("button", name="Predict").first.click()
    page.wait_for_selector("text=Defect probability", timeout=60_000)
    settle(page)


def shoot_prediction(page, name: str) -> None:
    """Screenshot the prediction block, which sits below the form.

    The heading is scrolled to the top of the viewport rather than centred, so
    that the verdict, the gauge and the metrics all fall inside the frame.
    """
    page.get_by_text("Prediction", exact=True).first.evaluate(
        "el => el.scrollIntoView({block: 'start', behavior: 'instant'})")
    time.sleep(1.8)
    page.screenshot(path=str(OUT / name))
    print("wrote", name)


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1500, "height": 1150},
                                device_scale_factor=2)
        page.goto(URL, wait_until="networkidle", timeout=90_000)
        page.wait_for_selector("text=Software Defect Prediction", timeout=90_000)
        settle(page, 4)

        # 1. the form as first presented
        page.screenshot(path=str(OUT / "shot_app_form.png"))
        print("wrote shot_app_form.png")

        # 2. the sidebar on its own
        sidebar = page.locator('section[data-testid="stSidebar"]')
        if sidebar.count():
            sidebar.screenshot(path=str(OUT / "shot_app_sidebar.png"))
            print("wrote shot_app_sidebar.png")

        # 3. a small, simple module -> expected non-defective
        choose_preset(page, "Small, simple module")
        predict(page)
        shoot_prediction(page, "shot_app_clean.png")

        # 4. a large, complex module -> expected defective
        choose_preset(page, "Large, complex module")
        predict(page)
        shoot_prediction(page, "shot_app_defective.png")

        # 5. the comparison table
        table = page.locator('[data-testid="stDataFrame"]').first
        if table.count():
            table.scroll_into_view_if_needed()
            time.sleep(1.0)
            table.screenshot(path=str(OUT / "shot_app_compare.png"))
            print("wrote shot_app_compare.png")

        browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"capture failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
