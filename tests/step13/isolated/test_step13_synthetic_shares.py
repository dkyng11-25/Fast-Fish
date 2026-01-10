"""
Step 13 Synthetic Share Alignment Tests

Tests that validate Step 13's share alignment logic using complete synthetic fixtures.
"""

import os
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import pytest


def _run_step13(sandbox: Path) -> None:
    """Run Step 13 in the sandbox environment."""
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env.setdefault("PYTHONPATH", str(sandbox))
    subprocess.run(
        ["python3", "src/step13_consolidate_spu_rules.py",
         "--target-yyyymm", "202510", "--target-period", "A"],
        cwd=sandbox,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _load_outputs(sandbox: Path) -> dict:
    """Load Step 13 outputs from sandbox."""
    detailed_path = sandbox / "output" / "consolidated_spu_rule_results_detailed_202510A.csv"
    store_path = sandbox / "output" / "consolidated_spu_rule_results.csv"
    cluster_path = sandbox / "output" / "consolidated_cluster_subcategory_results.csv"

    return {
        "detailed": pd.read_csv(detailed_path),
        "store": pd.read_csv(store_path),
        "cluster": pd.read_csv(cluster_path),
    }


PANTS = {"直筒裤", "锥形裤", "阔腿裤", "工装裤", "喇叭裤", "烟管裤", "弯刀裤", "中裤", "短裤", "束脚裤"}


def _label_family(sub_cate_name: str | float) -> str | None:
    s = str(sub_cate_name).lower()
    for alias in PANTS:
        if alias.lower() in s:
            return alias
    return None


def _alloc_shares(detailed: pd.DataFrame) -> pd.DataFrame:
    fam = detailed.copy()
    fam["add_qty"] = fam["recommended_quantity_change"].clip(lower=0)
    fam["family"] = fam["sub_cate_name"].map(_label_family)
    fam = fam.dropna(subset=["family"])
    if fam.empty:
        return fam
    agg = fam.groupby(["str_code", "family"], as_index=False)["add_qty"].sum()
    tot = agg.groupby("str_code", as_index=False)["add_qty"].sum().rename(columns={"add_qty": "alloc_tot"})
    agg = agg.merge(tot, on="str_code", how="left")
    agg["alloc_share"] = np.where(agg["alloc_tot"] > 0, agg["add_qty"] / agg["alloc_tot"], np.nan)
    return agg


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

    sales = pd.read_csv(step13_sandbox / "data" / "api_data" / "complete_spu_sales_202410A.csv")
    sales["str_code"] = sales["str_code"].astype(str)
    sales["family"] = sales["sub_cate_name"].map(_label_family)
    sales = sales.dropna(subset=["family"])
    sales_tot = sales.groupby("str_code", as_index=False)["spu_sales_amt"].sum().rename(columns={"spu_sales_amt": "sales_tot"})
    sales = sales.groupby(["str_code", "family"], as_index=False)["spu_sales_amt"].sum()
    sales = sales.merge(sales_tot, on="str_code", how="left")
    sales["sales_share"] = np.where(sales["sales_tot"] > 0, sales["spu_sales_amt"] / sales["sales_tot"], np.nan)

    return detailed, sales


def test_allocations_follow_sales_distribution_isolated(sandbox_outputs):
    detailed, sales = sandbox_outputs

    alloc = _alloc_shares(detailed)
    assert not alloc.empty, "No pants-family allocations found"

    comp = alloc.merge(
        sales[["str_code", "family", "sales_share"]],
        on=["str_code", "family"],
        how="left",
    )

    thresh = float(os.getenv("STEP13_SALES_SHARE_MAX_ABS_ERROR", "0.15"))
    comp["abs_err"] = (comp["alloc_share"] - comp["sales_share"]).abs()
    viol = comp[(comp["alloc_tot"] > 0) & comp["sales_share"].notna() & (comp["abs_err"] > thresh)]
    assert viol.empty, (
        f"Allocation vs sales share drift > {thresh} for {len(viol)} pairs: "
        f"{viol[['str_code', 'family', 'alloc_share', 'sales_share']].to_dict(orient='records')}"
    )
