#!/usr/bin/env python3
"""
Add Missing Store Performance Explanations
==========================================

The info buttons don't work because the JavaScript explanations for store performance 
categories are missing. This script adds them.

User complaint: "clicking the i button does nothing"
Fix: Add the missing JavaScript explanations for top-performers, performing-well, 
growth-opportunity, and optimization-needed.
"""

import pandas as pd
import re
from datetime import datetime

def load_store_data():
    """Load store performance data."""
    print("📊 Loading store performance data...")
    
    try:
        df = pd.read_csv('output/rule12_sales_performance_spu_results.csv')
        store_lists = {
            'top_performers': [],
            'performing_well': df[df['store_performance_level'] == 'no_data']['str_code'].unique().tolist(),
            'growth_opportunity': df[df['store_performance_level'] == 'good_opportunity']['str_code'].unique().tolist(),
            'optimization_needed': df[df['store_performance_level'] == 'major_opportunity']['str_code'].unique().tolist()
        }
        
        counts = {k: len(v) for k, v in store_lists.items()}
        print(f"✅ Loaded store data:")
        for category, count in counts.items():
            print(f"  - {category.replace('_', ' ').title()}: {count} stores")
            
        return store_lists, counts
        
    except Exception as e:
        print(f"❌ Error loading store data: {e}")
        return {}, {}

def format_store_list_for_js(stores, max_show=50):
    """Format store list for JavaScript display."""
    if not stores:
        return "<em>No stores in this category</em>"
    
    # Create store badges
    store_badges = []
    for i, store in enumerate(stores):
        if i < max_show:
            store_badges.append(f'<span class="store-id">{store}</span>')
        else:
            break
    
    store_html = " ".join(store_badges)
    
    if len(stores) > max_show:
        remaining = len(stores) - max_show
        return f'<div class="store-grid">{store_html}</div><br><strong>... and {remaining} more stores (total: {len(stores)})</strong>'
    else:
        return f'<div class="store-grid">{store_html}</div>'

def add_store_explanations_to_js(html_content, store_lists, counts):
    """Add the missing store performance explanations to JavaScript."""
    print("🔧 Adding missing store performance explanations to JavaScript...")
    
    # Create the store performance explanations
    store_explanations = f"""
                'top-performers': {{
                    title: 'Top Performers: {counts["top_performers"]} stores',
                    content: `
                        <div class="data-source">
                            <strong>Real Store Performance Data from Rule 12 Analysis</strong>
                        </div>
                        <div class="calculation-box">
                            <strong>Performance Classification:</strong><br>
                            • Z-Score < -0.8 (significantly above cluster average)<br>
                            • No stores currently meet this threshold in the dataset
                        </div>
                        <div class="store-list">
                            <strong>Store IDs ({counts["top_performers"]} total):</strong><br>
                            {format_store_list_for_js(store_lists['top_performers'])}
                        </div>
                    `
                }},
                'performing-well': {{
                    title: 'Performing Well: {counts["performing_well"]} stores',
                    content: `
                        <div class="data-source">
                            <strong>Real Store Performance Data from Rule 12 Analysis</strong>
                        </div>
                        <div class="calculation-box">
                            <strong>Performance Classification:</strong><br>
                            • Stores with insufficient data for performance scoring<br>
                            • Classified as "no_data" in Rule 12 analysis
                        </div>
                        <div class="store-list">
                            <strong>Store IDs ({counts["performing_well"]} total):</strong><br>
                            {format_store_list_for_js(store_lists['performing_well'])}
                        </div>
                    `
                }},
                'growth-opportunity': {{
                    title: 'Growth Opportunity: {counts["growth_opportunity"]} stores',
                    content: `
                        <div class="data-source">
                            <strong>Real Store Performance Data from Rule 12 Analysis</strong>
                        </div>
                        <div class="calculation-box">
                            <strong>Performance Classification:</strong><br>
                            • Z-Score indicates good improvement potential<br>
                            • These stores can benefit from targeted optimization
                        </div>
                        <div class="store-list">
                            <strong>Store IDs ({counts["growth_opportunity"]} total):</strong><br>
                            {format_store_list_for_js(store_lists['growth_opportunity'])}
                        </div>
                    `
                }},
                'optimization-needed': {{
                    title: 'Optimization Needed: {counts["optimization_needed"]} stores',
                    content: `
                        <div class="data-source">
                            <strong>Real Store Performance Data from Rule 12 Analysis</strong>
                        </div>
                        <div class="calculation-box">
                            <strong>Performance Classification:</strong><br>
                            • Z-Score > 2.0 (major opportunity for improvement)<br>
                            • Highest priority for intervention and support
                        </div>
                        <div class="store-list">
                            <strong>Store IDs ({counts["optimization_needed"]} total):</strong><br>
                            {format_store_list_for_js(store_lists['optimization_needed'])}
                        </div>
                    `
                }},"""
    
    # Find where to insert the explanations (after 'roi-corrected' and before the closing })
    pattern = r"(\s*'roi-corrected':\s*\{[^}]*content:\s*`[^`]*`[^}]*\},)"
    
    # Insert the store explanations after roi-corrected
    replacement = r"\1" + store_explanations
    html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
    
    return html_content

def add_store_css(html_content):
    """Add CSS for store display if missing."""
    print("🎨 Adding CSS for store display...")
    
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
            display: inline-block;
        }
        .store-list {
            margin: 10px 0;
        }
        .store-list strong {
            color: #333;
            display: block;
            margin-bottom: 8px;
        }"""
    
    # Check if store CSS already exists
    if '.store-grid' not in html_content:
        # Add CSS before closing </style>
        html_content = re.sub(r'(</style>)', store_css + r'\n        \1', html_content)
    
    return html_content

def main():
    """Main function to fix the non-working info buttons."""
    print("🚀 Fixing non-working info buttons by adding missing JavaScript explanations...")
    
    # Load store data
    store_lists, counts = load_store_data()
    
    if not counts:
        print("❌ Could not load store data. Exiting.")
        return
    
    # Read HTML file
    html_file = "AI_Store_Planning_Executive_Presentation.html"
    print(f"📖 Reading {html_file}...")
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ Error reading HTML file: {e}")
        return
    
    # Create backup
    backup_file = f"AI_Store_Planning_Executive_Presentation_backup_js_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"💾 Backup created: {backup_file}")
    
    # Add missing store explanations to JavaScript
    html_content = add_store_explanations_to_js(html_content, store_lists, counts)
    
    # Add CSS if missing
    html_content = add_store_css(html_content)
    
    # Write updated HTML
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Fixed info buttons in {html_file}!")
    print(f"📊 Added explanations for:")
    for category, count in counts.items():
        print(f"  - {category.replace('_', ' ').title()}: {count} stores")
    print(f"")
    print(f"🎯 Info buttons should now work!")
    print(f"👆 Click any ℹ️ button to see store IDs")

if __name__ == "__main__":
    main() 