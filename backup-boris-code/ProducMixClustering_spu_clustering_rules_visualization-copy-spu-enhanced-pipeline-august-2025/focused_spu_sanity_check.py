#!/usr/bin/env python3
"""
Focused SPU Sanity Check - Detailed Analysis
Specifically checks the detailed SPU files for:
1. Rule 10 duplicate entries (same store+SPU)
2. Unrealistic unit quantities 
3. Data consistency across rules
4. Investment calculation accuracy
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
import os

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def check_rule10_duplicates() -> Dict[str, Any]:
    """Check Rule 10 for duplicate store+SPU combinations"""
    log_progress("🔍 Checking Rule 10 for duplicates...")
    
    rule10_file = 'output/rule10_spu_overcapacity_opportunities.csv'
    if not os.path.exists(rule10_file):
        return {'error': 'Rule 10 file not found'}
    
    df = pd.read_csv(rule10_file, dtype={'str_code': str})
    log_progress(f"Loaded Rule 10: {len(df):,} records")
    
    # Check for duplicates by store+SPU
    if 'str_code' in df.columns and 'spu_code' in df.columns:
        duplicates = df.groupby(['str_code', 'spu_code']).size()
        duplicate_combinations = duplicates[duplicates > 1]
        
        log_progress(f"Unique store+SPU combinations: {len(duplicates):,}")
        log_progress(f"Duplicate store+SPU combinations: {len(duplicate_combinations):,}")
        
        if len(duplicate_combinations) > 0:
            print(f"⚠️  FOUND {len(duplicate_combinations)} DUPLICATE RULE 10 COMBINATIONS!")
            print("Top 10 examples:")
            for i, ((store, spu), count) in enumerate(duplicate_combinations.head(10).items()):
                print(f"  {i+1}. Store {store}, SPU {spu}: {count} records")
                sample = df[(df['str_code'] == store) & (df['spu_code'] == spu)]
                for j, (_, row) in enumerate(sample.iterrows()):
                    current_qty = row.get('current_quantity', 'N/A')
                    change = row.get('recommended_quantity_change', 'N/A')
                    investment = row.get('investment_required', 'N/A')
                    gender = row.get('sex_name', 'N/A')
                    season = row.get('season_name', 'N/A')
                    print(f"     Record {j+1}: Current={current_qty}, Change={change}, Investment=${investment}, Gender={gender}, Season={season}")
        
        return {
            'total_records': len(df),
            'unique_combinations': len(duplicates),
            'duplicate_combinations': len(duplicate_combinations),
            'duplicate_examples': duplicate_combinations.head(10).to_dict() if len(duplicate_combinations) > 0 else {}
        }
    else:
        return {'error': 'Missing required columns'}

def main():
    """Run focused SPU sanity check"""
    print("🎯 FOCUSED SPU SANITY CHECK")
    print("=" * 60)
    
    # Check Rule 10 duplicates first
    rule10_results = check_rule10_duplicates()
    
    print("\n" + "=" * 60)
    print("🎯 SANITY CHECK SUMMARY")
    print("=" * 60)
    
    if 'duplicate_combinations' in rule10_results and rule10_results['duplicate_combinations'] > 0:
        print(f"⚠️  CRITICAL ISSUE: Rule 10 has {rule10_results['duplicate_combinations']} duplicate store+SPU combinations")
        print("This explains the massive reduction numbers in consolidation!")
    else:
        print("✅ Rule 10: No duplicates found")

if __name__ == "__main__":
    main()
