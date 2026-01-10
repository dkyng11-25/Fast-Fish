"""
Step 14 Gender Separation Test - Isolated Synthetic
===================================================

Isolated synthetic test to validate that Step 14 creates SEPARATE rows for each
gender within the same store_group × category × subcategory combination.

This test validates the critical fix where gender was added to the groupby key,
preventing the loss of minority genders through mode() aggregation.

Test Scenario:
- Same subcategory (圆领T恤) sold in multiple genders (男, 女, 中)
- Verify output has separate rows for each gender
- Verify no gender data is lost
- Verify SPU counts are correct per gender
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


def _generate_gender_separation_test_data(sandbox: Path) -> Dict[str, int]:
    """
    Generate synthetic data with SAME subcategory in MULTIPLE genders.
    
    Test scenario:
    - Store Group 1: 圆领T恤 sold in 3 genders (男: 7 stores, 女: 5 stores, 中: 3 stores)
    - Store Group 2: 圆领T恤 sold in 2 genders (男: 4 stores, 女: 6 stores)
    - Store Group 1: 牛仔裤 sold in 2 genders (男: 8 stores, 女: 2 stores)
    
    Expected output:
    - 5 rows total (not 3!)
    - Store Group 1 × T恤 × 圆领T恤 × 男: 7 SPUs
    - Store Group 1 × T恤 × 圆领T恤 × 女: 5 SPUs
    - Store Group 1 × T恤 × 圆领T恤 × 中: 3 SPUs
    - Store Group 2 × T恤 × 圆领T恤 × 男: 4 SPUs
    - Store Group 2 × T恤 × 圆领T恤 × 女: 6 SPUs
    - Store Group 1 × 裤子 × 牛仔裤 × 男: 8 SPUs
    - Store Group 1 × 裤子 × 牛仔裤 × 女: 2 SPUs
    """
    np.random.seed(42)
    
    api_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    
    # Define test data structure
    test_scenarios = [
        # (store_group, cluster, store_codes, category, subcategory, gender, num_spus)
        (1, 0, ['S001', 'S002', 'S003', 'S004', 'S005', 'S006', 'S007'], 'T恤', '圆领T恤', '男', 7),
        (1, 0, ['S008', 'S009', 'S010', 'S011', 'S012'], 'T恤', '圆领T恤', '女', 5),
        (1, 0, ['S013', 'S014', 'S015'], 'T恤', '圆领T恤', '中', 3),
        (2, 1, ['S016', 'S017', 'S018', 'S019'], 'T恤', '圆领T恤', '男', 4),
        (2, 1, ['S020', 'S021', 'S022', 'S023', 'S024', 'S025'], 'T恤', '圆领T恤', '女', 6),
        (1, 0, ['S001', 'S002', 'S003', 'S004', 'S005', 'S006', 'S007', 'S008'], '裤子', '牛仔裤', '男', 8),
        (1, 0, ['S009', 'S010'], '裤子', '牛仔裤', '女', 2),
    ]
    
    # Generate SPU sales data
    # IMPORTANT: num_spus is the TOTAL unique SPUs for this gender/subcategory combo,
    # not per store. We distribute them across stores.
    spu_sales_data = []
    store_config_data = []
    spu_counter = 1
    
    for store_group, cluster, stores, category, subcategory, gender, num_spus in test_scenarios:
        # Create num_spus UNIQUE SPUs for this combination
        for i in range(num_spus):
            spu_code = f"SPU{spu_counter:04d}"
            spu_counter += 1
            
            # Assign this SPU to one store (distribute across stores)
            store = stores[i % len(stores)]
            
            # SPU sales record
            spu_sales_data.append({
                'str_code': store,
                'spu_code': spu_code,
                'cate_name': category,
                'sub_cate_name': subcategory,
                'spu_sales_amt': np.random.uniform(1000, 5000),
                'quantity': np.random.randint(10, 50),
                'unit_price': np.random.uniform(50, 200),
                'investment_per_unit': np.random.uniform(30, 120),
            })
            
            # Store config record (with dimensional attributes)
            store_config_data.append({
                'str_code': store,
                'str_name': f'Test Store {store}',
                'cate_name': category,
                'sub_cate_name': subcategory,
                'spu_code': spu_code,
                'season_name': '冬',  # All winter for simplicity
                'sex_name': gender,  # CRITICAL: Gender varies!
                'display_location_name': '后台',  # All back store for simplicity
            })
    
    # Save SPU sales
    spu_sales_df = pd.DataFrame(spu_sales_data)
    spu_sales_file = api_dir / f"complete_spu_sales_{PERIOD_LABEL}.csv"
    spu_sales_df.to_csv(spu_sales_file, index=False)
    
    # Save store config
    store_config_df = pd.DataFrame(store_config_data)
    store_config_file = api_dir / f"store_config_{PERIOD_LABEL}.csv"
    store_config_df.to_csv(store_config_file, index=False)
    
    # Create clustering results
    all_stores = set()
    cluster_map = {}
    for store_group, cluster, stores, *_ in test_scenarios:
        for store in stores:
            all_stores.add(store)
            cluster_map[store] = cluster
    
    clustering_data = [{'str_code': store, 'Cluster': cluster_map[store]} for store in sorted(all_stores)]
    clustering_df = pd.DataFrame(clustering_data)
    clustering_file = output_dir / f"clustering_results_spu_{PERIOD_LABEL}.csv"
    clustering_df.to_csv(clustering_file, index=False)
    
    # Return expected counts for validation
    # Note: '中' in input gets mapped to '中性' in output
    expected_counts = {
        ('Store Group 1', 'T恤', '圆领T恤', '男'): 7,
        ('Store Group 1', 'T恤', '圆领T恤', '女'): 5,
        ('Store Group 1', 'T恤', '圆领T恤', '中性'): 3,
        ('Store Group 2', 'T恤', '圆领T恤', '男'): 4,
        ('Store Group 2', 'T恤', '圆领T恤', '女'): 6,
        ('Store Group 1', '裤子', '牛仔裤', '男'): 8,
        ('Store Group 1', '裤子', '牛仔裤', '女'): 2,
    }
    
    return expected_counts


@pytest.fixture
def sandbox(tmp_path):
    """Create and return sandbox environment."""
    return _prepare_sandbox(tmp_path)


def test_step14_gender_separation_synthetic(sandbox, capsys):
    """
    Test that Step 14 creates SEPARATE rows for each gender.
    
    Critical validation:
    - Same subcategory with different genders → separate rows
    - Each gender has correct SPU count
    - No gender data is lost
    - Output row count matches expected (7 rows, not 3)
    """
    # Generate test data
    expected_counts = _generate_gender_separation_test_data(sandbox)
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = str(sandbox)
    env['PIPELINE_TARGET_YYYYMM'] = TARGET_YYYYMM
    env['PIPELINE_TARGET_PERIOD'] = TARGET_PERIOD
    
    # Run Step 14
    step14_script = sandbox / "src" / "step14_create_fast_fish_format.py"
    result = subprocess.run(
        ["python3", str(step14_script), "--target-yyyymm", TARGET_YYYYMM, "--target-period", TARGET_PERIOD],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
    )
    
    # Check execution
    assert result.returncode == 0, f"Step 14 failed:\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    
    # Load output
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    assert output_file.exists(), f"Output file not created: {output_file}"
    
    output_df = pd.read_csv(output_file)
    
    # CRITICAL VALIDATION 1: Check total row count
    expected_rows = len(expected_counts)
    actual_rows = len(output_df)
    
    print(f"\n{'='*80}")
    print(f"GENDER SEPARATION VALIDATION")
    print(f"{'='*80}")
    print(f"Expected rows: {expected_rows}")
    print(f"Actual rows: {actual_rows}")
    
    assert actual_rows == expected_rows, (
        f"Expected {expected_rows} rows (one per gender), got {actual_rows}. "
        f"This suggests genders are being collapsed!"
    )
    
    # CRITICAL VALIDATION 2: Check each gender combination exists
    print(f"\n{'='*80}")
    print(f"CHECKING EACH GENDER COMBINATION")
    print(f"{'='*80}")
    
    for (store_group, category, subcategory, gender), expected_spu_count in expected_counts.items():
        # Find matching row
        matching_rows = output_df[
            (output_df['Store_Group_Name'] == store_group) &
            (output_df['Category'] == category) &
            (output_df['Subcategory'] == subcategory) &
            (output_df['Gender'] == gender)
        ]
        
        print(f"\n{store_group} × {category} × {subcategory} × {gender}:")
        
        # Check row exists
        assert len(matching_rows) == 1, (
            f"Expected 1 row for {store_group} × {category} × {subcategory} × {gender}, "
            f"got {len(matching_rows)}. Gender separation failed!"
        )
        
        # Check SPU count
        actual_spu_count = matching_rows.iloc[0]['Current_SPU_Quantity']
        print(f"  Expected SPU count: {expected_spu_count}")
        print(f"  Actual SPU count: {actual_spu_count}")
        
        assert actual_spu_count == expected_spu_count, (
            f"SPU count mismatch for {store_group} × {category} × {subcategory} × {gender}. "
            f"Expected {expected_spu_count}, got {actual_spu_count}"
        )
        
        print(f"  ✅ PASSED")
    
    # CRITICAL VALIDATION 3: Check 圆领T恤 has multiple gender rows
    print(f"\n{'='*80}")
    print(f"VALIDATING SAME SUBCATEGORY WITH MULTIPLE GENDERS")
    print(f"{'='*80}")
    
    # Store Group 1 × 圆领T恤 should have 3 rows (男, 女, 中性)
    # Note: '中' gets mapped to '中性' in the output
    sg1_tshirt = output_df[
        (output_df['Store_Group_Name'] == 'Store Group 1') &
        (output_df['Subcategory'] == '圆领T恤')
    ]
    
    print(f"\nStore Group 1 × 圆领T恤:")
    print(f"  Expected genders: 男, 女, 中性 (3 rows)")
    print(f"  Actual genders: {sorted(sg1_tshirt['Gender'].tolist())}")
    print(f"  Actual rows: {len(sg1_tshirt)}")
    
    assert len(sg1_tshirt) == 3, (
        f"Store Group 1 × 圆领T恤 should have 3 rows (one per gender), got {len(sg1_tshirt)}"
    )
    
    assert set(sg1_tshirt['Gender'].tolist()) == {'男', '女', '中性'}, (
        f"Store Group 1 × 圆领T恤 missing genders! Got: {sg1_tshirt['Gender'].tolist()}"
    )
    
    print(f"  ✅ PASSED - All 3 genders preserved!")
    
    # Store Group 2 × 圆领T恤 should have 2 rows (男, 女)
    sg2_tshirt = output_df[
        (output_df['Store_Group_Name'] == 'Store Group 2') &
        (output_df['Subcategory'] == '圆领T恤')
    ]
    
    print(f"\nStore Group 2 × 圆领T恤:")
    print(f"  Expected genders: 男, 女 (2 rows)")
    print(f"  Actual genders: {sorted(sg2_tshirt['Gender'].tolist())}")
    print(f"  Actual rows: {len(sg2_tshirt)}")
    
    assert len(sg2_tshirt) == 2, (
        f"Store Group 2 × 圆领T恤 should have 2 rows (one per gender), got {len(sg2_tshirt)}"
    )
    
    assert set(sg2_tshirt['Gender'].tolist()) == {'男', '女'}, (
        f"Store Group 2 × 圆领T恤 missing genders! Got: {sg2_tshirt['Gender'].tolist()}"
    )
    
    print(f"  ✅ PASSED - Both genders preserved!")
    
    # CRITICAL VALIDATION 4: Verify no gender was lost to mode()
    print(f"\n{'='*80}")
    print(f"FINAL VALIDATION: NO GENDER DATA LOST")
    print(f"{'='*80}")
    
    # Count total genders in output
    total_genders_output = output_df['Gender'].value_counts()
    print(f"\nGender distribution in output:")
    for gender, count in total_genders_output.items():
        print(f"  {gender}: {count} rows")
    
    # Should have all 3 genders represented (中 mapped to 中性)
    assert '男' in total_genders_output.index, "Men's gender missing from output!"
    assert '女' in total_genders_output.index, "Women's gender missing from output!"
    assert '中性' in total_genders_output.index, "Neutral gender missing from output!"
    
    print(f"\n✅ ALL VALIDATIONS PASSED!")
    print(f"   - Correct number of rows (7)")
    print(f"   - Each gender has separate row")
    print(f"   - SPU counts are correct")
    print(f"   - No gender data lost")
    print(f"   - Same subcategory has multiple gender rows")
    print(f"\n🎉 Gender separation is working correctly!")


def test_step14_gender_separation_prevents_mode_collapse(sandbox):
    """
    Test that minority genders are NOT lost to mode() aggregation.
    
    Scenario:
    - Store Group 1 × 圆领T恤: 10 women's stores, 2 men's stores, 1 neutral store
    - OLD behavior: Would create 1 row with gender='女' (mode), losing men and neutral
    - NEW behavior: Should create 3 rows (one per gender)
    """
    np.random.seed(42)
    
    api_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    
    # Create data with HEAVY women's majority
    spu_sales_data = []
    store_config_data = []
    
    # Women's stores (10 stores, 10 SPUs each = 100 SPUs)
    for store_idx in range(1, 11):
        store = f"S{store_idx:03d}"
        for spu_idx in range(10):
            spu = f"SPUW{store_idx:02d}{spu_idx:02d}"
            spu_sales_data.append({
                'str_code': store,
                'spu_code': spu,
                'cate_name': 'T恤',
                'sub_cate_name': '圆领T恤',
                'spu_sales_amt': 1000,
                'quantity': 10,
                'unit_price': 100,
                'investment_per_unit': 60,
            })
            store_config_data.append({
                'str_code': store,
                'str_name': f'Store {store}',
                'cate_name': 'T恤',
                'sub_cate_name': '圆领T恤',
                'spu_code': spu,
                'season_name': '冬',
                'sex_name': '女',  # Women
                'display_location_name': '后台',
            })
    
    # Men's stores (2 stores, 5 SPUs each = 10 SPUs)
    for store_idx in range(11, 13):
        store = f"S{store_idx:03d}"
        for spu_idx in range(5):
            spu = f"SPUM{store_idx:02d}{spu_idx:02d}"
            spu_sales_data.append({
                'str_code': store,
                'spu_code': spu,
                'cate_name': 'T恤',
                'sub_cate_name': '圆领T恤',
                'spu_sales_amt': 1000,
                'quantity': 10,
                'unit_price': 100,
                'investment_per_unit': 60,
            })
            store_config_data.append({
                'str_code': store,
                'str_name': f'Store {store}',
                'cate_name': 'T恤',
                'sub_cate_name': '圆领T恤',
                'spu_code': spu,
                'season_name': '冬',
                'sex_name': '男',  # Men
                'display_location_name': '后台',
            })
    
    # Neutral store (1 store, 3 SPUs = 3 SPUs)
    store = "S013"
    for spu_idx in range(3):
        spu = f"SPUN{spu_idx:02d}"
        spu_sales_data.append({
            'str_code': store,
            'spu_code': spu,
            'cate_name': 'T恤',
            'sub_cate_name': '圆领T恤',
            'spu_sales_amt': 1000,
            'quantity': 10,
            'unit_price': 100,
            'investment_per_unit': 60,
        })
        store_config_data.append({
            'str_code': store,
            'str_name': f'Store {store}',
            'cate_name': 'T恤',
            'sub_cate_name': '圆领T恤',
            'spu_code': spu,
            'season_name': '冬',
            'sex_name': '中',  # Neutral
            'display_location_name': '后台',
        })
    
    # Save files
    pd.DataFrame(spu_sales_data).to_csv(api_dir / f"complete_spu_sales_{PERIOD_LABEL}.csv", index=False)
    pd.DataFrame(store_config_data).to_csv(api_dir / f"store_config_{PERIOD_LABEL}.csv", index=False)
    
    # Create clustering (all stores in cluster 0)
    clustering_data = [{'str_code': f"S{i:03d}", 'Cluster': 0} for i in range(1, 14)]
    pd.DataFrame(clustering_data).to_csv(output_dir / f"clustering_results_spu_{PERIOD_LABEL}.csv", index=False)
    
    # Run Step 14
    env = os.environ.copy()
    env['PYTHONPATH'] = str(sandbox)
    env['PIPELINE_TARGET_YYYYMM'] = TARGET_YYYYMM
    env['PIPELINE_TARGET_PERIOD'] = TARGET_PERIOD
    
    step14_script = sandbox / "src" / "step14_create_fast_fish_format.py"
    result = subprocess.run(
        ["python3", str(step14_script), "--target-yyyymm", TARGET_YYYYMM, "--target-period", TARGET_PERIOD],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, f"Step 14 failed:\n{result.stderr}"
    
    # Load and validate output
    output_file = sandbox / "output" / f"enhanced_fast_fish_format_{PERIOD_LABEL}.csv"
    output_df = pd.read_csv(output_file)
    
    # Should have 3 rows (one per gender)
    tshirt_rows = output_df[output_df['Subcategory'] == '圆领T恤']
    
    print(f"\n{'='*80}")
    print(f"MODE COLLAPSE PREVENTION TEST")
    print(f"{'='*80}")
    print(f"\nInput distribution:")
    print(f"  Women: 100 SPUs (88%)")
    print(f"  Men: 10 SPUs (9%)")
    print(f"  Neutral: 3 SPUs (3%)")
    print(f"\nOLD behavior (mode): Would create 1 row with gender='女', losing 13 SPUs")
    print(f"NEW behavior (groupby): Should create 3 rows preserving all genders")
    print(f"\nActual output:")
    print(f"  Total rows: {len(tshirt_rows)}")
    
    assert len(tshirt_rows) == 3, (
        f"Expected 3 rows (one per gender), got {len(tshirt_rows)}. "
        f"Minority genders were lost to mode() aggregation!"
    )
    
    # Verify each gender (中 mapped to 中性 in output)
    for gender, expected_spu_count in [('女', 100), ('男', 10), ('中性', 3)]:
        gender_row = tshirt_rows[tshirt_rows['Gender'] == gender]
        assert len(gender_row) == 1, f"Missing row for gender '{gender}'"
        
        actual_spu_count = gender_row.iloc[0]['Current_SPU_Quantity']
        print(f"  {gender}: {actual_spu_count} SPUs (expected {expected_spu_count})")
        
        assert actual_spu_count == expected_spu_count, (
            f"SPU count mismatch for gender '{gender}'. "
            f"Expected {expected_spu_count}, got {actual_spu_count}"
        )
    
    print(f"\n✅ SUCCESS: Minority genders (男, 中性) preserved despite being only 12% of data!")
    print(f"   This proves the fix prevents mode() collapse!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
