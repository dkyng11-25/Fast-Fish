import os
import glob
import subprocess
import pandas as pd
import pytest


def _period_label():
    # Rely on Step 7's own period label function by importing config
    from src.config import get_current_period, get_period_label
    yyyymm, period = get_current_period()
    return get_period_label(yyyymm, period)


def _latest(path_glob):
    candidates = sorted(glob.glob(path_glob))
    if not candidates:
        return None
    candidates.sort(key=lambda p: os.path.getmtime(p))
    return candidates[-1]


def _ensure_step7_run():
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

    subprocess.run(
        ["python3", "src/step7_missing_category_rule.py", "--target-yyyymm", plabel[:6], "--target-period", plabel[-1]],
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
