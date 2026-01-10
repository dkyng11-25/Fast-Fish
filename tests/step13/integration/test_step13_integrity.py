"""
Step 13 Integration Tests - Store Summary and Aggregation Validation

SETUP REQUIREMENTS:
-------------------
These tests require Step 13 to have been run with the target period.

Environment Variables (REQUIRED):
- PIPELINE_TARGET_YYYYMM: Target year-month (e.g., "202510")
- PIPELINE_TARGET_PERIOD: Target period (e.g., "A", "B", or "" for full month)

If not set, tests will use defaults: 202510A

To run these tests:
    export PIPELINE_TARGET_YYYYMM=202510
    export PIPELINE_TARGET_PERIOD=A
    python3 -m pytest tests/step13/integration/test_step13_integrity.py -v

Or use the provided script:
    ./run_step13_tests_clean.sh
"""

import os
import glob
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
    # Assumes upstream steps have run; Step 13 itself is fast
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    # Set target period for tests (override any existing values)
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    plabel = _period_label()
    # Use wildcards to match timestamped files
    detailed_glob = f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv"
    cluster_glob = "output/consolidated_cluster_subcategory_results*.csv"
    store_glob = "output/consolidated_spu_rule_results*.csv"
    if all(_latest(g) for g in [detailed_glob, cluster_glob, store_glob]):
        return
    import subprocess
    subprocess.run(["python3", "src/step13_consolidate_spu_rules.py", 
                    "--target-yyyymm", "202510", "--target-period", "A"], 
                   check=True, env=env)


