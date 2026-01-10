#!/usr/bin/env python3
"""
Check Store Inventory - Analyze actual stock levels for extreme case
"""

import pandas as pd
import json

def analyze_store_inventory():
    """Analyze actual stock levels for Store 51198."""
    
    # Load the detailed Rule 10 data
    rule10_df = pd.read_csv('output/rule10_spu_overcapacity_opportunities.csv')
    
    # Focus on Store 51198 T-shirts
    store_code = 51198
    spu_pattern = '休闲圆领T恤'
    
    print('🔍 STORE 51198 T-SHIRT INVENTORY ANALYSIS')
    print('=' * 60)
    
    # Get all T-shirt variants for this store
    variants = rule10_df[
        (rule10_df['str_code'] == store_code) & 
        (rule10_df['sub_cate_name'] == spu_pattern)
    ]
    
    if len(variants) > 0:
        print(f'📊 DETAILED BREAKDOWN:')
        print('-' * 40)
        
        total_current = 0
        total_reduction = 0
        total_after_reduction = 0
        
        for _, variant in variants.iterrows():
            gender = variant['sex_name']
            location = variant['display_location_name']
            current_qty = variant['current_quantity']
            reduction = variant['constrained_reduction']
            after_reduction = current_qty - reduction
            
            total_current += current_qty
            total_reduction += reduction
            total_after_reduction += after_reduction
            
            print(f'{gender} {location}:')
            print(f'  Current Stock: {current_qty:.1f} units')
            print(f'  Recommended Reduction: {reduction:.1f} units')
            print(f'  Stock After Reduction: {after_reduction:.1f} units')
            print()
        
        print(f'📈 TOTALS:')
        print(f'  Current Total Stock: {total_current:.1f} T-shirts')
        print(f'  Recommended Reduction: {total_reduction:.1f} T-shirts')
        print(f'  Stock After Reduction: {total_after_reduction:.1f} T-shirts')
        print(f'  Reduction Percentage: {(total_reduction/total_current)*100:.1f}%')
        
        # Check if there are sales data
        print(f'\n💰 SALES ANALYSIS:')
        print('-' * 40)
        
        total_sales = 0
        for _, variant in variants.iterrows():
            try:
                # Parse the sales data JSON
                sales_data = json.loads(variant['sty_sal_amt']) if pd.notna(variant['sty_sal_amt']) else {}
                variant_sales = sum(float(v) for v in sales_data.values() if v > 0)
                total_sales += variant_sales
                
                gender = variant['sex_name']
                location = variant['display_location_name']
                print(f'{gender} {location}: ${variant_sales:,.0f} in sales')
                
            except:
                continue
        
        print(f'\nTotal Sales Amount: ${total_sales:,.0f}')
        
        # Calculate inventory turnover metrics
        if total_sales > 0:
            avg_unit_price = total_sales / total_current
            print(f'Average Unit Price: ${avg_unit_price:.2f}')
            print(f'Total Inventory Value: ${total_current * avg_unit_price:,.0f}')
            print(f'Reduction Value: ${total_reduction * avg_unit_price:,.0f}')
        
        # Business context
        print(f'\n🏪 BUSINESS CONTEXT:')
        print('-' * 40)
        print(f'This represents a VERY HIGH volume T-shirt operation')
        print(f'For context:')
        print(f'  • Average clothing store might stock 100-500 T-shirts total')
        print(f'  • Department stores might stock 1,000-2,000 T-shirts total')
        print(f'  • This store has {total_current:.0f} T-shirts of ONE STYLE')
        print(f'  • This suggests either:')
        print(f'    - Large format store (department store, warehouse)')
        print(f'    - Seasonal bulk purchasing')
        print(f'    - Regional distribution center')
        print(f'    - Very high-traffic location')
        
        # Check other stores for comparison
        print(f'\n📊 COMPARISON WITH OTHER STORES:')
        print('-' * 40)
        
        # Get T-shirt data for all stores
        all_tshirts = rule10_df[rule10_df['sub_cate_name'] == spu_pattern]
        store_totals = all_tshirts.groupby('str_code')['current_quantity'].sum().sort_values(ascending=False)
        
        print(f'Top 10 stores by T-shirt inventory:')
        for i, (store, qty) in enumerate(store_totals.head(10).items()):
            marker = " ← THIS STORE" if store == store_code else ""
            print(f'  {i+1:2d}. Store {store}: {qty:.0f} T-shirts{marker}')
        
        print(f'\nStore 51198 ranks #{(store_totals > total_current).sum() + 1} out of {len(store_totals)} stores')
        
    else:
        print('No data found for Store 51198 T-shirts')

if __name__ == "__main__":
    analyze_store_inventory() 