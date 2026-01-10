#!/usr/bin/env python3

import os
import sys
import traceback

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, "src"))

print("Starting Step 35 test...")
print(f"Working directory: {os.getcwd()}")
print(f"Parent directory: {parent_dir}")

try:
    print("Importing config...")
    from src.config import get_period_label, OUTPUT_DIR
    print("✓ Config import successful")
    
    print("Importing Step 35 module...")
    sys.path.append(os.path.join(parent_dir, "src"))
    import importlib
    spec = importlib.util.spec_from_file_location("step35", os.path.join(parent_dir, "src", "step35_merchandising_strategy_deployment.py"))
    step35_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(step35_module)
    print("✓ Step 35 module import successful")
    
    print("Testing main function...")
    # Call the main function with test parameters
    step35_module.main(["--target-yyyymm", "202509", "--target-period", "A"])
    print("✓ Main function executed successfully")
    
except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
