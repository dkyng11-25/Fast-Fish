#!/usr/bin/env python3
"""
Synthetic Test Suite for Step 22: Temperature Coverage Validation

Tests that Step 22 preserves temperature data for ALL stores, not just stores with sales data.

Key Test Scenarios:
1. All stores get temperature data even if sales data is incomplete
2. Temperature data is preserved when sales data is missing for some stores
3. Merge strategy prioritizes temperature coverage over sales enrichment
4. Output row count matches temperature input row count (not sales row count)
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

# Test configuration
SYNTHETIC_STORE_COUNT = 100  # Total stores in temperature data
SYNTHETIC_SALES_STORE_COUNT = 10  # Stores with sales data (subset)


def _prepare_sandbox(tmp_path: Path) -> Path:
    """
    Create isolated test environment with copied source code.
    
    Returns:
        Path to sandbox directory
    """
    sandbox = tmp_path / "step22_sandbox"
    sandbox.mkdir()
    
    # Copy src directory
    src_dir = Path(__file__).parent.parent.parent.parent / "src"
    sandbox_src = sandbox / "src"
    shutil.copytree(src_dir, sandbox_src)
    
    # Create output and data directories
    (sandbox / "output").mkdir()
    (sandbox / "data" / "api_data").mkdir(parents=True)
    
    # Create dummy pipeline_manifest.py if it doesn't exist
    manifest_file = sandbox_src / "pipeline_manifest.py"
    if not manifest_file.exists():
        manifest_file.write_text("""
def get_manifest():
    class DummyManifest:
        def get_latest_output(self, step, key_prefix=None, period_label=None):
            return None
    return DummyManifest()

def register_step_output(step, key, path, metadata=None):
    pass
