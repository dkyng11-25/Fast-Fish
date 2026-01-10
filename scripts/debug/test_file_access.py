#!/usr/bin/env python3

import os
import pandas as pd

# Test file access
file_path = "/Users/frogtime/Desktop/code/boris-fix/ProducMixClustering_spu_clustering_rules_visualization-copy/output/store_tags_202509A.csv"

print(f"File path: {file_path}")
print(f"File exists: {os.path.exists(file_path)}")

if os.path.exists(file_path):
    try:
        # Try to read the file
        df = pd.read_csv(file_path)
        print(f"Successfully loaded file with {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        print("First few rows:")
        print(df.head())
    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()
else:
    print("File does not exist")
