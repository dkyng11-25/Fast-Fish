#!/usr/bin/env python3
"""
Simple test script for sell-through utilities
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

try:
    from src.sell_through_utils import (
        clip_to_unit_interval,
        fraction_to_percentage,
        percentage_to_fraction,
        calculate_spu_store_day_counts,
        calculate_sell_through_rate
    )
    import numpy as np
    print("✓ Successfully imported sell_through_utils")
    
    # Test clip_to_unit_interval
    assert clip_to_unit_interval(0.5) == 0.5
    assert clip_to_unit_interval(-0.5) == 0.0
    assert clip_to_unit_interval(1.5) == 1.0
    assert np.isnan(clip_to_unit_interval(np.nan))
    print("✓ clip_to_unit_interval tests passed")
    
    # Test fraction_to_percentage
    assert fraction_to_percentage(0.5) == 50.0
    assert fraction_to_percentage(-0.5) == 0.0
    assert fraction_to_percentage(1.5) == 100.0
    assert np.isnan(fraction_to_percentage(np.nan))
    print("✓ fraction_to_percentage tests passed")
    
    # Test percentage_to_fraction
    assert percentage_to_fraction(50.0) == 0.5
    assert percentage_to_fraction(-50.0) == 0.0
    assert percentage_to_fraction(150.0) == 1.0
    assert np.isnan(percentage_to_fraction(np.nan))
    print("✓ percentage_to_fraction tests passed")
    
    # Test calculate_spu_store_day_counts
    inventory, sales = calculate_spu_store_day_counts(
        target_spu_quantity=10.0,
        stores_in_group=5.0,
        historical_avg_daily_sales_per_store=2.0,
        period_days=15
    )
    assert inventory == 750.0  # 10 * 5 * 15
    assert sales == 150.0      # 2 * 5 * 15
    print("✓ calculate_spu_store_day_counts tests passed")
    
    # Test calculate_sell_through_rate
    frac, pct = calculate_sell_through_rate(150.0, 750.0)
    assert frac == 0.2
    assert pct == 20.0
    
    frac, pct = calculate_sell_through_rate(0.0, 750.0)
    assert frac == 0.0
    assert pct == 0.0
    
    frac, pct = calculate_sell_through_rate(750.0, 750.0)
    assert frac == 1.0
    assert pct == 100.0
    
    frac, pct = calculate_sell_through_rate(np.nan, 750.0)
    assert np.isnan(frac)
    assert np.isnan(pct)
    
    frac, pct = calculate_sell_through_rate(150.0, 0.0)
    assert np.isnan(frac)
    assert np.isnan(pct)
    print("✓ calculate_sell_through_rate tests passed")
    
    print("\n🎉 All sell-through utility tests passed!")
    
except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