@pytest.mark.timeout(60)
def test_step13_store_summary_matches_detailed():
    _ensure_step13_run()
    plabel = _period_label()

    detailed_path = _latest(f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv")
    store_summary_path = _latest("output/consolidated_spu_rule_results*.csv")
    assert detailed_path and os.path.exists(detailed_path), f"Detailed file not found for period {plabel}"
    assert store_summary_path and os.path.exists(store_summary_path), "Store summary file not found"

    dcols = ["str_code", "recommended_quantity_change", "period_label", "target_yyyymm", "target_period"]
    detailed = pd.read_csv(detailed_path, usecols=[c for c in dcols if c in pd.read_csv(detailed_path, nrows=1).columns], low_memory=False)
    if not set(dcols[:2]).issubset(detailed.columns):
        pytest.skip("Detailed output missing required columns; cannot verify store summary integrity")

    store = pd.read_csv(store_summary_path, low_memory=False)
    # Try to find an appropriate total column in store summary
    candidate_totals = [
        "total_quantity_change", "total_quantity_needed", "recommended_quantity_change",
    ]
    total_col = next((c for c in candidate_totals if c in store.columns), None)
    if total_col is None or "str_code" not in store.columns:
        pytest.skip("Store summary missing str_code/total columns; cannot verify")

    # Filter to the same period if period fields are available
    if {"period_label", "target_yyyymm", "target_period"}.issubset(detailed.columns) and {"period_label", "target_yyyymm", "target_period"}.issubset(store.columns):
        d_keys = detailed[["period_label", "target_yyyymm", "target_period"]].drop_duplicates().head(1)
        if not d_keys.empty:
            pl, ty, tp = d_keys.iloc[0].tolist()
            detailed = detailed[(detailed["period_label"] == pl) & (detailed["target_yyyymm"] == ty) & (detailed["target_period"] == tp)]
            store = store[(store["period_label"] == pl) & (store["target_yyyymm"] == ty) & (store["target_period"] == tp)]

    # Compare adds-only totals (business: store summary typically reflects approved adds)
    det_add = detailed.copy()
    det_add["add_qty"] = det_add["recommended_quantity_change"].clip(lower=0)
    agg = det_add.groupby("str_code", as_index=False)["add_qty"].sum()

    store = store.copy()
    store["store_add_qty"] = pd.to_numeric(store[total_col], errors="coerce").fillna(0).clip(lower=0)
    store_sum = store.groupby("str_code", as_index=False)["store_add_qty"].sum()

    merged = agg.merge(store_sum, on="str_code", how="inner")
    # Allow small numeric tolerance
    diff = (merged["add_qty"] - merged["store_add_qty"]).abs()
    assert (diff < 1e-6).all(), (
        f"Store summary adds-only totals mismatch for {int((diff >= 1e-6).sum())} stores; max abs diff={diff.max()}"
    )


@pytest.mark.timeout(60)
def test_step13_cluster_subcategory_sums_match_detailed():
    _ensure_step13_run()
    plabel = _period_label()

    detailed_path = _latest(f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv")
    cluster_summary_path = _latest("output/consolidated_cluster_subcategory_results*.csv")
    assert detailed_path and os.path.exists(detailed_path)
    assert cluster_summary_path and os.path.exists(cluster_summary_path)

    # Detailed needs cluster/subcategory
    d_keep = ["sub_cate_name", "recommended_quantity_change"]
    cluster_col = None
    # try common cluster column names
    for c in ["cluster_id", "Cluster_ID", "cluster"]:
        if c in pd.read_csv(detailed_path, nrows=1).columns:
            cluster_col = c
            d_keep.insert(0, c)
            break
    if cluster_col is None:
        pytest.skip("No cluster column in detailed output; cannot verify cluster-subcategory sums")

    detailed = pd.read_csv(detailed_path, usecols=d_keep, low_memory=False)
    d_agg = detailed.groupby([cluster_col, "sub_cate_name"], as_index=False)["recommended_quantity_change"].sum()

    # Cluster summary expected columns
    cluster = pd.read_csv(cluster_summary_path, low_memory=False)
    if not {"cluster", "subcategory", "total_quantity_change"}.issubset(cluster.columns):
        pytest.skip("Cluster summary missing expected columns")
    cluster_ren = cluster.rename(columns={"cluster": cluster_col, "subcategory": "sub_cate_name"})

    merged = d_agg.merge(cluster_ren[[cluster_col, "sub_cate_name", "total_quantity_change"]],
                         on=[cluster_col, "sub_cate_name"], how="inner")
    diff = (merged["recommended_quantity_change"] - merged["total_quantity_change"]).abs()
    assert (diff < 1e-6).all(), (
        f"Cluster-subcategory totals mismatch for {int((diff >= 1e-6).sum())} rows; max abs diff={diff.max()}"
    )


@pytest.mark.timeout(90)
def test_step13_no_sales_new_classes_blocked():
    """Every allocated (cluster, sub_cate_name) should have positive peer sales in that cluster.
    Uses current-period SPU sales + cluster mapping to compute cluster-subcategory sales.
    """
    _ensure_step13_run()
    from src.config import get_api_data_files
    yyyymm, period = __import__("src.config", fromlist=["get_current_period"]).get_current_period()
    plabel = _period_label()

    detailed_path = _latest(f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv")
    assert detailed_path and os.path.exists(detailed_path)

    # Load detailed
    det = pd.read_csv(detailed_path, low_memory=False)
    # Need cluster and subcategory
    cluster_col = next((c for c in ["cluster_id", "Cluster_ID", "cluster"] if c in det.columns), None)
    if cluster_col is None or "sub_cate_name" not in det.columns:
        pytest.skip("Detailed output missing cluster/sub_cate_name; cannot validate no-sales guard")

    # Load SPU sales current period
    api_paths = get_api_data_files(yyyymm, period)
    sales_path = api_paths.get("complete_spu_sales") or api_paths.get("spu_sales")
    if sales_path is None or not os.path.exists(sales_path):
        # Fallback to pattern
        sales_path = _latest(f"data/api_data/complete_spu_sales_{plabel}.csv")
    assert sales_path and os.path.exists(sales_path), "SPU sales file not found"

    sales_cols = ["str_code", "sub_cate_name", "spu_sales_amt", "sal_amt", "sales_amt"]
    s_df = pd.read_csv(sales_path, usecols=[c for c in sales_cols if c in pd.read_csv(sales_path, nrows=1).columns], low_memory=False)
    # unify sales amount column
    for c in ["spu_sales_amt", "sal_amt", "sales_amt"]:
        if c in s_df.columns:
            s_df["sales_amt_unified"] = pd.to_numeric(s_df[c], errors="coerce")
            break
    assert "sales_amt_unified" in s_df.columns, "No sales amount column in SPU sales file"

    # Load cluster mapping for stores for this period
    cluster_candidates = [
        f"output/clustering_results_spu_{plabel}.csv",
        "output/clustering_results_spu.csv",
    ]
    cpath = next((p for p in cluster_candidates if os.path.exists(p)), None)
    assert cpath, "Cluster mapping file for SPU not found"
    # Clustering file has 'Cluster' column, rename to 'cluster_id' for consistency
    cmap = pd.read_csv(cpath, dtype={"str_code": str}, low_memory=False)
    if 'Cluster' in cmap.columns and 'cluster_id' not in cmap.columns:
        cmap = cmap.rename(columns={'Cluster': 'cluster_id'})
    cmap = cmap[["str_code", "cluster_id"]]

    # Coerce join keys to consistent dtype
    s_df["str_code"] = s_df["str_code"].astype(str)
    cmap["str_code"] = cmap["str_code"].astype(str)
    s_df = s_df.merge(cmap, on="str_code", how="left")
    s_df = s_df.dropna(subset=["cluster_id"])  # keep rows with cluster id
    sales_agg = s_df.groupby(["cluster_id", "sub_cate_name"], as_index=False)["sales_amt_unified"].sum()

    # For each allocated (cluster, subcategory), assert positive peer sales
    alloc_pairs = det[[cluster_col, "sub_cate_name"]].dropna().drop_duplicates()
    merged = alloc_pairs.merge(sales_agg.rename(columns={"cluster_id": cluster_col}),
                               on=[cluster_col, "sub_cate_name"], how="left")
    missing = merged[merged["sales_amt_unified"].isna() | (merged["sales_amt_unified"] <= 0)]
    assert missing.empty, (
        f"No-sales leakage: {len(missing)} (cluster, sub_cate_name) pairs have zero peer sales. "
        f"Examples: {missing.head(10).to_dict(orient='records')}"
    )


@pytest.mark.timeout(120)
def test_step13_allocations_follow_sales_distribution():
    """Allocation shares for pants family should roughly follow each store's historical sales shares.
    Flags large drift to avoid severe under/over-weighting pre-formatting.
    """
    _ensure_step13_run()
    from src.config import get_api_data_files
    yyyymm, period = __import__("src.config", fromlist=["get_current_period"]).get_current_period()
    plabel = _period_label()

    detailed_path = _latest(f"output/consolidated_spu_rule_results_detailed_{plabel}*.csv")
    assert detailed_path and os.path.exists(detailed_path)

    det = pd.read_csv(detailed_path, usecols=["str_code", "sub_cate_name", "recommended_quantity_change"], low_memory=False)
    # consider add-qty shares only
    det = det.assign(add_qty=det["recommended_quantity_change"].clip(lower=0))

    pants_aliases = ["直筒裤", "锥形裤", "阔腿裤", "工装裤", "喇叭裤", "烟管裤", "弯刀裤", "中裤", "短裤", "束脚裤"]

    def label_family(name: str) -> str:
        s = str(name).lower()
        for a in pants_aliases:
            if a.lower() in s:
                return a
        return None

    det["family"] = det["sub_cate_name"].map(label_family)
    det_fam = det.dropna(subset=["family"])  # only pants family
    if det_fam.empty:
        pytest.skip("No pants-family allocations present; cannot evaluate distribution alignment")

    # Sales by store and family
    api_paths = get_api_data_files(yyyymm, period)
    sales_path = api_paths.get("complete_spu_sales") or api_paths.get("spu_sales")
    if sales_path is None or not os.path.exists(sales_path):
        sales_path = _latest(f"data/api_data/complete_spu_sales_{plabel}.csv")
    assert sales_path and os.path.exists(sales_path)

    s_use = ["str_code", "sub_cate_name", "spu_sales_amt", "sal_amt", "sales_amt"]
    s_df = pd.read_csv(sales_path, usecols=[c for c in s_use if c in pd.read_csv(sales_path, nrows=1).columns], low_memory=False)
    for c in ["spu_sales_amt", "sal_amt", "sales_amt"]:
        if c in s_df.columns:
            s_df["sales_amt"] = pd.to_numeric(s_df[c], errors="coerce")
            break
    assert "sales_amt" in s_df.columns

    s_df["family"] = s_df["sub_cate_name"].map(label_family)
    s_fam = s_df.dropna(subset=["family"]).copy()

    # per-store allocation share vs sales share by family alias
    alloc = det_fam.groupby(["str_code", "family"], as_index=False)["add_qty"].sum()
    alloc_tot = alloc.groupby("str_code", as_index=False)["add_qty"].sum().rename(columns={"add_qty": "alloc_tot"})
    alloc = alloc.merge(alloc_tot, on="str_code", how="left")
    alloc["alloc_share"] = alloc["add_qty"] / alloc["alloc_tot"].where(alloc["alloc_tot"] > 0)

    sales = s_fam.groupby(["str_code", "family"], as_index=False)["sales_amt"].sum()
    sales_tot = sales.groupby("str_code", as_index=False)["sales_amt"].sum().rename(columns={"sales_amt": "sales_tot"})
    sales = sales.merge(sales_tot, on="str_code", how="left")
    sales["sales_share"] = sales["sales_amt"] / sales["sales_tot"].where(sales["sales_tot"] > 0)

    comp = alloc.merge(sales[["str_code", "family", "sales_share", "sales_tot"]], on=["str_code", "family"], how="left")

    # Threshold for absolute share error
    thresh = float(os.getenv("STEP13_SALES_SHARE_MAX_ABS_ERROR", "0.15"))
    comp["abs_err"] = (comp["alloc_share"] - comp["sales_share"]).abs()

    # Only evaluate where both sides have valid denominators/shares
    viol = comp[(comp["alloc_tot"] > 0) & comp["sales_share"].notna() & (comp["abs_err"] > thresh)]
    assert viol.empty, (
        f"Allocation vs sales share drift > {thresh} for {len(viol)} (store,family) pairs. "
        f"Examples: {viol.head(10).to_dict(orient='records')}"
    )
