#!/usr/bin/env python3

import pandas as pd
import traceback

try:
    print("Attempting to read enhanced_clustering_results.csv...")
    df = pd.read_csv("output/enhanced_clustering_results.csv")
    print(f"Successfully read {len(df)} rows")
    print("Columns:")
    for col in df.columns:
        print(f"  {col}")
    print("First row sample:")
    print(df.iloc[0])
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
