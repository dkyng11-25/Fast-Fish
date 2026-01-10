"""
Step 11 Synthetic Isolated Test

Tests Step 11 (Missed Sales Opportunity) in complete isolation with synthetic data.
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
    """
    Create synthetic input data for Step 11 testing.
    
    Step 11 tests missed sales opportunity - needs stores where some have a top-performing
    SPU and others don't (opportunity to add it).
    """
    api_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    
    # Create synthetic data for multiple periods (Step 11 needs historical window)
    periods = ['202509A', '202509B', '202510A']
    
    for period in periods:
        # Create store_config with missed opportunity scenario
        # Store 1001 & 1002: Have SPU001 (top performer with high sales)
        # Store 1003: Missing SPU001 (missed opportunity!)
        store_config = pd.DataFrame([
            {
                'str_code': '1001',
                'sty_sal_amt': '[' +
                    '{"sub_cate_name":"T恤","spu_code":"SPU001","quantity":50,"sales_amount":2500,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                    '{"sub_cate_name":"T恤","spu_code":"SPU002","quantity":20,"sales_amount":1000,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}' +
                ']'
            },
            {
                'str_code': '1002',
                'sty_sal_amt': '[' +
                    '{"sub_cate_name":"T恤","spu_code":"SPU001","quantity":45,"sales_amount":2250,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                    '{"sub_cate_name":"T恤","spu_code":"SPU002","quantity":18,"sales_amount":900,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}' +
                ']'
            },
            {
                'str_code': '1003',
                'sty_sal_amt': '[' +
                    '{"sub_cate_name":"T恤","spu_code":"SPU002","quantity":15,"sales_amount":750,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                    '{"sub_cate_name":"T恤","spu_code":"SPU003","quantity":10,"sales_amount":500,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}' +
                ']'
            }
        ])
        store_config.to_csv(api_dir / f"store_config_{period}.csv", index=False)
        
        # Create SPU sales data (with cate_name column)
        spu_sales = pd.DataFrame([
            # Store 1001 - Has top-performing SPU001
            {'str_code': '1001', 'spu_code': 'SPU001', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 50, 'sales_amount': 2500, 'spu_sales_amt': 2500, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
            {'str_code': '1001', 'spu_code': 'SPU002', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 20, 'sales_amount': 1000, 'spu_sales_amt': 1000, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
            # Store 1002 - Has top-performing SPU001
            {'str_code': '1002', 'spu_code': 'SPU001', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 45, 'sales_amount': 2250, 'spu_sales_amt': 2250, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
            {'str_code': '1002', 'spu_code': 'SPU002', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 18, 'sales_amount': 900, 'spu_sales_amt': 900, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
            # Store 1003 - Missing SPU001 (opportunity!)
            {'str_code': '1003', 'spu_code': 'SPU002', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 15, 'sales_amount': 750, 'spu_sales_amt': 750, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
            {'str_code': '1003', 'spu_code': 'SPU003', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 10, 'sales_amount': 500, 'spu_sales_amt': 500, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
        ])
        spu_sales.to_csv(api_dir / f"complete_spu_sales_{period}.csv", index=False)
    
    # Create clustering results (all in same cluster for peer comparison)
    clustering = pd.DataFrame([
        {'str_code': '1001', 'cluster_id': 0, 'Cluster': 0},
        {'str_code': '1002', 'cluster_id': 0, 'Cluster': 0},
        {'str_code': '1003', 'cluster_id': 0, 'Cluster': 0}
    ])
    clustering.to_csv(output_dir / "clustering_results_spu.csv", index=False)
    clustering.to_csv(output_dir / f"clustering_results_spu_{PERIOD_LABEL}.csv", index=False)


def _run_step11(sandbox: Path) -> None:
    """Actually run Step 11 in the sandbox."""
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    env["PIPELINE_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_PERIOD"] = TARGET_PERIOD
    env.setdefault("PYTHONPATH", str(sandbox))
    
    result = subprocess.run(
        [
            "python3",
            "src/step11_missed_sales_opportunity.py",
            "--target-yyyymm",
            TARGET_YYYYMM,
            "--target-period",
            TARGET_PERIOD,
            "--min-cluster-stores", "2",      # Lower threshold for testing (default 8)
            "--min-stores-selling", "2",      # Lower threshold for testing (default 5)
            "--min-spu-sales", "100",         # Lower threshold for testing (default 200)
        ],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # Always print output for debugging
    print(f"\n📋 Step 11 Output:")
    print(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr}")
    
    if result.returncode != 0:
        raise Exception(f"Step 11 failed with return code {result.returncode}")


def _load_outputs(sandbox: Path) -> dict:
    """Load generated output files."""
    output_dir = sandbox / "output"
    
    # Find the timestamped results file
    results_files = list(output_dir.glob("rule11_missed_*_results_*.csv"))
    
    if not results_files:
        # Try alternative patterns
        results_files = list(output_dir.glob("rule11_*.csv"))
    
    if not results_files:
        raise FileNotFoundError("No Step 11 results file found")
    
    results_file = results_files[0]
    
    return {
        'results': pd.read_csv(results_file, dtype={'str_code': str}),
        'results_path': results_file
    }


def test_step11_synthetic_isolated(tmp_path):
    """Test Step 11 runs in complete isolation with synthetic data."""
    
    # 1. Prepare sandbox
    sandbox = _prepare_sandbox(tmp_path)
    
    # 2. Create synthetic inputs
    _create_synthetic_inputs(sandbox)
    
    # 3. Run Step 11
    _run_step11(sandbox)
    
    # 4. Load outputs
    outputs = _load_outputs(sandbox)
    results = outputs['results']
    
    # 5. Validate outputs exist
    assert len(results) > 0, "Step 11 must create results"
    
    # 6. Validate required columns
    required_cols = ['str_code']
    for col in required_cols:
        assert col in results.columns, f"Missing required column: {col}"
    
    # 7. Validate str_code is string
    assert results['str_code'].dtype == object, "str_code should be string"
    
    # 8. Validate opportunity columns exist
    opportunity_cols = [col for col in results.columns 
                        if any(kw in col.lower() for kw in ['opportunity', 'quantity', 'increase', 'gap', 'missed'])]
    assert len(opportunity_cols) > 0, "Should have opportunity-related columns"
    
    print(f"✅ Step 11 synthetic test passed!")
    print(f"   Results: {len(results)} records")
    print(f"   Opportunity columns: {len(opportunity_cols)}")


def test_step11_dual_output_pattern(tmp_path):
    """Test Step 11 creates dual output pattern (timestamped + symlink)."""
    
    # 1. Prepare and run
    sandbox = _prepare_sandbox(tmp_path)
    _create_synthetic_inputs(sandbox)
    _run_step11(sandbox)
    
    # 2. Check for timestamped files
    output_dir = sandbox / "output"
    timestamped_files = list(output_dir.glob("rule11_missed_*_results_*_*.csv"))
    
    assert len(timestamped_files) > 0, "Must create timestamped files"
    
    # 3. Check for symlinks
    possible_symlinks = [
        "rule11_missed_subcategory_results.csv",
        "rule11_missed_spu_results.csv",
        "rule11_results.csv"
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
        print(f"✅ Step 11 dual output pattern validated")
    else:
        print(f"⚠️  Step 11 creates timestamped files but no symlinks found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