""")
    
    return sandbox


def _seed_synthetic_temperature_data(sandbox: Path, store_count: int = SYNTHETIC_STORE_COUNT) -> None:
    """
    Create synthetic temperature data for ALL stores.
    
    This simulates Step 5 output with complete store coverage.
    """
    stores = [f"{10000 + i}" for i in range(store_count)]
    
    # Realistic temperature distribution
    np.random.seed(42)
    temps = np.random.uniform(0, 30, store_count)
    
    def _get_temp_band(temp: float) -> str:
        if temp < 5:
            return "0°C to 5°C"
        elif temp < 10:
            return "5°C to 10°C"
        elif temp < 15:
            return "10°C to 15°C"
        elif temp < 20:
            return "15°C to 20°C"
        elif temp < 25:
            return "20°C to 25°C"
        else:
            return "25°C to 30°C"
    
    temp_df = pd.DataFrame({
        'store_code': stores,
        'str_code': stores,  # Both column names for compatibility
        'feels_like_temperature': temps,
        'temperature_band': [_get_temp_band(t) for t in temps],
        'avg_temperature': temps,
        'avg_humidity': np.random.uniform(40, 80, store_count),
        'elevation': np.random.uniform(0, 2000, store_count),
    })
    
    temp_file = sandbox / "output" / "stores_with_feels_like_temperature.csv"
    temp_df.to_csv(temp_file, index=False)
    print(f"   ✓ Created temperature data: {len(temp_df)} stores")


def _seed_synthetic_sales_data(sandbox: Path, store_count: int = SYNTHETIC_SALES_STORE_COUNT) -> None:
    """
    Create synthetic sales data for SUBSET of stores.
    
    This simulates incomplete sales data (e.g., single cluster testing).
    """
    # Only create sales for first N stores
    stores = [f"{10000 + i}" for i in range(store_count)]
    
    np.random.seed(42)
    
    # Store sales data
    store_sales_df = pd.DataFrame({
        'str_code': stores,
        'total_sales_amt': np.random.uniform(10000, 100000, store_count),
        'total_sales_qty': np.random.randint(100, 1000, store_count),
        'fashion_sales_amt': np.random.uniform(5000, 50000, store_count),
        'basic_sales_amt': np.random.uniform(5000, 50000, store_count),
        'str_type': np.random.choice(['A', 'B', 'C'], store_count),
    })
    
    # SPU sales data (more detailed)
    spu_sales_rows = []
    for store in stores:
        n_spus = np.random.randint(5, 20)
        for i in range(n_spus):
            spu_sales_rows.append({
                'str_code': store,
                'spu_code': f'SPU{i:04d}',
                'sub_cate_name': np.random.choice(['T恤', '裤子', '外套', '裙子']),
                'sal_amt': np.random.uniform(100, 5000),
                'sal_qty': np.random.randint(1, 50),
            })
    
    spu_sales_df = pd.DataFrame(spu_sales_rows)
    
    # Save to both output and data/api_data for compatibility
    store_sales_file = sandbox / "output" / "store_sales_202510A.csv"
    store_sales_df.to_csv(store_sales_file, index=False)
    
    spu_sales_file = sandbox / "data" / "api_data" / "complete_spu_sales_202510A.csv"
    spu_sales_df.to_csv(spu_sales_file, index=False)
    
    print(f"   ✓ Created sales data: {len(stores)} stores (subset of total)")


def _seed_synthetic_clustering_data(sandbox: Path, store_count: int = SYNTHETIC_STORE_COUNT) -> None:
    """
    Create synthetic clustering data for ALL stores.
    """
    stores = [f"{10000 + i}" for i in range(store_count)]
    
    np.random.seed(42)
    cluster_df = pd.DataFrame({
        'str_code': stores,
        'Cluster': np.random.randint(0, 10, store_count),
    })
    
    cluster_file = sandbox / "output" / "clustering_results_spu.csv"
    cluster_df.to_csv(cluster_file, index=False)
    print(f"   ✓ Created clustering data: {len(cluster_df)} stores")


def _run_step22(sandbox: Path, target_yyyymm: str = "202510", target_period: str = "A") -> subprocess.CompletedProcess:
    """
    Execute Step 22 in the sandbox environment.
    
    Returns:
        CompletedProcess with stdout/stderr
    """
    env = os.environ.copy()
    env['PYTHONPATH'] = str(sandbox)
    
    cmd = [
        sys.executable,
        str(sandbox / "src" / "step22_store_attribute_enrichment.py"),
        "--target-yyyymm", target_yyyymm,
        "--target-period", target_period,
    ]
    
    result = subprocess.run(
        cmd,
        cwd=sandbox,
        capture_output=True,
        text=True,
        env=env,
    )
    
    return result


def _load_step22_output(sandbox: Path) -> pd.DataFrame:
    """
    Load Step 22 output from sandbox.
    
    Returns:
        DataFrame with enriched store attributes
    """
    # Find the latest timestamped output
    output_dir = sandbox / "output"
    pattern = "enriched_store_attributes_202510A_*.csv"
    
    import glob
    files = sorted(glob.glob(str(output_dir / pattern)))
    
    if not files:
        raise FileNotFoundError(f"No Step 22 output found matching {pattern}")
    
    latest_file = files[-1]
    df = pd.read_csv(latest_file)
    
    return df


# ============================================================================
# TEST CASES
# ============================================================================

def test_step22_preserves_all_stores_with_temperature_data(tmp_path):
    """
    CRITICAL TEST: Step 22 output should include ALL stores from temperature data,
    not just stores with sales data.
    
    Scenario:
    - 100 stores have temperature data
    - Only 10 stores have sales data
    - Expected: Step 22 output has 100 rows (all stores)
    - Current Bug: Step 22 output has 10 rows (only sales stores)
    """
    print("\n" + "="*70)
    print("TEST: Step 22 preserves all stores with temperature data")
    print("="*70)
    
    # Setup
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_temperature_data(sandbox, store_count=SYNTHETIC_STORE_COUNT)
    _seed_synthetic_sales_data(sandbox, store_count=SYNTHETIC_SALES_STORE_COUNT)
    _seed_synthetic_clustering_data(sandbox, store_count=SYNTHETIC_STORE_COUNT)
    
    print(f"\n📊 Test Setup:")
    print(f"   - Temperature data: {SYNTHETIC_STORE_COUNT} stores")
    print(f"   - Sales data: {SYNTHETIC_SALES_STORE_COUNT} stores (subset)")
    print(f"   - Expected output: {SYNTHETIC_STORE_COUNT} stores")
    
    # Execute
    print(f"\n🔧 Running Step 22...")
    result = _run_step22(sandbox)
    
    if result.returncode != 0:
        print(f"\n❌ Step 22 failed:")
        print(result.stderr)
        pytest.fail(f"Step 22 execution failed: {result.stderr}")
    
    # Validate
    output_df = _load_step22_output(sandbox)
    
    print(f"\n📈 Results:")
    print(f"   - Output rows: {len(output_df)}")
    print(f"   - Temperature coverage: {output_df['temperature_band'].notna().sum()} stores")
    print(f"   - Sales enrichment: {output_df['store_type'].notna().sum() if 'store_type' in output_df.columns else 0} stores")
    
    # CRITICAL ASSERTION: Output should have ALL stores from temperature data
    assert len(output_df) == SYNTHETIC_STORE_COUNT, (
        f"Step 22 output has {len(output_df)} rows, expected {SYNTHETIC_STORE_COUNT}. "
        f"This indicates Step 22 is only processing stores with sales data instead of all stores."
    )
    
    # Temperature data should be present for all stores
    temp_coverage = output_df['temperature_band'].notna().sum()
    assert temp_coverage >= SYNTHETIC_STORE_COUNT * 0.95, (
        f"Only {temp_coverage}/{SYNTHETIC_STORE_COUNT} stores have temperature data. "
        f"Expected at least 95% coverage."
    )
    
    print(f"\n✅ PASSED: Step 22 preserved all {SYNTHETIC_STORE_COUNT} stores")


def test_step22_temperature_data_not_lost_in_merge(tmp_path):
    """
    Test that temperature data is not lost during merge operations.
    
    Validates that the merge strategy uses 'left' join on temperature data,
    not on sales data.
    """
    print("\n" + "="*70)
    print("TEST: Temperature data not lost in merge")
    print("="*70)
    
    # Setup
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_temperature_data(sandbox, store_count=50)
    _seed_synthetic_sales_data(sandbox, store_count=5)  # Very small subset
    _seed_synthetic_clustering_data(sandbox, store_count=50)
    
    # Execute
    result = _run_step22(sandbox)
    
    if result.returncode != 0:
        pytest.fail(f"Step 22 execution failed: {result.stderr}")
    
    # Validate
    output_df = _load_step22_output(sandbox)
    
    # Check that stores WITHOUT sales data still have temperature data
    stores_with_temp = set(output_df[output_df['temperature_band'].notna()]['str_code'])
    stores_with_sales = set(output_df[output_df.get('store_type', pd.Series()).notna()]['str_code'])
    
    stores_temp_only = stores_with_temp - stores_with_sales
    
    print(f"\n📊 Merge Analysis:")
    print(f"   - Stores with temperature: {len(stores_with_temp)}")
    print(f"   - Stores with sales enrichment: {len(stores_with_sales)}")
    print(f"   - Stores with temp but no sales: {len(stores_temp_only)}")
    
    # CRITICAL: There should be stores with temperature but no sales enrichment
    assert len(stores_temp_only) >= 40, (
        f"Only {len(stores_temp_only)} stores have temperature without sales enrichment. "
        f"Expected at least 40 (50 temp stores - 5 sales stores). "
        f"This indicates temperature data is being lost in the merge."
    )
    
    print(f"\n✅ PASSED: Temperature data preserved for stores without sales data")


def test_step22_requires_sales_data(tmp_path):
    """
    Test that Step 22 correctly requires sales data and fails gracefully when missing.
    
    Step 22 is designed to require sales data (see line 265: "Require primary period 
    store-level sales; do not fallback"). This test validates that it fails with a 
    clear error message when sales data is missing.
    """
    print("\n" + "="*70)
    print("TEST: Step 22 requires sales data (expected failure)")
    print("="*70)
    
    # Setup - NO sales data at all
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_temperature_data(sandbox, store_count=30)
    # Don't create any sales data - this should cause Step 22 to fail
    _seed_synthetic_clustering_data(sandbox, store_count=30)
    
    print(f"\n📊 Test Setup:")
    print(f"   - Temperature data: 30 stores")
    print(f"   - Sales data: 0 stores (none)")
    print(f"   - Expected: Step 22 should fail with clear error message")
    
    # Execute
    result = _run_step22(sandbox)
    
    # Print Step 22 execution details for debugging
    print(f"\n🔍 Step 22 Execution:")
    print(f"   - Return code: {result.returncode}")
    
    # Step 22 should fail with non-zero return code
    assert result.returncode != 0, (
        "Step 22 should fail when sales data is missing, but it succeeded"
    )
    
    # Check that the error message is clear and helpful
    assert "Missing required source store sales" in result.stderr, (
        f"Step 22 should provide clear error about missing sales data. "
        f"Got stderr: {result.stderr[-500:]}"
    )
    
    print(f"\n✅ PASSED: Step 22 correctly requires sales data and fails with clear error")
    print(f"   Error message: 'Missing required source store sales'")
    
    # Verify no output was created (as expected)
    output_dir = sandbox / "output"
    pattern = "enriched_store_attributes_202510A_*.csv"
    import glob
    files = sorted(glob.glob(str(output_dir / pattern)))
    assert len(files) == 0, (
        f"Step 22 should not produce output when sales data is missing, "
        f"but found {len(files)} files"
    )


def test_step22_output_row_count_validation(tmp_path):
    """
    Test that Step 22 includes validation warnings when output row count
    is suspiciously low compared to temperature data.
    """
    print("\n" + "="*70)
    print("TEST: Step 22 output row count validation")
    print("="*70)
    
    # Setup - Large temperature data, small sales data
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_temperature_data(sandbox, store_count=200)
    _seed_synthetic_sales_data(sandbox, store_count=10)
    _seed_synthetic_clustering_data(sandbox, store_count=200)
    
    # Execute
    result = _run_step22(sandbox)
    
    if result.returncode != 0:
        pytest.fail(f"Step 22 execution failed: {result.stderr}")
    
    # Check output
    output_df = _load_step22_output(sandbox)
    
    print(f"\n📊 Validation Check:")
    print(f"   - Temperature input: 200 stores")
    print(f"   - Step 22 output: {len(output_df)} stores")
    print(f"   - Coverage: {len(output_df)/200*100:.1f}%")
    
    # Should warn if coverage is low
    if len(output_df) < 100:  # Less than 50% coverage
        print(f"\n⚠️ WARNING: Step 22 output has low store coverage!")
        print(f"   This suggests incomplete sales data or incorrect merge strategy.")
        
        # Check if Step 22 logged a warning
        if "WARNING" not in result.stdout and "⚠️" not in result.stdout:
            pytest.fail(
                f"Step 22 produced only {len(output_df)}/200 stores but did not log a warning. "
                f"Step 22 should validate output row count and warn when coverage is low."
            )
    
    # For this test, we expect the fix to be applied, so output should be ~200
    assert len(output_df) >= 180, (
        f"Step 22 output has only {len(output_df)}/200 stores. "
        f"Expected at least 90% coverage after fix is applied."
    )
    
    print(f"\n✅ PASSED: Step 22 output has proper store coverage")


def test_step22_temperature_band_distribution(tmp_path):
    """
    Test that temperature band distribution in output matches input distribution.
    
    This validates that temperature data is not being filtered or corrupted.
    """
    print("\n" + "="*70)
    print("TEST: Temperature band distribution preservation")
    print("="*70)
    
    # Setup
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_temperature_data(sandbox, store_count=100)
    _seed_synthetic_sales_data(sandbox, store_count=20)
    _seed_synthetic_clustering_data(sandbox, store_count=100)
    
    # Load input temperature data for comparison
    temp_input = pd.read_csv(sandbox / "output" / "stores_with_feels_like_temperature.csv")
    input_dist = temp_input['temperature_band'].value_counts()
    
    # Execute
    result = _run_step22(sandbox)
    
    if result.returncode != 0:
        pytest.fail(f"Step 22 execution failed: {result.stderr}")
    
    # Validate
    output_df = _load_step22_output(sandbox)
    output_dist = output_df['temperature_band'].value_counts()
    
    print(f"\n📊 Distribution Comparison:")
    print(f"\n   Input Distribution:")
    for band, count in input_dist.items():
        print(f"      {band}: {count} stores ({count/len(temp_input)*100:.1f}%)")
    
    print(f"\n   Output Distribution:")
    for band, count in output_dist.items():
        print(f"      {band}: {count} stores ({count/len(output_df)*100:.1f}%)")
    
    # Check that all temperature bands are preserved
    missing_bands = set(input_dist.index) - set(output_dist.index)
    if missing_bands:
        pytest.fail(
            f"Temperature bands missing in output: {missing_bands}. "
            f"This indicates temperature data is being filtered."
        )
    
    # Check that distribution is similar (within 20% for each band)
    for band in input_dist.index:
        input_pct = input_dist[band] / len(temp_input)
        output_pct = output_dist.get(band, 0) / len(output_df)
        
        diff = abs(input_pct - output_pct)
        assert diff < 0.20, (
            f"Temperature band '{band}' distribution changed significantly: "
            f"input {input_pct*100:.1f}% vs output {output_pct*100:.1f}% (diff: {diff*100:.1f}%). "
            f"This suggests temperature data is being corrupted or filtered."
        )
    
    print(f"\n✅ PASSED: Temperature band distribution preserved")


# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
