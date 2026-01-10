#!/usr/bin/env python3

import sys
import os

# Add src to path so we can import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config import load_margin_rates
    
    print("Testing load_margin_rates function...")
    
    # Test loading category-level margin rates
    print("\n1. Testing category-level margin rates:")
    category_margins = load_margin_rates(margin_type='category')
    print(f"   Loaded {len(category_margins)} category margin records")
    print(f"   Columns: {list(category_margins.columns)}")
    if len(category_margins) > 0:
        print(f"   Sample data:\n{category_margins.head()}")
    
    # Test loading SPU-level margin rates
    print("\n2. Testing SPU-level margin rates:")
    spu_margins = load_margin_rates(margin_type='spu')
    print(f"   Loaded {len(spu_margins)} SPU margin records")
    print(f"   Columns: {list(spu_margins.columns)}")
    if len(spu_margins) > 0:
        print(f"   Sample data:\n{spu_margins.head()}")
        
    print("\n✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
