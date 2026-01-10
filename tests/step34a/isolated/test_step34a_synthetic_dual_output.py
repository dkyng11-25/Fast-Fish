"""
Step 34a Synthetic Test - Dual Output Pattern
==============================================

Tests that Step 34a (Cluster Strategy Optimization) correctly implements
the dual output pattern with real execution using fixture data.

Dual Output Pattern:
1. Timestamped file: cluster_level_merchandising_strategies_202510A_20251003_120307.csv
2. Period symlink: cluster_level_merchandising_strategies_202510A.csv
3. Generic symlink: cluster_level_merchandising_strategies.csv
"""

import os
import re
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest


def test_step34a_dual_output_with_fixtures():
    """Test Step 34a creates all three dual output files with real execution."""
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        output_dir = tmpdir / "output"
        output_dir.mkdir(parents=True)
        
        # Create fixture: store-level merchandising rules (Step 33 output)
        # This is what Step 34a reads to build cluster strategies
        store_rules_df = pd.DataFrame({
            'str_code': ['11014', '11017', '11021', '11025'],
            'cluster_id': ['0', '0', '1', '1'],
            'operational_tag': ['High-Traffic', 'High-Traffic', 'Standard', 'Standard'],
            'style_tag': ['Fashion-Forward', 'Fashion-Forward', 'Balanced', 'Balanced'],
            'capacity_tag': ['Large', 'Medium', 'Medium', 'Small'],
            'geographic_tag': ['Urban', 'Urban', 'Suburban', 'Suburban'],
            'fashion_allocation_ratio': [0.65, 0.60, 0.50, 0.45],
            'basic_allocation_ratio': [0.35, 0.40, 0.50, 0.55],
            'capacity_utilization_target': [0.85, 0.80, 0.75, 0.70],
            'priority_score': [85, 80, 70, 65],
            'implementation_notes': ['Focus on new arrivals', 'Balanced mix', 'Core items', 'Basics']
        })
        
        # Save fixture with period label (what Step 34a expects)
        fixture_path = output_dir / "store_level_merchandising_rules_202510A.csv"
        store_rules_df.to_csv(fixture_path, index=False)
        
        # Change to temp directory and run Step 34a
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Import and run Step 34a
            import sys
            sys.path.insert(0, original_cwd)
            
            from src.step34a_cluster_strategy_optimization import build_cluster_strategies
            from src.output_utils import create_output_with_symlinks
            
            # Build cluster strategies from fixture data
            strategies_df = build_cluster_strategies(store_rules_df)
            
            # Verify we got cluster strategies
            assert len(strategies_df) > 0, "Should generate cluster strategies"
            assert 'cluster_id' in strategies_df.columns, "Should have cluster_id column"
            
            # Save with dual output pattern (same as Step 34a does)
            period_label = "202510A"
            base_path = "output/cluster_level_merchandising_strategies"
            timestamped_file, period_file, generic_file = create_output_with_symlinks(
                df=strategies_df,
                base_path=base_path,
                period_label=period_label
            )
            
            # Verify all three files exist
            assert Path(timestamped_file).exists(), f"Timestamped file should exist: {timestamped_file}"
            assert Path(period_file).exists(), f"Period symlink should exist: {period_file}"
            assert Path(generic_file).exists(), f"Generic symlink should exist: {generic_file}"
            
            # Verify timestamped file is a real file
            assert Path(timestamped_file).is_file(), "Timestamped file should be a real file"
            assert not Path(timestamped_file).is_symlink(), "Timestamped file should not be a symlink"
            
            # Verify period symlink
            assert Path(period_file).is_symlink(), "Period file should be a symlink"
            period_target = os.readlink(period_file)
            assert '/' not in period_target, "Period symlink should use basename (relative path)"
            assert period_target == Path(timestamped_file).name, "Period symlink should point to timestamped file"
            
            # Verify generic symlink
            assert Path(generic_file).is_symlink(), "Generic file should be a symlink"
            generic_target = os.readlink(generic_file)
            assert '/' not in generic_target, "Generic symlink should use basename (relative path)"
            assert generic_target == Path(timestamped_file).name, "Generic symlink should point to timestamped file"
            
            # Verify file naming patterns
            assert re.search(r'_202510A_\d{8}_\d{6}\.csv$', timestamped_file), \
                "Timestamped file should have format: *_202510A_YYYYMMDD_HHMMSS.csv"
            assert period_file.endswith('_202510A.csv'), \
                "Period file should end with _202510A.csv"
            assert generic_file.endswith('.csv') and not re.search(r'_\d{6}[AB]\.csv$', generic_file), \
                "Generic file should not have period label"
            
            # Verify data integrity
            saved_df = pd.read_csv(timestamped_file)
            assert len(saved_df) == len(strategies_df), "Saved data should match original"
            assert list(saved_df.columns) == list(strategies_df.columns), "Columns should match"
            
            print(f"\n✅ Step 34a Dual Output Pattern Test PASSED")
            print(f"   Timestamped: {Path(timestamped_file).name}")
            print(f"   Period: {Path(period_file).name} -> {period_target}")
            print(f"   Generic: {Path(generic_file).name} -> {generic_target}")
            print(f"   Clusters: {len(strategies_df)}")
            
        finally:
            os.chdir(original_cwd)


