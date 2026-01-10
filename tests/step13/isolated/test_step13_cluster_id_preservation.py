"""
Step 13 Cluster ID Preservation Test (Isolated Synthetic)
==========================================================

Tests that Step 13 preserves cluster_id from rule files instead of losing it.

Root Cause:
-----------
Step 13 was creating a new 'cluster' column by mapping str_code, which caused
the original cluster_id from rule files to be lost during consolidation.

Expected Behavior:
------------------
- Rule files from Steps 7-12 have cluster_id column with values
- Step 13 should preserve these cluster_id values
- Consolidated output should have cluster_id for ALL recommendations
- No cluster_id should be NaN unless it was NaN in the original rule file

Test Strategy:
--------------
1. Create synthetic rule files with cluster_id
2. Run Step 13 consolidation
3. Verify cluster_id is preserved in output
4. Verify no cluster_id values are lost
"""

import os
import shutil
from pathlib import Path
import pandas as pd
import pytest
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _create_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox with Step 13 code."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)
    
    # Copy src directory
    src_target = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_target)
    
    return sandbox


def _create_synthetic_rule_files(sandbox: Path, period_label: str = "202510A"):
    """Create synthetic rule files with cluster_id."""
    output_dir = sandbox / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data_dir = sandbox / "data" / "api_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create clustering file
    clustering = pd.DataFrame({
        'str_code': ['1001', '1002', '1003', '1004', '1005'],
        'Cluster': [0, 0, 1, 1, 2]
    })
    clustering.to_csv(output_dir / f"clustering_results_spu_{period_label}.csv", index=False)
    
    # Create SPU sales file - ensure ALL subcategories have sales in ALL clusters
    # This prevents no-sales guard from filtering out recommendations
    spu_sales_data = []
    for store, cluster in [('1001', 0), ('1002', 0), ('1003', 1), ('1004', 1), ('1005', 2)]:
        for subcat in ['T恤', '裤子', '鞋']:
            spu_sales_data.append({
                'str_code': store,
                'spu_code': f'SPU_{subcat}',
                'sub_cate_name': subcat,
                'spu_sales_amt': 100.0
            })
    
    spu_sales = pd.DataFrame(spu_sales_data)
    spu_sales.to_csv(data_dir / f"complete_spu_sales_{period_label}.csv", index=False)
    
    # Create rule files with cluster_id
    # Rule 7: All stores, all have cluster_id
    rule7 = pd.DataFrame({
        'str_code': ['1001', '1002', '1003', '1004', '1005'],
        'spu_code': ['SPU001', 'SPU002', 'SPU003', 'SPU001', 'SPU002'],
        'sub_cate_name': ['T恤', '裤子', '鞋', 'T恤', '裤子'],
        'recommended_quantity_change': [5.0, 10.0, 3.0, 7.0, 12.0],
        'investment_required': [50.0, 100.0, 30.0, 70.0, 120.0],
        'unit_price': [10.0, 10.0, 10.0, 10.0, 10.0],
        'cluster_id': [0, 0, 1, 1, 2],  # ← This should be preserved!
        'rule7_flag': [True, True, True, True, True]
    })
    rule7.to_csv(output_dir / f"rule7_missing_spu_sellthrough_results_{period_label}.csv", index=False)
    
    # Rule 8: Subset of stores, all have cluster_id
    rule8 = pd.DataFrame({
        'str_code': ['1001', '1003'],
        'spu_code': ['SPU001', 'SPU003'],
        'sub_cate_name': ['T恤', '鞋'],
        'recommended_quantity_change': [2.0, 4.0],
        'investment_required': [20.0, 40.0],
        'unit_price': [10.0, 10.0],
        'cluster_id': [0, 1],  # ← This should be preserved!
        'rule8_flag': [True, True]
    })
    rule8.to_csv(output_dir / f"rule8_imbalanced_spu_results_{period_label}.csv", index=False)
    
    # Rule 9: Different stores, all have cluster_id
    rule9 = pd.DataFrame({
        'str_code': ['1002', '1004', '1005'],
        'spu_code': ['SPU002', 'SPU001', 'SPU002'],
        'sub_cate_name': ['裤子', 'T恤', '裤子'],
        'recommended_quantity_change': [1.0, 3.0, 2.0],
        'investment_required': [10.0, 30.0, 20.0],
        'unit_price': [10.0, 10.0, 10.0],
        'cluster_id': [0, 1, 2],  # ← This should be preserved!
        'rule9_flag': [True, True, True]
    })
    rule9.to_csv(output_dir / f"rule9_below_minimum_spu_sellthrough_results_{period_label}.csv", index=False)
    
    # Create minimal rule files for 10, 11, 12 (to avoid errors)
    for rule_num in [10, 11, 12]:
        rule_df = pd.DataFrame({
            'str_code': ['1001'],
            'spu_code': ['SPU001'],
            'sub_cate_name': ['T恤'],
            'recommended_quantity_change': [1.0],
            'investment_required': [10.0],
            'unit_price': [10.0],
            'cluster_id': [0],
            f'rule{rule_num}_flag': [True]
        })
        rule_df.to_csv(output_dir / f"rule{rule_num}_test_results_{period_label}.csv", index=False)


