import os
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tests.step13_synthetic.test_step13_synthetic_regression import (
    TARGET_PERIOD,
    TARGET_YYYYMM,
    PERIOD_LABEL,
    _prepare_sandbox,
    _seed_synthetic_inputs,
    _run_step13,
    _load_outputs,
)


@pytest.fixture()
def sandbox_outputs(tmp_path):
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_inputs(sandbox)

    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    env.setdefault("PYTHONPATH", str(sandbox))

    _run_step13(sandbox)
    outputs = _load_outputs(sandbox)

    detailed = outputs["detailed"].copy()
    detailed["str_code"] = detailed["str_code"].astype(str)
    detailed["add_qty"] = detailed["recommended_quantity_change"].clip(lower=0)

    store = outputs["store"].copy()
    if "str_code" in store.columns:
        store["str_code"] = store["str_code"].astype(str)

    cluster = outputs["cluster"].copy()

    return {
        "sandbox": sandbox,
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


def test_net_reductions_remain_above_floor_when_env_override(tmp_path):
    sandbox = _prepare_sandbox(tmp_path)

    # Seed base inputs then introduce a negative adjustment for store 1002
    _seed_synthetic_inputs(sandbox)
    detailed_path = sandbox / "output" / f"rule10_spu_overcapacity_opportunities_{PERIOD_LABEL}.csv"
    df = pd.read_csv(detailed_path)
    df.loc[df["str_code"] == "1002", "recommended_quantity_change"] = -5.0
    df.to_csv(detailed_path, index=False)

    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    env["STEP13_MIN_STORE_NET_VOLUME_FLOOR"] = "0"
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

    detailed = pd.read_csv(
        sandbox / "output" / f"consolidated_spu_rule_results_detailed_{PERIOD_LABEL}.csv"
    )
    detailed["str_code"] = detailed["str_code"].astype(str)
    net = detailed.groupby("str_code", as_index=False)["recommended_quantity_change"].sum()
    assert (net["recommended_quantity_change"] >= 0 - 1e-9).all(), "Net floor overriden scenario violated"
