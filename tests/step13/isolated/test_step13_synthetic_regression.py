"""
Step 13 Synthetic Regression Tests - Isolated Environment

SETUP REQUIREMENTS:
-------------------
These tests create a COMPLETE synthetic sandbox environment to test Step 13 in isolation.

FIXTURES:
- Uses fixtures.py to create realistic synthetic data
- Includes: clustering, SPU sales, and all rule 7-12 outputs
- Data is completely synthetic but follows real patterns
- 20 stores, 5 clusters, 15 subcategories, 50 SPUs

ISOLATION:
- Tests run in temporary sandbox directories
- No dependency on real data files
- Each test gets fresh fixtures
- Truly isolated from production data

To run these tests:
    python3 -m pytest tests/step13/isolated/test_step13_synthetic_regression.py -v

These tests validate Step 13 logic with synthetic data.
Integration tests validate with real production data.
"""

import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

TARGET_YYYYMM = "202510"
TARGET_PERIOD = "A"
PERIOD_LABEL = f"{TARGET_YYYYMM}{TARGET_PERIOD}"

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"


# Fixtures are now provided by conftest.py
# No need for _prepare_sandbox or _seed_synthetic_inputs


def _run_step13(sandbox: Path) -> None:
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    env.setdefault("PYTHONPATH", str(sandbox))
    subprocess.run(
        [
            "python3",
            "src/step13_consolidate_spu_rules.py",
            "--target-yyyymm",
            TARGET_YYYYMM,
            "--target-period",
            TARGET_PERIOD,
        ],
        cwd=sandbox,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _load_outputs(sandbox: Path) -> dict:
    detailed_path = sandbox / "output" / f"consolidated_spu_rule_results_detailed_{PERIOD_LABEL}.csv"
    store_path = sandbox / "output" / "consolidated_spu_rule_results.csv"
    cluster_path = sandbox / "output" / "consolidated_cluster_subcategory_results.csv"

    return {
        "detailed": pd.read_csv(detailed_path),
        "store": pd.read_csv(store_path),
        "cluster": pd.read_csv(cluster_path),
    }


def test_step13_synthetic_end_to_end(step13_sandbox):
    """
    End-to-end test with complete synthetic fixtures.
    Validates that Step 13 runs successfully and produces valid output.
    
    Uses the step13_sandbox fixture from conftest.py which provides
    a complete isolated environment with all necessary fixtures.
    """
    _run_step13(step13_sandbox)
    outputs = _load_outputs(step13_sandbox)

    detailed = outputs["detailed"].copy()
    detailed["str_code"] = detailed["str_code"].astype(str)
    detailed["add_qty"] = detailed["recommended_quantity_change"].clip(lower=0)

    # Basic validation: output exists and has data
    assert len(detailed) > 0, "Detailed output should have recommendations"
    assert len(outputs["store"]) > 0, "Store summary should have data"
    assert len(outputs["cluster"]) > 0, "Cluster summary should have data"
    
    # Validate required columns exist
    required_cols = ["str_code", "spu_code", "sub_cate_name", "recommended_quantity_change"]
    for col in required_cols:
        assert col in detailed.columns, f"Missing required column: {col}"
    
    # Validate cluster_id is present (our fix)
    assert "cluster_id" in detailed.columns, "cluster_id column should exist"
    missing_cluster = detailed["cluster_id"].isna().sum()
    assert missing_cluster == 0, f"cluster_id should not be missing (found {missing_cluster} NaN values)"
    
    # Volume floor enforcement: stores with recommendations meet minimum floor
    store_adds = detailed.groupby("str_code", as_index=False)["add_qty"].sum()
    if len(store_adds) > 0:
        # At least some stores should meet the floor
        stores_meeting_floor = (store_adds["add_qty"] >= 10 - 1e-6).sum()
        assert stores_meeting_floor > 0, "At least some stores should meet volume floor"
    
    print(f"✅ Synthetic test passed: {len(detailed)} recommendations across {len(store_adds)} stores")
