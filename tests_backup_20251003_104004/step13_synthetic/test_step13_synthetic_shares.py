import os

import numpy as np
import pandas as pd
import pytest

from tests.step13_synthetic.test_step13_synthetic_regression import (
    _prepare_sandbox,
    _seed_synthetic_inputs,
    _run_step13,
    _load_outputs,
)


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
def sandbox_outputs(tmp_path):
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_inputs(sandbox)
    _run_step13(sandbox)
    outputs = _load_outputs(sandbox)

    detailed = outputs["detailed"].copy()
    detailed["str_code"] = detailed["str_code"].astype(str)

    sales = pd.read_csv(sandbox / "data" / "api_data" / "complete_spu_sales_202501A.csv")
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
