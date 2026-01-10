#!/usr/bin/env python3

import os
import sys

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, "src"))

print("Starting module inspection...")

try:
    print("Importing step35 module...")
    import src.step35_merchandising_strategy_deployment as step35
    
    print("Module imported successfully")
    print(f"Module file: {step35.__file__}")
    
    # List all functions in the module
    print("\nAvailable functions in step35 module:")
    for name in dir(step35):
        if not name.startswith('_'):
            obj = getattr(step35, name)
            if callable(obj):
                print(f"  {name}: {obj}")
    
    # Check if main function exists
    if hasattr(step35, 'main'):
        print("\nMain function found")
        print(f"Main function: {step35.main}")
    else:
        print("\nMain function NOT found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
