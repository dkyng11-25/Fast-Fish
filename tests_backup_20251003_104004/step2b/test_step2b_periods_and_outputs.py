import os
import glob
import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest

# Test periods (fictitious to avoid collisions)
P1 = "209901A"
P2 = "209901B"


def _ensure_output_dir() -> Path:
    out = Path("output")
    out.mkdir(exist_ok=True)
    return out


def _write_minimal_inputs(period: str):
    out = _ensure_output_dir()
    # Minimal inputs expected by Step 2B
    (out / f"complete_category_sales_{period}.csv").write_text(
        "str_code,sub_cate_name,sal_amt\nS0001,CatX,10\n",
        encoding="utf-8",
    )
    (out / f"complete_spu_sales_{period}.csv").write_text(
        "str_code,spu_code\nS0001,X1\n",
        encoding="utf-8",
    )
    (out / f"store_config_{period}.csv").write_text(
        "str_code,store_name\nS0001,Demo Store\n",
        encoding="utf-8",
    )


def _run_step2b(periods):
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    cmd = [
        "python3",
        "src/step2b_consolidate_seasonal_data.py",
        "--periods",
        ",".join(periods),
    ]
    # capture_output=False to surface tqdm/prints when debugging locally; pytest captures stdout by default
    subprocess.check_call(cmd, env=env)


def _latest_metadata_json() -> Path:
    candidates = sorted(glob.glob("output/seasonal_clustering_metadata_*.json"))
    assert candidates, "No seasonal_clustering_metadata_*.json found"
    return Path(candidates[-1])


def _read_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_step2b_cli_two_periods_generates_consolidated_outputs(tmp_path):
    # Arrange: two small periods
    _write_minimal_inputs(P1)
    _write_minimal_inputs(P2)

    # Snapshot existing metadata files
    before = set(glob.glob("output/seasonal_clustering_metadata_*.json"))

    # Act
    _run_step2b([P1, P2])

    # Assert: new metadata created
    after = set(glob.glob("output/seasonal_clustering_metadata_*.json"))
    new = sorted(after - before)
    if new:
        meta_path = Path(new[-1])
    else:
        # Fallback: latest by mtime
        meta_path = _latest_metadata_json()
    meta = _read_json(meta_path)

    assert meta.get("input_periods") == [P1, P2], "--periods CLI should be honored and ordered"
    assert meta.get("total_stores", 0) >= 1, "Expected at least one store in features"

    # Consolidated outputs exist
    consolidated = Path("output/consolidated_seasonal_features.csv")
    assert consolidated.exists(), "consolidated_seasonal_features.csv should exist"

    df = pd.read_csv(consolidated)
    assert not df.empty and "str_code" in df.columns, "Consolidated features should include str_code"
    assert (df["str_code"] == "S0001").any(), "Expected test store S0001 in consolidated features"


def test_step2b_cli_single_period_still_works(tmp_path):
    # Arrange: single period
    single = "209902A"
    _write_minimal_inputs(single)

    # Act
    _run_step2b([single])

    # Assert basic output existence
    consolidated = Path("output/consolidated_seasonal_features.csv")
    assert consolidated.exists()
    df = pd.read_csv(consolidated)
    assert (df["str_code"] == "S0001").any()
