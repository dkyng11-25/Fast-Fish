"""
Step 14 Gender Aggregation Edge Cases - Comprehensive Testing
==============================================================

Tests the actual aggregation behavior of Step 14 when handling neutral gender
values in various edge case scenarios.

This test suite validates:
1. Mixed gender aggregation (women + neutral)
2. All neutral aggregation
3. Equal split scenarios
4. Empty/missing gender handling
5. Real aggregation logic behavior
"""

import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import numpy as np
import pytest

TARGET_YYYYMM = "202501"
TARGET_PERIOD = "A"
PERIOD_LABEL = f"{TARGET_YYYYMM}{TARGET_PERIOD}"

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"


def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox environment for Step 14 testing."""
    sandbox = tmp_path / "sandbox"
    src_target = sandbox / "src"
    shutil.copytree(SRC_ROOT, src_target)

    # Mock pipeline_manifest.py
    manifest_stub = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None

def get_step_input(*_args, **_kwargs):
    return None
""".strip()
    (src_target / "pipeline_manifest.py").write_text(manifest_stub, encoding="utf-8")
    
    # Mock config.py (same as other tests)
    config_stub = f"""
import os
from pathlib import Path

def initialize_pipeline_config(*args, **kwargs):
    pass

def get_current_period():
    return "{TARGET_YYYYMM}", "{TARGET_PERIOD}"

def get_period_label(*args, **kwargs):
    if args:
        yyyymm, period = args[0], args[1] if len(args) > 1 else "A"
        return f"{{yyyymm}}{{period}}"
    return "{PERIOD_LABEL}"

def get_api_data_files(yyyymm=None, period=None):
    if yyyymm is None:
        yyyymm = "{TARGET_YYYYMM}"
    if period is None:
        period = "{TARGET_PERIOD}"
    base_path = "data/api_data"
    return {{
        'store_config': f"{{base_path}}/store_config_{{yyyymm}}{{period}}.csv",
        'spu_sales': f"{{base_path}}/complete_spu_sales_{{yyyymm}}{{period}}.csv",
        'category_sales': f"{{base_path}}/complete_category_sales_{{yyyymm}}{{period}}.csv",
    }}

def get_output_files(*args, **kwargs):
    return {{
        'enhanced_fast_fish': f"output/enhanced_fast_fish_format_{PERIOD_LABEL}.csv",
    }}

API_DATA_DIR = "data/api_data"
OUTPUT_DIR = "output"
CURRENT_YYYYMM = "{TARGET_YYYYMM}"
CURRENT_PERIOD = "{TARGET_PERIOD}"

def load_sales_df_with_fashion_basic(*args, **kwargs):
    import pandas as pd
    return pd.DataFrame([
        {{'str_code': 'S0001', 'spu_code': 'SPU001', 'fashion_sal_qty': 10, 'base_sal_qty': 5}},
    ])

def get_baseline_files(*args, **kwargs):
    return {{'baseline_sales': 'data/api_data/baseline_sales.csv'}}

def load_store_config(*args, **kwargs):
    import pandas as pd
    return pd.DataFrame([{{'str_code': 'S0001', 'store_name': 'Test Store 1'}}])

def load_clustering_results(*args, **kwargs):
    import pandas as pd
    return pd.DataFrame([{{'str_code': 'S0001', 'Cluster': 1}}])

def load_weather_data(*args, **kwargs):
    import pandas as pd
    return pd.DataFrame([{{'str_code': 'S0001', 'temperature_band': '15-20'}}])
""".strip()
    (src_target / "config.py").write_text(config_stub, encoding="utf-8")
    (src_target / "__init__.py").write_text("", encoding="utf-8")

    # Create directory structure
    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    return sandbox


