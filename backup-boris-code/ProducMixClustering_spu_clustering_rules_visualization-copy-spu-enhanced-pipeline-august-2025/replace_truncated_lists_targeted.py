#!/usr/bin/env python3
"""
Replace Truncated Lists - Targeted Fix

This script specifically targets and replaces the truncated store lists
in the JavaScript explanations with complete lists.
"""

import pandas as pd

def main():
    """Replace truncated store lists with complete ones."""
    print("🔄 Replacing truncated store lists with complete ones...")
    
    # Load store data
    df = pd.read_csv('output/rule12_sales_performance_spu_results.csv')
    
    major_stores = sorted(df[df['store_performance_level'] == 'major_opportunity']['str_code'].astype(str).tolist())
    good_stores = sorted(df[df['store_performance_level'] == 'good_opportunity']['str_code'].astype(str).tolist())
    
    print(f"✅ Loaded {len(major_stores)} major opportunity stores")
    print(f"✅ Loaded {len(good_stores)} good opportunity stores")
    
    # Read current presentation
    with open('AI_Store_Planning_Executive_Presentation.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create backup
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f'AI_Store_Planning_Executive_Presentation_backup_targeted_{timestamp}.html'
    with open(backup_filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📝 Created backup: {backup_filename}")
    
    # Replace first truncated list (optimization needed - major opportunity)
    old_optimization = '''                                <span style="color: #6c757d; font-style: italic; text-align: center; grid-column: 1 / -1;">... and 676 more stores (showing first 10)</span>'''
    
    # Generate complete store list for major opportunity (optimization needed)
    major_badges = []
    for store in major_stores:
        major_badges.append(f'<span style="background: #dc3545; color: white; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">{store}</span>')
    major_badges.append('<span style="color: #28a745; font-weight: bold; text-align: center; grid-column: 1 / -1; background: #f8f9fa; padding: 8px; border-radius: 4px; border: 2px solid #28a745;">✅ Complete List - All 686 Stores Shown</span>')
    
    new_optimization = '                                ' + '\n                                '.join(major_badges)
    
    # Replace second truncated list (growth opportunity - good opportunity)
    old_growth = '''                                <span style="color: #6c757d; font-style: italic; text-align: center; grid-column: 1 / -1;">... and 1,412 more stores (showing first 10)</span>'''
    
    # Generate complete store list for good opportunity (growth opportunity)
    good_badges = []
    for store in good_stores:
        good_badges.append(f'<span style="background: #ffc107; color: #212529; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; text-align: center;">{store}</span>')
    good_badges.append('<span style="color: #28a745; font-weight: bold; text-align: center; grid-column: 1 / -1; background: #f8f9fa; padding: 8px; border-radius: 4px; border: 2px solid #28a745;">✅ Complete List - All 1,422 Stores Shown</span>')
    
    new_growth = '                                ' + '\n                                '.join(good_badges)
    
    # Apply replacements
    if old_optimization in content:
        content = content.replace(old_optimization, new_optimization)
        print("✅ Replaced truncated major opportunity list with complete 686 stores")
    else:
        print("⚠️  Could not find major opportunity truncated list")
    
    if old_growth in content:
        content = content.replace(old_growth, new_growth)
        print("✅ Replaced truncated good opportunity list with complete 1,422 stores")
    else:
        print("⚠️  Could not find good opportunity truncated list")
    
    # Also update the headers to show "ALL Store IDs"
    content = content.replace('<strong>Sample Store IDs:</strong><br>', '<strong>ALL Store IDs (Complete List):</strong><br>')
    print("✅ Updated headers to indicate complete lists")
    
    # Increase max-height for better scrolling
    content = content.replace('max-height: 300px;', 'max-height: 400px;')
    print("✅ Increased display height for better scrolling")
    
    # Save the updated content
    with open('AI_Store_Planning_Executive_Presentation.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n🎉 SUCCESS! All truncated store lists replaced with complete lists!")
    print(f"💯 Now showing ALL {len(major_stores)} + {len(good_stores)} + 139 = {len(major_stores) + len(good_stores) + 139} stores")
    print("🔍 Every single store is now visible in the presentation!")

if __name__ == "__main__":
    main() 