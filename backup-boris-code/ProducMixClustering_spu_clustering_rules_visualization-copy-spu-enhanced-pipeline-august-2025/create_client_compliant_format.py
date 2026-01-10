#!/usr/bin/env python3
"""
Client-Compliant Format Generator

This script converts our detailed practical recommendations into the exact format
requested by the client, with only the 6 required columns and proper formatting.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import json

def load_detailed_recommendations() -> pd.DataFrame:
    """Load our detailed recommendations"""
    print("Loading detailed recommendations...")
    
    try:
        df = pd.read_csv('output/PRACTICAL_client_recommendations_6B_FULL.csv')
        print(f"Loaded {len(df):,} detailed recommendations")
        return df
    except FileNotFoundError:
        print("❌ Error: PRACTICAL_client_recommendations_6B_FULL.csv not found")
        print("Please run create_practical_client_recommendations.py first")
        return None

def convert_to_client_format(df: pd.DataFrame) -> pd.DataFrame:
    """Convert detailed format to client-compliant format"""
    print("Converting to client-compliant format...")
    
    # Keep ALL columns, just fix the two issues
    client_df = df.copy()
    
    # Fix Issue #2: Replace 'Quantity_Change' with 'Target SPU Quantity' (exact client specification)
    client_df = client_df.drop('Quantity_Change', axis=1)
    client_df.insert(client_df.columns.get_loc('Current_Quantity'), 'Target SPU Quantity', client_df['Target_Quantity'])
    
    # Fix Issue #3: Format month with leading zero
    client_df['Month'] = client_df['Month'].apply(lambda x: f"{x:02d}")
    
    print(f"Converted to {len(client_df):,} client-compliant records")
    return client_df

def create_summary_report(df: pd.DataFrame) -> Dict:
    """Create summary report for client format"""
    print("Creating client format summary...")
    
    if len(df) == 0:
        return {"error": "No data to summarize"}
    
    summary = {
        'total_recommendations': len(df),
        'time_period': f"{df['Year'].iloc[0]}-{df['Month'].iloc[0]}-{df['Period'].iloc[0]}",
        'store_groups': df['Store_Group'].nunique(),
        'store_groups_list': sorted(df['Store_Group'].unique().tolist()),
        'unique_style_combinations': df['Style_Tags'].nunique(),
        'total_target_quantity': int(df['Target SPU Quantity'].sum()),
        'avg_quantity_per_recommendation': round(df['Target SPU Quantity'].mean(), 2),
        'quantity_range': {
            'min': int(df['Target SPU Quantity'].min()),
            'max': int(df['Target SPU Quantity'].max()),
            'median': int(df['Target SPU Quantity'].median())
        },
        'top_10_style_combinations': df['Style_Tags'].value_counts().head(10).to_dict(),
        'columns_count': len(df.columns),
        'rule_participation_summary': {
            'Rule_7_Applied': int((df['Rule_7_Applied'] == 'YES').sum()),
            'Rule_8_Applied': int((df['Rule_8_Applied'] == 'YES').sum()),
            'Rule_9_Applied': int((df['Rule_9_Applied'] == 'YES').sum()),
            'Rule_10_Applied': int((df['Rule_10_Applied'] == 'YES').sum()),
            'Rule_11_Applied': int((df['Rule_11_Applied'] == 'YES').sum()),
            'Rule_12_Applied': int((df['Rule_12_Applied'] == 'YES').sum())
        }
    }
    
    return summary

def main():
    """Generate client-compliant format"""
    print("Generating Client-Compliant Format")
    print("=" * 50)
    
    # Load detailed recommendations
    detailed_df = load_detailed_recommendations()
    if detailed_df is None:
        return
    
    # Convert to client format
    client_df = convert_to_client_format(detailed_df)
    
    # Save client-compliant format
    output_file = 'output/CLIENT_COMPLIANT_recommendations_6B.csv'
    client_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Generated client-compliant format: {output_file}")
    
    # Create and save summary
    summary = create_summary_report(client_df)
    summary_file = 'output/CLIENT_COMPLIANT_summary.json'
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Display summary
    print(f"\n📊 Client-Compliant Format Summary:")
    print(f"- Total recommendations: {summary['total_recommendations']:,}")
    print(f"- Time period: {summary['time_period']}")
    print(f"- Store groups: {summary['store_groups']} ({', '.join(summary['store_groups_list'])})")
    print(f"- Unique style combinations: {summary['unique_style_combinations']:,}")
    print(f"- Total target quantity: {summary['total_target_quantity']:,}")
    print(f"- Average quantity per recommendation: {summary['avg_quantity_per_recommendation']}")
    print(f"- Quantity range: {summary['quantity_range']['min']} - {summary['quantity_range']['max']} (median: {summary['quantity_range']['median']})")
    
    print(f"\n🔝 Top 5 Style Combinations:")
    for style, count in list(summary['top_10_style_combinations'].items())[:5]:
        print(f"  {style}: {count:,} recommendations")
    
    # Show sample data
    print(f"\n🔍 Sample Client-Compliant Data:")
    sample = client_df.head(3)
    for col in client_df.columns:
        print(f"\n{col}:")
        for i, val in enumerate(sample[col]):
            print(f"  Row {i+1}: {val}")
    
    print(f"\n✅ Client-compliant format ready!")
    print(f"📁 Files created:")
    print(f"  - {output_file} (client-compliant format)")
    print(f"  - {summary_file} (summary)")
    
    print(f"\n📋 Format Compliance Check:")
    print(f"  ✅ Year: {client_df['Year'].iloc[0]}")
    print(f"  ✅ Month: {client_df['Month'].iloc[0]} (with leading zero)")
    print(f"  ✅ Period: {client_df['Period'].iloc[0]}")
    print(f"  ✅ Store Group: {client_df['Store_Group'].iloc[0]}")
    print(f"  ✅ Style Tags: {client_df['Style_Tags'].iloc[0]}")
    print(f"  ✅ Target SPU Quantity: {client_df['Target SPU Quantity'].iloc[0]} (was Quantity_Change)")
    print(f"  ✅ Total Columns: {len(client_df.columns)} (keeping all detailed analysis)")
    
    print(f"\n📋 Rule Participation Summary:")
    for rule, count in summary['rule_participation_summary'].items():
        rule_name = rule.replace('_Applied', '').replace('_', ' ')
        print(f"  {rule_name}: {count:,} recommendations")

if __name__ == "__main__":
    main() 