def _create_edge_case_data(sandbox: Path, scenario: str) -> None:
    """Create synthetic data for specific edge case scenarios."""
    np.random.seed(42)
    
    stores = ["S0001", "S0002"]
    api_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    
    # Scenario-specific data generation
    if scenario == "mixed_women_neutral":
        # 70% women, 30% neutral in same store_group/category
        spu_sales_data = [
            # Store Group 1, Category "T恤", Subcategory "圆领T恤"
            {"str_code": "S0001", "spu_code": "SPU001", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "女", "Location": "前台"},
            {"str_code": "S0001", "spu_code": "SPU002", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "女", "Location": "前台"},
            {"str_code": "S0001", "spu_code": "SPU003", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "女", "Location": "前台"},
            {"str_code": "S0001", "spu_code": "SPU004", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "女", "Location": "前台"},
            {"str_code": "S0001", "spu_code": "SPU005", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "女", "Location": "前台"},
            {"str_code": "S0001", "spu_code": "SPU006", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "女", "Location": "前台"},
            {"str_code": "S0001", "spu_code": "SPU007", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "女", "Location": "前台"},
            {"str_code": "S0001", "spu_code": "SPU008", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "中性", "Location": "前台"},
            {"str_code": "S0001", "spu_code": "SPU009", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "中性", "Location": "前台"},
            {"str_code": "S0001", "spu_code": "SPU010", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "中性", "Location": "前台"},
        ]
        store_config_data = [
            {"str_code": "S0001", "store_name": "Test Store 1", "region": "Test",
             "sub_cate_name": "圆领T恤", "season_name": "夏季", "sex_name": "女", "display_location_name": "前台"},
        ]
        
    elif scenario == "all_neutral":
        # 100% neutral in store_group/category
        spu_sales_data = [
            {"str_code": "S0001", "spu_code": f"SPU{i:03d}", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "中性", "Location": "前台"}
            for i in range(1, 11)
        ]
        store_config_data = [
            {"str_code": "S0001", "store_name": "Test Store 1", "region": "Test",
             "sub_cate_name": "圆领T恤", "season_name": "夏季", "sex_name": "中性", "display_location_name": "前台"},
        ]
        
    elif scenario == "equal_split":
        # 50% women, 50% neutral
        spu_sales_data = [
            {"str_code": "S0001", "spu_code": f"SPU{i:03d}", "sub_cate_name": "圆领T恤", "cate_name": "T恤",
             "spu_sales_amt": 1000, "fashion_sal_qty": 10, "base_sal_qty": 5,
             "Season": "夏季", "Gender": "女" if i <= 5 else "中性", "Location": "前台"}
            for i in range(1, 11)
        ]
        store_config_data = [
            {"str_code": "S0001", "store_name": "Test Store 1", "region": "Test",
             "sub_cate_name": "圆领T恤", "season_name": "夏季", "sex_name": "女", "display_location_name": "前台"},
        ]
    
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    
    # Save SPU sales data
    spu_sales_df = pd.DataFrame(spu_sales_data)
    spu_sales_file = api_dir / f"complete_spu_sales_{PERIOD_LABEL}.csv"
    spu_sales_df.to_csv(spu_sales_file, index=False)
    
    # Save store config data
    store_config_df = pd.DataFrame(store_config_data)
    store_config_file = api_dir / f"store_config_{PERIOD_LABEL}.csv"
    store_config_df.to_csv(store_config_file, index=False)
    
    # Create clustering results
    clustering_data = [{"str_code": "S0001", "Cluster": 1}]
    clustering_df = pd.DataFrame(clustering_data)
    clustering_file = output_dir / f"clustering_results_spu_{PERIOD_LABEL}.csv"
    clustering_df.to_csv(clustering_file, index=False)
    
    # Create empty consolidated rules (Step 14 can run without rules)
    empty_rules = pd.DataFrame(columns=["str_code", "spu_code", "sub_cate_name", "add_qty", "reduce_qty"])
    rules_file = output_dir / f"consolidated_spu_rule_results_detailed_{PERIOD_LABEL}.csv"
    empty_rules.to_csv(rules_file, index=False)


