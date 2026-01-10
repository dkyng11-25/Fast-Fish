#!/usr/bin/env python3

import sys
import os
import pandas as pd

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config import initialize_pipeline_config, get_api_data_files, load_margin_rates
    from src.step10_spu_assortment_optimization import fast_expand_spu_data
    
    print("Testing Step 10 margin rate integration...")
    
    # Initialize pipeline config
    initialize_pipeline_config()
    
    # Load a small sample of data to test with
    api_files = get_api_data_files()
    print(f"API files: {api_files}")
    
    # Try to load a small sample of SPU sales data
    spu_file = api_files.get('spu_sales')
    if spu_file and os.path.exists(spu_file):
        print(f"\nLoading SPU data from {spu_file}...")
        # Load a small sample
        spu_df = pd.read_csv(spu_file, nrows=100)
        print(f"Loaded {len(spu_df)} sample records")
        print(f"Columns: {list(spu_df.columns)}")
        
        # Test load_margin_rates function
        print("\nTesting load_margin_rates function...")
        margin_rates = load_margin_rates(margin_type='spu')
        print(f"Loaded {len(margin_rates)} margin rate records")
        print(f"Columns: {list(margin_rates.columns)}")
        if len(margin_rates) > 0:
            print(f"Sample margin rates:\n{margin_rates.head()}")
        
        print("\n✅ Test completed successfully!")
    else:
        print(f"SPU file not found: {spu_file}")
        
        # Test margin rates independently
        print("\nTesting load_margin_rates function independently...")
        margin_rates = load_margin_rates(margin_type='spu')
        print(f"Loaded {len(margin_rates)} margin rate records")
        print(f"Columns: {list(margin_rates.columns)}")
        if len(margin_rates) > 0:
            print(f"Sample margin rates:\n{margin_rates.head()}")
        
        print("\n✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
