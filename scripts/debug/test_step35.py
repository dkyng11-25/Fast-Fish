#!/usr/bin/env python3

import sys
import os

# Add the project root to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, "src"))

print(f"Parent directory: {parent_dir}")
print(f"Python path: {sys.path}")

try:
    # Try importing Step 35
    import src.step35_merchandising_strategy_deployment as step35
    print("✓ Step 35 import successful")
    
    # Mock command line arguments for Step 35
    import argparse
    original_argv = sys.argv
    sys.argv = [
        'step35_merchandising_strategy_deployment.py',
        '--target-yyyymm', '202509',
        '--target-period', 'A'
    ]
    
    # Run Step 35
    step35.main()
    print("✓ Step 35 completed successfully.")
    
    # Restore original argv
    sys.argv = original_argv
    
except Exception as e:
    print(f"✗ Step 35 failed: {e}")
    import traceback
    traceback.print_exc()
