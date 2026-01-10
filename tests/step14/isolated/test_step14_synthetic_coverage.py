"""
Step 14 Synthetic Tests - Coverage and Format (Isolated)
=======================================================

Isolated synthetic tests for Step 14 (Fast Fish Format) that generate
their own test data and validate business logic without depending on
real pipeline outputs.

Converts the existing Step 14 tests to use synthetic data with controlled
seasonal coverage, gender distribution, and location coverage.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

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
    
    # Mock config.py
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
        'store_breakdown': f"output/store_level_recommendation_breakdown_{PERIOD_LABEL}.csv",
    }}

# Additional config variables and functions
API_DATA_DIR = "data/api_data"
OUTPUT_DIR = "output"
CURRENT_YYYYMM = "{TARGET_YYYYMM}"
CURRENT_PERIOD = "{TARGET_PERIOD}"

def load_sales_df_with_fashion_basic(*args, **kwargs):
    import pandas as pd
    return pd.DataFrame([
        {{'str_code': 'S0001', 'spu_code': 'SPU001', 'fashion_sal_qty': 10, 'base_sal_qty': 5}},
        {{'str_code': 'S0002', 'spu_code': 'SPU002', 'fashion_sal_qty': 15, 'base_sal_qty': 8}},
    ])

def get_baseline_files(*args, **kwargs):
    return {{
        'baseline_sales': 'data/api_data/baseline_sales.csv',
        'baseline_raw': 'data/api_data/baseline_raw.csv',
    }}

def load_store_config(*args, **kwargs):
    import pandas as pd
    return pd.DataFrame([
        {{'str_code': 'S0001', 'store_name': 'Test Store 1'}},
        {{'str_code': 'S0002', 'store_name': 'Test Store 2'}},
    ])

def load_clustering_results(*args, **kwargs):
    import pandas as pd
    return pd.DataFrame([
        {{'str_code': 'S0001', 'Cluster': 1}},
        {{'str_code': 'S0002', 'Cluster': 2}},
    ])

def load_weather_data(*args, **kwargs):
    import pandas as pd
    return pd.DataFrame([
        {{'str_code': 'S0001', 'temperature_band': '15-20'}},
        {{'str_code': 'S0002', 'temperature_band': '20-25'}},
    ])
""".strip()
    (src_target / "config.py").write_text(config_stub, encoding="utf-8")
    (src_target / "__init__.py").write_text("", encoding="utf-8")

    # Create directory structure
    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    return sandbox


