#!/usr/bin/env python3
"""
Fix Info Buttons and Complete Store Lists

This script fixes:
1. Mismatched button IDs vs explanations object keys
2. Incorrect category labels (139 stores are 'no_data', not 'performing well')
3. Truncated store lists - show ALL stores, not just samples
4. Add proper scrolling for long store lists
"""

import pandas as pd
import re
from typing import Dict, List
import json

def get_complete_store_data() -> Dict:
    """Get complete store data with all store IDs for each category."""
    print("📊 Loading complete store performance data...")
    
    df = pd.read_csv('output/rule12_sales_performance_spu_results.csv')
    
    # Get ALL stores for each category (not just samples)
    store_data = {
        'major_opportunity': {
            'stores': df[df['store_performance_level'] == 'major_opportunity']['str_code'].tolist(),
            'count': len(df[df['store_performance_level'] == 'major_opportunity']),
            'percentage': len(df[df['store_performance_level'] == 'major_opportunity']) / len(df) * 100
        },
        'good_opportunity': {
            'stores': df[df['store_performance_level'] == 'good_opportunity']['str_code'].tolist(),
            'count': len(df[df['store_performance_level'] == 'good_opportunity']),
            'percentage': len(df[df['store_performance_level'] == 'good_opportunity']) / len(df) * 100
        },
        'no_data': {
            'stores': df[df['store_performance_level'] == 'no_data']['str_code'].tolist(),
            'count': len(df[df['store_performance_level'] == 'no_data']),
            'percentage': len(df[df['store_performance_level'] == 'no_data']) / len(df) * 100
        }
    }
    
    print(f"✅ Complete store data loaded:")
    print(f"   • Major opportunities: {store_data['major_opportunity']['count']} stores")
    print(f"   • Good opportunities: {store_data['good_opportunity']['count']} stores") 
    print(f"   • No data: {store_data['no_data']['count']} stores")
    
    return store_data

def create_store_grid(stores: List[str], max_per_page: int = 100) -> str:
    """Create HTML for store grid with pagination if needed."""
    if not stores:
        return '<p>No stores in this category</p>'
    
    # Sort stores for consistent display
    stores = sorted([str(store) for store in stores])
    total_stores = len(stores)
    
    # Create store badges
    store_badges = []
    for i, store in enumerate(stores):
        store_badges.append(f'<span class="store-badge">{store}</span>')
    
    # If more than max_per_page, create paginated view
    if total_stores > max_per_page:
        # Show first max_per_page stores
        visible_stores = ' '.join(store_badges[:max_per_page])
        remaining_count = total_stores - max_per_page
        
        grid_html = f'''
        <div class="store-grid-container">
            <div class="store-grid" id="storeGrid">
                {visible_stores}
            </div>
            <div class="pagination-controls">
                <button class="show-more-btn" onclick="showAllStores(this, {json.dumps(store_badges)})">
                    Show All {total_stores} Stores ({remaining_count} more)
                </button>
            </div>
        </div>'''
    else:
        # Show all stores if under the limit
        all_stores = ' '.join(store_badges)
        grid_html = f'''
        <div class="store-grid-container">
            <div class="store-grid">
                {all_stores}
            </div>
            <p class="store-count">Showing all {total_stores} stores</p>
        </div>'''
    
    return grid_html

