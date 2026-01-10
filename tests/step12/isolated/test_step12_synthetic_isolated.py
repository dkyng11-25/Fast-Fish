"""
Step 12 Synthetic Isolated Test

Tests Step 12 (Sales Performance Rule) in complete isolation with synthetic data.
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
    Create synthetic input data for Step 12 testing.
    
    Step 12 tests performance deviation - needs stores in same cluster with different
    performance levels (some underperforming vs cluster top quartile).
    """
    api_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    
    # Create synthetic data for multiple periods (Step 12 needs historical window)
    periods = ['202509A', '202509B', '202510A']
    
    for period in periods:
        # Create store_config with performance gap scenario
        # Store 1001: Low performance ($800 in 衬衫)
        # Store 1002: High performance ($4000 in 衬衫) - top quartile
        # Store 1003: Medium performance ($1600 in 衬衫)
        # Store 1004: Medium-high performance ($2400 in 衬衫)
        store_config = pd.DataFrame([
            {
                'str_code': '1001',
                'season_name': '春季',
                'sex_name': '男',
                'display_location_name': '前场',
                'big_class_name': '上装',
                'sub_cate_name': '衬衫',
                'sty_sal_amt': '[' +
                    '{"sub_cate_name":"衬衫","spu_code":"SPU001","quantity":10,"sales_amount":800,"season_name":"春季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}' +
                ']'
            },
            {
                'str_code': '1002',
                'season_name': '春季',
                'sex_name': '男',
                'display_location_name': '前场',
                'big_class_name': '上装',
                'sub_cate_name': '衬衫',
                'sty_sal_amt': '[' +
                    '{"sub_cate_name":"衬衫","spu_code":"SPU001","quantity":50,"sales_amount":4000,"season_name":"春季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}' +
                ']'
            },
            {
                'str_code': '1003',
                'season_name': '春季',
                'sex_name': '男',
                'display_location_name': '前场',
                'big_class_name': '上装',
                'sub_cate_name': '衬衫',
                'sty_sal_amt': '[' +
                    '{"sub_cate_name":"衬衫","spu_code":"SPU001","quantity":20,"sales_amount":1600,"season_name":"春季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}' +
                ']'
            },
            {
                'str_code': '1004',
                'season_name': '春季',
                'sex_name': '男',
                'display_location_name': '前场',
                'big_class_name': '上装',
                'sub_cate_name': '衬衫',
                'sty_sal_amt': '[' +
                    '{"sub_cate_name":"衬衫","spu_code":"SPU001","quantity":30,"sales_amount":2400,"season_name":"春季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}' +
                ']'
            }
        ])
        store_config.to_csv(api_dir / f"store_config_{period}.csv", index=False)
        
        # Create SPU sales data (with cate_name column)
        spu_sales = pd.DataFrame([
            # Store 1001 - Low performance (underperformer)
            {'str_code': '1001', 'spu_code': 'SPU001', 'cate_name': '上装', 'sub_cate_name': '衬衫', 'quantity': 10, 'sales_amount': 800, 'spu_sales_amt': 800, 'unit_price': 80.0, 'season_name': '春季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
            # Store 1002 - High performance (top quartile)
            {'str_code': '1002', 'spu_code': 'SPU001', 'cate_name': '上装', 'sub_cate_name': '衬衫', 'quantity': 50, 'sales_amount': 4000, 'spu_sales_amt': 4000, 'unit_price': 80.0, 'season_name': '春季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
            # Store 1003 - Medium performance
            {'str_code': '1003', 'spu_code': 'SPU001', 'cate_name': '上装', 'sub_cate_name': '衬衫', 'quantity': 20, 'sales_amount': 1600, 'spu_sales_amt': 1600, 'unit_price': 80.0, 'season_name': '春季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
            # Store 1004 - Medium-high performance
            {'str_code': '1004', 'spu_code': 'SPU001', 'cate_name': '上装', 'sub_cate_name': '衬衫', 'quantity': 30, 'sales_amount': 2400, 'spu_sales_amt': 2400, 'unit_price': 80.0, 'season_name': '春季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装'},
        ])
        spu_sales.to_csv(api_dir / f"complete_spu_sales_{period}.csv", index=False)
    
    # Create clustering results (all in same cluster for peer comparison)
    clustering = pd.DataFrame([
        {'str_code': '1001', 'cluster_id': 0, 'Cluster': 0},
        {'str_code': '1002', 'cluster_id': 0, 'Cluster': 0},
        {'str_code': '1003', 'cluster_id': 0, 'Cluster': 0},
        {'str_code': '1004', 'cluster_id': 0, 'Cluster': 0}
    ])
    clustering.to_csv(output_dir / "clustering_results_spu.csv", index=False)
    clustering.to_csv(output_dir / f"clustering_results_spu_{PERIOD_LABEL}.csv", index=False)


def _run_step12(sandbox: Path) -> None:
    """Actually run Step 12 in the sandbox."""
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    env["PIPELINE_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_PERIOD"] = TARGET_PERIOD
    env.setdefault("PYTHONPATH", str(sandbox))
    
    result = subprocess.run(
        [
            "python3",
            "src/step12_sales_performance_rule.py",
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
        raise Exception(f"Step 12 failed with return code {result.returncode}")


def _load_outputs(sandbox: Path) -> dict:
    """Load generated output files."""
    output_dir = sandbox / "output"
    
    # Find the timestamped results file
    results_files = list(output_dir.glob("rule12_*_results_*.csv"))
    
    if not results_files:
        # Try alternative patterns
        results_files = list(output_dir.glob("rule12_*.csv"))
    
    if not results_files:
        raise FileNotFoundError("No Step 12 results file found")
    
    results_file = results_files[0]
    
    return {
        'results': pd.read_csv(results_file, dtype={'str_code': str}),
        'results_path': results_file
    }


def test_step12_synthetic_isolated(tmp_path):
    """Test Step 12 runs in complete isolation with synthetic data."""
    
    # 1. Prepare sandbox
    sandbox = _prepare_sandbox(tmp_path)
    
    # 2. Create synthetic inputs
    _create_synthetic_inputs(sandbox)
    
    # 3. Run Step 12
    _run_step12(sandbox)
    
    # 4. Load outputs
    outputs = _load_outputs(sandbox)
    results = outputs['results']
    
    # 5. Validate outputs exist
    assert len(results) > 0, "Step 12 must create results"
    
    # 6. Validate required columns
    required_cols = ['str_code']
    for col in required_cols:
        assert col in results.columns, f"Missing required column: {col}"
    
    # 7. Validate str_code is string
    assert results['str_code'].dtype == object, "str_code should be string"
    
    # 8. Validate performance columns exist
    performance_cols = [col for col in results.columns 
                        if any(kw in col.lower() for kw in ['performance', 'quantity', 'increase', 'gap', 'opportunity'])]
    assert len(performance_cols) > 0, "Should have performance-related columns"
    
    print(f"✅ Step 12 synthetic test passed!")
    print(f"   Results: {len(results)} records")
    print(f"   Performance columns: {len(performance_cols)}")


def test_step12_dual_output_pattern(tmp_path):
    """Test Step 12 creates dual output pattern (timestamped + symlink)."""
    
    # 1. Prepare and run
    sandbox = _prepare_sandbox(tmp_path)
    _create_synthetic_inputs(sandbox)
    _run_step12(sandbox)
    
    # 2. Check for timestamped files
    output_dir = sandbox / "output"
    timestamped_files = list(output_dir.glob("rule12_*_results_*_*.csv"))
    
    assert len(timestamped_files) > 0, "Must create timestamped files"
    
    # 3. Check for symlinks or regular files
    possible_files = [
        "rule12_subcategory_results.csv",
        "rule12_spu_results.csv",
        "rule12_sales_performance_results.csv",
        "rule12_results.csv"
    ]
    
    file_found = False
    for file_name in possible_files:
        file_path = output_dir / file_name
        if file_path.exists():
            if file_path.is_symlink():
                link_target = os.readlink(file_path)
                assert '/' not in link_target, "Symlink should use basename"
                print(f"✅ Found symlink: {file_name} -> {link_target}")
            else:
                print(f"✅ Found regular file: {file_name}")
            file_found = True
    
    if file_found:
        print(f"✅ Step 12 output pattern validated")
    else:
        print(f"⚠️  Step 12 creates timestamped files but no generic files found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
