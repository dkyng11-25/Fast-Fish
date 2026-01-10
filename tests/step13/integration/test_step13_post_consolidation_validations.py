"""
Step 13 Integration Tests - Post-Consolidation Validations

SETUP REQUIREMENTS:
-------------------
These tests validate Step 13 output quality and business logic enforcement.

Environment Variables (REQUIRED):
- PIPELINE_TARGET_YYYYMM: Target year-month (e.g., "202510")
- PIPELINE_TARGET_PERIOD: Target period (e.g., "A", "B", or "" for full month)

If not set, tests will use defaults: 202510A

To run these tests:
    export PIPELINE_TARGET_YYYYMM=202510
    export PIPELINE_TARGET_PERIOD=A
    python3 -m pytest tests/step13/integration/test_step13_post_consolidation_validations.py -v

Or use the provided script:
    ./run_step13_tests_clean.sh
"""

import os
import glob
import subprocess
import pandas as pd
import pytest

# Set default test period if not already set
# This must be done BEFORE importing src.config
if "PIPELINE_TARGET_YYYYMM" not in os.environ:
    os.environ["PIPELINE_TARGET_YYYYMM"] = "202510"
if "PIPELINE_TARGET_PERIOD" not in os.environ:
    os.environ["PIPELINE_TARGET_PERIOD"] = "A"

# Now import config - it will read the environment variables we just set
from src.config import get_current_period, get_period_label


# ------------------- Helpers -------------------

def _period_label():
    """Get the current test period label."""
    yyyymm, period = get_current_period()
    return get_period_label(yyyymm, period)


def _latest(path_glob):
    candidates = sorted(glob.glob(path_glob))
    if not candidates:
        return None
    candidates.sort(key=lambda p: os.path.getmtime(p))
    return candidates[-1]


def _ensure_step13_run():
    # Runs Step 13 once if period outputs are missing. Assumes earlier steps have been run.
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    # Set target period for tests (override any existing values)
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"

    plabel = _period_label()
    detailed_glob = f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv"
    cluster_glob = "output/consolidated_cluster_subcategory_results*.csv"

    if os.path.exists(_latest(detailed_glob) or "") and os.path.exists(_latest(cluster_glob) or ""):
        return

    subprocess.run(["python3", "src/step13_consolidate_spu_rules.py",
                    "--target-yyyymm", "202510", "--target-period", "A"], 
                   check=True, env=env)


# ------------------- Tests -------------------


