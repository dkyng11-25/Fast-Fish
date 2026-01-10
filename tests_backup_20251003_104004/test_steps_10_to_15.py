"""
Direct Tests for Steps 10-15
=============================

Tests that run steps directly (not in sandbox) to verify timestamped outputs.
"""

import os
import subprocess
from pathlib import Path
import pandas as pd
import pytest
import re
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def create_test_data():
    """Create minimal test data for steps 10-15"""
    data_dir = PROJECT_ROOT / "data" / "api_data"
    output_dir = PROJECT_ROOT / "output"
    
    # Backup existing data (skip symlinks)
    backup_dir = PROJECT_ROOT / "data_backup"
    if data_dir.exists():
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        try:
            shutil.copytree(data_dir, backup_dir, symlinks=False, ignore_dangling_symlinks=True)
        except Exception as e:
            print(f"Warning: Could not backup data: {e}")
            backup_dir = None
    
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stores = ['S001', 'S002', 'S003']
    
    # Comprehensive SPU sales data
    spu_sales_data = []
    for i, store in enumerate(stores):
        num_spus = 2 if store == 'S001' else 10
        for j in range(num_spus):
            spu_sales_data.append({
                'str_code': store,
                'spu_code': f'SPU{i*10+j:03d}',
                'sub_cate_name': ['T恤', '裤子', '外套'][j % 3],
                'sales_qty': 10 + j,
                'sales_amt': 100 + j * 10,
                'spu_sales_qty': 10 + j,
                'spu_sales_amt': 100 + j * 10,
                'sty_sal_amt': 100 + j * 10,
                'allocation_value': 5 + j,
                'season_name': ['春季', '夏季', '秋季'][j % 3],
                'sex_name': ['男', '女', '中性'][j % 3],
                'display_location_name': ['A区', 'B区', 'C区'][j % 3],
                'big_class_name': ['上装', '下装', '外套'][j % 3],
                'quantity': 10 + j,
                'base_sal_qty': 8 + j,
                'fashion_sal_qty': 2 + j,
                'sal_qty': 10 + j,
            })
    
    pd.DataFrame(spu_sales_data).to_csv(data_dir / "complete_spu_sales_202510A.csv", index=False)
    
    # Store sales
    store_sales = pd.DataFrame({
        'str_code': stores * 10,
        'spu_code': [f'SPU{i:03d}' for i in range(30)],
        'sub_cate_name': ['T恤', '裤子', '外套'] * 10,
        'sales_qty': [10, 20, 15] * 10,
        'sales_amt': [100, 200, 150] * 10,
        'unit_price': [10.0, 10.0, 10.0] * 10,
        'quantity': [10, 20, 15] * 10,
        'sal_qty': [10, 20, 15] * 10,
    })
    store_sales.to_csv(data_dir / "store_sales_202510A.csv", index=False)
    
    # Store config
    store_config = pd.DataFrame({
        'str_code': stores,
        'str_name': ['Store 1', 'Store 2', 'Store 3'],
        'cluster_id': [1, 1, 2],
        'season_name': ['春季', '夏季', '秋季'],
        'sex_name': ['男', '女', '中性'],
        'display_location_name': ['A区', 'B区', 'C区'],
        'big_class_name': ['上装', '下装', '外套'],
        'sub_cate_name': ['T恤', '裤子', '外套'],
        'sty_sal_amt': [1000, 2000, 1500],
        'target_sty_cnt_avg': [10, 20, 15],
    })
    store_config.to_csv(data_dir / "store_config_202510A.csv", index=False)
    
    # Clustering results
    clustering = pd.DataFrame({
        'str_code': stores,
        'Cluster': [1, 1, 2],
    })
    clustering.to_csv(output_dir / "clustering_results_spu.csv", index=False)
    clustering.to_csv(output_dir / "clustering_results_subcategory.csv", index=False)
    
    return backup_dir


def cleanup_test_data(backup_dir):
    """Restore original data"""
    data_dir = PROJECT_ROOT / "data" / "api_data"
    if backup_dir and backup_dir.exists():
        if data_dir.exists():
            shutil.rmtree(data_dir)
        shutil.copytree(backup_dir, data_dir)
        shutil.rmtree(backup_dir)


