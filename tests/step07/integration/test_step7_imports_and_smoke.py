"""
Step 7 Integration Tests - Imports and Output Validation

TEST REQUIREMENTS FOR PASSING:
================================

1. DATA REQUIREMENTS:
   - Must have sales data files: data/api_data/complete_spu_sales_{PERIOD}.csv
   - Must have clustering results: output/clustering_results_subcategory_{PERIOD}.csv
   - Must have store sales data: data/api_data/store_sales_{PERIOD}.csv
   
2. PERIOD CONFIGURATION:
   - Default fallback period: 202410A
   - To use a different period, set environment variables:
     * PIPELINE_TARGET_YYYYMM=YYYYMM (e.g., "202410")
     * PIPELINE_TARGET_PERIOD=A or B
   
3. CLUSTERING FILE REQUIREMENTS:
   - File must exist: output/clustering_results_subcategory_{PERIOD}.csv
   - Must contain columns: str_code, Cluster (or cluster_id)
   - Must have actual store codes (not test data like S001, S002)
   - Store codes must match those in sales data files
   
4. COMMON FAILURE MODES:
   
   a) "Sales data not found: complete_spu_sales_None.csv"
      → CAUSE: get_current_period() returned (None, None)
      → FIX: Set PIPELINE_TARGET_YYYYMM and PIPELINE_TARGET_PERIOD env vars
      
   b) "Clustering results not found"
      → CAUSE: No clustering file for the target period
      → FIX: Create symlink: clustering_results_subcategory_{PERIOD}.csv
      
   c) "Stores analyzed: 0" or very few stores
      → CAUSE: Clustering file has test data or wrong store codes
      → FIX: Ensure clustering file has real store codes matching sales data
      
   d) Test runs but finds 0 opportunities
      → CAUSE: Using wrong analysis level (spu vs subcategory)
      → FIX: Check that test uses correct --analysis-level flag

5. DEBUGGING CHECKLIST:
   - [ ] Check period label returned by _period_label()
   - [ ] Verify sales data exists for that period
   - [ ] Verify clustering file exists and has correct store codes
   - [ ] Check that environment variables are passed to subprocess
   - [ ] Ensure CLI arguments use --yyyymm and --period (not --target-*)
"""

import os
import glob
import subprocess
import pandas as pd
import pytest


def _period_label():
    """
    Get the period label for testing.
    
    Returns the period from environment variables, or falls back to 202410A.
    
    IMPORTANT: This function must return a period that has:
    - Sales data in data/api_data/complete_spu_sales_{PERIOD}.csv
    - Clustering results in output/clustering_results_subcategory_{PERIOD}.csv
    - Store sales data in data/api_data/store_sales_{PERIOD}.csv
    """
    from src.config import get_current_period, get_period_label
    yyyymm, period = get_current_period()
    
    # Fallback to a known good period if environment not configured
    if yyyymm is None or period is None:
        # Use 202410A as default (we know this data exists)
        # UPDATE THIS if you change the default test period
        yyyymm, period = "202410", "A"
    
    return get_period_label(yyyymm, period)


def _latest(path_glob):
    candidates = sorted(glob.glob(path_glob))
    if not candidates:
        return None
    candidates.sort(key=lambda p: os.path.getmtime(p))
    return candidates[-1]


