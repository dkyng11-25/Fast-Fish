#!/usr/bin/env python3
"""
Remove Single Redundant Column
Removes ONLY the Target_Quantity column (redundant with Target SPU Quantity)
Keeps ALL other columns intact.
"""

import pandas as pd
import json

def remove_single_redundant_column() -> None:
    """
    Remove ONLY the Target_Quantity column which is redundant with 'Target SPU Quantity'.
    Keep all other 29 columns intact.
    """
    print("🎯 Removing ONLY the redundant Target_Quantity column...")
    
    # Read the current client compliant file
    input_file = "output/CLIENT_COMPLIANT_recommendations_6B.csv"
    
    try:
        df = pd.read_csv(input_file)
        print(f"📊 Loaded {len(df):,} recommendations")
        print(f"📋 Original columns: {len(df.columns)}")
        
        # Show original columns
        print(f"\n📋 Original Columns ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            marker = " ❌ (REMOVING)" if col == "Target_Quantity" else ""
            print(f"  {i:2d}. {col}{marker}")
        
        # Remove ONLY the Target_Quantity column
        if 'Target_Quantity' in df.columns:
            df_cleaned = df.drop('Target_Quantity', axis=1)
            print(f"\n✅ Removed 'Target_Quantity' column")
        else:
            df_cleaned = df.copy()
            print(f"\n⚠️  'Target_Quantity' column not found")
        
        print(f"📋 Final columns: {len(df_cleaned.columns)}")
        
        # Save the corrected file
        output_file = "output/CORRECTED_client_recommendations_6B.csv"
        df_cleaned.to_csv(output_file, index=False)
        
        # Create summary
        summary = {
            "action": "Removed single redundant column",
            "removed_column": "Target_Quantity",
            "reason": "Redundant with 'Target SPU Quantity'",
            "original_columns": len(df.columns),
            "final_columns": len(df_cleaned.columns),
            "columns_removed": 1,
            "records": len(df_cleaned),
            "remaining_columns": list(df_cleaned.columns)
        }
        
        # Save summary
        with open("output/CORRECTED_format_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Corrected format created successfully!")
        print(f"📄 File: {output_file}")
        print(f"📊 Records: {len(df_cleaned):,}")
        print(f"📋 Columns: {len(df_cleaned.columns)} (removed 1)")
        
        print(f"\n🎯 Final Column Structure:")
        for i, col in enumerate(df_cleaned.columns, 1):
            print(f"  {i:2d}. {col}")
        
        print(f"\n✅ Kept ALL other columns intact - only removed the redundant 'Target_Quantity'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return

if __name__ == "__main__":
    remove_single_redundant_column() 