def _generate_synthetic_rule_data(sandbox: Path, winter_coverage: float = 0.35, frontcourt_coverage: float = 0.4) -> None:
    """Generate synthetic consolidated rule data with controlled coverage."""
    np.random.seed(42)  # Reproducible results
    
    # Generate synthetic rule recommendations with controlled seasonal distribution
    stores = [f"S{i:04d}" for i in range(1, 101)]  # 100 stores
    spus = [f"SPU{i:03d}" for i in range(1, 201)]   # 200 SPUs
    subcategories = ["休闲裤", "牛仔裤", "运动裤", "短裤", "连衣裙", "T恤", "衬衫", "外套", "毛衣", "鞋子"]
    
    # Define seasonal distribution (controlled for testing)
    seasons = ["春季", "夏季", "秋季", "冬季"]
    season_weights = [0.25, 0.25, 0.25 - winter_coverage + 0.25, winter_coverage]  # Controlled winter coverage
    
    genders = ["男", "女", "中性"]
    gender_weights = [0.4, 0.5, 0.1]
    
    locations = ["前台", "后台", "仓库"]
    location_weights = [frontcourt_coverage, 0.4, 0.2]  # Controlled frontcourt coverage
    
    # Generate synthetic recommendations
    n_recommendations = 500
    data = []
    
    for i in range(n_recommendations):
        store = np.random.choice(stores)
        spu = np.random.choice(spus)
        subcategory = np.random.choice(subcategories)
        season = np.random.choice(seasons, p=season_weights)
        gender = np.random.choice(genders, p=gender_weights)
        location = np.random.choice(locations, p=location_weights)
        
        # Generate realistic quantities
        add_qty = np.random.randint(5, 50)
        reduce_qty = np.random.randint(0, 10) if np.random.random() > 0.7 else 0
        net_qty = add_qty - reduce_qty
        
        data.append({
            "str_code": store,
            "spu_code": spu,
            "sub_cate_name": subcategory,
            "add_qty": add_qty,
            "reduce_qty": reduce_qty,
            "net_qty": net_qty,
            "rule_source": f"rule{np.random.randint(7, 13)}",
            "Season": season,
            "Gender": gender,
            "Location": location,
            "retail_price": np.random.uniform(50, 500),
            "margin_rate": np.random.uniform(0.3, 0.6),
        })
    
    # Save consolidated rule data
    df = pd.DataFrame(data)
    output_file = sandbox / "output" / f"consolidated_spu_rule_results_detailed_{PERIOD_LABEL}.csv"
    df.to_csv(output_file, index=False)
    
    # Also create store summary for Step 14
    store_summary = df.groupby(["str_code", "rule_source"]).agg({
        "add_qty": "sum",
        "reduce_qty": "sum", 
        "net_qty": "sum"
    }).reset_index()
    
    summary_file = sandbox / "output" / f"consolidated_spu_rule_results_{PERIOD_LABEL}.csv"
    store_summary.to_csv(summary_file, index=False)
    
    # Create API data files that Step 14 needs
    api_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    
    # Create SPU sales file with dimensional attributes
    spu_sales_data = []
    for i in range(200):  # Create SPU sales data
        store = np.random.choice(stores[:20])  # Use subset of stores
        spu = f"SPU{i:03d}"
        subcategory = np.random.choice(subcategories)
        season = np.random.choice(seasons, p=season_weights)
        gender = np.random.choice(genders, p=gender_weights)
        location = np.random.choice(locations, p=location_weights)
        
        spu_sales_data.append({
            "str_code": store,
            "spu_code": spu,
            "sub_cate_name": subcategory,
            "cate_name": f"Category_{subcategory}",  # Add category name
            "spu_sales_amt": np.random.uniform(1000, 10000),
            "fashion_sal_qty": np.random.randint(10, 100),
            "base_sal_qty": np.random.randint(5, 50),
            "Season": season,
            "Gender": gender,
            "Location": location,
        })
    
    spu_sales_df = pd.DataFrame(spu_sales_data)
    spu_sales_file = api_dir / f"complete_spu_sales_{PERIOD_LABEL}.csv"
    spu_sales_df.to_csv(spu_sales_file, index=False)
    
    # Create store config file with subcategory info and dimensional attributes
    store_config_data = []
    for store in stores[:20]:
        for subcategory in subcategories[:5]:  # Add multiple subcategories per store
            season = np.random.choice(seasons, p=season_weights)
            gender = np.random.choice(genders, p=gender_weights)
            location = np.random.choice(locations, p=location_weights)
            
            store_config_data.append({
                "str_code": store,
                "store_name": f"Test Store {store}",
                "region": "Test Region",
                "sub_cate_name": subcategory,
                "season_name": season,
                "sex_name": gender,
                "display_location_name": location,
            })
    
    store_config_df = pd.DataFrame(store_config_data)
    store_config_file = api_dir / f"store_config_{PERIOD_LABEL}.csv"
    store_config_df.to_csv(store_config_file, index=False)
    
    # Create clustering results file
    clustering_data = []
    for i, store in enumerate(stores[:20]):
        clustering_data.append({
            "str_code": store,
            "Cluster": i % 5 + 1,  # Assign stores to 5 clusters
        })
    
    clustering_df = pd.DataFrame(clustering_data)
    clustering_file = output_dir / f"clustering_results_spu_{PERIOD_LABEL}.csv"
    clustering_df.to_csv(clustering_file, index=False)


