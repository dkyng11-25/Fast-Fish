#!/usr/bin/env python3

import os
import sys

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, "src"))

print("Starting debug test...")
print(f"Working directory: {os.getcwd()}")
print(f"Parent directory: {parent_dir}")

try:
    from src.config import get_period_label, OUTPUT_DIR
    print("✓ Config import successful")
    period_label = get_period_label('202509', 'A')
    print(f"✓ Period label: {period_label}")
    
    output_dir = os.path.join(parent_dir, "output")
    print(f"✓ Output directory: {output_dir}")
    print(f"✓ Output directory exists: {os.path.exists(output_dir)}")
    
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        store_tags_files = [f for f in files if "store_tags" in f and "202509A" in f]
        print(f"✓ Store tags files for 202509A: {store_tags_files}")
    
    print("✓ Debug test completed successfully")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
