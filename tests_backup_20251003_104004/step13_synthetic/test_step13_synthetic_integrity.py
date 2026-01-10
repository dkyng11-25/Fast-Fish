import numpy as np
import pandas as pd
import pytest

from tests.step13_synthetic.test_step13_synthetic_regression import (
    TARGET_PERIOD,
    TARGET_YYYYMM,
    _prepare_sandbox,
    _seed_synthetic_inputs,
    _run_step13,
    _load_outputs,
)


@pytest.fixture()
def sandbox_outputs(tmp_path):
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_inputs(sandbox)
    _run_step13(sandbox)
    outputs = _load_outputs(sandbox)

    detailed = outputs["detailed"].copy()
    detailed["str_code"] = detailed["str_code"].astype(str)
    detailed["add_qty"] = detailed["recommended_quantity_change"].clip(lower=0)

    store = outputs["store"].copy()
    store["str_code"] = store["str_code"].astype(str)

    cluster = outputs["cluster"].copy()
    cluster = cluster.rename(columns={"cluster": "cluster_id", "subcategory": "sub_cate_name"})
    cluster["cluster_id"] = cluster["cluster_id"].astype(str)

    return detailed, store, cluster


def test_store_summary_matches_detailed_isolated(sandbox_outputs):
    detailed, store, _ = sandbox_outputs

    store_adds = detailed.groupby("str_code", as_index=False)["add_qty"].sum()
    total_col = next(
        (c for c in ["total_quantity_change", "recommended_quantity_change", "total_quantity_needed"] if c in store.columns),
        None,
    )
    assert total_col is not None

    store_sum = store.copy()
    store_sum["store_add_qty"] = pd.to_numeric(store_sum[total_col], errors="coerce").fillna(0).clip(lower=0)
    store_summary = store_sum.groupby("str_code", as_index=False)["store_add_qty"].sum()

    merged = store_adds.merge(store_summary, on="str_code", how="left")
    assert np.allclose(merged["add_qty"], merged["store_add_qty"], atol=1e-6)


def test_cluster_subcategory_sums_match_detailed_isolated(sandbox_outputs):
    detailed, _, cluster = sandbox_outputs

    cluster_id_col = "cluster_id" if "cluster_id" in detailed.columns else next(
        c for c in ["Cluster_ID", "cluster"] if c in detailed.columns
    )

    cluster_det = detailed.groupby([cluster_id_col, "sub_cate_name"], as_index=False)["recommended_quantity_change"].sum()
    cluster_det[cluster_id_col] = cluster_det[cluster_id_col].astype(str)

    merged = cluster_det.merge(
        cluster[["cluster_id", "sub_cate_name", "total_quantity_change"]],
        left_on=[cluster_id_col, "sub_cate_name"],
        right_on=["cluster_id", "sub_cate_name"],
        how="left",
    )

    diff = (merged["recommended_quantity_change"] - merged["total_quantity_change"]).abs()
    assert (diff <= 1e-6).all(), f"Cluster totals mismatch: {diff.max()}"
