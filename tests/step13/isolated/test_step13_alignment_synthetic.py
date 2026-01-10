import os
import pandas as pd
import numpy as np
from src.step13_consolidate_spu_rules import apply_data_quality_corrections

# Utilities
PANTS = ["直筒裤", "工装裤", "锥形裤"]

def _setup_sales(period_label: str, rows: list[dict]):
    os.makedirs("data/api_data", exist_ok=True)
    path = f"data/api_data/complete_spu_sales_{period_label}.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path

def _alloc_shares(df: pd.DataFrame):
    d = df.copy()
    d["add_qty"] = d["recommended_quantity_change"].clip(lower=0)
    fam = d[d["sub_cate_name"].isin(PANTS)].groupby(["str_code","sub_cate_name"], as_index=False)["add_qty"].sum()
    tot = fam.groupby("str_code", as_index=False)["add_qty"].sum().rename(columns={"add_qty":"alloc_tot"})
    fam = fam.merge(tot, on="str_code", how="left")
    fam["alloc_share"] = fam["add_qty"] / fam["alloc_tot"].where(fam["alloc_tot"]>0)
    return fam

def _sales_shares(sales_rows: list[dict]):
    s = pd.DataFrame(sales_rows)
    s = s[s["sub_cate_name"].isin(PANTS)].copy()
    g = s.groupby(["str_code","sub_cate_name"], as_index=False)["sales_amt"].sum()
    tot = g.groupby("str_code", as_index=False)["sales_amt"].sum().rename(columns={"sales_amt":"sales_tot"})
    g = g.merge(tot, on="str_code", how="left")
    g["sales_share"] = g["sales_amt"] / g["sales_tot"].where(g["sales_tot"]>0)
    return g

def test_alignment_non_zero_mix(tmp_path):
    # Baseline period and sales
    os.environ["PIPELINE_TARGET_YYYYMM"] = "209901"
    os.environ["PIPELINE_TARGET_PERIOD"] = "A"
    plabel = "209901A"

    sales_rows = [
        {"str_code":"S1","sub_cate_name":"直筒裤","sales_amt":600},
        {"str_code":"S1","sub_cate_name":"工装裤","sales_amt":400},
    ]
    _setup_sales(plabel, sales_rows)

    # Skewed initial adds (90/10) should be pulled toward 60/40 within 0.15 abs error
    cons = pd.DataFrame([
        {"str_code":"S1","spu_code":"A1","sub_cate_name":"直筒裤","recommended_quantity_change":9.0},
        {"str_code":"S1","spu_code":"B1","sub_cate_name":"工装裤","recommended_quantity_change":1.0},
    ])

    corrected, _, _ = apply_data_quality_corrections(cons)
    fam = _alloc_shares(corrected)
    sales = _sales_shares(sales_rows)
    comp = fam.merge(sales[["str_code","sub_cate_name","sales_share"]], on=["str_code","sub_cate_name"], how="left")
    comp["abs_err"] = (comp["alloc_share"] - comp["sales_share"]).abs()
    assert comp["abs_err"].max() <= 0.15


def test_alignment_zero_history_cap(tmp_path):
    # Baseline where S2 has 0% for 直筒裤 and 100% for 工装裤
    os.environ["PIPELINE_TARGET_YYYYMM"] = "209902"
    os.environ["PIPELINE_TARGET_PERIOD"] = "A"
    plabel = "209902A"

    # Provide minimal baseline sales for the new family so no-sales enforcement won't prune it
    sales_rows = [
        {"str_code":"S2","sub_cate_name":"工装裤","sales_amt":1000},
        {"str_code":"S2","sub_cate_name":"直筒裤","sales_amt":1},
    ]
    _setup_sales(plabel, sales_rows)

    # Initial adds give 1 unit of 直筒裤 and 9 units of 工装裤 (10% share for 直筒裤)
    cons = pd.DataFrame([
        {"str_code":"S2","spu_code":"C1","sub_cate_name":"直筒裤","recommended_quantity_change":1.0},
        {"str_code":"S2","spu_code":"D1","sub_cate_name":"工装裤","recommended_quantity_change":9.0},
    ])

    # Allow default cap 0.15 for zero-history seeding; expect aligned share for 直筒裤 <= 0.15
    corrected, _, _ = apply_data_quality_corrections(cons)
    fam = _alloc_shares(corrected)
    share_new = fam.loc[(fam["str_code"]=="S2") & (fam["sub_cate_name"]=="直筒裤"), "alloc_share"].max()
    assert pd.notna(share_new) and share_new <= 0.15
