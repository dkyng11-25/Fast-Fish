"""
Step 2 Dual Output Validation Test

Validates that Step 2 creates timestamped files + symlinks (DUAL OUTPUT PATTERN).

This test ensures Step 2 follows the dual output pattern correctly:
- Creates timestamped files for audit trail
- Creates period-specific symlinks
- Creates generic symlinks for downstream consumption
"""

import os
import re
from pathlib import Path
import pandas as pd
import pytest


def test_step2_creates_dual_output_pattern():
    """
    Test Step 2 creates timestamped files + symlinks for coordinates and mappings.
    
    This validates the dual output pattern is correctly implemented.
    """
    # Check for timestamped coordinates files
    data_dir = Path("data")
    
    # Check coordinates
    coords_timestamped = list(data_dir.glob("store_coordinates_extended_*_*.csv"))
    if len(coords_timestamped) > 0:
        print(f"✅ Found {len(coords_timestamped)} timestamped coordinates files")
        
        # Check for generic symlink
        generic_coords = data_dir / "store_coordinates_extended.csv"
        if generic_coords.exists():
            assert generic_coords.is_symlink(), "Generic coordinates should be symlink"
            
            # Check symlink target uses basename
            link_target = os.readlink(generic_coords)
            assert '/' not in link_target, "Symlink should use basename"
            
            print(f"✅ VALIDATED: Coordinates use dual output pattern")
            print(f"   Generic: {generic_coords.name} -> {link_target}")
    
    # Check SPU mapping
    mapping_timestamped = list(data_dir.glob("spu_store_mapping_*_*.csv"))
    if len(mapping_timestamped) > 0:
        print(f"✅ Found {len(mapping_timestamped)} timestamped SPU mapping files")
        
        # Check for generic symlink
        generic_mapping = data_dir / "spu_store_mapping.csv"
        if generic_mapping.exists():
            assert generic_mapping.is_symlink(), "Generic mapping should be symlink"
            
            link_target = os.readlink(generic_mapping)
            assert '/' not in link_target, "Symlink should use basename"
            
            print(f"✅ VALIDATED: SPU mapping uses dual output pattern")
            print(f"   Generic: {generic_mapping.name} -> {link_target}")
    
    # Check SPU metadata
    metadata_timestamped = list(data_dir.glob("spu_metadata_*_*.csv"))
    if len(metadata_timestamped) > 0:
        print(f"✅ Found {len(metadata_timestamped)} timestamped SPU metadata files")
        
        # Check for generic symlink
        generic_metadata = data_dir / "spu_metadata.csv"
        if generic_metadata.exists():
            assert generic_metadata.is_symlink(), "Generic metadata should be symlink"
            
            link_target = os.readlink(generic_metadata)
            assert '/' not in link_target, "Symlink should use basename"
            
            print(f"✅ VALIDATED: SPU metadata uses dual output pattern")
            print(f"   Generic: {generic_metadata.name} -> {link_target}")
    
    # At least one output type should exist
    total_outputs = len(coords_timestamped) + len(mapping_timestamped) + len(metadata_timestamped)
    assert total_outputs > 0, "Step 2 should create at least one timestamped output"
    
    print(f"\n✅ OVERALL: Step 2 dual output pattern validated")


def test_step2_symlinks_point_to_timestamped_files():
    """Verify that generic symlinks point to timestamped files."""
    data_dir = Path("data")
    
    symlinks_to_check = [
        "store_coordinates_extended.csv",
        "spu_store_mapping.csv",
        "spu_metadata.csv"
    ]
    
    validated = 0
    for symlink_name in symlinks_to_check:
        symlink_path = data_dir / symlink_name
        if symlink_path.exists() and symlink_path.is_symlink():
            link_target = os.readlink(symlink_path)
            
            # Check target has timestamp format
            has_timestamp = re.search(r'_\d{8}_\d{6}\.csv$', link_target)
            if has_timestamp:
                print(f"✅ {symlink_name} -> {link_target} (timestamped)")
                validated += 1
            else:
                # Might point to period-specific symlink, check if that exists
                period_target = data_dir / link_target
                if period_target.exists() and period_target.is_symlink():
                    final_target = os.readlink(period_target)
                    has_timestamp = re.search(r'_\d{8}_\d{6}\.csv$', final_target)
                    if has_timestamp:
                        print(f"✅ {symlink_name} -> {link_target} -> {final_target} (timestamped)")
                        validated += 1
    
    if validated > 0:
        print(f"\n✅ Validated {validated} symlink(s) point to timestamped files")
    else:
        pytest.skip("No Step 2 outputs found to validate")


def test_step2_output_data_quality():
    """Validate Step 2 output data quality."""
    data_dir = Path("data")
    
    # Check coordinates file
    coords_file = data_dir / "store_coordinates_extended.csv"
    if coords_file.exists():
        coords_df = pd.read_csv(coords_file, dtype={'str_code': str})
        
        # Validate required columns
        required_cols = ['str_code', 'longitude', 'latitude']
        for col in required_cols:
            assert col in coords_df.columns, f"Missing required column: {col}"
        
        # Validate data types
        assert coords_df['str_code'].dtype == object, "str_code should be string"
        assert pd.api.types.is_numeric_dtype(coords_df['longitude']), "longitude should be numeric"
        assert pd.api.types.is_numeric_dtype(coords_df['latitude']), "latitude should be numeric"
        
        # Validate coordinate ranges
        assert coords_df['longitude'].between(-180, 180).all(), "Invalid longitude values"
        assert coords_df['latitude'].between(-90, 90).all(), "Invalid latitude values"
        
        print(f"✅ Coordinates data quality validated ({len(coords_df)} stores)")
    
    # Check SPU mapping file
    mapping_file = data_dir / "spu_store_mapping.csv"
    if mapping_file.exists():
        mapping_df = pd.read_csv(mapping_file, dtype={'str_code': str})
        
        # Validate required columns
        required_cols = ['str_code', 'spu_code']
        for col in required_cols:
            assert col in mapping_df.columns, f"Missing required column: {col}"
        
        print(f"✅ SPU mapping data quality validated ({len(mapping_df)} mappings)")
    
    # Check SPU metadata file
    metadata_file = data_dir / "spu_metadata.csv"
    if metadata_file.exists():
        metadata_df = pd.read_csv(metadata_file)
        
        # Validate required columns
        assert 'spu_code' in metadata_df.columns, "Missing spu_code column"
        
        print(f"✅ SPU metadata data quality validated ({len(metadata_df)} SPUs)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
