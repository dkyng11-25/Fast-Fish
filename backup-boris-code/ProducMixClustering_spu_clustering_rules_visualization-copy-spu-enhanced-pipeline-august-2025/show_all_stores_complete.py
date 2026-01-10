#!/usr/bin/env python3
"""
Show All Stores Complete

Generates complete store lists for each category and updates the presentation
to show ALL stores instead of just samples.
"""

import pandas as pd

def get_all_stores():
    """Get complete lists of all stores in each category."""
    df = pd.read_csv('output/rule12_sales_performance_spu_results.csv')
    
    return {
        'major_opportunity': sorted(df[df['store_performance_level'] == 'major_opportunity']['str_code'].astype(str).tolist()),
        'good_opportunity': sorted(df[df['store_performance_level'] == 'good_opportunity']['str_code'].astype(str).tolist()),
        'no_data': sorted(df[df['store_performance_level'] == 'no_data']['str_code'].astype(str).tolist())
    }

def create_complete_html_grid(stores, color, category_name):
    """Create HTML grid with ALL stores."""
    if not stores:
        return '<p>No stores in this category</p>'
    
    badges = []
    for store in stores:
        badges.append(f'<span style="background: {color}; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">{store}</span>')
    
    # Add completion indicator
    badges.append(f'<span style="color: #28a745; font-weight: bold; text-align: center; grid-column: 1 / -1; background: #f8f9fa; padding: 8px; border-radius: 4px; border: 2px solid #28a745;">✅ Complete List - All {len(stores)} Stores Shown</span>')
    
    grid_html = f'''<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 8px; max-height: 400px; overflow-y: auto; padding: 15px; background: #f8f9fa; border-radius: 8px; margin: 10px 0;">
                {' '.join(badges)}
            </div>'''
    
    return grid_html

def main():
    """Generate complete store lists and print for manual insertion."""
    print("🔄 Generating complete store lists for all categories...")
    
    all_stores = get_all_stores()
    
    print(f"\n📊 Store Count Summary:")
    print(f"   • Insufficient Data: {len(all_stores['no_data'])} stores")
    print(f"   • Growth Opportunity: {len(all_stores['good_opportunity'])} stores")
    print(f"   • Optimization Needed: {len(all_stores['major_opportunity'])} stores")
    print(f"   • Total: {sum(len(stores) for stores in all_stores.values())} stores")
    
    # Generate HTML for insufficient data stores (the user specifically asked about this)
    print(f"\n✅ Complete HTML for Insufficient Data Stores:")
    print("=" * 60)
    insufficient_data_html = create_complete_html_grid(all_stores['no_data'], '#6c757d', 'Insufficient Data')
    print(f'<strong>ALL Store IDs (Complete List - {len(all_stores["no_data"])} stores):</strong><br>')
    print(insufficient_data_html)
    
    print(f"\n✅ Complete HTML for Growth Opportunity Stores:")
    print("=" * 60)
    growth_html = create_complete_html_grid(all_stores['good_opportunity'], '#ffc107', 'Growth Opportunity')
    print(f'<strong>ALL Store IDs (Complete List - {len(all_stores["good_opportunity"])} stores):</strong><br>')
    print(growth_html)
    
    print(f"\n✅ Complete HTML for Optimization Needed Stores:")
    print("=" * 60)
    optimization_html = create_complete_html_grid(all_stores['major_opportunity'], '#dc3545', 'Optimization Needed')
    print(f'<strong>ALL Store IDs (Complete List - {len(all_stores["major_opportunity"])} stores):</strong><br>')
    print(optimization_html)
    
    print(f"\n🎯 All stores are now available for display!")
    print(f"💡 The user specifically wanted to see ALL stores, not samples.")

if __name__ == "__main__":
    main() 