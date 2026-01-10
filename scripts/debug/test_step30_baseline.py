#!/usr/bin/env python3
"""
Simple test script for Step 30 baseline calculation
"""

import sys
import os
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    from src.step30_sellthrough_optimization_engine import calculate_baseline_sellthrough_rates
    print("✓ Successfully imported Step 30 functions")
    
    # Create sample test data
    sales_data = pd.DataFrame({
        'str_code': ['S001', 'S001', 'S002', 'S002'],
        'spu_code': ['P001', 'P002', 'P001', 'P002'],
        'fashion_sal_amt': [100.0, 50.0, 200.0, 75.0],
        'basic_sal_amt': [80.0, 40.0, 160.0, 60.0],
        'fashion_sal_qty': [10.0, 5.0, 20.0, 7.5],
        'basic_sal_qty': [8.0, 4.0, 16.0, 6.0],
        'total_inventory_qty': [50.0, 30.0, 100.0, 40.0]
    })
    
    cluster_data = pd.DataFrame({
        'str_code': ['S001', 'S002'],
        'cluster_id': [1, 1]
    })
    
    roles_data = pd.DataFrame({
        'spu_code': ['P001', 'P002'],
        'product_role': ['CORE', 'FILLER']
    })
    
    print("✓ Created sample test data")
    
    # Test baseline calculation
    result = calculate_baseline_sellthrough_rates(
        sales_data, 
        cluster_data, 
        roles_data,
        period_days=15
    )
    
    print("✓ Baseline sell-through calculation completed")
    print(f"  Result shape: {result.shape}")
    print(f"  Columns: {list(result.columns)}")
    
    # Basic validation
    assert not result.empty, "Result should not be empty"
    assert 'str_code' in result.columns, "Should have str_code column"
    assert 'cluster_id' in result.columns, "Should have cluster_id column"
    assert 'baseline_sellthrough_rate' in result.columns, "Should have baseline_sellthrough_rate column"
    assert 'spu_store_days_inventory' in result.columns, "Should have spu_store_days_inventory column"
    assert 'spu_store_days_sales' in result.columns, "Should have spu_store_days_sales column"
    
    # Check value ranges
    assert (result['baseline_sellthrough_rate'] >= 0.0).all(), "Sell-through rates should be >= 0"
    assert (result['baseline_sellthrough_rate'] <= 1.0).all(), "Sell-through rates should be <= 1"
    assert (result['spu_store_days_inventory'] >= 0).all(), "SPU-store-days inventory should be >= 0"
    assert (result['spu_store_days_sales'] >= 0).all(), "SPU-store-days sales should be >= 0"
    
    print("✓ All validations passed")
    
    # Print sample results
    print("\nSample results:")
    print(result.head())
    
    print("\n🎉 Step 30 baseline calculation test passed!")
    
except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