def _run_step13(sandbox: Path, period_label: str = "202510A"):
    """Run Step 13 in the sandbox."""
    env = os.environ.copy()
    env['PYTHONPATH'] = str(sandbox)
    env['PIPELINE_TARGET_YYYYMM'] = period_label[:6]
    env['PIPELINE_TARGET_PERIOD'] = period_label[6:]
    # Disable volume floor to prevent filtering out test data
    env['STEP13_MIN_STORE_VOLUME_FLOOR'] = '0'
    env['STEP13_MIN_STORE_NET_VOLUME_FLOOR'] = '0'
    
    result = subprocess.run(
        ['python3', str(sandbox / 'src' / 'step13_consolidate_spu_rules.py'),
         '--target-yyyymm', period_label[:6],
         '--target-period', period_label[6:]],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        raise RuntimeError(f"Step 13 failed with exit code {result.returncode}")
    
    return result


def test_cluster_id_preserved_from_rule_files(tmp_path):
    """Test that cluster_id from rule files is preserved in consolidated output."""
    
    # Setup
    sandbox = _create_sandbox(tmp_path)
    period_label = "202510A"
    _create_synthetic_rule_files(sandbox, period_label)
    
    # Run Step 13
    _run_step13(sandbox, period_label)
    
    # Load consolidated output
    output_file = sandbox / "output" / f"consolidated_spu_rule_results_detailed_{period_label}.csv"
    assert output_file.exists(), f"Consolidated output not found: {output_file}"
    
    consolidated = pd.read_csv(output_file)
    
    # Verify cluster_id column exists
    assert 'cluster_id' in consolidated.columns, "cluster_id column missing from consolidated output"
    
    # Verify NO cluster_id values are NaN
    missing_cluster_id = consolidated['cluster_id'].isna().sum()
    total_recs = len(consolidated)
    
    assert missing_cluster_id == 0, (
        f"cluster_id preservation FAILED: {missing_cluster_id}/{total_recs} recommendations have NaN cluster_id. "
        f"Rule breakdown:\n{consolidated.groupby('rule_source')['cluster_id'].apply(lambda x: x.isna().sum())}"
    )
    
    # Verify cluster_id values match expected clusters
    # Check that we have recommendations from at least one rule
    assert total_recs > 0, "No recommendations in consolidated output"
    
    # Verify cluster_id values are in expected range (0-2 for our test data)
    cluster_values = consolidated['cluster_id'].unique()
    assert all(c in [0, 1, 2] for c in cluster_values), (
        f"Unexpected cluster_id values: {cluster_values}"
    )
    
    # Verify each store has the correct cluster_id
    store_clusters = consolidated.groupby('str_code')['cluster_id'].first()
    expected_store_clusters = {'1001': 0, '1002': 0, '1003': 1, '1004': 1, '1005': 2}
    
    for store, expected_cluster in expected_store_clusters.items():
        if store in store_clusters.index:
            actual_cluster = store_clusters[store]
            assert actual_cluster == expected_cluster, (
                f"Store {store}: expected cluster {expected_cluster}, got {actual_cluster}"
            )
    
    print(f"✅ PASS: All {total_recs} recommendations have cluster_id preserved")
    print(f"   Unique clusters: {sorted(cluster_values)}")
    print(f"   Stores with recommendations: {len(store_clusters)}")
    print(f"   Rules present: {consolidated['rule_source'].unique().tolist()}")


def test_cluster_column_matches_cluster_id(tmp_path):
    """Test that 'cluster' column matches 'cluster_id' column."""
    
    # Setup
    sandbox = _create_sandbox(tmp_path)
    period_label = "202510A"
    _create_synthetic_rule_files(sandbox, period_label)
    
    # Run Step 13
    _run_step13(sandbox, period_label)
    
    # Load consolidated output
    output_file = sandbox / "output" / f"consolidated_spu_rule_results_detailed_{period_label}.csv"
    consolidated = pd.read_csv(output_file)
    
    # Verify both columns exist
    assert 'cluster' in consolidated.columns, "cluster column missing"
    assert 'cluster_id' in consolidated.columns, "cluster_id column missing"
    
    # Verify they match
    mismatches = (consolidated['cluster'] != consolidated['cluster_id']).sum()
    
    assert mismatches == 0, (
        f"cluster and cluster_id mismatch in {mismatches}/{len(consolidated)} records"
    )
    
    print(f"✅ PASS: cluster and cluster_id columns match for all {len(consolidated)} recommendations")


def test_no_cluster_id_loss_in_preserved_recommendations(tmp_path):
    """Test that recommendations that survive filtering still have cluster_id."""
    
    # Setup
    sandbox = _create_sandbox(tmp_path)
    period_label = "202510A"
    _create_synthetic_rule_files(sandbox, period_label)
    
    # Run Step 13
    _run_step13(sandbox, period_label)
    
    # Load consolidated output
    output_file = sandbox / "output" / f"consolidated_spu_rule_results_detailed_{period_label}.csv"
    consolidated = pd.read_csv(output_file)
    
    # For ALL recommendations that made it through, verify they have cluster_id
    total_recs = len(consolidated)
    assert total_recs > 0, "No recommendations in consolidated output"
    
    missing_cluster_id = consolidated['cluster_id'].isna().sum()
    
    assert missing_cluster_id == 0, (
        f"cluster_id loss detected in {missing_cluster_id}/{total_recs} recommendations that survived filtering. "
        f"Rule breakdown:\n{consolidated.groupby('rule_source')['cluster_id'].apply(lambda x: x.isna().sum())}"
    )
    
    print(f"✅ PASS: All {total_recs} recommendations that survived filtering have cluster_id")
    print(f"   Rules present: {consolidated['rule_source'].value_counts().to_dict()}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
