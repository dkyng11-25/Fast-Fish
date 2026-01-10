"""Utility helpers for detecting available data periods for tests.

This module searches the data/api_data directory for period-labeled files
and selects the best available period based on a preference order.

It enables tests to run against 202509A by default, but will gracefully
fallback to 202508B or 202508A when 202509A is unavailable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple


PREFERRED_PERIODS = (
    "202509A",
    "202508B",
    "202508A",
)


def detect_available_period(project_root: Path) -> Optional[str]:
    """Return the first available period label based on preferred order.

    A period is considered available if both store_config and spu_sales files
    exist for that period label under data/api_data/.
    """
    api_dir = project_root / "data" / "api_data"
    for period in PREFERRED_PERIODS:
        store_cfg = api_dir / f"store_config_{period}.csv"
        spu_sales = api_dir / f"complete_spu_sales_{period}.csv"
        if store_cfg.exists() and spu_sales.exists():
            return period
    return None


def split_period_label(period_label: str) -> Tuple[str, str]:
    """Split a period label like 202509A into (yyyymm, period_char)."""
    return period_label[:6], period_label[6:]






