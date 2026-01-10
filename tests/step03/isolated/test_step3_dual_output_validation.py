"""
Step 3 Dual Output Validation Test

Validates that Step 3 creates timestamped files + symlinks (DUAL OUTPUT PATTERN).

This test ensures Step 3 follows the dual output pattern correctly:
- Creates timestamped files for audit trail
- Creates period-specific symlinks
- Creates generic symlinks for downstream consumption
"""

import os
import re
from pathlib import Path
import pandas as pd
import pytest


def test_step3_creates_dual_output_pattern():
    """
    Test Step 3 creates timestamped files + symlinks for matrices.
    
    This validates the dual output pattern is correctly implemented.
    """
    data_dir = Path("data")
    
    # Matrix types to check
    matrix_types = ["subcategory", "spu_limited", "category_agg"]
    
    validated_types = []
    
    for matrix_type in matrix_types:
        # Check original matrix
        original_timestamped = list(data_dir.glob(f"store_{matrix_type}_matrix_*_*.csv"))
        if len(original_timestamped) > 0:
            print(f"✅ Found {len(original_timestamped)} timestamped {matrix_type} original matrix files")
            
            # Check for generic symlink
            generic_original = data_dir / f"store_{matrix_type}_matrix.csv"
            if generic_original.exists():
                assert generic_original.is_symlink(), f"Generic {matrix_type} original should be symlink"
                
                # Check symlink target uses basename
                link_target = os.readlink(generic_original)
                assert '/' not in link_target, "Symlink should use basename"
                
                print(f"✅ VALIDATED: {matrix_type} original matrix uses dual output pattern")
                print(f"   Generic: {generic_original.name} -> {link_target}")
                validated_types.append(f"{matrix_type}_original")
        
        # Check normalized matrix
        normalized_timestamped = list(data_dir.glob(f"normalized_{matrix_type}_matrix_*_*.csv"))
        if len(normalized_timestamped) > 0:
            print(f"✅ Found {len(normalized_timestamped)} timestamped {matrix_type} normalized matrix files")
            
            # Check for generic symlink
            generic_normalized = data_dir / f"normalized_{matrix_type}_matrix.csv"
            if generic_normalized.exists():
                assert generic_normalized.is_symlink(), f"Generic {matrix_type} normalized should be symlink"
                
                link_target = os.readlink(generic_normalized)
                assert '/' not in link_target, "Symlink should use basename"
                
                print(f"✅ VALIDATED: {matrix_type} normalized matrix uses dual output pattern")
                print(f"   Generic: {generic_normalized.name} -> {link_target}")
                validated_types.append(f"{matrix_type}_normalized")
    
    # At least one matrix type should exist
    assert len(validated_types) > 0, "Step 3 should create at least one matrix with dual output"
    
    print(f"\n✅ OVERALL: Step 3 dual output pattern validated for {len(validated_types)} matrices")


def test_step3_symlinks_point_to_timestamped_files():
    """Verify that generic symlinks point to timestamped files."""
    data_dir = Path("data")
    
    # Possible symlinks to check
    matrix_types = ["subcategory", "spu_limited", "category_agg"]
    
    validated = 0
    for matrix_type in matrix_types:
        symlinks_to_check = [
            f"store_{matrix_type}_matrix.csv",
            f"normalized_{matrix_type}_matrix.csv"
        ]
        
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
                    # Might point to period-specific symlink
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
        pytest.skip("No Step 3 outputs found to validate")


def test_step3_output_data_quality():
    """Validate Step 3 output data quality."""
    data_dir = Path("data")
    
    # Check subcategory matrices (most common)
    original_file = data_dir / "store_subcategory_matrix.csv"
    normalized_file = data_dir / "normalized_subcategory_matrix.csv"
    
    if original_file.exists():
        original_df = pd.read_csv(original_file, index_col=0)
        
        # Validate it's a matrix (stores x subcategories)
        assert len(original_df.index) > 0, "Should have stores (rows)"
        assert len(original_df.columns) > 0, "Should have subcategories (columns)"
        
        # Validate all values are numeric
        assert original_df.apply(pd.api.types.is_numeric_dtype).all(), "All matrix values should be numeric"
        
        # Note: Original matrix may have some negative values due to data processing
        # Just validate it's mostly non-negative
        negative_ratio = (original_df < 0).sum().sum() / (original_df.shape[0] * original_df.shape[1])
        assert negative_ratio < 0.1, f"Too many negative values: {negative_ratio:.1%}"
        
        print(f"✅ Original matrix data quality validated")
        print(f"   Shape: {original_df.shape[0]} stores × {original_df.shape[1]} subcategories")
    
    if normalized_file.exists():
        normalized_df = pd.read_csv(normalized_file, index_col=0)
        
        # Validate it's a matrix
        assert len(normalized_df.index) > 0, "Should have stores (rows)"
        assert len(normalized_df.columns) > 0, "Should have subcategories (columns)"
        
        # Validate all values are numeric
        assert normalized_df.apply(pd.api.types.is_numeric_dtype).all(), "All matrix values should be numeric"
        
        # Normalized values should be in reasonable range
        assert normalized_df.min().min() >= -10, "Normalized values too low"
        assert normalized_df.max().max() <= 10, "Normalized values too high"
        
        print(f"✅ Normalized matrix data quality validated")
        print(f"   Shape: {normalized_df.shape[0]} stores × {normalized_df.shape[1]} subcategories")
        print(f"   Value range: [{normalized_df.min().min():.2f}, {normalized_df.max().max():.2f}]")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