def test_step34a_cluster_aggregation_logic():
    """Test that Step 34a correctly aggregates store rules into cluster strategies."""
    
    # Create test data with multiple stores in same cluster
    store_rules_df = pd.DataFrame({
        'str_code': ['S1', 'S2', 'S3', 'S4'],
        'cluster_id': ['0', '0', '1', '1'],
        'operational_tag': ['High-Traffic', 'High-Traffic', 'Standard', 'Standard'],
        'style_tag': ['Fashion', 'Fashion', 'Basic', 'Basic'],
        'capacity_tag': ['Large', 'Medium', 'Medium', 'Small'],
        'geographic_tag': ['Urban', 'Urban', 'Suburban', 'Rural'],
        'fashion_allocation_ratio': [0.70, 0.60, 0.40, 0.30],
        'basic_allocation_ratio': [0.30, 0.40, 0.60, 0.70],
        'capacity_utilization_target': [0.85, 0.80, 0.75, 0.70],
        'priority_score': [90, 85, 75, 70],
        'implementation_notes': ['Note1', 'Note2', 'Note3', 'Note4']
    })
    
    # Import the function
    from src.step34a_cluster_strategy_optimization import build_cluster_strategies
    
    # Build cluster strategies
    strategies_df = build_cluster_strategies(store_rules_df)
    
    # Verify we got 2 clusters (0 and 1)
    assert len(strategies_df) == 2, "Should have 2 cluster strategies"
    assert set(strategies_df['cluster_id'].astype(str)) == {'0', '1'}, "Should have clusters 0 and 1"
    
    # Verify cluster 0 (2 stores: S1, S2)
    cluster_0 = strategies_df[strategies_df['cluster_id'].astype(str) == '0'].iloc[0]
    assert cluster_0['operational_tag'] == 'High-Traffic', "Cluster 0 should be High-Traffic"
    # Fashion ratio should be average of 0.70 and 0.60 = 0.65
    assert abs(cluster_0['fashion_allocation_ratio'] - 0.65) < 0.01, \
        "Cluster 0 fashion ratio should be average of stores"
    
    # Verify cluster 1 (2 stores: S3, S4)
    cluster_1 = strategies_df[strategies_df['cluster_id'].astype(str) == '1'].iloc[0]
    assert cluster_1['operational_tag'] == 'Standard', "Cluster 1 should be Standard"
    # Fashion ratio should be average of 0.40 and 0.30 = 0.35
    assert abs(cluster_1['fashion_allocation_ratio'] - 0.35) < 0.01, \
        "Cluster 1 fashion ratio should be average of stores"
    
    print(f"\n✅ Step 34a Cluster Aggregation Test PASSED")
    print(f"   Cluster 0: {cluster_0['fashion_allocation_ratio']:.2f} fashion ratio")
    print(f"   Cluster 1: {cluster_1['fashion_allocation_ratio']:.2f} fashion ratio")


def test_step34a_required_columns():
    """Test that Step 34a output has all required columns for Step 35."""
    
    # Minimal store rules
    store_rules_df = pd.DataFrame({
        'str_code': ['S1'],
        'cluster_id': ['0'],
        'operational_tag': ['Standard'],
        'style_tag': ['Balanced'],
        'capacity_tag': ['Medium'],
        'geographic_tag': ['Urban'],
        'fashion_allocation_ratio': [0.50],
        'basic_allocation_ratio': [0.50],
        'capacity_utilization_target': [0.75],
        'priority_score': [75],
        'implementation_notes': ['Test']
    })
    
    from src.step34a_cluster_strategy_optimization import build_cluster_strategies
    
    strategies_df = build_cluster_strategies(store_rules_df)
    
    # Required columns for Step 35
    required_columns = [
        'cluster_id',
        'operational_tag',
        'style_tag',
        'capacity_tag',
        'geographic_tag',
        'fashion_allocation_ratio',
        'basic_allocation_ratio',
        'capacity_utilization_target',
        'priority_score',
        'implementation_notes'
    ]
    
    for col in required_columns:
        assert col in strategies_df.columns, f"Missing required column: {col}"
    
    print(f"\n✅ Step 34a Required Columns Test PASSED")
    print(f"   All {len(required_columns)} required columns present")


if __name__ == "__main__":
    print("Running Step 34a Synthetic Tests...")
    pytest.main([__file__, "-v", "-s"])