def _ensure_step7_run():
    """
    Run Step 7 if outputs don't already exist for the current period.
    
    CRITICAL CONFIGURATION NOTES:
    - Uses permissive settings to ensure test reliability
    - Environment variables MUST be set before subprocess.run()
    - CLI arguments MUST use --yyyymm and --period (NOT --target-yyyymm/--target-period)
    - The subprocess inherits env vars via the env= parameter
    
    TROUBLESHOOTING:
    - If Step 7 fails with "Sales data not found: complete_spu_sales_None.csv":
      → Check that env["PIPELINE_TARGET_YYYYMM"] and env["PIPELINE_TARGET_PERIOD"] are set
      → Verify CLI args are --yyyymm and --period (not --target-*)
    
    - If Step 7 runs but finds 0 stores:
      → Check clustering file exists: output/clustering_results_subcategory_{PERIOD}.csv
      → Verify clustering file has real store codes (not S001, S002 test data)
    """
    # Run Step 7 in a permissive, fast configuration so the test is reliable
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", ".")
    env.setdefault("USE_BLENDED_SEASONAL", "1")
    env.setdefault("RECENT_MONTHS_BACK", "3")
    env.setdefault("SEASONAL_YEARS_BACK", "0")
    env.setdefault("RULE7_USE_ROI", "0")
    env.setdefault("RULE7_MIN_STORES_SELLING", "2")
    env.setdefault("RULE7_MIN_ADOPTION", "0.10")
    env.setdefault("RULE7_MIN_PREDICTED_ST", "15")

    # If outputs already exist for the current period, skip re-run
    plabel = _period_label()
    opp_glob = f"output/rule7_missing_spu_sellthrough_opportunities_{plabel}.csv"
    res_glob = f"output/rule7_missing_spu_sellthrough_results_{plabel}.csv"
    if os.path.exists(_latest(opp_glob) or "") and os.path.exists(_latest(res_glob) or ""):
        return

    # CRITICAL: Set environment variables for the subprocess to use
    # These MUST be set so get_current_period() in the subprocess returns valid values
    env["PIPELINE_TARGET_YYYYMM"] = plabel[:6]  # e.g., "202410"
    env["PIPELINE_TARGET_PERIOD"] = plabel[-1]  # e.g., "A"
    
    # CRITICAL: Use --yyyymm and --period (NOT --target-yyyymm/--target-period)
    # The --target-* flags are for output labeling, not data loading
    subprocess.run(
        ["python3", "src/step7_missing_category_rule.py", "--yyyymm", plabel[:6], "--period", plabel[-1]],
        check=True,
        env=env,
    )


def test_step7_module_imports():
    # Smoke import
    import importlib
    mod = importlib.import_module("src.step7_missing_category_rule")
    # required symbols exist
    assert hasattr(mod, "identify_missing_opportunities_with_sellthrough"), "Missing identify_missing_opportunities_with_sellthrough()"
    assert hasattr(mod, "load_quantity_data"), "Missing load_quantity_data()"


@pytest.mark.timeout(120)
def test_step7_generates_outputs_and_schema():
    _ensure_step7_run()
    plabel = _period_label()

    # Locate outputs
    opp_path = _latest(f"output/rule7_missing_spu_sellthrough_opportunities_{plabel}.csv")
    res_path = _latest(f"output/rule7_missing_spu_sellthrough_results_{plabel}.csv")
    assert opp_path and os.path.exists(opp_path), "Opportunities CSV not found for current period"
    assert res_path and os.path.exists(res_path), "Results CSV not found for current period"

    # Validate schema
    opp = pd.read_csv(opp_path, nrows=100, low_memory=False)
    res = pd.read_csv(res_path, nrows=100, low_memory=False)

    expected_opp_cols = {
        "str_code", "cluster_id", "spu_code", "recommended_quantity_change",
        "investment_required", "retail_value", "margin_rate_used", "sub_cate_name",
        "predicted_sell_through_rate", "sell_through_improvement",
    }
    missing_opp = [c for c in expected_opp_cols if c not in opp.columns]
    assert not missing_opp, f"Opportunities missing expected columns: {missing_opp} in {opp_path}"

    expected_res_cols = {
        "str_code", "cluster_id", "total_investment_required", "total_quantity_needed",
        "avg_predicted_sellthrough", "fastfish_approved_count", "rule7_description",
    }
    missing_res = [c for c in expected_res_cols if c not in res.columns]
    assert not missing_res, f"Results missing expected columns: {missing_res} in {res_path}"
