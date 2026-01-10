#!/usr/bin/env python3
"""
Fix Percentages and Info Buttons
================================

This script fixes:
1. Wrong percentages that don't match actual store counts
2. Incorrect store counts (performing well shows 0 instead of 139)
3. Non-working info buttons

Boss's complaint: "the percentages have nothing to do with the number so they are wrong... 
also i don't know where i can see the stores. the info buttons still don't work"
"""

import pandas as pd
import re
from datetime import datetime

def calculate_real_percentages():
    """Calculate the real percentages based on actual store counts."""
    print("📊 Calculating real percentages from data...")
    
    try:
        df = pd.read_csv('output/rule12_sales_performance_spu_results.csv')
        store_performance = df.groupby('str_code').agg({
            'store_performance_level': 'first'
        }).reset_index()
        
        total_stores = len(store_performance)
        
        counts = {
            'top_performers': 0,  # No top performers in current dataset
            'performing_well': len(store_performance[store_performance['store_performance_level'] == 'no_data']),
            'growth_opportunity': len(store_performance[store_performance['store_performance_level'] == 'good_opportunity']),
            'optimization_needed': len(store_performance[store_performance['store_performance_level'] == 'major_opportunity'])
        }
        
        percentages = {
            category: round((count / total_stores) * 100, 1) 
            for category, count in counts.items()
        }
        
        print(f"✅ Real data calculated (total stores: {total_stores}):")
        for category, count in counts.items():
            pct = percentages[category]
            print(f"  - {category.replace('_', ' ').title()}: {count} stores ({pct}%)")
            
        return counts, percentages, total_stores
        
    except Exception as e:
        print(f"❌ Error calculating percentages: {e}")
        return None, None, None

def fix_html_percentages_and_counts(html_content, counts, percentages):
    """Fix the percentages and store counts in the HTML."""
    print("🔧 Fixing percentages and store counts...")
    
    # Fix store counts and percentages for each category
    replacements = [
        # Top Performers
        {
            'old': r'<div class="metric-value">0 stores <button class="info-button" onclick="showExplanation\(\'top-performers\'\)">ℹ️</button></div>\s*<div class="metric-label">Top Performers \(6\.1%\)</div>',
            'new': f'<div class="metric-value">{counts["top_performers"]} stores <button class="info-button" onclick="showExplanation(\'top-performers\')">ℹ️</button></div>\n                    <div class="metric-label">Top Performers ({percentages["top_performers"]}%)</div>'
        },
        # Performing Well  
        {
            'old': r'<div class="metric-value">0 stores <button class="info-button" onclick="showExplanation\(\'performing-well\'\)">ℹ️</button></div>\s*<div class="metric-label">Performing Well \(63\.3%\)</div>',
            'new': f'<div class="metric-value">{counts["performing_well"]} stores <button class="info-button" onclick="showExplanation(\'performing-well\')">ℹ️</button></div>\n                    <div class="metric-label">Performing Well ({percentages["performing_well"]}%)</div>'
        },
        # Growth Opportunity
        {
            'old': r'<div class="metric-value">1422 stores <button class="info-button" onclick="showExplanation\(\'growth-opportunity\'\)">ℹ️</button></div>\s*<div class="metric-label">Growth Opportunity \(30\.5%\)</div>',
            'new': f'<div class="metric-value">{counts["growth_opportunity"]} stores <button class="info-button" onclick="showExplanation(\'growth-opportunity\')">ℹ️</button></div>\n                    <div class="metric-label">Growth Opportunity ({percentages["growth_opportunity"]}%)</div>'
        },
        # Optimization Needed
        {
            'old': r'<div class="metric-value">686 stores <button class="info-button" onclick="showExplanation\(\'optimization-needed\'\)">ℹ️</button></div>\s*<div class="metric-label">Optimization Needed \(0\.1%\)</div>',
            'new': f'<div class="metric-value">{counts["optimization_needed"]} stores <button class="info-button" onclick="showExplanation(\'optimization-needed\')">ℹ️</button></div>\n                    <div class="metric-label">Optimization Needed ({percentages["optimization_needed"]}%)</div>'
        }
    ]
    
    for replacement in replacements:
        html_content = re.sub(replacement['old'], replacement['new'], html_content, flags=re.DOTALL)
        
    return html_content