def _run_step14_in_sandbox(sandbox: Path, extra_args: List[str] = None) -> subprocess.CompletedProcess:
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
    
    if extra_args:
        cmd.extend(extra_args)
    
    return subprocess.run(
        cmd,
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_step14_winter_coverage_synthetic_sufficient(tmp_path):
    """Test Step 14 with synthetic data that has sufficient winter coverage (35%)."""
    sandbox = _prepare_sandbox(tmp_path)
    
    # Generate synthetic data with 35% winter coverage (above 30% threshold)
    _generate_synthetic_rule_data(sandbox, winter_coverage=0.35, frontcourt_coverage=0.4)
    
    result = _run_step14_in_sandbox(sandbox)
    
    # Step 14 should complete successfully
    assert result.returncode == 0, f"Step 14 failed: STDOUT: {result.stdout} STDERR: {result.stderr}"
    
    # Check output file exists
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    assert output_file.exists(), "Enhanced Fast Fish format file not created"
    
    # Validate winter coverage in output
    df = pd.read_csv(output_file)
    assert len(df) > 0, "Output should not be empty"
    assert "Season" in df.columns, "Season column missing"
    
    winter_mask = df["Season"].astype(str).str.strip() == "冬季"
    winter_share = winter_mask.sum() / len(df)
    
    # Should have sufficient winter coverage (allow some variance due to processing)
    assert winter_share >= 0.25, f"Winter coverage {winter_share:.3f} should be >= 0.25 in synthetic test"


def test_step14_winter_coverage_synthetic_insufficient(tmp_path):
    """Test Step 14 with synthetic data that has insufficient winter coverage (5%)."""
    sandbox = _prepare_sandbox(tmp_path)
    
    # Generate synthetic data with only 5% winter coverage (below 30% threshold)
    _generate_synthetic_rule_data(sandbox, winter_coverage=0.05, frontcourt_coverage=0.4)
    
    result = _run_step14_in_sandbox(sandbox)
    
    # Step 14 should still complete (it's a formatting step, not validation)
    assert result.returncode == 0, f"Step 14 failed: STDOUT: {result.stdout} STDERR: {result.stderr}"
    
    # Check output file exists
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    assert output_file.exists(), "Enhanced Fast Fish format file not created"
    
    # Validate that low winter coverage is preserved (Step 14 doesn't modify seasonal distribution)
    df = pd.read_csv(output_file)
    assert len(df) > 0, "Output should not be empty"
    assert "Season" in df.columns, "Season column missing"
    
    winter_mask = df["Season"].astype(str).str.strip() == "冬季"
    winter_share = winter_mask.sum() / len(df)
    
    # Should preserve low winter coverage from input
    assert winter_share <= 0.15, f"Winter coverage {winter_share:.3f} should be low in insufficient test"


def test_step14_frontcourt_coverage_synthetic(tmp_path):
    """Test Step 14 frontcourt coverage with synthetic data."""
    sandbox = _prepare_sandbox(tmp_path)
    
    # Generate synthetic data with 40% frontcourt coverage
    _generate_synthetic_rule_data(sandbox, winter_coverage=0.3, frontcourt_coverage=0.4)
    
    result = _run_step14_in_sandbox(sandbox)
    assert result.returncode == 0, f"Step 14 failed: {result.stderr}"
    
    # Check frontcourt coverage
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    df = pd.read_csv(output_file)
    
    assert "Location" in df.columns, "Location column missing"
    front_mask = df["Location"].astype(str).str.strip() == "前台"
    assert front_mask.any(), "No frontcourt (前台) coverage found"
    
    front_share = front_mask.sum() / len(df)
    assert front_share >= 0.3, f"Frontcourt coverage {front_share:.3f} should be >= 0.3"


def test_step14_gender_distribution_synthetic(tmp_path):
    """Test Step 14 gender distribution with synthetic data."""
    sandbox = _prepare_sandbox(tmp_path)
    
    _generate_synthetic_rule_data(sandbox, winter_coverage=0.3, frontcourt_coverage=0.4)
    
    result = _run_step14_in_sandbox(sandbox)
    assert result.returncode == 0, f"Step 14 failed: {result.stderr}"
    
    # Check gender distribution
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    df = pd.read_csv(output_file)
    
    assert "Gender" in df.columns, "Gender column missing"
    
    # Should have both male and female coverage
    genders = df["Gender"].value_counts()
    assert "男" in genders.index, "Male (男) coverage missing"
    assert "女" in genders.index, "Female (女) coverage missing"
    
    # Each gender should have reasonable representation
    male_share = genders.get("男", 0) / len(df)
    female_share = genders.get("女", 0) / len(df)
    
    assert male_share >= 0.2, f"Male coverage {male_share:.3f} should be >= 0.2"
    assert female_share >= 0.2, f"Female coverage {female_share:.3f} should be >= 0.2"


def test_step14_output_format_validation_synthetic(tmp_path):
    """Test Step 14 output format validation with synthetic data."""
    sandbox = _prepare_sandbox(tmp_path)
    
    _generate_synthetic_rule_data(sandbox, winter_coverage=0.3, frontcourt_coverage=0.4)
    
    result = _run_step14_in_sandbox(sandbox)
    assert result.returncode == 0, f"Step 14 failed: {result.stderr}"
    
    # Validate output format
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    df = pd.read_csv(output_file)
    
    # Required columns for Fast Fish format (updated to match actual Step 14 output)
    required_columns = ["Store_Group_Name", "Season", "Gender", "Location", "Category", "Subcategory"]
    for col in required_columns:
        assert col in df.columns, f"Required column '{col}' missing from output"
    
    # Quantity columns should be present
    qty_columns = ["ΔQty", "Current_SPU_Quantity", "Target_SPU_Quantity"]
    has_qty = any(col in df.columns for col in qty_columns)
    assert has_qty, "No quantity columns found in output"
    
    # Should have reasonable number of records
    assert len(df) > 0, "Output should not be empty"
    assert len(df) <= 1000, "Output should not be excessively large for synthetic test"


def test_step14_isolation_synthetic(tmp_path):
    """Test that Step 14 runs in complete isolation without affecting main output."""
    sandbox = _prepare_sandbox(tmp_path)
    
    _generate_synthetic_rule_data(sandbox, winter_coverage=0.3, frontcourt_coverage=0.4)
    
    result = _run_step14_in_sandbox(sandbox)
    assert result.returncode == 0, f"Step 14 isolation test failed: {result.stderr}"
    
    # Check outputs are in sandbox
    sandbox_output = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    assert sandbox_output.exists(), "Output should exist in sandbox"
    
    # Verify isolation - synthetic test should work regardless of main project state
    df = pd.read_csv(sandbox_output)
    assert len(df) > 0, "Isolated test should produce valid output"


def test_step14_neutral_gender_preservation(tmp_path):
    """Test that neutral gender items ('中性') are preserved, not converted to women/men.
    
    This test validates the fix for AIS-146: Step 14 should preserve explicit neutral
    gender values during store_group aggregation, not override them based on customer mix.
    """
    sandbox = _prepare_sandbox(tmp_path)
    
    # Generate synthetic data with explicit neutral gender items (12% neutral)
    _generate_synthetic_rule_data_with_neutral(sandbox, neutral_pct=0.12)
    
    result = _run_step14_in_sandbox(sandbox)
    assert result.returncode == 0, f"Step 14 failed: {result.stderr}"
    
    # Check that neutral items are preserved in output
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    df = pd.read_csv(output_file)
    
    assert "Gender" in df.columns, "Gender column missing from output"
    
    # Count neutral gender items (both '中性' and '中' should map to neutral)
    genders = df["Gender"].value_counts()
    neutral_count = genders.get('中性', 0) + genders.get('中', 0) + genders.get('Unisex', 0)
    
    # Critical assertion: Neutral items must be preserved!
    assert neutral_count > 0, (
        f"FAILED: All neutral items were converted! "
        f"Gender distribution: {genders.to_dict()}"
    )
    
    # Check that neutral percentage is reasonable (allow some variance due to aggregation)
    neutral_pct = neutral_count / len(df)
    assert neutral_pct >= 0.08, (
        f"Neutral percentage {neutral_pct:.3f} is too low (expected ~0.12). "
        f"Neutral items may have been incorrectly converted. "
        f"Gender distribution: {genders.to_dict()}"
    )
    
    # Also verify we still have men and women (not all converted to neutral)
    assert '男' in genders.index or 'Men' in genders.index, "Male gender missing"
    assert '女' in genders.index or 'Women' in genders.index, "Female gender missing"
    
    print(f"✅ Neutral gender preservation test PASSED!")
    print(f"   Gender distribution: {genders.to_dict()}")
    print(f"   Neutral percentage: {neutral_pct:.1%}")


def _generate_synthetic_rule_data_with_neutral(sandbox: Path, neutral_pct: float = 0.12) -> None:
    """Generate synthetic data with explicit neutral gender items for testing.
    
    This is a specialized version of _generate_synthetic_rule_data that ensures
    a specific percentage of items have neutral gender ('中性').
    """
    np.random.seed(42)  # Reproducible results
    
    # Generate synthetic rule recommendations with controlled gender distribution
    stores = [f"S{i:04d}" for i in range(1, 101)]  # 100 stores
    spus = [f"SPU{i:03d}" for i in range(1, 201)]   # 200 SPUs
    subcategories = ["休闲裤", "牛仔裤", "运动裤", "短裤", "连衣裙", "T恤", "衬衫", "外套", "毛衣", "鞋子"]
    
    seasons = ["春季", "夏季", "秋季", "冬季"]
    season_weights = [0.25, 0.35, 0.25, 0.15]
    
    # Controlled gender distribution with explicit neutral percentage
    genders = ["男", "女", "中性"]
    gender_weights = [0.40, 0.48, neutral_pct]  # 40% men, 48% women, 12% neutral
    
    locations = ["前台", "后台", "仓库"]
    location_weights = [0.4, 0.4, 0.2]
    
    # Generate synthetic recommendations
    n_recommendations = 500
    data = []
    
    for i in range(n_recommendations):
        store = np.random.choice(stores)
        spu = np.random.choice(spus)
        subcategory = np.random.choice(subcategories)
        season = np.random.choice(seasons, p=season_weights)
        gender = np.random.choice(genders, p=gender_weights)
        location = np.random.choice(locations, p=location_weights)
        
        # Generate realistic quantities
        add_qty = np.random.randint(5, 50)
        reduce_qty = np.random.randint(0, 10) if np.random.random() > 0.7 else 0
        net_qty = add_qty - reduce_qty
        
        data.append({
            "str_code": store,
            "spu_code": spu,
            "sub_cate_name": subcategory,
            "add_qty": add_qty,
            "reduce_qty": reduce_qty,
            "net_qty": net_qty,
            "rule_source": f"rule{np.random.randint(7, 13)}",
            "Season": season,
            "Gender": gender,  # Explicit gender including neutral
            "Location": location,
            "retail_price": np.random.uniform(50, 500),
            "margin_rate": np.random.uniform(0.3, 0.6),
        })
    
    # Save consolidated rule data
    df = pd.DataFrame(data)
    output_file = sandbox / "output" / f"consolidated_spu_rule_results_detailed_{PERIOD_LABEL}.csv"
    df.to_csv(output_file, index=False)
    
    # Also create store summary
    store_summary = df.groupby(["str_code", "rule_source"]).agg({
        "add_qty": "sum",
        "reduce_qty": "sum", 
        "net_qty": "sum"
    }).reset_index()
    
    summary_file = sandbox / "output" / f"consolidated_spu_rule_results_{PERIOD_LABEL}.csv"
    store_summary.to_csv(summary_file, index=False)
    
    # Create API data files that Step 14 needs
    api_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    
    # Create SPU sales file with dimensional attributes (including neutral gender)
    spu_sales_data = []
    for i in range(200):
        store = np.random.choice(stores[:20])
        spu = f"SPU{i:03d}"
        subcategory = np.random.choice(subcategories)
        season = np.random.choice(seasons, p=season_weights)
        gender = np.random.choice(genders, p=gender_weights)  # Include neutral
        location = np.random.choice(locations, p=location_weights)
        
        spu_sales_data.append({
            "str_code": store,
            "spu_code": spu,
            "sub_cate_name": subcategory,
            "cate_name": f"Category_{subcategory}",
            "spu_sales_amt": np.random.uniform(1000, 10000),
            "fashion_sal_qty": np.random.randint(10, 100),
            "base_sal_qty": np.random.randint(5, 50),
            "Season": season,
            "Gender": gender,  # Explicit gender including neutral
            "Location": location,
        })
    
    spu_sales_df = pd.DataFrame(spu_sales_data)
    spu_sales_file = api_dir / f"complete_spu_sales_{PERIOD_LABEL}.csv"
    spu_sales_df.to_csv(spu_sales_file, index=False)
    
    # Create store config file with subcategory info and dimensional attributes (including neutral)
    store_config_data = []
    for store in stores[:20]:
        for subcategory in subcategories[:5]:
            season = np.random.choice(seasons, p=season_weights)
            gender = np.random.choice(genders, p=gender_weights)  # Include neutral
            location = np.random.choice(locations, p=location_weights)
            
            store_config_data.append({
                "str_code": store,
                "store_name": f"Test Store {store}",
                "region": "Test Region",
                "sub_cate_name": subcategory,
                "season_name": season,
                "sex_name": gender,  # Explicit gender including neutral
                "display_location_name": location,
            })
    
    store_config_df = pd.DataFrame(store_config_data)
    store_config_file = api_dir / f"store_config_{PERIOD_LABEL}.csv"
    store_config_df.to_csv(store_config_file, index=False)
    
    # Create clustering results file
    clustering_data = []
    for i, store in enumerate(stores[:20]):
        clustering_data.append({
            "str_code": store,
            "Cluster": i % 5 + 1,
        })
    
    clustering_df = pd.DataFrame(clustering_data)
    clustering_file = output_dir / f"clustering_results_spu_{PERIOD_LABEL}.csv"
    clustering_df.to_csv(clustering_file, index=False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