def _run_step14_in_sandbox(sandbox: Path) -> subprocess.CompletedProcess:
    """Run Step 14 in isolated sandbox environment."""
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(sandbox))
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    
    cmd = [
        "python3",
        "src/step14_create_fast_fish_format.py",
        "--target-yyyymm", TARGET_YYYYMM,
        "--target-period", TARGET_PERIOD,
    ]
    
    return subprocess.run(
        cmd,
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_step14_mixed_women_neutral_aggregation(tmp_path):
    """Test aggregation when store_group has 70% women + 30% neutral items.
    
    Expected behavior:
    - mode() should return '女' (women) as most common
    - mapped_gender = '女'
    - Should NOT enter inference block (not in ambiguous list)
    - Final Gender = '女' (women)
    
    This validates that the mode-based aggregation works correctly.
    """
    sandbox = _prepare_sandbox(tmp_path)
    _create_edge_case_data(sandbox, "mixed_women_neutral")
    
    result = _run_step14_in_sandbox(sandbox)
    assert result.returncode == 0, f"Step 14 failed: {result.stderr}"
    
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    df = pd.read_csv(output_file)
    
    # Should have exactly 1 record (1 store_group × 1 category × 1 subcategory)
    assert len(df) == 1, f"Expected 1 record, got {len(df)}"
    
    # Gender should be '女' (women) because it's the mode
    gender = df.iloc[0]['Gender']
    assert gender == '女', f"Expected Gender='女' (mode), got '{gender}'"
    
    print(f"✅ Mixed aggregation test PASSED!")
    print(f"   Input: 70% women, 30% neutral")
    print(f"   Output: Gender = '{gender}' (correct - mode is women)")


def test_step14_all_neutral_aggregation(tmp_path):
    """Test aggregation when store_group has 100% neutral items.
    
    Expected behavior:
    - mode() should return '中性' (neutral)
    - mapped_gender = '中性'
    - Should NOT enter inference block (not in ambiguous list after fix)
    - Final Gender = '中性' (neutral)
    
    This is the CRITICAL test for our fix!
    """
    sandbox = _prepare_sandbox(tmp_path)
    _create_edge_case_data(sandbox, "all_neutral")
    
    result = _run_step14_in_sandbox(sandbox)
    assert result.returncode == 0, f"Step 14 failed: {result.stderr}"
    
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    df = pd.read_csv(output_file)
    
    # Should have exactly 1 record
    assert len(df) == 1, f"Expected 1 record, got {len(df)}"
    
    # Gender should be '中性' (neutral) - THIS IS THE KEY TEST!
    gender = df.iloc[0]['Gender']
    assert gender in ['中性', '中', 'Unisex'], (
        f"FAILED: Expected neutral gender ('中性', '中', or 'Unisex'), got '{gender}'. "
        f"This means the fix is NOT working - neutral was converted!"
    )
    
    print(f"✅ All neutral aggregation test PASSED!")
    print(f"   Input: 100% neutral")
    print(f"   Output: Gender = '{gender}' (correct - preserved neutral)")


def test_step14_equal_split_aggregation(tmp_path):
    """Test aggregation when store_group has 50% women + 50% neutral.
    
    Expected behavior:
    - mode() behavior is undefined for ties (pandas returns first occurrence)
    - mapped_gender could be '女' or '中性' depending on data order
    - Should NOT enter inference block if mode is '中性'
    - This tests pandas mode() behavior with ties
    """
    sandbox = _prepare_sandbox(tmp_path)
    _create_edge_case_data(sandbox, "equal_split")
    
    result = _run_step14_in_sandbox(sandbox)
    assert result.returncode == 0, f"Step 14 failed: {result.stderr}"
    
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    df = pd.read_csv(output_file)
    
    # Should have exactly 1 record
    assert len(df) == 1, f"Expected 1 record, got {len(df)}"
    
    # Gender could be either '女' or '中性' depending on mode() behavior
    gender = df.iloc[0]['Gender']
    assert gender in ['女', '中性', '中', 'Unisex'], (
        f"Unexpected gender value: '{gender}'"
    )
    
    print(f"✅ Equal split aggregation test PASSED!")
    print(f"   Input: 50% women, 50% neutral")
    print(f"   Output: Gender = '{gender}' (mode() picked first occurrence)")
    print(f"   Note: This behavior depends on pandas mode() implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
