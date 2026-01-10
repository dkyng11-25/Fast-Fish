#!/usr/bin/env python3

import os
import sys
import pandas as pd

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from config import get_period_label, OUTPUT_DIR

print(f"Parent directory: {parent_dir}")
print(f"Output directory: {os.path.join(parent_dir, 'output')}")
print(f"Current working directory: {os.getcwd()}")

# Check if store tags file exists
period_label = get_period_label("202509", "A")
print(f"Period label: {period_label}")

store_tags_file = os.path.join(parent_dir, "output", f"store_tags_{period_label}.csv")
print(f"Looking for store tags file: {store_tags_file}")
print(f"File exists: {os.path.exists(store_tags_file)}")

if os.path.exists(store_tags_file):
    df = pd.read_csv(store_tags_file)
    print(f"Loaded {len(df)} records with {df['cluster_id'].nunique()} clusters")
    print(f"Columns: {list(df.columns)}")
else:
    print("Store tags file not found")
    # List available files
    output_dir = os.path.join(parent_dir, "output")
    if os.path.exists(output_dir):
        files = [f for f in os.listdir(output_dir) if "store_tags" in f]
        print(f"Available store tags files: {files}")
