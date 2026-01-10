"""
Execution Tests for All Updated Steps (7-15)
=============================================

Tests that actually run each updated step with synthetic data and verify outputs.
"""

import os
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"


def create_minimal_synthetic_data(sandbox: Path):
    """Create comprehensive synthetic data that works for all steps"""
    data_dir = sandbox / "data" / "api_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create comprehensive synthetic data
    stores = ['S001', 'S002', 'S003']
    spus = [f'SPU{i:03d}' for i in range(30)]
    subcats = ['T恤', '裤子', '外套'] * 10
    
    # SPU sales with ALL required columns for all steps
    # Create varied data to trigger rules (some stores with few SPUs for Step 9)
    spu_sales_data = []
    for i, store in enumerate(stores):
        # Store S001 has only 2 SPUs (below minimum) to trigger Step 9
        num_spus = 2 if store == 'S001' else 10
        for j in range(num_spus):
            spu_sales_data.append({
                'str_code': store,
                'spu_code': f'SPU{i*10+j:03d}',
                'sub_cate_name': subcats[j % 3],
                'sales_qty': 10 + j,
                'sales_amt': 100 + j * 10,
                'spu_sales_qty': 10 + j,
                'spu_sales_amt': 100 + j * 10,
                'sty_sal_amt': 100 + j * 10,
                'allocation_value': 5 + j,
                'season_name': ['春季', '夏季', '秋季'][j % 3],
                'sex_name': ['男', '女', '中性'][j % 3],
                'display_location_name': ['A区', 'B区', 'C区'][j % 3],
                'big_class_name': ['上装', '下装', '外套'][j % 3],
                'quantity': 10 + j,
                'base_sal_qty': 8 + j,
                'fashion_sal_qty': 2 + j,
                'sal_qty': 10 + j,
            })
    
    spu_sales = pd.DataFrame(spu_sales_data)
    spu_sales.to_csv(data_dir / "complete_spu_sales_202510A.csv", index=False)
    
    # Store sales with comprehensive columns
    store_sales = pd.DataFrame({
        'str_code': stores * 10,
        'spu_code': spus,
        'sub_cate_name': subcats,
        'sales_qty': [10, 20, 15] * 10,
        'sales_amt': [100, 200, 150] * 10,
        'unit_price': [10.0, 10.0, 10.0] * 10,
        'quantity': [10, 20, 15] * 10,
        'sal_qty': [10, 20, 15] * 10,
    })
    store_sales.to_csv(data_dir / "store_sales_202510A.csv", index=False)
    
    # Category sales for Step 8
    category_sales = pd.DataFrame({
        'str_code': stores * 3,
        'category_key': ['T恤', '裤子', '外套'] * 3,
        'sales_qty': [30, 60, 45] * 3,
        'sales_amt': [300, 600, 450] * 3,
        'allocation_value': [15, 30, 23] * 3,
    })
    category_sales.to_csv(data_dir / "complete_category_sales_202510A.csv", index=False)
    
    # Store config with planning data columns (for Step 8)
    store_config = pd.DataFrame({
        'str_code': stores,
        'str_name': ['Store 1', 'Store 2', 'Store 3'],
        'cluster_id': [1, 1, 2],
        # Planning data columns for Step 8
        'season_name': ['春季', '夏季', '秋季'],
        'sex_name': ['男', '女', '中性'],
        'display_location_name': ['A区', 'B区', 'C区'],
        'big_class_name': ['上装', '下装', '外套'],
        'sub_cate_name': ['T恤', '裤子', '外套'],
        'sty_sal_amt': [1000, 2000, 1500],
        'target_sty_cnt_avg': [10, 20, 15],
    })
    store_config.to_csv(data_dir / "store_config_202510A.csv", index=False)
    
    # Clustering results
    clustering = pd.DataFrame({
        'str_code': stores,
        'Cluster': [1, 1, 2],
    })
    (sandbox / "output").mkdir(exist_ok=True)
    clustering.to_csv(sandbox / "output" / "clustering_results_spu.csv", index=False)
    
    # Clustering results for subcategory (for Step 8)
    clustering_subcat = pd.DataFrame({
        'str_code': stores,
        'Cluster': [1, 1, 2],
    })
    clustering_subcat.to_csv(sandbox / "output" / "clustering_results_subcategory.csv", index=False)


def setup_sandbox(tmp_path: Path) -> Path:
    """Setup sandbox with src code and synthetic data"""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    
    # Copy src
    src_target = sandbox / "src"
    shutil.copytree(SRC_ROOT, src_target)
    
    # Create synthetic data
    create_minimal_synthetic_data(sandbox)
    
    # Create stub manifest
    stub = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}

def get_manifest():
    return _DummyManifest()

def register_step_output(*args, **kwargs):
    return None

def get_step_input(*args, **kwargs):
    return None