def test_step13_outputs_and_schema_exist():
    _ensure_step13_run()
    plabel = _period_label()

    detailed_path = _latest(f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv")
    store_summary_path = _latest("output/consolidated_spu_rule_results*.csv")
    cluster_summary_path = _latest("output/consolidated_cluster_subcategory_results*.csv")

    assert detailed_path and os.path.exists(detailed_path), "Detailed consolidated file not found"
    assert store_summary_path and os.path.exists(store_summary_path), "Store summary file not found"
    assert cluster_summary_path and os.path.exists(cluster_summary_path), "Cluster-subcategory summary file not found"

    # Basic schema checks
    detailed = pd.read_csv(detailed_path, nrows=1000, low_memory=False)
    assert len(detailed) > 0, "Detailed consolidated output is empty"

    required_detailed = {"str_code", "spu_code", "sub_cate_name", "recommended_quantity_change", "investment_required"}
    missing_detailed = [c for c in required_detailed if c not in detailed.columns]
    assert not missing_detailed, f"Detailed consolidated missing columns: {missing_detailed}"

    cluster = pd.read_csv(cluster_summary_path, nrows=1000, low_memory=False)
    assert len(cluster) >= 0, "Cluster summary seems unreadable"
    required_cluster = {"cluster", "subcategory", "total_quantity_change", "total_investment"}
    missing_cluster = [c for c in required_cluster if c not in cluster.columns]
    assert not missing_cluster, f"Cluster summary missing columns: {missing_cluster}"


@pytest.mark.timeout(60)
def test_step13_presence_of_target_subcategories_enforced():
    """Enforce presence of key pants-related subcategories after Step 13 (no env required).

    Uses hardcoded alias families aligned to observed taxonomy.
    """
    _ensure_step13_run()
    plabel = _period_label()

    detailed_path = _latest(f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv")
    assert detailed_path and os.path.exists(detailed_path), "Detailed consolidated file not found"

    df = pd.read_csv(detailed_path, usecols=["sub_cate_name"], low_memory=False)
    if "sub_cate_name" not in df.columns:
        pytest.skip("sub_cate_name not present; Step 7 enrichment may be disabled")

    s = df["sub_cate_name"].astype(str).str.lower()
    casual_aliases = ["直筒裤", "锥形裤", "阔腿裤", "工装裤", "喇叭裤", "烟管裤", "弯刀裤", "中裤", "短裤"]
    jogger_aliases = ["束脚裤"]
    casual_found = any(any(a.lower() in name for a in casual_aliases) for name in s)
    jogger_found = any(any(a.lower() in name for a in jogger_aliases) for name in s)

    assert casual_found, f"ABSENCE: Casual pants family not found in consolidated detailed output. Aliases={casual_aliases}"
    assert jogger_found, f"ABSENCE: Jogger pants not found in consolidated detailed output. Aliases={jogger_aliases}"


@pytest.mark.timeout(60)
def test_step13_minimum_store_volume_floor():
    _ensure_step13_run()
    plabel = _period_label()

    # Enforce a sensible default per-store floor (units). Adjust if needed.
    floor = float(os.getenv("STEP13_MIN_STORE_VOLUME_FLOOR", "10"))

    path = _latest(f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv")
    assert path and os.path.exists(path), "Detailed consolidated file not found"

    usecols = ["str_code", "recommended_quantity_change"]
    df = pd.read_csv(path, usecols=usecols, low_memory=False)
    if not set(usecols).issubset(df.columns):
        pytest.skip("Required columns not present for volume floor check; skipping")

    # Enforce floor on positive additions only (some rules may reduce quantities legitimately)
    df_add = df.copy()
    df_add["add_qty"] = df_add["recommended_quantity_change"].clip(lower=0)
    g = df_add.groupby("str_code", as_index=False)["add_qty"].sum()
    viol = g[g["add_qty"] < floor]
    assert viol.empty, (
        f"Stores under add-volume floor {floor}: {viol['str_code'].tolist()[:10]} (total {len(viol)})"
    )


@pytest.mark.timeout(60)
def test_step13_minimum_store_net_volume_floor():
    """Enforce a minimum NET allocation per store (adds - reductions).

    This surfaces true under-allocation when net goes negative. Default floor=0.
    """
    _ensure_step13_run()
    plabel = _period_label()

    net_floor = float(os.getenv("STEP13_MIN_STORE_NET_VOLUME_FLOOR", "0"))

    path = _latest(f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv")
    assert path and os.path.exists(path), "Detailed consolidated file not found"

    usecols = ["str_code", "recommended_quantity_change"]
    df = pd.read_csv(path, usecols=usecols, low_memory=False)
    if not set(usecols).issubset(df.columns):
        pytest.skip("Required columns not present for net volume floor check; skipping")

    g = df.groupby("str_code", as_index=False)["recommended_quantity_change"].sum()
    viol = g[g["recommended_quantity_change"] < net_floor]
    assert viol.empty, (
        f"Stores under NET volume floor {net_floor}: {viol['str_code'].tolist()[:10]} (total {len(viol)})"
    )


# ------------------- Hard-fail presence tests with meaningful names -------------------

def _subcat_found_in_detailed(aliases):
    plabel = _period_label()
    detailed_path = _latest(f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv")
    assert detailed_path and os.path.exists(detailed_path), "Detailed consolidated file not found"
    df = pd.read_csv(detailed_path, usecols=["sub_cate_name"], low_memory=False)
    if "sub_cate_name" not in df.columns:
        return False
    s = df["sub_cate_name"].astype(str).str.lower()
    return any(any(alias.lower() in name for alias in aliases) for name in s)


def test_step13_absence_of_casual_pants_fails():
    """FAILS if casual pants-like subcategories are absent after Step 13 consolidation.

    This catches the condition where casual pants (e.g., 9A bucket) never appear in the consolidated
    detailed output, meaning later steps cannot resurrect them.
    """
    _ensure_step13_run()
    # Hardcoded alias family for casual pants per observed taxonomy
    aliases = [
        "直筒裤", "锥形裤", "阔腿裤", "工装裤", "喇叭裤", "烟管裤", "弯刀裤", "中裤", "短裤"
    ]
    found = _subcat_found_in_detailed(aliases)
    assert found, (
        f"ABSENCE: Casual Pants not found in consolidated detailed output. Aliases tried={aliases}. "
        f"Ensure upstream rules (e.g., Step 7) produce coverage or add a post-13 top-up."
    )


def test_step13_absence_of_jogger_pants_fails():
    """FAILS if jogger-like subcategories are absent after Step 13 consolidation.

    Ensures jogger coverage exists before formatting/trend/sell-through enrichment, where it cannot be added.
    """
    _ensure_step13_run()
    # Hardcoded alias family for joggers per observed taxonomy
    aliases = ["束脚裤"]
    found = _subcat_found_in_detailed(aliases)
    assert found, (
        f"ABSENCE: Jogger pants not found in consolidated detailed output. Aliases tried={aliases}. "
        f"Ensure upstream rules (e.g., Step 7) produce coverage or add a post-13 top-up."
    )