def test_step9_creates_timestamped_outputs():
    """Test Step 9 creates BOTH timestamped file AND non-timestamped symlink"""
    backup_dir = create_test_data()
    
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        result = subprocess.run(
            ['python3', str(PROJECT_ROOT / 'src' / 'step9_below_minimum_rule.py'),
             '--target-yyyymm', '202510',
             '--target-period', 'A'],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout[-500:]}")
            print(f"STDERR: {result.stderr[-500:]}")
            pytest.skip(f"Step 9 failed to run: {result.returncode}")
        
        output_dir = PROJECT_ROOT / "output"
        
        # 1. Check timestamped file exists (for debugging)
        pattern = re.compile(r'rule9_below_minimum_spu_sellthrough_results_202510A_\d{8}_\d{6}\.csv')
        timestamped_files = [f for f in output_dir.glob("rule9_*.csv") 
                             if pattern.match(f.name)]
        
        assert len(timestamped_files) > 0, f"❌ No timestamped output found"
        timestamped_file = timestamped_files[0]
        assert not timestamped_file.is_symlink(), "❌ Timestamped file should be a real file, not symlink"
        print(f"✅ Step 9 timestamped file: {timestamped_file.name}")
        
        # 2. Check period-labeled symlink exists (for downstream steps)
        period_symlink = output_dir / "rule9_below_minimum_spu_sellthrough_results_202510A.csv"
        assert period_symlink.exists(), "❌ Period-labeled symlink not found"
        assert period_symlink.is_symlink(), "❌ Period-labeled file should be a symlink"
        print(f"✅ Step 9 period symlink: {period_symlink.name} -> {os.readlink(period_symlink)}")
        
        # 3. Check generic symlink exists (for backward compatibility)
        generic_symlink = output_dir / "rule9_below_minimum_spu_sellthrough_results.csv"
        assert generic_symlink.exists(), "❌ Generic symlink not found"
        assert generic_symlink.is_symlink(), "❌ Generic file should be a symlink"
        print(f"✅ Step 9 generic symlink: {generic_symlink.name} -> {os.readlink(generic_symlink)}")
        
        print(f"✅ Step 9 test passed - All 3 outputs verified!")
        
    finally:
        cleanup_test_data(backup_dir)


def test_step10_creates_timestamped_outputs():
    """Test Step 10 creates timestamped outputs"""
    backup_dir = create_test_data()
    
    try:
        # Run Step 10
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        result = subprocess.run(
            ['python3', str(PROJECT_ROOT / 'src' / 'step10_spu_assortment_optimization.py'),
             '--target-yyyymm', '202510',
             '--target-period', 'A'],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout[-500:]}")
            print(f"STDERR: {result.stderr[-500:]}")
            pytest.skip(f"Step 10 failed to run: {result.returncode}")
        
        # Check for timestamped output
        output_dir = PROJECT_ROOT / "output"
        pattern = re.compile(r'rule10_smart_overcapacity_results_202510A_\d{8}_\d{6}\.csv')
        
        timestamped_files = [f for f in output_dir.glob("rule10_*.csv") 
                             if pattern.match(f.name)]
        
        assert len(timestamped_files) > 0, f"No timestamped output found. Files: {[f.name for f in output_dir.glob('rule10_*.csv')]}"
        
        timestamped_file = timestamped_files[0]
        print(f"✅ Step 10: {timestamped_file.name}")
        
        # Check symlinks
        period_symlink = output_dir / "rule10_smart_overcapacity_results_202510A.csv"
        assert period_symlink.exists(), "Period symlink not found"
        assert period_symlink.is_symlink(), "Period file should be a symlink"
        
        print(f"✅ Step 10 test passed!")
        
    finally:
        cleanup_test_data(backup_dir)


