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
    from src.config import get_period_label, OUTPUT_DIR
    print("✓ Config import successful")
    print(f"Period label for 202509A: {get_period_label('202509', 'A')}")
    print(f"Output directory: {OUTPUT_DIR}")
except Exception as e:
    print(f"✗ Config import failed: {e}")
    import traceback
    traceback.print_exc()
