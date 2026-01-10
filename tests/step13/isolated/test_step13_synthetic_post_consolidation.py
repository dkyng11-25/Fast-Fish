"""
Step 13 Synthetic Post-Consolidation Tests

Tests that validate Step 13's post-consolidation logic using complete synthetic fixtures.
"""

import os
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Test constants
TARGET_YYYYMM = "202510"
TARGET_PERIOD = "A"
PERIOD_LABEL = f"{TARGET_YYYYMM}{TARGET_PERIOD}"


def _run_step13(sandbox: Path, env_overrides: dict = None) -> None:
    """Run Step 13 in the sandbox environment with optional env overrides."""
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    env.setdefault("PYTHONPATH", str(sandbox))
    
    # Apply any environment overrides
    if env_overrides:
        env.update(env_overrides)
    
    subprocess.run(
        ["python3", "src/step13_consolidate_spu_rules.py",
         "--target-yyyymm", TARGET_YYYYMM, "--target-period", TARGET_PERIOD],
        cwd=sandbox,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _load_outputs(sandbox: Path) -> dict:
    """Load Step 13 outputs from sandbox."""
    detailed_path = sandbox / "output" / f"consolidated_spu_rule_results_detailed_{PERIOD_LABEL}.csv"
    store_path = sandbox / "output" / "consolidated_spu_rule_results.csv"
    cluster_path = sandbox / "output" / "consolidated_cluster_subcategory_results.csv"

    return {
        "detailed": pd.read_csv(detailed_path),
        "store": pd.read_csv(store_path),
        "cluster": pd.read_csv(cluster_path),
    }


@pytest.fixture()
def sandbox_outputs(step13_sandbox):
    """
    Fixture that runs Step 13 and returns processed outputs.
    Uses step13_sandbox from conftest.py for the environment.
    """
    _run_step13(step13_sandbox)
    outputs = _load_outputs(step13_sandbox)

    detailed = outputs["detailed"].copy()
    detailed["str_code"] = detailed["str_code"].astype(str)
    detailed["add_qty"] = detailed["recommended_quantity_change"].clip(lower=0)

    store = outputs["store"].copy()
    if "str_code" in store.columns:
        store["str_code"] = store["str_code"].astype(str)

    cluster = outputs["cluster"].copy()

    return {
        "sandbox": step13_sandbox,
        "detailed": detailed,
        "store": store,
        "cluster": cluster,
    }


def test_outputs_and_schema_exist_isolated(sandbox_outputs):
    detailed = sandbox_outputs["detailed"]
    store = sandbox_outputs["store"]
    cluster = sandbox_outputs["cluster"]

    required_detailed = {
        "str_code",
        "spu_code",
        "sub_cate_name",
        "recommended_quantity_change",
        "investment_required",
    }
    missing_detailed = required_detailed - set(detailed.columns)
    assert not missing_detailed, f"Missing detailed columns: {missing_detailed}"

    required_cluster = {"cluster", "subcategory", "total_quantity_change", "total_investment"}
    missing_cluster = required_cluster - set(cluster.columns)
    assert not missing_cluster, f"Missing cluster columns: {missing_cluster}"

    required_store = {"str_code", "total_quantity_change", "total_investment"}
    missing_store = required_store - set(store.columns)
    assert not missing_store, f"Missing store columns: {missing_store}"


def test_presence_of_target_subcategories_isolated(sandbox_outputs):
    detailed = sandbox_outputs["detailed"]
    names = detailed["sub_cate_name"].astype(str).str.lower()

    casual_aliases = ["直筒裤", "锥形裤", "阔腿裤", "工装裤", "喇叭裤", "烟管裤", "弯刀裤", "中裤", "短裤"]
    jogger_aliases = ["束脚裤"]

    casual_found = any(any(alias.lower() in name for alias in casual_aliases) for name in names)
    jogger_found = any(any(alias.lower() in name for alias in jogger_aliases) for name in names)

    assert casual_found, "Casual pants aliases not found in synthetic detailed output"
    assert jogger_found, "Jogger pants alias not found in synthetic detailed output"


def test_minimum_store_volume_floor_isolated(sandbox_outputs):
    detailed = sandbox_outputs["detailed"]
    floor = float(os.getenv("STEP13_MIN_STORE_VOLUME_FLOOR", "10"))

    store_adds = detailed.groupby("str_code", as_index=False)["add_qty"].sum()
    viol = store_adds[store_adds["add_qty"] + 1e-9 < floor]
    assert viol.empty, f"Stores under add-volume floor {floor}: {viol}"


def test_minimum_store_net_volume_floor_isolated(sandbox_outputs):
    detailed = sandbox_outputs["detailed"]
    net_floor = float(os.getenv("STEP13_MIN_STORE_NET_VOLUME_FLOOR", "0"))

    net = detailed.groupby("str_code", as_index=False)["recommended_quantity_change"].sum()
    viol = net[net["recommended_quantity_change"] + 1e-9 < net_floor]
    assert viol.empty, f"Stores under net volume floor {net_floor}: {viol}"


def test_net_reductions_remain_above_floor_when_env_override(step13_sandbox):
    """
    Test that net volume floor is enforced when set via environment variable.
    Uses step13_sandbox from conftest.py for the environment.
    """
    # Modify rule file to introduce a negative adjustment for store 1002
    # (fixtures are already created by step13_sandbox)
    detailed_path = step13_sandbox / "output" / f"rule10_smart_overcapacity_results_{PERIOD_LABEL}.csv"
    df = pd.read_csv(detailed_path)
    # Find a store and set negative recommendation
    if len(df) > 0:
        df.loc[0, "recommended_quantity_change"] = -5.0
        df.to_csv(detailed_path, index=False)
    
    # Run Step 13 with net volume floor override
    _run_step13(step13_sandbox, env_overrides={"STEP13_MIN_STORE_NET_VOLUME_FLOOR": "0"})

    detailed = pd.read_csv(
        step13_sandbox / "output" / f"consolidated_spu_rule_results_detailed_{PERIOD_LABEL}.csv"
    )
    detailed["str_code"] = detailed["str_code"].astype(str)
    net = detailed.groupby("str_code", as_index=False)["recommended_quantity_change"].sum()
    assert (net["recommended_quantity_change"] >= 0 - 1e-9).all(), "Net floor overriden scenario violated"
