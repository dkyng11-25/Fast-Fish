#!/usr/bin/env python3

import os
import sys

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, "src"))

print(f"Parent directory: {parent_dir}")
print(f"Python path: {sys.path}")

try:
    # Try importing Step 18 with the fixed imports
    import src.step18_validate_results as step18
    print("✓ Step 18 import successful")
    
    # Mock command line arguments for Step 18 with input file and baseline period (Period A)
    import argparse
    original_argv = sys.argv
    sys.argv = [
        'step18_validate_results.py',
        '--target-yyyymm', '202509',
        '--target-period', 'A',
        '--input-file', 'output/enhanced_fast_fish_format_202509A_for_step17.csv',
        '--baseline-period', '202409A',
        '--show-progress'
    ]
    
    # Run Step 18
    output_file = step18.main()
    print(f"✓ Step 18 completed successfully. Output file: {output_file}")
    
    # Restore original argv
    sys.argv = original_argv
    
except Exception as e:
    print(f"✗ Step 18 failed: {e}")
    import traceback
    traceback.print_exc()
