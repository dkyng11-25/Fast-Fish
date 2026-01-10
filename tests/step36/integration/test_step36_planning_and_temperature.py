import os
import re
import glob
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd


PERIOD_YYYYMM = "202508"
PERIOD_HALF = "A"
PERIOD_LABEL = f"{PERIOD_YYYYMM}{PERIOD_HALF}"


def _ensure_clean_output(tmp_marker: str):
    out = Path("output")
    out.mkdir(exist_ok=True)
    # Clean any previous test artifacts for this marker
    for p in out.glob(f"*{tmp_marker}*"):
        try:
            p.unlink()
        except Exception:
            pass


def _write_minimal_inputs(tmp_marker: str):
    out = Path("output")
    out.mkdir(exist_ok=True)

    st18_path = out / f"fast_fish_with_sell_through_analysis_{PERIOD_LABEL}.csv"
    group_df = pd.DataFrame(
        {
            "Store_Group_Name": ["Group 1"],
            "Target_Style_Tags": ["[Summer, Women, Back, T恤, 合体圆领T恤, 夏, 女, 后台]"],
            "Category": ["T恤"],
            "Subcategory": ["合体圆领T恤"],
            "ΔQty": [5],
            "Current_SPU_Quantity": [10],
            "Target_SPU_Quantity": [15],
            "Season": ["Summer"],
            "Gender": ["Women"],
            "Location": ["Back"],
        }
    )
    group_df.to_csv(st18_path, index=False)

    alloc_path = out / f"store_level_allocation_results_{PERIOD_LABEL}_zzfixture.csv"
    alloc_df = pd.DataFrame(
        {
            "Store_Code": ["11017"],
            "Store_Group_Name": ["Group 1"],
            "Target_Style_Tags": ["[Summer, Women, Back, T恤, 合体圆领T恤, 夏, 女, 后台]"],
            "Category": ["T恤"],
            "Subcategory": ["合体圆领T恤"],
            "Allocated_ΔQty": [5.0],
            "Allocated_ΔQty_Rounded": [5],
        }
    )
    alloc_df.to_csv(alloc_path, index=False)

    attrs_path = out / "enriched_store_attributes.csv"
    attrs_df = pd.DataFrame(
        {
            "str_code": ["11017"],
            "temperature_band": ["15°C to 20°C"],
            "feels_like_temperature": [16.0],
        }
    )
    attrs_df.to_csv(attrs_path, index=False)

    tags_path = out / f"store_tags_{PERIOD_LABEL}.csv"
    tags_df = pd.DataFrame(
        {
            "str_code": ["11017"],
            "temperature_band": ["15°C to 20°C"],
            "feels_like_temperature": [16.0],
        }
    )
    tags_df.to_csv(tags_path, index=False)

    return {
        "st18": str(st18_path),
        "alloc": str(alloc_path),
        "attrs": str(attrs_path),
        "tags": str(tags_path),
    }


def _run_step36(paths: dict):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    # Force Step 36 to use our fixtures
    env["STEP36_OVERRIDE_STEP18"] = paths["st18"]
    env["STEP36_OVERRIDE_ALLOC"] = paths["alloc"]
    env["STEP36_OVERRIDE_ATTRS"] = paths["attrs"]
    env["STEP36_OVERRIDE_STORE_TAGS"] = paths["tags"]
    cmd = [
        "python3",
        "src/step36_unified_delivery_builder.py",
        "--target-yyyymm",
        PERIOD_YYYYMM,
        "--target-period",
        PERIOD_HALF,
    ]
    subprocess.check_call(cmd, env=env)


def _latest_unified_csv() -> str:
    candidates = sorted(glob.glob(f"output/unified_delivery_{PERIOD_LABEL}_*.csv"))
    # Prefer non-auxiliary files (exclude *_top_* etc.)
    candidates = [p for p in candidates if "_top_" not in p]
    assert candidates, "No unified_delivery CSVs found"
    # Try latest first; fall back to earlier if empty
    for p in reversed(candidates):
        try:
            df = pd.read_csv(p)
            if len(df) > 0:
                return p
        except Exception:
            continue
    # If all are empty/unreadable, return the newest for debugging
    return candidates[-1]


def test_step36_generates_planning_season_and_temperature_zone(tmp_path):
    """
    Integration-style test that prepares minimal period-specific inputs, runs Step 36,
    and validates that the resulting file has:
      - Planning_Season derived from yyyymm (202508 -> Autumn)
      - Temperature_Zone populated (via band mapping) and not NaN
    """
    tmp_marker = "pytestmini"
    _ensure_clean_output(tmp_marker)
    paths = _write_minimal_inputs(tmp_marker)

    _run_step36(paths)

    csv_path = _latest_unified_csv()
    df = pd.read_csv(csv_path)

    # Global assertions based on current Step 36 behavior
    assert len(df) >= 1
    assert "Planning_Season" in df.columns
    assert set(df["Planning_Season"].dropna().unique()) == {"Autumn"}
    assert "Temperature_Zone" in df.columns
    # We expect zone to be fully populated after ordering fix
    assert df["Temperature_Zone"].notna().mean() >= 0.95

    # Clean test artifacts related to this run
    # Do not delete general outputs, only those with the tmp_marker suffix
    for p in Path("output").glob(f"*{tmp_marker}*"):
        try:
            p.unlink()
        except Exception:
            pass
