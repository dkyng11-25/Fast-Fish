import os
import glob
import subprocess
from pathlib import Path

import pandas as pd

PERIOD_YYYYMM = "202508"
PERIOD_HALF = "A"
PERIOD_LABEL = f"{PERIOD_YYYYMM}{PERIOD_HALF}"


def _write_fixtures(category_cn: str = "休闲裤"):
    out = Path("output")
    out.mkdir(exist_ok=True)

    # Step 18 – include Group_ΔQty so Step 36 can compute buffer validation
    st18_path = out / f"fast_fish_with_sell_through_analysis_{PERIOD_LABEL}.csv"
    group_df = pd.DataFrame(
        {
            "Store_Group_Name": ["Group 1"],
            "Target_Style_Tags": [f"[Summer, Women, Back, {category_cn}, 女{category_cn}]"],
            "Category": [category_cn],
            "Subcategory": [f"女{category_cn}"],
            "ΔQty": [5],
            "Group_ΔQty": [5],
            "Current_SPU_Quantity": [10],
            "Target_SPU_Quantity": [15],
            "Season": ["Summer"],
            "Gender": ["Women"],
            "Location": ["Back"],
        }
    )
    group_df.to_csv(st18_path, index=False)

    # Step 32 allocation
    alloc_path = out / f"store_level_allocation_results_{PERIOD_LABEL}_zzfixture.csv"
    alloc_df = pd.DataFrame(
        {
            "Store_Code": ["11017"],
            "Store_Group_Name": ["Group 1"],
            "Target_Style_Tags": [f"[Summer, Women, Back, {category_cn}, 女{category_cn}]"],
            "Category": [category_cn],
            "Subcategory": [f"女{category_cn}"],
            "Allocated_ΔQty": [5.0],
            "Allocated_ΔQty_Rounded": [5],
        }
    )
    alloc_df.to_csv(alloc_path, index=False)

    # Step 22 attrs + Step 24 tags with moderate temp
    attrs_path = out / "enriched_store_attributes.csv"
    attrs_df = pd.DataFrame(
        {"str_code": ["11017"], "temperature_band": ["15°C to 20°C"], "feels_like_temperature": [16.0]}
    )
    attrs_df.to_csv(attrs_path, index=False)

    tags_path = out / f"store_tags_{PERIOD_LABEL}.csv"
    tags_df = pd.DataFrame(
        {"str_code": ["11017"], "temperature_band": ["15°C to 20°C"], "feels_like_temperature": [16.0]}
    )
    tags_df.to_csv(tags_path, index=False)

    return {"st18": str(st18_path), "alloc": str(alloc_path), "attrs": str(attrs_path), "tags": str(tags_path)}


def _run_step36(paths: dict):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
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


def _latest_unified_and_qa():
    # choose most recent non-empty unified csv
    candidates = sorted(glob.glob(f"output/unified_delivery_{PERIOD_LABEL}_*.csv"))
    candidates = [p for p in candidates if "_top_" not in p]
    assert candidates, "No unified_delivery CSVs found"
    csv_path = None
    for p in reversed(candidates):
        try:
            if len(pd.read_csv(p)) > 0:
                csv_path = p
                break
        except Exception:
            continue
    assert csv_path, "No non-empty unified CSV found"
    qa_path = csv_path.replace(".csv", "_validation.json").replace("unified_delivery_", "unified_delivery_")
    if not os.path.exists(qa_path):
        # Step 36 uses separate path building; compute base
        base = csv_path[:-4]
        qa_path = f"{base}_validation.json"
    assert os.path.exists(qa_path), "QA validation JSON not found"
    return csv_path, qa_path


def test_category_coverage_casual_pants_and_buffer_and_tempzone():
    paths = _write_fixtures(category_cn="休闲裤")
    _run_step36(paths)
    csv_path, qa_path = _latest_unified_and_qa()

    df = pd.read_csv(csv_path)
    # Category presence: 休闲裤 must be present
    assert (df.get("Category") == "休闲裤").any(), "Category 休闲裤 should be present in output"

    # Temperature_Zone coverage should be present for these fixtures
    assert "Temperature_Zone" in df.columns
    assert df["Temperature_Zone"].notna().all(), "Temperature_Zone must be populated for test fixtures"

    # Buffer: ensure QA contains buffer coverage metric
    import json as _json
    with open(qa_path, "r", encoding="utf-8") as f:
        qa = _json.load(f)
    checks = qa.get("checks", {})
    # Either the metric exists, or group columns missing are flagged
    assert (
        "buffer_within_20pct_ratio" in checks or any("reconciliation" in k for k in checks)
    ), "QA should include buffer validation or reconciliation checks"
