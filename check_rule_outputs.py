#!/usr/bin/env python3
import pandas as pd
import glob

print("🔍 Checking Business Rule Outputs (Steps 7-12)")
print("="*80)

for rule_num in [7, 8, 9, 10, 11, 12]:
    print(f"\n📋 Rule {rule_num}:")
    files = glob.glob(f"output/rule{rule_num}_*results*.csv") + glob.glob(f"output/rule{rule_num}_*details*.csv")
    
    for f in files[:2]:  # Check first 2 files
        try:
            df = pd.read_csv(f, dtype={'str_code': str})
            
            # Find cluster column
            cluster_col = None
            for col in ['cluster_id', 'Cluster', 'cluster']:
                if col in df.columns:
                    cluster_col = col
                    break
            
            if cluster_col:
                unique_clusters = df[cluster_col].nunique()
                print(f"  ✅ {f.split('/')[-1]}: {unique_clusters} clusters, {len(df):,} rows")
            else:
                print(f"  ⚠️  {f.split('/')[-1]}: No cluster column, {len(df):,} rows")
        except Exception as e:
            print(f"  ❌ {f.split('/')[-1]}: Error - {e}")

print("\n" + "="*80)
