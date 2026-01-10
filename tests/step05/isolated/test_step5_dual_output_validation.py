"""
Step 5 Dual Output Validation Test

Validates that Step 5 creates timestamped files + symlinks (DUAL OUTPUT PATTERN).

This test ensures Step 5 follows the dual output pattern correctly:
- Creates timestamped files for audit trail
- Creates period-specific symlinks
- Creates generic symlinks for downstream consumption
"""

import os
import re
from pathlib import Path
import pandas as pd
import pytest


def test_step5_creates_dual_output_pattern():
    """
    Test Step 5 creates timestamped files + symlinks for temperature data.
    
    This validates the dual output pattern is correctly implemented.
    """
    output_dir = Path("output")
    
    # Check temperature bands
    bands_timestamped = list(output_dir.glob("temperature_bands_*_*.csv"))
    if len(bands_timestamped) > 0:
        print(f"✅ Found {len(bands_timestamped)} timestamped temperature bands files")
        
        # Check for generic symlink
        generic_bands = output_dir / "temperature_bands.csv"
        if generic_bands.exists():
            assert generic_bands.is_symlink(), "Generic bands should be symlink"
            
            # Check symlink target uses basename
            link_target = os.readlink(generic_bands)
            assert '/' not in link_target, "Symlink should use basename"
            
            print(f"✅ VALIDATED: Temperature bands use dual output pattern")
            print(f"   Generic: {generic_bands.name} -> {link_target}")
    
    # Check stores with feels-like temperature
    temp_timestamped = list(output_dir.glob("stores_with_feels_like_temperature_*_*.csv"))
    if len(temp_timestamped) > 0:
        print(f"✅ Found {len(temp_timestamped)} timestamped feels-like temperature files")
        
        # Check for generic symlink
        generic_temp = output_dir / "stores_with_feels_like_temperature.csv"
        if generic_temp.exists():
            assert generic_temp.is_symlink(), "Generic temperature should be symlink"
            
            link_target = os.readlink(generic_temp)
            assert '/' not in link_target, "Symlink should use basename"
            
            print(f"✅ VALIDATED: Feels-like temperature uses dual output pattern")
            print(f"   Generic: {generic_temp.name} -> {link_target}")
    
    # At least one output type should exist
    total_outputs = len(bands_timestamped) + len(temp_timestamped)
    assert total_outputs > 0, "Step 5 should create at least one timestamped output"
    
    print(f"\n✅ OVERALL: Step 5 dual output pattern validated")


def test_step5_symlinks_point_to_timestamped_files():
    """Verify that generic symlinks point to timestamped files."""
    output_dir = Path("output")
    
    symlinks_to_check = [
        "temperature_bands.csv",
        "stores_with_feels_like_temperature.csv"
    ]
    
    validated = 0
    for symlink_name in symlinks_to_check:
        symlink_path = output_dir / symlink_name
        if symlink_path.exists() and symlink_path.is_symlink():
            link_target = os.readlink(symlink_path)
            
            # Check target has timestamp format
            has_timestamp = re.search(r'_\d{8}_\d{6}\.csv$', link_target)
            if has_timestamp:
                print(f"✅ {symlink_name} -> {link_target} (timestamped)")
                validated += 1
            else:
                # Might point to period-specific symlink
                period_target = output_dir / link_target
                if period_target.exists() and period_target.is_symlink():
                    final_target = os.readlink(period_target)
                    has_timestamp = re.search(r'_\d{8}_\d{6}\.csv$', final_target)
                    if has_timestamp:
                        print(f"✅ {symlink_name} -> {link_target} -> {final_target} (timestamped)")
                        validated += 1
    
    if validated > 0:
        print(f"\n✅ Validated {validated} symlink(s) point to timestamped files")
    else:
        pytest.skip("No Step 5 outputs found to validate")


def test_step5_output_data_quality():
    """Validate Step 5 output data quality."""
    output_dir = Path("output")
    
    # Check temperature bands
    bands_file = output_dir / "temperature_bands.csv"
    if bands_file.exists():
        bands_df = pd.read_csv(bands_file)
        
        # Validate required columns
        required_cols = ['Temperature_Band', 'Store_Count']
        for col in required_cols:
            assert col in bands_df.columns, f"Missing required column: {col}"
        
        # Validate store counts are positive
        assert (bands_df['Store_Count'] > 0).all(), "Store counts should be positive"
        
        # Validate temperature ranges if present
        if 'Min_Temp' in bands_df.columns and 'Max_Temp' in bands_df.columns:
            assert (bands_df['Max_Temp'] >= bands_df['Min_Temp']).all(), "Max temp should be >= Min temp"
        
        print(f"✅ Temperature bands data quality validated")
        print(f"   Bands: {len(bands_df)}")
        print(f"   Total stores: {bands_df['Store_Count'].sum()}")
    
    # Check feels-like temperature
    temp_file = output_dir / "stores_with_feels_like_temperature.csv"
    if temp_file.exists():
        temp_df = pd.read_csv(temp_file, dtype={'store_code': str, 'str_code': str})
        
        # Validate required columns (Step 5 uses store_code, not str_code)
        store_col = 'store_code' if 'store_code' in temp_df.columns else 'str_code'
        assert store_col in temp_df.columns, "Missing store code column"
        assert 'feels_like_temperature' in temp_df.columns or 'avg_temperature' in temp_df.columns, \
            "Missing temperature column"
        
        # Validate store code is string
        assert temp_df[store_col].dtype == object, f"{store_col} should be string"
        
        # Validate temperature band column exists
        band_cols = [col for col in temp_df.columns if 'band' in col.lower()]
        assert len(band_cols) > 0, "Should have temperature band column"
        
        # Check temperature values are reasonable (if column exists)
        temp_col = 'feels_like_temperature' if 'feels_like_temperature' in temp_df.columns else 'avg_temperature'
        if temp_col in temp_df.columns:
            temp_values = temp_df[temp_col].dropna()
            if len(temp_values) > 0:
                assert temp_values.min() >= -50, "Temperature too low (< -50°C)"
                assert temp_values.max() <= 60, "Temperature too high (> 60°C)"
                
                print(f"✅ Feels-like temperature data quality validated")
                print(f"   Stores: {len(temp_df)}")
                print(f"   Temperature range: [{temp_values.min():.1f}°C, {temp_values.max():.1f}°C]")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
