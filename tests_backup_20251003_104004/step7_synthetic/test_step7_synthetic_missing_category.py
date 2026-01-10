"""
Step 7 Synthetic Tests - Missing Category Rule (Isolated)
========================================================

This module provides isolated, synthetic tests for Step 7 (Missing Category Rule)
following the same pattern as Step 13 synthetic tests.

Key Features:
- Self-contained sandbox environments
- Synthetic data generation
- No external dependencies
- Isolated business logic testing
- Predictable, repeatable results
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import pytest

TARGET_YYYYMM = "202501"
TARGET_PERIOD = "A"
PERIOD_LABEL = f"{TARGET_YYYYMM}{TARGET_PERIOD}"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"


def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox environment for Step 7 testing."""
    sandbox = tmp_path / "sandbox"
    src_target = sandbox / "src"
    shutil.copytree(SRC_ROOT, src_target)

    # Mock pipeline_manifest.py to avoid external dependencies
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
    
    # Mock config.py for Step 7 dependencies
    config_stub = f"""
import os
from pathlib import Path

def initialize_pipeline_config(*args, **kwargs):
    pass

def get_current_period():
    return "{TARGET_YYYYMM}", "{TARGET_PERIOD}"

def get_period_label(*args, **kwargs):
    return "{PERIOD_LABEL}"

def get_api_data_files(yyyymm, period):
    base_path = "data/api_data"
    return {{
        'spu_sales': f"{{base_path}}/complete_spu_sales_{{yyyymm}}{{period}}.csv",
        'category_sales': f"{{base_path}}/complete_category_sales_{{yyyymm}}{{period}}.csv",
        'store_sales': f"{{base_path}}/store_sales_{{yyyymm}}{{period}}.csv",
    }}

def get_output_files():
    return {{
        'clustering_spu': f"output/clustering_results_spu_{PERIOD_LABEL}.csv",
        'clustering_subcategory': f"output/clustering_results_subcategory_{PERIOD_LABEL}.csv",
    }}

def load_margin_rates(period_label, analysis_type='spu'):
    # Mock margin rates
    import pandas as pd
    return pd.DataFrame([
        {{'spu_code': 'SPU001', 'margin_rate': 0.4}},
        {{'spu_code': 'SPU002', 'margin_rate': 0.35}},
        {{'spu_code': 'SPU003', 'margin_rate': 0.45}},
        {{'spu_code': 'SPU004', 'margin_rate': 0.38}},
        {{'spu_code': 'SPU005', 'margin_rate': 0.42}},
    ])
""".strip()
    (src_target / "config.py").write_text(config_stub, encoding="utf-8")
    (src_target / "__init__.py").write_text("", encoding="utf-8")

    # Create directory structure
    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    return sandbox


def _generate_synthetic_cluster_data(sandbox: Path) -> None:
    """Generate synthetic clustering results for Step 7 testing."""
    cluster_data = pd.DataFrame([
        {"str_code": "1001", "Cluster": 1},
        {"str_code": "1002", "Cluster": 1},
        {"str_code": "1003", "Cluster": 1},
        {"str_code": "2001", "Cluster": 2},
        {"str_code": "2002", "Cluster": 2},
        {"str_code": "2003", "Cluster": 2},
        {"str_code": "3001", "Cluster": 3},
        {"str_code": "3002", "Cluster": 3},
    ])
    
    cluster_file = sandbox / "output" / f"clustering_results_spu_{PERIOD_LABEL}.csv"
    cluster_data.to_csv(cluster_file, index=False)


def _generate_synthetic_sales_data(sandbox: Path) -> None:
    """Generate synthetic SPU sales data for Step 7 testing."""
    # Create sales data with some stores missing certain SPUs (the "missing" opportunities)
    sales_data = []
    
    spus = ["SPU001", "SPU002", "SPU003", "SPU004", "SPU005"]
    subcategories = ["休闲裤", "牛仔裤", "运动裤"]
    
    for store in ["1001", "1002", "1003", "2001", "2002", "2003", "3001", "3002"]:
        for i, spu in enumerate(spus):
            # Simulate missing SPUs: some stores don't carry certain SPUs
            if store == "1001" and spu == "SPU003":  # Store 1001 missing SPU003
                continue
            if store == "2001" and spu in ["SPU004", "SPU005"]:  # Store 2001 missing SPU004, SPU005
                continue
            
            sales_data.append({
                "str_code": store,
                "spu_code": spu,
                "sub_cate_name": subcategories[i % len(subcategories)],
                "spu_sales_amt": np.random.uniform(1000, 5000),
                "base_sal_qty": np.random.uniform(10, 50),
                "fashion_sal_qty": np.random.uniform(5, 25),
            })
    
    sales_df = pd.DataFrame(sales_data)
    
    # Save current period sales
    current_file = sandbox / "data" / "api_data" / f"complete_spu_sales_{PERIOD_LABEL}.csv"
    sales_df.to_csv(current_file, index=False)
    
    # Save seasonal reference data (December 2024)
    seasonal_file = sandbox / "data" / "api_data" / "complete_spu_sales_202412B.csv"
    # Add some seasonal variation
    seasonal_df = sales_df.copy()
    seasonal_df["spu_sales_amt"] *= np.random.uniform(0.8, 1.2, len(seasonal_df))
    seasonal_df.to_csv(seasonal_file, index=False)


