"""
Step 10 Synthetic Isolated Test

Tests Step 10 (SPU Assortment Optimization) in complete isolation with synthetic data.
No dependencies on real pipeline - creates own data and runs the step.

Based on Step 11's successful pattern.
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
    Create synthetic input data for Step 10 testing.
    
    Step 10 tests overcapacity - needs stores with too many SPUs in a category.
    Step 10 also needs multiple periods for historical window (3 half-months).
    """
    api_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    
    # Create data for multiple periods (Step 10 needs historical window)
    periods = ['202509A', '202509B', '202510A']
    
    for period in periods:
        # Create store_config with overcapacity scenario
        # Store 1001: Has 5 SPUs in T恤 category (overcapacity!)
        # Store 1002: Has 3 SPUs in T恤 category (normal)
        # Store 1003: Has 4 SPUs in T恤 category (slight overcapacity)
        store_config = pd.DataFrame([
            {
                'str_code': '1001',
            'sty_sal_amt': '[' +
                '{"sub_cate_name":"T恤","spu_code":"SPU001","quantity":10,"sales_amount":500,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                '{"sub_cate_name":"T恤","spu_code":"SPU002","quantity":8,"sales_amount":400,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                '{"sub_cate_name":"T恤","spu_code":"SPU003","quantity":5,"sales_amount":250,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                '{"sub_cate_name":"T恤","spu_code":"SPU004","quantity":3,"sales_amount":150,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                '{"sub_cate_name":"T恤","spu_code":"SPU005","quantity":2,"sales_amount":100,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}' +
            ']'
        },
        {
            'str_code': '1002',
            'sty_sal_amt': '[' +
                '{"sub_cate_name":"T恤","spu_code":"SPU001","quantity":15,"sales_amount":750,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                '{"sub_cate_name":"T恤","spu_code":"SPU002","quantity":12,"sales_amount":600,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                '{"sub_cate_name":"T恤","spu_code":"SPU003","quantity":8,"sales_amount":400,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}' +
            ']'
        },
        {
            'str_code': '1003',
            'sty_sal_amt': '[' +
                '{"sub_cate_name":"T恤","spu_code":"SPU001","quantity":12,"sales_amount":600,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                '{"sub_cate_name":"T恤","spu_code":"SPU002","quantity":10,"sales_amount":500,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                '{"sub_cate_name":"T恤","spu_code":"SPU003","quantity":6,"sales_amount":300,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"},' +
                '{"sub_cate_name":"T恤","spu_code":"SPU006","quantity":4,"sales_amount":200,"season_name":"夏季","sex_name":"男","display_location_name":"前场","big_class_name":"上装"}' +
            ']'
        }
    ])
        store_config.to_csv(api_dir / f"store_config_{period}.csv", index=False)
        
        # Create SPU sales data with all required columns
        spu_sales = pd.DataFrame([
            # Store 1001 - Overcapacity with 5 SPUs
            {'str_code': '1001', 'spu_code': 'SPU001', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 10, 'sales_amount': 500, 'spu_sales_amt': 500, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 10, 'fashion_sal_qty': 0},
        {'str_code': '1001', 'spu_code': 'SPU002', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 8, 'sales_amount': 400, 'spu_sales_amt': 400, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 8, 'fashion_sal_qty': 0},
        {'str_code': '1001', 'spu_code': 'SPU003', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 5, 'sales_amount': 250, 'spu_sales_amt': 250, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 5, 'fashion_sal_qty': 0},
        {'str_code': '1001', 'spu_code': 'SPU004', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 3, 'sales_amount': 150, 'spu_sales_amt': 150, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 3, 'fashion_sal_qty': 0},
        {'str_code': '1001', 'spu_code': 'SPU005', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 2, 'sales_amount': 100, 'spu_sales_amt': 100, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 2, 'fashion_sal_qty': 0},
        # Store 1002 - Normal capacity with 3 SPUs
        {'str_code': '1002', 'spu_code': 'SPU001', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 15, 'sales_amount': 750, 'spu_sales_amt': 750, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 15, 'fashion_sal_qty': 0},
        {'str_code': '1002', 'spu_code': 'SPU002', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 12, 'sales_amount': 600, 'spu_sales_amt': 600, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 12, 'fashion_sal_qty': 0},
        {'str_code': '1002', 'spu_code': 'SPU003', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 8, 'sales_amount': 400, 'spu_sales_amt': 400, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 8, 'fashion_sal_qty': 0},
        # Store 1003 - Slight overcapacity with 4 SPUs
        {'str_code': '1003', 'spu_code': 'SPU001', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 12, 'sales_amount': 600, 'spu_sales_amt': 600, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 12, 'fashion_sal_qty': 0},
        {'str_code': '1003', 'spu_code': 'SPU002', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 10, 'sales_amount': 500, 'spu_sales_amt': 500, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 10, 'fashion_sal_qty': 0},
        {'str_code': '1003', 'spu_code': 'SPU003', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 6, 'sales_amount': 300, 'spu_sales_amt': 300, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 6, 'fashion_sal_qty': 0},
        {'str_code': '1003', 'spu_code': 'SPU006', 'cate_name': '上装', 'sub_cate_name': 'T恤', 'quantity': 4, 'sales_amount': 200, 'spu_sales_amt': 200, 'unit_price': 50.0, 'season_name': '夏季', 'sex_name': '男', 'display_location_name': '前场', 'big_class_name': '上装', 'base_sal_qty': 4, 'fashion_sal_qty': 0},
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


def _run_step10(sandbox: Path) -> None:
    """Actually run Step 10 in the sandbox.
    
    Note: Step 10 is computationally intensive even with minimal data because it:
    - Builds a 3-month historical window
    - Performs SPU assortment optimization calculations
    - Analyzes overcapacity across all stores and categories
    
    We use --skip-sellthrough and --min-cluster-size to speed it up for testing.
    """
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    env["PIPELINE_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_PERIOD"] = TARGET_PERIOD
    env.setdefault("PYTHONPATH", str(sandbox))
    
    result = subprocess.run(
        [
            "python3",
            "src/step10_spu_assortment_optimization.py",
            "--target-yyyymm",
            TARGET_YYYYMM,
            "--target-period",
            TARGET_PERIOD,
            "--skip-sellthrough",  # Skip validation to speed up test
            "--min-cluster-size", "2",  # Lower threshold for testing
        ],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=180  # Give it more time but with optimizations
    )
    
    # Always print output for debugging
    print(f"\n📋 Step 10 Output:")
    if result.stdout:
        print(f"STDOUT (last 1000 chars):\n{result.stdout[-1000:]}")
    if result.stderr:
        print(f"STDERR (last 500 chars):\n{result.stderr[-500:]}")
    
    if result.returncode != 0:
        raise Exception(f"Step 10 failed with return code {result.returncode}")


def _load_outputs(sandbox: Path) -> dict:
    """Load generated output files."""
    output_dir = sandbox / "output"
    
    # Find the timestamped results file
    results_files = list(output_dir.glob("rule10_*_results_*.csv"))
    
    if not results_files:
        # Try alternative patterns
        results_files = list(output_dir.glob("rule10_*.csv"))
    
    if not results_files:
        raise FileNotFoundError("No Step 10 results file found")
    
    results_file = results_files[0]
    
    return {
        'results': pd.read_csv(results_file, dtype={'str_code': str}),
        'results_path': results_file
    }


def test_step10_synthetic_isolated(tmp_path):
    """Test Step 10 runs in complete isolation with synthetic data."""
    
    # 1. Prepare sandbox
    sandbox = _prepare_sandbox(tmp_path)
    
    # 2. Create synthetic inputs
    _create_synthetic_inputs(sandbox)
    
    # 3. Run Step 10
    _run_step10(sandbox)
    
    # 4. Load outputs
    outputs = _load_outputs(sandbox)
    results = outputs['results']
    
    # 5. Validate outputs exist
    assert len(results) > 0, "Step 10 must create results"
    
    # 6. Validate required columns
    required_cols = ['str_code']
    for col in required_cols:
        assert col in results.columns, f"Missing required column: {col}"
    
    # 7. Validate str_code is string
    assert results['str_code'].dtype == object, "str_code should be string"
    
    # 8. Validate overcapacity columns exist
    overcapacity_cols = [col for col in results.columns 
                        if any(kw in col.lower() for kw in ['overcapacity', 'reduction', 'quantity', 'excess'])]
    assert len(overcapacity_cols) > 0, "Should have overcapacity-related columns"
    
    print(f"✅ Step 10 synthetic test passed!")
    print(f"   Results: {len(results)} records")
    print(f"   Overcapacity columns: {len(overcapacity_cols)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