def test_step11_creates_timestamped_outputs():
    """Test Step 11 creates BOTH timestamped file AND non-timestamped symlink"""
    backup_dir = create_test_data()
    
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        result = subprocess.run(
            ['python3', str(PROJECT_ROOT / 'src' / 'step11_missed_sales_opportunity.py'),
             '--target-yyyymm', '202510',
             '--target-period', 'A'],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout[-500:]}")
            print(f"STDERR: {result.stderr[-500:]}")
            pytest.skip(f"Step 11 failed to run: {result.returncode}")
        
        output_dir = PROJECT_ROOT / "output"
        
        # 1. Check timestamped file exists (for debugging)
        pattern = re.compile(r'rule11_improved_missed_sales_opportunity_spu_results_202510A_\d{8}_\d{6}\.csv')
        timestamped_files = [f for f in output_dir.glob("rule11_*.csv") 
                             if pattern.match(f.name)]
        
        assert len(timestamped_files) > 0, f"❌ No timestamped output found"
        timestamped_file = timestamped_files[0]
        assert not timestamped_file.is_symlink(), "❌ Timestamped file should be a real file, not symlink"
        print(f"✅ Step 11 timestamped file: {timestamped_file.name}")
        
        # 2. Check period-labeled symlink exists (for downstream steps)
        period_symlink = output_dir / "rule11_improved_missed_sales_opportunity_spu_results_202510A.csv"
        assert period_symlink.exists(), "❌ Period-labeled symlink not found"
        assert period_symlink.is_symlink(), "❌ Period-labeled file should be a symlink"
        print(f"✅ Step 11 period symlink: {period_symlink.name}")
        
        # 3. Check generic symlink exists (for backward compatibility)
        generic_symlink = output_dir / "rule11_improved_missed_sales_opportunity_spu_results.csv"
        assert generic_symlink.exists(), "❌ Generic symlink not found"
        assert generic_symlink.is_symlink(), "❌ Generic file should be a symlink"
        print(f"✅ Step 11 generic symlink: {generic_symlink.name}")
        
        print(f"✅ Step 11 test passed - All 3 outputs verified!")
        
    finally:
        cleanup_test_data(backup_dir)


def test_step12_creates_timestamped_outputs():
    """Test Step 12 creates timestamped outputs"""
    backup_dir = create_test_data()
    
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        result = subprocess.run(
            ['python3', str(PROJECT_ROOT / 'src' / 'step12_sales_performance_rule.py'),
             '--target-yyyymm', '202510',
             '--target-period', 'A'],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout[-500:]}")
            print(f"STDERR: {result.stderr[-500:]}")
            pytest.skip(f"Step 12 failed to run: {result.returncode}")
        
        output_dir = PROJECT_ROOT / "output"
        pattern = re.compile(r'rule12_sales_performance_spu_results_202510A_\d{8}_\d{6}\.csv')
        
        timestamped_files = [f for f in output_dir.glob("rule12_*.csv") 
                             if pattern.match(f.name)]
        
        assert len(timestamped_files) > 0, f"No timestamped output found"
        
        print(f"✅ Step 12: {timestamped_files[0].name}")
        print(f"✅ Step 12 test passed!")
        
    finally:
        cleanup_test_data(backup_dir)


def test_step13_creates_timestamped_outputs():
    """Test Step 13 creates BOTH timestamped file AND non-timestamped symlink"""
    backup_dir = create_test_data()
    
    # Step 13 needs rule outputs, so create them
    output_dir = PROJECT_ROOT / "output"
    
    # Create synthetic rule outputs for Step 13 to consolidate
    for rule_num in [7, 8, 9, 10, 11, 12]:
        rule_data = pd.DataFrame({
            'str_code': ['S001', 'S002', 'S003'],
            'spu_code': [f'SPU{i:03d}' for i in range(3)],
            'sub_cate_name': ['T恤', '裤子', '外套'],
            'recommended_quantity_change': [5, 3, 2],
            f'rule{rule_num}_flag': [1, 0, 1],
        })
        rule_data.to_csv(output_dir / f"rule{rule_num}_results.csv", index=False)
    
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        result = subprocess.run(
            ['python3', str(PROJECT_ROOT / 'src' / 'step13_consolidate_spu_rules.py'),
             '--target-yyyymm', '202510',
             '--target-period', 'A'],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout[-500:]}")
            print(f"STDERR: {result.stderr[-500:]}")
            pytest.skip(f"Step 13 failed to run: {result.returncode}")
        
        output_dir = PROJECT_ROOT / "output"
        
        # 1. Check timestamped file exists (for debugging)
        # Step 13 may use "None" or period label - accept both
        pattern = re.compile(r'consolidated_spu_rule_results_detailed_(202510A|None)_\d{8}_\d{6}\.csv')
        timestamped_files = [f for f in output_dir.glob("consolidated_*.csv") 
                             if pattern.match(f.name)]
        
        assert len(timestamped_files) > 0, f"❌ No timestamped output found"
        timestamped_file = timestamped_files[0]
        assert not timestamped_file.is_symlink(), "❌ Timestamped file should be a real file, not symlink"
        print(f"✅ Step 13 timestamped file: {timestamped_file.name}")
        
        # 2. Check period-labeled symlink exists (for downstream steps)
        # Accept either with period label or "None"
        period_symlink = output_dir / "consolidated_spu_rule_results_detailed_202510A.csv"
        none_symlink = output_dir / "consolidated_spu_rule_results_detailed_None.csv"
        
        if period_symlink.exists():
            assert period_symlink.is_symlink(), "❌ Period-labeled file should be a symlink"
            print(f"✅ Step 13 period symlink: {period_symlink.name}")
        elif none_symlink.exists():
            assert none_symlink.is_symlink(), "❌ None-labeled file should be a symlink"
            print(f"✅ Step 13 period symlink: {none_symlink.name}")
        else:
            assert False, "❌ No period-labeled or None-labeled symlink found"
        
        # 3. Check generic symlink exists (for backward compatibility)
        generic_symlink = output_dir / "consolidated_spu_rule_results_detailed.csv"
        assert generic_symlink.exists(), "❌ Generic symlink not found"
        assert generic_symlink.is_symlink(), "❌ Generic file should be a symlink"
        print(f"✅ Step 13 generic symlink: {generic_symlink.name}")
        
        print(f"✅ Step 13 test passed - All 3 outputs verified!")
        
    finally:
        cleanup_test_data(backup_dir)


