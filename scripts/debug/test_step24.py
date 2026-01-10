#!/usr/bin/env python3

try:
    print("Testing Step 24 imports...")
    from src.config import get_period_label
    print("✓ config import successful")
    from src.pipeline_manifest import register_step_output
    print("✓ pipeline_manifest import successful")
    import pandas as pd
    print("✓ pandas import successful")
    import numpy as np
    print("✓ numpy import successful")
    print("All imports successful!")
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
