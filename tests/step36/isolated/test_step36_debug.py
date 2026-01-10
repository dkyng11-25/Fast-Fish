"""Debug test to understand why Step 36 produces empty output"""

import subprocess
import sys
from pathlib import Path
import pandas as pd
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step36_debug(tmp_path):
    """Debug Step 36 with minimal synthetic data"""
    
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    output_dir = sandbox / "output"
    output_dir.mkdir()
    
    # Copy source
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Create minimal Step 14 data
    step14_data = {
        'Year': [2025],
        'Month': [10],
        'Period': ['A'],
        'Store_Group_Name': ['TestGroup'],
        'Target_Style_Tags': ['[夏, 女, 后台]'],
        'Category': ['T恤'],
        'Subcategory': ['圆领T恤'],
        'ΔQty': [10],
        'Current_SPU_Quantity': [20],
        'Target_SPU_Quantity': [30],
        'Season': ['夏'],
        'Gender': ['女'],
        'Location': ['后台'],
    }
    df14 = pd.DataFrame(step14_data)
    df14.to_csv(output_dir / "enhanced_fast_fish_format_202510A.csv", index=False)
    print(f"\n✓ Created Step 14 file with {len(df14)} rows")
    print(df14)
    
    # Create minimal Step 32 data
    step32_data = {
        'Period': ['A'],
        'Store_Code': ['11001'],
        'Store_Group_Name': ['TestGroup'],
        'Target_Style_Tags': ['[夏, 女, 后台]'],
        'Category': ['T恤'],
        'Subcategory': ['圆领T恤'],
        'Season': ['夏'],
        'Gender': ['女'],
        'Location': ['后台'],
        'Group_ΔQty': [10.0],
        'Store_Allocation_Weight': [1.0],
        'Allocated_ΔQty': [10.0],
        'Allocation_Rationale': ['Test'],
        'Cluster_ID': [1],
        'Store_Sales_Amount': [50000.0]
    }
    df32 = pd.DataFrame(step32_data)
    df32.to_csv(output_dir / "store_level_allocation_results_202510A_20251003_test.csv", index=False)
    print(f"\n✓ Created Step 32 file with {len(df32)} rows")
    print(df32)
    
    # Run Step 36
    print("\n🚀 Running Step 36...")
    result = subprocess.run(
        [sys.executable, 'src/step36_unified_delivery_builder.py',
         '--target-yyyymm', '202510',
         '--target-period', 'A'],
        cwd=sandbox,
        capture_output=True,
        text=True
    )
    
    print(f"\nReturn code: {result.returncode}")
    print(f"\nStdout (last 1000 chars):")
    print(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
    
    if result.returncode != 0:
        print(f"\nStderr:")
        print(result.stderr)
        assert False, "Step 36 failed"
    
    # Check output
    output_files = list(output_dir.glob("unified_delivery_202510A_*.csv"))
    print(f"\n📁 Output files: {len(output_files)}")
    for f in output_files:
        print(f"  - {f.name}")
    
    if output_files:
        df_out = pd.read_csv(output_files[0])
        print(f"\n📊 Output DataFrame: {len(df_out)} rows, {len(df_out.columns)} columns")
        if len(df_out) > 0:
            print("\nFirst row:")
            for col in ['Store_Code', 'Category', 'Subcategory', 'Season', 'Gender', 'Allocated_ΔQty']:
                if col in df_out.columns:
                    print(f"  {col}: {df_out[col].iloc[0]}")
        else:
            print("\n⚠️ DataFrame is EMPTY!")
            print(f"Columns: {list(df_out.columns)[:10]}")
    
    assert len(output_files) > 0, "No output files created"
    df_out = pd.read_csv(output_files[0])
    assert len(df_out) > 0, f"Output is empty! Check Step 36 logs above"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
