#!/usr/bin/env python3

import os
import sys

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, "src"))

print("Starting main function test...")

try:
    print("Importing step35 module...")
    import src.step35_merchandising_strategy_deployment as step35
    
    print("Calling main function with test arguments...")
    # Call main function with test arguments
    step35.main(["--target-yyyymm", "202509", "--target-period", "A"])
    
    print("Main function completed successfully")
    
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
