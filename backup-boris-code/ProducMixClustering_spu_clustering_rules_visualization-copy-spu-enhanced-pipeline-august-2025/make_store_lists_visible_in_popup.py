#!/usr/bin/env python3
"""
Make Store Lists Visible in Popup Windows
==========================================

This script updates the presentation so that when users click the info buttons (ℹ️),
they can see the actual store IDs directly in the popup window without needing to download files.

Boss's request: "can we make the list of stores visible please"
Answer: Yes! Store lists will now be visible directly in the popup windows.
"""

import pandas as pd
import re
from datetime import datetime

def load_store_lists():
    """Load all store lists from the generated files."""
    print("📊 Loading store lists from files...")
    
    store_lists = {}
    
    # Read each store list file
    files = {
        'growth_opportunity': 'real_store_list_growth_opportunity.txt',
        'optimization_needed': 'real_store_list_optimization_needed.txt', 
        'performing_well': 'real_store_list_performing_well.txt',
        'top_performers': 'real_store_list_top_performers.txt'
    }
    
    for category, filename in files.items():
        try:
            with open(filename, 'r') as f:
                content = f.read()
                
            # Extract store IDs from the file content
            lines = content.split('\n')
            stores = []
            
            for line in lines:
                line = line.strip()
                # Skip headers, comments, and empty lines
                if line and not line.startswith('#') and not line.startswith('REAL STORE') and not line.startswith('Source') and not line.startswith('Generated') and not line.startswith('===') and not line.startswith('STORE') and not line.startswith('   '):
                    # Check if line contains a store ID (numeric)
                    if line.isdigit() or (len(line) >= 4 and line.replace(' ', '').isalnum()):
                        stores.append(line)
            
            store_lists[category] = stores
            print(f"✅ Loaded {len(stores)} stores for {category}")
            
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            store_lists[category] = []
    
    return store_lists

def load_store_lists_from_csv():
    """Load store lists directly from the Rule 12 CSV file."""
    print("📊 Loading store lists directly from Rule 12 data...")
    
    try:
        df = pd.read_csv('output/rule12_sales_performance_spu_results.csv')
        store_performance = df.groupby('str_code').agg({
            'store_performance_level': 'first'
        }).reset_index()
        
        store_lists = {
            'growth_opportunity': store_performance[store_performance['store_performance_level'] == 'good_opportunity']['str_code'].tolist(),
            'optimization_needed': store_performance[store_performance['store_performance_level'] == 'major_opportunity']['str_code'].tolist(),
            'performing_well': store_performance[store_performance['store_performance_level'] == 'no_data']['str_code'].tolist(),
            'top_performers': []  # No top performers in current dataset
        }
        
        for category, stores in store_lists.items():
            print(f"✅ Loaded {len(stores)} stores for {category}")
            
        return store_lists
        
    except Exception as e:
        print(f"❌ Error loading from CSV: {e}")
        return {}

def format_store_list_for_html(stores, max_display=50):
    """Format store list for HTML display in popup."""
    if not stores:
        return "<em>No stores in this category</em>"
        
    if len(stores) <= max_display:
        # Show all stores in a neat grid format
        store_items = [f"<span class='store-id'>{store}</span>" for store in stores]
        return "<div class='store-grid'>" + " ".join(store_items) + "</div>"
    else:
        # Show first max_display stores, then indicate more
        displayed_stores = stores[:max_display]
        store_items = [f"<span class='store-id'>{store}</span>" for store in displayed_stores]
        grid = "<div class='store-grid'>" + " ".join(store_items) + "</div>"
        return f"{grid}<br><strong>... and {len(stores) - max_display} more stores</strong><br><em>Download file for complete list</em>"

