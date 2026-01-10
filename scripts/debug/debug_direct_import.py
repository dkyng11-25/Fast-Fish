#!/usr/bin/env python3

import os
import sys

print("Starting direct import test...")
print(f"Current working directory: {os.getcwd()}")

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, "src"))

print(f"Parent directory: {parent_dir}")
print(f"Python path: {sys.path}")

try:
    print("Attempting to import step35 module...")
    import src.step35_merchandising_strategy_deployment as step35
    print("✓ Step 35 module imported successfully")
    
    print("Attempting to call main function...")
    step35.main(["--target-yyyymm", "202509", "--target-period", "A"])
    print("✓ Main function executed successfully")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
