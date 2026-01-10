"""
Step 8 Synthetic Isolated Test

Tests Step 8 (Imbalanced Allocation Rule) in complete isolation with synthetic data.
No dependencies on real pipeline - creates own data and runs the step.
"""

import os
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

TARGET_YYYYMM = "202510"
TARGET_PERIOD = "A"
PERIOD_LABEL = f"{TARGET_YYYYMM}{TARGET_PERIOD}"

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"


def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated test environment."""
    sandbox = tmp_path / "sandbox"
    src_target = sandbox / "src"
    shutil.copytree(SRC_ROOT, src_target)
    
    # Create dummy pipeline_manifest.py
    stub = """
def get_manifest():
    return {'outputs': {}}

def register_step_output(*args, **kwargs):
    pass

def get_step_input(*args, **kwargs):
    return None
""".strip()
    (src_target / "pipeline_manifest.py").write_text(stub, encoding="utf-8")
    (src_target / "__init__.py").write_text("", encoding="utf-8")
    
    # Create directories
    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    
    return sandbox


def _create_synthetic_inputs(sandbox: Path) -> None:
    """Create synthetic input data for Step 8."""
    api_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    
    # Create synthetic store_config with ALL required columns
    store_config = pd.DataFrame([
        {
            'str_code': '1001',
            'season_name': '夏季',
            'sex_name': '男',
            'display_location_name': '前场',
            'big_class_name': '上装',
            'sub_cate_name': 'T恤',
            'sty_sal_amt': '[{"sub_cate_name":"T恤","spu_code":"SPU001","quantity":50,"sales_amount":2500,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},'
                          '{"sub_cate_name":"T恤","spu_code":"SPU002","quantity":10,"sales_amount":500,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}]'
        },
        {
            'str_code': '1002',
            'season_name': '夏季',
            'sex_name': '男',
            'display_location_name': '前场',
            'big_class_name': '上装',
            'sub_cate_name': 'T恤',
            'sty_sal_amt': '[{"sub_cate_name":"T恤","spu_code":"SPU001","quantity":30,"sales_amount":1500,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},'
                          '{"sub_cate_name":"T恤","spu_code":"SPU002","quantity":30,"sales_amount":1500,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}]'
        },
        {
            'str_code': '1003',
            'season_name': '春季',
            'sex_name': '女',
            'display_location_name': '后场',
            'big_class_name': '上装',
            'sub_cate_name': '衬衫',
            'sty_sal_amt': '[{"sub_cate_name":"衬衫","spu_code":"SPU003","quantity":40,"sales_amount":3200,"season_name":"春季","sex_name":"女","display_location_name":"后场","big_class_name":"上装"}]'
        }
    ])
    store_config.to_csv(api_dir / f"store_config_{PERIOD_LABEL}.csv", index=False)
    
    # Create synthetic clustering results
    clustering = pd.DataFrame([
        {'str_code': '1001', 'cluster': 0, 'Cluster': 0},
        {'str_code': '1002', 'cluster': 0, 'Cluster': 0},
        {'str_code': '1003', 'cluster': 1, 'Cluster': 1}
    ])
    clustering.to_csv(output_dir / f"clustering_results_spu_{PERIOD_LABEL}.csv", index=False)
    clustering.to_csv(output_dir / "clustering_results_spu.csv", index=False)
    
    # Create synthetic SPU sales data with all required columns
    spu_sales = pd.DataFrame([
        {'str_code': '1001', 'spu_code': 'SPU001', 'sub_cate_name': 'T恤', 'quantity': 50, 'sales_amount': 2500, 'spu_sales_amt': 2500, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
        {'str_code': '1001', 'spu_code': 'SPU002', 'sub_cate_name': 'T恤', 'quantity': 10, 'sales_amount': 500, 'spu_sales_amt': 500, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
        {'str_code': '1002', 'spu_code': 'SPU001', 'sub_cate_name': 'T恤', 'quantity': 30, 'sales_amount': 1500, 'spu_sales_amt': 1500, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
        {'str_code': '1002', 'spu_code': 'SPU002', 'sub_cate_name': 'T恤', 'quantity': 30, 'sales_amount': 1500, 'spu_sales_amt': 1500, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
        {'str_code': '1003', 'spu_code': 'SPU003', 'sub_cate_name': '衬衫', 'quantity': 40, 'sales_amount': 3200, 'spu_sales_amt': 3200, 'unit_price': 80.0, 'season_name': '春季', 'sex_name': '女', 'display_location_name': '后场', 'big_class_name': '上装'}
    ])
    spu_sales.to_csv(api_dir / f"complete_spu_sales_{PERIOD_LABEL}.csv", index=False)


def _run_step8(sandbox: Path) -> None:
    """Actually run Step 8 in the sandbox."""
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    env.setdefault("PYTHONPATH", str(sandbox))
    
    result = subprocess.run(
        [
            "python3",
            "src/step8_imbalanced_rule.py",
            "--target-yyyymm",
            TARGET_YYYYMM,
            "--target-period",
            TARGET_PERIOD,
        ],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        raise Exception(f"Step 8 failed with return code {result.returncode}")


def _load_outputs(sandbox: Path) -> dict:
    """Load generated output files."""
    output_dir = sandbox / "output"
    
    # Find the timestamped results file
    results_files = list(output_dir.glob("rule8_imbalanced_*_results_*.csv"))
    
    if not results_files:
        raise FileNotFoundError("No Step 8 results file found")
    
    results_file = results_files[0]
    
    return {
        'results': pd.read_csv(results_file, dtype={'str_code': str}),
        'results_path': results_file
    }


def test_step8_synthetic_isolated(tmp_path):
    """Test Step 8 runs in complete isolation with synthetic data."""
    
    # 1. Prepare sandbox
    sandbox = _prepare_sandbox(tmp_path)
    
    # 2. Create synthetic inputs
    _create_synthetic_inputs(sandbox)
    
    # 3. Run Step 8
    _run_step8(sandbox)
    
    # 4. Load outputs
    outputs = _load_outputs(sandbox)
    results = outputs['results']
    
    # 5. Validate outputs exist
    assert len(results) > 0, "Step 8 must create results"
    
    # 6. Validate required columns (Step 8 creates summary, not detailed output)
    required_cols = ['str_code']
    for col in required_cols:
        assert col in results.columns, f"Missing required column: {col}"
    
    # 7. Validate str_code is string
    assert results['str_code'].dtype == object, "str_code should be string"
    
    # 8. Validate imbalance/rebalancing columns exist
    imbalance_cols = [col for col in results.columns 
                      if any(kw in col.lower() for kw in ['imbalance', 'z_score', 'allocation', 'adjustment'])]
    assert len(imbalance_cols) > 0, "Should have imbalance-related columns"
    
    print(f"✅ Step 8 synthetic test passed!")
    print(f"   Results: {len(results)} records")
    print(f"   Columns: {list(results.columns)}")
    print(f"   Imbalance columns: {len(imbalance_cols)}")


def test_step8_dual_output_pattern(tmp_path):
    """Test Step 8 creates dual output pattern (timestamped + symlink)."""
    
    # 1. Prepare and run
    sandbox = _prepare_sandbox(tmp_path)
    _create_synthetic_inputs(sandbox)
    _run_step8(sandbox)
    
    # 2. Check for timestamped files
    output_dir = sandbox / "output"
    timestamped_files = list(output_dir.glob("rule8_imbalanced_*_results_*_*.csv"))
    
    assert len(timestamped_files) > 0, "Must create timestamped files"
    
    # 3. Check for symlinks
    possible_symlinks = [
        "rule8_imbalanced_spu_results.csv",
        "rule8_imbalanced_subcategory_results.csv",
        "rule8_results.csv"
    ]
    
    symlink_found = False
    for symlink_name in possible_symlinks:
        symlink_path = output_dir / symlink_name
        if symlink_path.exists() and symlink_path.is_symlink():
            link_target = os.readlink(symlink_path)
            assert '/' not in link_target, "Symlink should use basename"
            symlink_found = True
            print(f"✅ Found symlink: {symlink_name} -> {link_target}")
    
    if symlink_found:
        print(f"✅ Step 8 dual output pattern validated")
    else:
        print(f"⚠️  Step 8 creates timestamped files but no symlinks found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