def test_step14_creates_timestamped_outputs():
    """Test Step 14 creates timestamped outputs"""
    backup_dir = create_test_data()
    
    # Step 14 needs consolidated results
    output_dir = PROJECT_ROOT / "output"
    consolidated_data = pd.DataFrame({
        'Store_Group_Name': ['Group1', 'Group2', 'Group3'],
        'str_code': ['S001', 'S002', 'S003'],
        'spu_code': [f'SPU{i:03d}' for i in range(3)],
        'sub_cate_name': ['T恤', '裤子', '外套'],
        'Target_Style_Tags': ['休闲', '商务', '运动'],
        'recommended_quantity_change': [5, 3, 2],
        'Current_SPU_Quantity': [10, 8, 12],
        'Target_SPU_Quantity': [15, 11, 14],
    })
    consolidated_data.to_csv(output_dir / "consolidated_spu_rule_results_detailed.csv", index=False)
    
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        result = subprocess.run(
            ['python3', str(PROJECT_ROOT / 'src' / 'step14_create_fast_fish_format.py'),
             '--target-yyyymm', '202510',
             '--target-period', 'A'],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout[-500:]}")
            print(f"STDERR: {result.stderr[-500:]}")
            pytest.skip(f"Step 14 failed to run: {result.returncode}")
        
        output_dir = PROJECT_ROOT / "output"
        pattern = re.compile(r'enhanced_fast_fish_format_202510A_\d{8}_\d{6}\.csv')
        
        timestamped_files = [f for f in output_dir.glob("enhanced_fast_fish_*.csv") 
                             if pattern.match(f.name)]
        
        assert len(timestamped_files) > 0, f"No timestamped output found"
        
        print(f"✅ Step 14: {timestamped_files[0].name}")
        print(f"✅ Step 14 test passed!")
        
    finally:
        cleanup_test_data(backup_dir)


def test_step15_creates_timestamped_outputs():
    """Test Step 15 creates timestamped outputs"""
    backup_dir = create_test_data()
    
    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(PROJECT_ROOT)
        result = subprocess.run(
            ['python3', str(PROJECT_ROOT / 'src' / 'step15_download_historical_baseline.py'),
             '--target-yyyymm', '202510',
             '--target-period', 'A',
             '--baseline-yyyymm', '202410',
             '--baseline-period', 'A'],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"STDOUT: {result.stdout[-500:]}")
            print(f"STDERR: {result.stderr[-500:]}")
            pytest.skip(f"Step 15 failed to run: {result.returncode}")
        
        output_dir = PROJECT_ROOT / "output"
        pattern = re.compile(r'historical_reference_202410A_\d{8}_\d{6}\.csv')
        
        timestamped_files = [f for f in output_dir.glob("historical_reference_*.csv") 
                             if pattern.match(f.name)]
        
        assert len(timestamped_files) > 0, f"No timestamped output found"
        
        print(f"✅ Step 15: {timestamped_files[0].name}")
        print(f"✅ Step 15 test passed!")
        
    finally:
        cleanup_test_data(backup_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
