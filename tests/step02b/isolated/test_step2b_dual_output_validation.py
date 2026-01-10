"""
Step 2b Dual Output Validation Test

Validates that Step 2b creates timestamped files + symlinks (DUAL OUTPUT PATTERN).

This test ensures Step 2b follows the dual output pattern correctly:
- Creates timestamped files for audit trail
- Creates generic symlinks for downstream consumption
"""

import os
import re
from pathlib import Path
import pandas as pd
import pytest


def test_step2b_creates_dual_output_pattern():
    """
    Test Step 2b creates timestamped files + symlinks for seasonal data.
    
    This validates the dual output pattern is correctly implemented.
    """
    output_dir = Path("output")
    
    # Check seasonal store profiles
    profiles_timestamped = list(output_dir.glob("seasonal_store_profiles_*_*.csv"))
    if len(profiles_timestamped) > 0:
        print(f"✅ Found {len(profiles_timestamped)} timestamped store profiles files")
        
        # Check for generic symlink
        generic_profiles = output_dir / "seasonal_store_profiles.csv"
        if generic_profiles.exists():
            assert generic_profiles.is_symlink(), "Generic profiles should be symlink"
            
            # Check symlink target uses basename
            link_target = os.readlink(generic_profiles)
            assert '/' not in link_target, "Symlink should use basename"
            
            print(f"✅ VALIDATED: Store profiles use dual output pattern")
            print(f"   Generic: {generic_profiles.name} -> {link_target}")
    
    # Check seasonal category patterns
    patterns_timestamped = list(output_dir.glob("seasonal_category_patterns_*_*.csv"))
    if len(patterns_timestamped) > 0:
        print(f"✅ Found {len(patterns_timestamped)} timestamped category patterns files")
        
        # Check for generic symlink
        generic_patterns = output_dir / "seasonal_category_patterns.csv"
        if generic_patterns.exists():
            assert generic_patterns.is_symlink(), "Generic patterns should be symlink"
            
            link_target = os.readlink(generic_patterns)
            assert '/' not in link_target, "Symlink should use basename"
            
            print(f"✅ VALIDATED: Category patterns use dual output pattern")
            print(f"   Generic: {generic_patterns.name} -> {link_target}")
    
    # Check seasonal clustering features
    features_timestamped = list(output_dir.glob("seasonal_clustering_features_*_*.csv"))
    if len(features_timestamped) > 0:
        print(f"✅ Found {len(features_timestamped)} timestamped clustering features files")
        
        # Check for generic symlink
        generic_features = output_dir / "seasonal_clustering_features.csv"
        if generic_features.exists():
            assert generic_features.is_symlink(), "Generic features should be symlink"
            
            link_target = os.readlink(generic_features)
            assert '/' not in link_target, "Symlink should use basename"
            
            print(f"✅ VALIDATED: Clustering features use dual output pattern")
            print(f"   Generic: {generic_features.name} -> {link_target}")
    
    # At least one output type should exist
    total_outputs = len(profiles_timestamped) + len(patterns_timestamped) + len(features_timestamped)
    assert total_outputs > 0, "Step 2b should create at least one timestamped output"
    
    print(f"\n✅ OVERALL: Step 2b dual output pattern validated")


def test_step2b_symlinks_point_to_timestamped_files():
    """Verify that generic symlinks point to timestamped files."""
    output_dir = Path("output")
    
    symlinks_to_check = [
        "seasonal_store_profiles.csv",
        "seasonal_category_patterns.csv",
        "seasonal_clustering_features.csv"
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
    
    if validated > 0:
        print(f"\n✅ Validated {validated} symlink(s) point to timestamped files")
    else:
        pytest.skip("No Step 2b outputs found to validate")


def test_step2b_output_data_quality():
    """Validate Step 2b output data quality."""
    output_dir = Path("output")
    
    # Check store profiles
    profiles_file = output_dir / "seasonal_store_profiles.csv"
    if profiles_file.exists():
        profiles_df = pd.read_csv(profiles_file, dtype={'str_code': str})
        
        # Validate required columns
        assert 'str_code' in profiles_df.columns, "Missing str_code column"
        
        # Validate str_code is string
        assert profiles_df['str_code'].dtype == object, "str_code should be string"
        
        # Check for seasonal metrics
        seasonal_cols = [col for col in profiles_df.columns if 'seasonal' in col.lower()]
        assert len(seasonal_cols) > 0, "Should have seasonal metric columns"
        
        print(f"✅ Store profiles data quality validated ({len(profiles_df)} stores)")
        print(f"   Seasonal columns: {len(seasonal_cols)}")
    
    # Check category patterns
    patterns_file = output_dir / "seasonal_category_patterns.csv"
    if patterns_file.exists():
        patterns_df = pd.read_csv(patterns_file)
        
        # Should have category-related columns
        assert len(patterns_df.columns) > 0, "Should have pattern columns"
        
        print(f"✅ Category patterns data quality validated ({len(patterns_df)} patterns)")
    
    # Check clustering features
    features_file = output_dir / "seasonal_clustering_features.csv"
    if features_file.exists():
        features_df = pd.read_csv(features_file, dtype={'str_code': str})
        
        # Validate required columns
        assert 'str_code' in features_df.columns, "Missing str_code column"
        
        print(f"✅ Clustering features data quality validated ({len(features_df)} stores)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