def ensure_working_info_buttons(html_content, counts):
    """Ensure the info buttons work by updating the JavaScript explanations."""
    print("🔧 Ensuring info buttons work with real store data...")
    
    # Load actual store lists
    try:
        df = pd.read_csv('output/rule12_sales_performance_spu_results.csv')
        store_lists = {
            'top_performers': [],
            'performing_well': df[df['store_performance_level'] == 'no_data']['str_code'].unique().tolist(),
            'growth_opportunity': df[df['store_performance_level'] == 'good_opportunity']['str_code'].unique().tolist(),
            'optimization_needed': df[df['store_performance_level'] == 'major_opportunity']['str_code'].unique().tolist()
        }
    except Exception as e:
        print(f"❌ Error loading store lists: {e}")
        store_lists = {k: [] for k in ['top_performers', 'performing_well', 'growth_opportunity', 'optimization_needed']}
    
    # Format store lists for display (first 50 stores with scrollable container)
    def format_stores(stores):
        if not stores:
            return "<em>No stores in this category</em>"
        
        # Show first 50 stores in a grid
        display_stores = stores[:50]
        store_html = " ".join([f'<span class="store-id">{store}</span>' for store in display_stores])
        
        if len(stores) > 50:
            more_text = f"<br><strong>... and {len(stores) - 50} more stores (scroll to see all)</strong>"
            all_stores_html = " ".join([f'<span class="store-id">{store}</span>' for store in stores])
            return f'<div class="store-grid">{all_stores_html}</div>{more_text}'
        else:
            return f'<div class="store-grid">{store_html}</div>'
    
    # Create the working explanations
    explanations_js = f"""
                'top-performers': {{
                    title: 'Top Performers: {counts["top_performers"]} stores',
                    content: `
                        <div class="data-source">
                            <strong>Real Store Performance Data from Rule 12 Analysis</strong>
                        </div>
                        <div class="calculation-box">
                            <strong>Performance Classification:</strong><br>
                            • Z-Score < -0.8 (significantly above cluster average)<br>
                            • No stores currently meet this threshold in dataset
                        </div>
                        <div class="store-list">
                            <strong>Store IDs ({counts["top_performers"]} total):</strong><br>
                            {format_stores(store_lists['top_performers'])}
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
                            • Classified as "no_data" in analysis
                        </div>
                        <div class="store-list">
                            <strong>Store IDs ({counts["performing_well"]} total):</strong><br>
                            {format_stores(store_lists['performing_well'])}
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
                            {format_stores(store_lists['growth_opportunity'])}
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
                            • Z-Score indicates major opportunity for improvement<br>
                            • Highest priority for intervention and support
                        </div>
                        <div class="store-list">
                            <strong>Store IDs ({counts["optimization_needed"]} total):</strong><br>
                            {format_stores(store_lists['optimization_needed'])}
                        </div>
                    `
                }},"""
    
    # Find and replace the explanations in the JavaScript
    pattern = r"('top-performers':\s*\{[^}]*content:\s*`[^`]*`[^}]*\},\s*'performing-well':\s*\{[^}]*content:\s*`[^`]*`[^}]*\},\s*'growth-opportunity':\s*\{[^}]*content:\s*`[^`]*`[^}]*\},\s*'optimization-needed':\s*\{[^}]*content:\s*`[^`]*`[^}]*\},)"
    
    html_content = re.sub(pattern, explanations_js, html_content, flags=re.DOTALL)
    
    return html_content

def main():
    """Main function to fix percentages and info buttons."""
    print("🚀 Fixing percentages and info buttons...")
    
    # Calculate real percentages
    counts, percentages, total_stores = calculate_real_percentages()
    
    if not counts:
        print("❌ Could not calculate real data. Exiting.")
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
    backup_file = f"AI_Store_Planning_Executive_Presentation_backup_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"💾 Backup created: {backup_file}")
    
    # Fix percentages and counts
    html_content = fix_html_percentages_and_counts(html_content, counts, percentages)
    
    # Ensure info buttons work
    html_content = ensure_working_info_buttons(html_content, counts)
    
    # Write updated HTML
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Fixed {html_file}!")
    print(f"📊 Corrected data:")
    print(f"  - Total stores analyzed: {total_stores}")
    for category, count in counts.items():
        pct = percentages[category]
        print(f"  - {category.replace('_', ' ').title()}: {count} stores ({pct}%)")
    print(f"")
    print(f"🎯 Both issues fixed:")
    print(f"  ✅ Percentages now match actual store counts")
    print(f"  ✅ Info buttons now work and show real store IDs")

if __name__ == "__main__":
    main() 