def _generate_synthetic_store_sales_data(sandbox: Path) -> None:
    """Generate synthetic store-level sales data for quantity calculations."""
    store_data = []
    
    for store in ["1001", "1002", "1003", "2001", "2002", "2003", "3001", "3002"]:
        store_data.append({
            "str_code": store,
            "total_sales_amt": np.random.uniform(50000, 200000),
            "total_quantity": np.random.uniform(500, 2000),
        })
    
    store_df = pd.DataFrame(store_data)
    store_file = sandbox / "data" / "api_data" / f"store_sales_{PERIOD_LABEL}.csv"
    store_df.to_csv(store_file, index=False)


def _seed_synthetic_inputs(sandbox: Path) -> None:
    """Generate all synthetic input data for Step 7 testing."""
    _generate_synthetic_cluster_data(sandbox)
    _generate_synthetic_sales_data(sandbox)
    _generate_synthetic_store_sales_data(sandbox)


def _run_step7_isolated(sandbox: Path) -> subprocess.CompletedProcess:
    """Run Step 7 in isolated sandbox environment."""
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(sandbox))
    
    cmd = [
        "python3", 
        "src/step7_missing_category_rule.py",
        "--yyyymm", TARGET_YYYYMM,
        "--period", TARGET_PERIOD,
        "--analysis-level", "spu",
        "--target-yyyymm", TARGET_YYYYMM,
        "--target-period", TARGET_PERIOD,
    ]
    
    return subprocess.run(
        cmd,
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
    )


def test_step7_synthetic_missing_spu_detection_isolated(tmp_path):
    """Test that Step 7 correctly identifies missing SPU opportunities in synthetic environment."""
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_inputs(sandbox)
    
    # Run Step 7
    result = _run_step7_isolated(sandbox)
    
    # Check that Step 7 completed successfully
    assert result.returncode == 0, f"Step 7 failed: {result.stderr}"
    
    # Check output files exist
    output_file = sandbox / "output" / f"rule7_missing_spu_sellthrough_results_{PERIOD_LABEL}.csv"
    assert output_file.exists(), "Step 7 results file not created"
    
    # Load and validate results
    results_df = pd.read_csv(output_file)
    
    # Should have results for stores that were analyzed
    assert len(results_df) > 0, "No results generated"
    assert "str_code" in results_df.columns, "Missing str_code column"
    assert "missing_spus_count" in results_df.columns, "Missing missing_spus_count column"


def test_step7_synthetic_cluster_based_analysis_isolated(tmp_path):
    """Test that Step 7 performs cluster-based analysis correctly."""
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_inputs(sandbox)
    
    result = _run_step7_isolated(sandbox)
    assert result.returncode == 0, f"Step 7 failed: {result.stderr}"
    
    # Check that cluster-based logic is working
    opportunities_file = sandbox / "output" / f"rule7_missing_spu_sellthrough_opportunities_{PERIOD_LABEL}.csv"
    
    if opportunities_file.exists():
        opps_df = pd.read_csv(opportunities_file)
        if len(opps_df) > 0:
            # Should have cluster information
            assert "cluster_id" in opps_df.columns or "Cluster" in opps_df.columns, "Missing cluster information"
            assert "spu_code" in opps_df.columns, "Missing SPU code"
            assert "sub_cate_name" in opps_df.columns, "Missing subcategory information"


def test_step7_synthetic_seasonal_blending_isolated(tmp_path):
    """Test that Step 7 handles seasonal blending correctly."""
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_inputs(sandbox)
    
    # Run with seasonal blending enabled
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(sandbox))
    
    cmd = [
        "python3", 
        "src/step7_missing_category_rule.py",
        "--yyyymm", TARGET_YYYYMM,
        "--period", TARGET_PERIOD,
        "--analysis-level", "spu",
        "--seasonal-blending",
        "--seasonal-yyyymm", "202412",
        "--seasonal-period", "B",
        "--seasonal-weight", "0.7",
        "--target-yyyymm", TARGET_YYYYMM,
        "--target-period", TARGET_PERIOD,
    ]
    
    result = subprocess.run(
        cmd,
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, f"Step 7 seasonal blending failed: {result.stderr}"
    
    # Verify output exists
    output_file = sandbox / "output" / f"rule7_missing_spu_sellthrough_results_{PERIOD_LABEL}.csv"
    assert output_file.exists(), "Step 7 seasonal results file not created"


def test_step7_synthetic_fast_fish_validation_isolated(tmp_path):
    """Test that Step 7 Fast Fish validation works correctly."""
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_inputs(sandbox)
    
    result = _run_step7_isolated(sandbox)
    assert result.returncode == 0, f"Step 7 failed: {result.stderr}"
    
    # Check that Fast Fish validation messages appear in output
    assert "Fast Fish" in result.stdout or "sell-through" in result.stdout, \
        "Fast Fish validation not detected in output"


def test_step7_synthetic_quantity_recommendations_isolated(tmp_path):
    """Test that Step 7 generates quantity-based recommendations."""
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_inputs(sandbox)
    
    result = _run_step7_isolated(sandbox)
    assert result.returncode == 0, f"Step 7 failed: {result.stderr}"
    
    # Check for quantity-related output
    opportunities_file = sandbox / "output" / f"rule7_missing_spu_sellthrough_opportunities_{PERIOD_LABEL}.csv"
    
    if opportunities_file.exists():
        opps_df = pd.read_csv(opportunities_file)
        if len(opps_df) > 0:
            # Should have quantity recommendations
            quantity_cols = [col for col in opps_df.columns if "qty" in col.lower() or "quantity" in col.lower()]
            assert len(quantity_cols) > 0, "No quantity columns found in opportunities"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