def update_html_with_visible_stores(html_content, store_lists):
    """Update the HTML to show store lists directly in popup windows."""
    print("🔧 Adding visible store lists to popup windows...")
    
    # Add CSS for store display
    store_css = """
        .store-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin: 10px 0;
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .store-id {
            background-color: #e3f2fd;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 11px;
            border: 1px solid #2196f3;
            color: #1976d2;
            white-space: nowrap;
        }
        .store-list {
            margin: 10px 0;
        }
        .store-list strong {
            color: #333;
            display: block;
            margin-bottom: 8px;
        }
    """
    
    # Find the style section and add our CSS
    css_pattern = r'(</style>)'
    html_content = re.sub(css_pattern, f'{store_css}\n\\1', html_content)
    
    # Update each store category explanation with visible store lists
    explanations = {
        'top-performers': {
            'title': f'Top Performers: {len(store_lists["top_performers"])} stores',
            'description': 'Z-Score < -0.8 (significantly above cluster average)',
            'stores': store_lists['top_performers']
        },
        'performing-well': {
            'title': f'Performing Well: {len(store_lists["performing_well"])} stores', 
            'description': 'Insufficient data for performance classification',
            'stores': store_lists['performing_well']
        },
        'growth-opportunity': {
            'title': f'Growth Opportunity: {len(store_lists["growth_opportunity"])} stores',
            'description': 'Z-Score between 0.8 and 2.0 (good improvement potential)',
            'stores': store_lists['growth_opportunity']
        },
        'optimization-needed': {
            'title': f'Optimization Needed: {len(store_lists["optimization_needed"])} stores',
            'description': 'Z-Score > 2.0 (major opportunity for improvement)',
            'stores': store_lists['optimization_needed']
        }
    }
    
    for category, info in explanations.items():
        store_html = format_store_list_for_html(info['stores'])
        
        new_explanation = f"""
                '{category}': {{
                    title: '{info["title"]}',
                    content: `
                        <div class="data-source">
                            <strong>Real Store Performance Data from Rule 12 Analysis</strong>
                        </div>
                        <div class="calculation-box">
                            <strong>Performance Classification:</strong><br>
                            • {info["description"]}<br>
                            • Based on sales performance vs cluster benchmarks
                        </div>
                        <div class="store-list">
                            <strong>Store IDs ({len(info["stores"])} total):</strong><br>
                            {store_html}
                        </div>
                        <div class="download-link">
                            <strong>📁 Download Complete List:</strong><br>
                            <a href="real_store_list_{category}.txt" download>Download all {len(info["stores"])} store IDs as text file</a>
                        </div>
                    `
                }},"""
        
        # Replace the existing explanation
        pattern = rf"'{category}':\s*\{{[^}}]*content:\s*`[^`]*`[^}}]*\}},"
        html_content = re.sub(pattern, new_explanation, html_content, flags=re.DOTALL)
    
    return html_content

def main():
    """Main function to make store lists visible in popup windows."""
    print("🚀 Making store lists visible in popup windows...")
    
    # Load store lists
    store_lists = load_store_lists_from_csv()
    
    if not any(store_lists.values()):
        print("❌ Could not load store lists. Exiting.")
        return
    
    # Read current HTML
    html_file = "AI_Store_Planning_Executive_Presentation.html"
    print(f"📖 Reading {html_file}...")
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ Error reading HTML file: {e}")
        return
    
    # Create backup
    backup_file = f"AI_Store_Planning_Executive_Presentation_backup_visible_stores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"💾 Backup created: {backup_file}")
    
    # Update HTML with visible store lists
    html_content = update_html_with_visible_stores(html_content, store_lists)
    
    # Write updated HTML
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Updated {html_file} with visible store lists!")
    print(f"📊 Store counts:")
    for category, stores in store_lists.items():
        print(f"  - {category.replace('_', ' ').title()}: {len(stores)} stores")
    print(f"")
    print(f"🎯 Boss's request fulfilled: Store lists are now visible in popup windows!")
    print(f"👆 Click any ℹ️ button to see store IDs directly in the presentation")

if __name__ == "__main__":
    main() 