"""
    (src_target / "pipeline_manifest.py").write_text(stub)
    
    return sandbox


def run_step_and_verify(sandbox: Path, step_num: int, step_file: str, 
                        expected_output_pattern: str) -> bool:
    """Run a step and verify it creates timestamped outputs"""
    env = os.environ.copy()
    env['PYTHONPATH'] = str(sandbox)
    env['PIPELINE_TARGET_YYYYMM'] = '202510'
    env['PIPELINE_TARGET_PERIOD'] = 'A'
    
    result = subprocess.run(
        ['python3', str(sandbox / 'src' / step_file),
         '--target-yyyymm', '202510',
         '--target-period', 'A'],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        print(f"❌ Step {step_num} failed:")
        print(f"   STDOUT: {result.stdout[-300:]}")
        print(f"   STDERR: {result.stderr[-300:]}")
        return False
    
    # Check for timestamped output
    output_dir = sandbox / "output"
    timestamp_pattern = re.compile(expected_output_pattern)
    
    timestamped_files = [f for f in output_dir.glob("*") 
                         if timestamp_pattern.match(f.name)]
    
    if not timestamped_files:
        print(f"❌ Step {step_num}: No timestamped output found")
        print(f"   Files in output dir: {[f.name for f in output_dir.glob('*') if f.is_file()][:10]}")
        return False
    
    timestamped_file = timestamped_files[0]
    print(f"✅ Step {step_num}: {timestamped_file.name}")
    
    # Verify it's a real file (not a symlink)
    if timestamped_file.is_symlink():
        print(f"   ⚠️  Timestamped file should not be a symlink")
        return False
    
    # Check for symlinks
    base_name = timestamped_file.name.rsplit('_', 2)[0]  # Remove timestamp
    period_symlink = output_dir / f"{base_name}_202510A{timestamped_file.suffix}"
    
    if period_symlink.exists() and period_symlink.is_symlink():
        print(f"   ✅ Period symlink: {period_symlink.name}")
    
    return True


@pytest.mark.parametrize("step_num,step_file,output_pattern", [
    (7, "step7_missing_category_rule.py", r"rule7_missing_spu_sellthrough_results_202510A_\d{8}_\d{6}\.csv"),
    (8, "step8_imbalanced_rule.py", r"rule8_imbalanced_spu_results_202510A_\d{8}_\d{6}\.csv"),
    (9, "step9_below_minimum_rule.py", r"rule9_below_minimum_spu_sellthrough_results_202510A_\d{8}_\d{6}\.csv"),
    (10, "step10_spu_assortment_optimization.py", r"rule10_smart_overcapacity_results_202510A_\d{8}_\d{6}\.csv"),
    (11, "step11_missed_sales_opportunity.py", r"rule11_improved_missed_sales_opportunity_spu_results_202510A_\d{8}_\d{6}\.csv"),
    (12, "step12_sales_performance_rule.py", r"rule12_sales_performance_spu_results_202510A_\d{8}_\d{6}\.csv"),
])
def test_business_rules_create_timestamped_outputs(tmp_path, step_num, step_file, output_pattern):
    """Test that business rule steps (7-12) create timestamped outputs"""
    sandbox = setup_sandbox(tmp_path)
    
    success = run_step_and_verify(sandbox, step_num, step_file, output_pattern)
    
    assert success, f"Step {step_num} failed to create proper timestamped outputs"


def test_step13_consolidate_creates_timestamped_outputs(tmp_path):
    """Test Step 13 (requires outputs from Steps 7-12)"""
    sandbox = setup_sandbox(tmp_path)
    
    # First run Steps 7-12 to create inputs for Step 13
    steps_to_run = [
        (7, "step7_missing_category_rule.py"),
        (8, "step8_imbalanced_rule.py"),
        (9, "step9_below_minimum_rule.py"),
        (10, "step10_spu_assortment_optimization.py"),
        (11, "step11_missed_sales_opportunity.py"),
        (12, "step12_sales_performance_rule.py"),
    ]
    
    for step_num, step_file in steps_to_run:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(sandbox)
        env['PIPELINE_TARGET_YYYYMM'] = '202510'
        env['PIPELINE_TARGET_PERIOD'] = 'A'
        
        result = subprocess.run(
            ['python3', str(sandbox / 'src' / step_file),
             '--target-yyyymm', '202510',
             '--target-period', 'A'],
            cwd=sandbox,
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            pytest.skip(f"Step {step_num} failed, cannot test Step 13")
    
    # Now run Step 13
    success = run_step_and_verify(
        sandbox, 13, "step13_consolidate_spu_rules.py",
        r"consolidated_spu_rule_results_detailed_202510A_\d{8}_\d{6}\.csv"
    )
    
    assert success, "Step 13 failed to create proper timestamped outputs"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