def fix_presentation_html(store_data: Dict) -> None:
    """Fix the presentation HTML with correct labels, buttons, and complete store lists."""
    print("\n🔧 Fixing presentation HTML...")
    
    with open('AI_Store_Planning_Executive_Presentation.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Fix the store performance section with CORRECT labels and button IDs
    new_store_performance = f'''
                <div class="metric-card">
                    <div class="metric-value">0 stores <button class="info-button" onclick="showExplanation('not-available')">ℹ️</button></div>
                    <div class="metric-label">Top Performers (0.0%)</div>
                    <div class="metric-description">Category not available - Rule 12 focuses on improvement opportunities.</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value">{store_data['no_data']['count']} stores <button class="info-button" onclick="showExplanation('insufficient-data')">ℹ️</button></div>
                    <div class="metric-label">Insufficient Data ({store_data['no_data']['percentage']:.1f}%)</div>
                    <div class="metric-description">Stores with limited data for performance analysis.</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value">{store_data['good_opportunity']['count']} stores <button class="info-button" onclick="showExplanation('growth-opportunity')">ℹ️</button></div>
                    <div class="metric-label">Growth Opportunity ({store_data['good_opportunity']['percentage']:.1f}%)</div>
                    <div class="metric-description">Stores with moderate sales opportunities for improvement.</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value">{store_data['major_opportunity']['count']} stores <button class="info-button" onclick="showExplanation('optimization-needed')">ℹ️</button></div>
                    <div class="metric-label">Optimization Needed ({store_data['major_opportunity']['percentage']:.1f}%)</div>
                    <div class="metric-description">Stores requiring immediate attention with significant opportunities.</div>
                </div>'''
    
    # Replace the store performance section
    pattern = r'<div class="metric-card">.*?<div class="metric-value">0 stores.*?</div>\s*<div class="metric-card">.*?<div class="metric-value">139 stores.*?</div>\s*<div class="metric-card">.*?<div class="metric-value">1422 stores.*?</div>\s*<div class="metric-card">.*?<div class="metric-value">686 stores.*?</div>'
    html_content = re.sub(pattern, new_store_performance, html_content, flags=re.DOTALL)
    
    # Create complete explanations with ALL stores
    complete_explanations = f'''
        const explanations = {{
            'optimization-needed': {{
                title: 'Optimization Needed Stores',
                content: `
                    <div class="explanation-content">
                        <p><strong>Analysis Method:</strong> Rule 12 - Sales Performance Gap Analysis</p>
                        <p><strong>Classification:</strong> Stores with significant sales opportunities (major_opportunity)</p>
                        <p><strong>Criteria:</strong> High Z-scores indicating substantial gaps vs cluster top 90th percentile</p>
                        <p><strong>Total Stores:</strong> {store_data['major_opportunity']['count']} stores ({store_data['major_opportunity']['percentage']:.1f}% of analyzed stores)</p>
                        
                        <div class="store-section">
                            <p><strong>All Store IDs:</strong></p>
                            {create_store_grid(store_data['major_opportunity']['stores'])}
                        </div>
                        
                        <p><strong>Business Impact:</strong> These stores show the highest potential for sales growth through targeted interventions.</p>
                    </div>
                `
            }},
            'growth-opportunity': {{
                title: 'Growth Opportunity Stores', 
                content: `
                    <div class="explanation-content">
                        <p><strong>Analysis Method:</strong> Rule 12 - Sales Performance Gap Analysis</p>
                        <p><strong>Classification:</strong> Stores with moderate sales opportunities (good_opportunity)</p>
                        <p><strong>Criteria:</strong> Moderate Z-scores indicating achievable improvement opportunities</p>
                        <p><strong>Total Stores:</strong> {store_data['good_opportunity']['count']} stores ({store_data['good_opportunity']['percentage']:.1f}% of analyzed stores)</p>
                        
                        <div class="store-section">
                            <p><strong>All Store IDs:</strong></p>
                            {create_store_grid(store_data['good_opportunity']['stores'])}
                        </div>
                        
                        <p><strong>Business Impact:</strong> These stores represent solid opportunities for incremental sales improvements.</p>
                    </div>
                `
            }},
            'insufficient-data': {{
                title: 'Insufficient Data Stores',
                content: `
                    <div class="explanation-content">
                        <p><strong>Analysis Method:</strong> Rule 12 - Sales Performance Gap Analysis</p>
                        <p><strong>Classification:</strong> Stores with insufficient data (no_data)</p>
                        <p><strong>Criteria:</strong> Zero categories analyzed due to data limitations</p>
                        <p><strong>Total Stores:</strong> {store_data['no_data']['count']} stores ({store_data['no_data']['percentage']:.1f}% of analyzed stores)</p>
                        
                        <div class="store-section">
                            <p><strong>All Store IDs:</strong></p>
                            {create_store_grid(store_data['no_data']['stores'])}
                        </div>
                        
                        <p><strong>Business Impact:</strong> These stores require data collection improvements before performance optimization.</p>
                    </div>
                `
            }},
            'not-available': {{
                title: 'Top Performers - Not Available',
                content: `
                    <div class="explanation-content">
                        <p><strong>Why No Top Performers?</strong></p>
                        <p>Rule 12 is specifically designed to identify <strong>performance gaps and improvement opportunities</strong>, not to highlight top-performing stores.</p>
                        
                        <p><strong>Analysis Focus:</strong></p>
                        <ul>
                            <li>Identifies stores underperforming vs cluster benchmarks</li>
                            <li>Quantifies sales opportunity gaps using Z-score analysis</li>
                            <li>Recommends quantity increases for specific categories</li>
                            <li>Focuses on stores that need improvement, not those already performing well</li>
                        </ul>
                        
                        <p><strong>Business Logic:</strong> A store performing at or above cluster benchmarks would not appear in Rule 12 results, as there would be no identified "opportunity gap" to address.</p>
                        
                        <p><strong>For Top Performer Analysis:</strong> Consider using different metrics such as absolute sales volume, growth rates, or profitability measures rather than gap analysis.</p>
                    </div>
                `
            }}
        }};'''
    
    # Replace the explanations object
    pattern = r'const explanations = \{.*?\};'
    html_content = re.sub(pattern, complete_explanations, html_content, flags=re.DOTALL)
    
    # Add CSS for better store grid display and pagination
    additional_css = '''
        .store-grid-container {
            margin: 15px 0;
        }
        
        .store-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
            gap: 8px;
            max-height: 400px;
            overflow-y: auto;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        
        .store-badge {
            background: #007bff;
            color: white;
            padding: 6px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-align: center;
            display: inline-block;
            min-width: 60px;
        }
        
        .pagination-controls {
            text-align: center;
            margin-top: 15px;
        }
        
        .show-more-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        
        .show-more-btn:hover {
            background: #218838;
        }
        
        .store-count {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            margin-top: 10px;
        }
    '''
    
    # Add CSS before closing </style> tag
    html_content = html_content.replace('</style>', additional_css + '\n    </style>')
    
    # Add JavaScript function for showing all stores
    show_all_stores_js = '''
        function showAllStores(button, allStoreBadges) {
            const grid = button.parentElement.previousElementSibling;
            grid.innerHTML = allStoreBadges.join(' ');
            button.parentElement.innerHTML = '<p class="store-count">Showing all stores</p>';
        }
    '''
    
    # Add JavaScript before closing </script> tag
    html_content = html_content.replace('</script>', show_all_stores_js + '\n    </script>')
    
    # Save the updated file
    with open('AI_Store_Planning_Executive_Presentation.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Presentation fixed with:")
    print("   • Corrected button IDs to match explanations object")
    print("   • Fixed category labels (139 stores = 'Insufficient Data', not 'Performing Well')")
    print("   • Complete store lists (all stores visible, not truncated)")
    print("   • Proper scrolling for long lists")
    print("   • Pagination controls for very large lists")

def main():
    """Main execution function."""
    print("🔧 Fixing Info Buttons and Complete Store Lists")
    print("=" * 50)
    
    try:
        # Get complete store data
        store_data = get_complete_store_data()
        
        # Fix the presentation
        fix_presentation_html(store_data)
        
        print(f"\n✅ All fixes completed!")
        print(f"\n📊 Summary:")
        print(f"   • Top Performers: 0 stores (0.0%) - Category not available")
        print(f"   • Insufficient Data: {store_data['no_data']['count']} stores ({store_data['no_data']['percentage']:.1f}%)")
        print(f"   • Growth Opportunity: {store_data['good_opportunity']['count']} stores ({store_data['good_opportunity']['percentage']:.1f}%)")  
        print(f"   • Optimization Needed: {store_data['major_opportunity']['count']} stores ({store_data['major_opportunity']['percentage']:.1f}%)")
        print(f"\n🎯 Now all info buttons work and show complete store lists!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    main() 