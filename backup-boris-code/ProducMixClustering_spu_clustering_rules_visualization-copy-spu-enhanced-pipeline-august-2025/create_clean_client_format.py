#!/usr/bin/env python3
"""
Clean Client Format Generator
Removes redundant columns and creates a clear, non-confusing format for the client.
"""

import pandas as pd
import json
from typing import Dict, Any
import numpy as np

def clean_client_format() -> None:
    """
    Create a clean client format by removing redundant columns.
    
    Removes:
    - Target_Quantity (redundant with Target SPU Quantity)
    - Other potentially confusing columns
    
    Keeps essential columns for business clarity.
    """
    print("🧹 Creating clean client format...")
    
    # Read the current client compliant file
    input_file = "output/CLIENT_COMPLIANT_recommendations_6B.csv"
    
    try:
        df = pd.read_csv(input_file)
        print(f"📊 Loaded {len(df):,} recommendations")
        
        # Define essential columns to keep (removing redundant ones)
        essential_columns = [
            # Client Requirements
            'Year',
            'Month', 
            'Period',
            'Store_Group',
            
            # Store Information
            'Store_Code',
            'Store_Name',
            
            # Product Information
            'SPU_Code',
            'Style_Tags',
            'Category',
            'Subcategory',
            
            # Action & Quantity (NO REDUNDANCY)
            'Action',
            'Target SPU Quantity',  # This is what client asked for
            'Current_Quantity',     # For context (current stock)
            
            # Business Context
            'Is_New_Item',
            'Recommendation',
            'Priority',
            
            # Rule Information (simplified)
            'Contributing_Rules_Count',
            'Business_Impact_Yuan'
        ]
        
        # Check which columns exist
        available_columns = [col for col in essential_columns if col in df.columns]
        missing_columns = [col for col in essential_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️  Missing columns: {missing_columns}")
        
        print(f"✅ Keeping {len(available_columns)} essential columns")
        
        # Create clean dataframe
        clean_df = df[available_columns].copy()
        
        # Sort by priority and business impact for better presentation
        clean_df = clean_df.sort_values(['Priority', 'Business_Impact_Yuan'], 
                                      ascending=[True, False])
        
        # Save clean format
        output_file = "output/CLEAN_client_recommendations_6B.csv"
        clean_df.to_csv(output_file, index=False)
        
        # Create summary
        summary = {
            "file_info": {
                "filename": "CLEAN_client_recommendations_6B.csv",
                "total_recommendations": len(clean_df),
                "columns_count": len(available_columns),
                "removed_redundant_columns": True
            },
            "column_structure": {
                "client_required": ["Year", "Month", "Period", "Store_Group", "Target SPU Quantity"],
                "business_essential": ["Store_Code", "SPU_Code", "Action", "Current_Quantity"],
                "context": ["Style_Tags", "Category", "Priority", "Business_Impact_Yuan"]
            },
            "data_summary": {
                "stores_affected": clean_df['Store_Code'].nunique(),
                "spus_affected": clean_df['SPU_Code'].nunique(),
                "total_business_impact": float(clean_df['Business_Impact_Yuan'].sum()),
                "action_breakdown": clean_df['Action'].value_counts().to_dict(),
                "priority_breakdown": clean_df['Priority'].value_counts().to_dict()
            },
            "clarity_improvements": [
                "Removed redundant 'Target_Quantity' column",
                "Kept only 'Target SPU Quantity' as requested by client",
                "Maintained 'Current_Quantity' for business context",
                "Simplified to essential columns only",
                "Clear action-oriented format"
            ]
        }
        
        # Save summary
        with open("output/CLEAN_format_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Clean format created successfully!")
        print(f"📄 File: {output_file}")
        print(f"📊 Records: {len(clean_df):,}")
        print(f"📋 Columns: {len(available_columns)}")
        print(f"💰 Total Impact: ¥{clean_df['Business_Impact_Yuan'].sum():,.2f}")
        
        print(f"\n🎯 Column Structure:")
        for i, col in enumerate(available_columns, 1):
            print(f"  {i:2d}. {col}")
        
        print(f"\n🧹 Removed Redundant Columns:")
        print(f"  - Target_Quantity (same as 'Target SPU Quantity')")
        print(f"  - Other non-essential columns for client clarity")
        
        # Show sample
        print(f"\n📋 Sample Records:")
        print(clean_df.head(3).to_string(index=False, max_cols=10))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return

if __name__ == "__main__":
    clean_client_format() 