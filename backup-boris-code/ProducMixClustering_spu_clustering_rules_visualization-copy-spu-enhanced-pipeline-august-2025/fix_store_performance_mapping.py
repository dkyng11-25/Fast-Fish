#!/usr/bin/env python3
"""
Fix Store Performance Mapping in Executive Presentation

This script corrects the store performance categories to accurately reflect
the Rule 12 sales performance analysis data structure.

Rule 12 Analysis Details:
- Identifies performance gaps and opportunities vs cluster benchmarks
- Does NOT identify "top performers" - focuses on improvement opportunities
- Uses Z-score analysis to quantify sales gaps

Actual Categories:
1. major_opportunity: Stores with significant improvement opportunities (high Z-scores)
2. good_opportunity: Stores with moderate improvement opportunities  
3. no_data: Stores with insufficient data for analysis
4. top_performer: Does not exist in Rule 12 methodology
"""

import pandas as pd
import re
from typing import Dict, List, Tuple
import json

def analyze_rule12_data() -> Dict:
    """Analyze the Rule 12 data to understand actual store distributions."""
    print("📊 Analyzing Rule 12 sales performance data...")
    
    df = pd.read_csv('output/rule12_sales_performance_spu_results.csv')
    
    # Get actual distribution
    distribution = df['store_performance_level'].value_counts().to_dict()
    total_stores = len(df)
    
    # Calculate percentages
    percentages = {level: (count / total_stores * 100) for level, count in distribution.items()}
    
    # Get sample store IDs for each category
    store_samples = {}
    for level in distribution.keys():
        stores = df[df['store_performance_level'] == level]['str_code'].tolist()
        store_samples[level] = stores
    
    analysis = {
        'total_stores': total_stores,
        'distribution': distribution,
        'percentages': percentages,
        'store_samples': store_samples,
        'summary': {
            'major_opportunity': {
                'count': distribution.get('major_opportunity', 0),
                'percentage': percentages.get('major_opportunity', 0),
                'description': 'Stores with significant sales opportunities (high Z-scores)',
                'sample_stores': store_samples.get('major_opportunity', [])[:50]
            },
            'good_opportunity': {
                'count': distribution.get('good_opportunity', 0), 
                'percentage': percentages.get('good_opportunity', 0),
                'description': 'Stores with moderate sales opportunities',
                'sample_stores': store_samples.get('good_opportunity', [])[:50]
            },
            'no_data': {
                'count': distribution.get('no_data', 0),
                'percentage': percentages.get('no_data', 0), 
                'description': 'Stores with insufficient data for performance analysis',
                'sample_stores': store_samples.get('no_data', [])[:50]
            },
            'top_performer': {
                'count': 0,
                'percentage': 0.0,
                'description': 'Category not available - Rule 12 focuses on improvement opportunities',
                'sample_stores': []
            }
        }
    }
    
    print(f"✅ Total stores analyzed: {total_stores}")
    print(f"   • Major opportunities: {distribution.get('major_opportunity', 0)} ({percentages.get('major_opportunity', 0):.1f}%)")
    print(f"   • Good opportunities: {distribution.get('good_opportunity', 0)} ({percentages.get('good_opportunity', 0):.1f}%)")
    print(f"   • No data: {distribution.get('no_data', 0)} ({percentages.get('no_data', 0):.1f}%)")
    print(f"   • Top performers: 0 (0.0%) - Not identified by Rule 12")
    
    return analysis

def update_presentation_with_correct_mapping(analysis: Dict) -> None:
    """Update the presentation with correct store performance mapping."""
    print("\n🔧 Updating presentation with correct mapping...")
    
    # Read current presentation
    with open('AI_Store_Planning_Executive_Presentation.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Correct mapping: Rule 12 categories -> Presentation categories
    # major_opportunity -> Optimization Needed  
    # good_opportunity -> Growth Opportunity
    # no_data -> Insufficient Data
    # top_performer -> Not Available (0 stores)
    
    summary = analysis['summary']
    
    # Update the store performance section with correct data
    new_store_performance = f'''
                <div class="metric-row">
                    <div class="metric-item">
                        <div class="metric-value">{summary["major_opportunity"]["count"]} stores <i class="info-btn" onclick="showExplanation('optimization-needed')">ℹ️</i></div>
                        <div class="metric-label">Optimization Needed ({summary["major_opportunity"]["percentage"]:.1f}%)</div>
                        <div class="metric-description">Stores with significant sales opportunity gaps vs cluster benchmarks.</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{summary["good_opportunity"]["count"]} stores <i class="info-btn" onclick="showExplanation('growth-opportunity')">ℹ️</i></div>
                        <div class="metric-label">Growth Opportunity ({summary["good_opportunity"]["percentage"]:.1f}%)</div>
                        <div class="metric-description">Stores with moderate sales opportunities for improvement.</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{summary["no_data"]["count"]} stores <i class="info-btn" onclick="showExplanation('insufficient-data')">ℹ️</i></div>
                        <div class="metric-label">Insufficient Data ({summary["no_data"]["percentage"]:.1f}%)</div>
                        <div class="metric-description">Stores with limited data for performance analysis.</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">N/A <i class="info-btn" onclick="showExplanation('not-available')">ℹ️</i></div>
                        <div class="metric-label">Top Performers (N/A)</div>
                        <div class="metric-description">Rule 12 focuses on improvement opportunities, not top performer identification.</div>
                    </div>
                </div>'''
    
    # Replace the store performance section
    pattern = r'<div class="metric-row">.*?</div>\s*</div>\s*</div>\s*</div>'
    html_content = re.sub(pattern, new_store_performance + '\n                </div>\n            </div>\n        </div>', html_content, flags=re.DOTALL)
    
    # Update JavaScript explanations with correct data and explanations
    explanations_js = f'''
        const explanations = {{
            'optimization-needed': {{
                title: 'Optimization Needed Stores',
                content: `
                    <div class="explanation-content">
                        <p><strong>Analysis Method:</strong> Rule 12 - Sales Performance Gap Analysis</p>
                        <p><strong>Classification:</strong> Stores with significant sales opportunities (major_opportunity)</p>
                        <p><strong>Criteria:</strong> High Z-scores indicating substantial gaps vs cluster top 90th percentile</p>
                        <p><strong>Total Stores:</strong> {summary["major_opportunity"]["count"]} stores ({summary["major_opportunity"]["percentage"]:.1f}% of analyzed stores)</p>
                        
                        <div class="store-section">
                            <p><strong>Sample Store IDs:</strong></p>
                            <div class="store-grid">
                                {" ".join([f'<span class="store-badge">{store}</span>' for store in summary["major_opportunity"]["sample_stores"][:30]])}
                                {f'<span class="more-indicator">... and {len(summary["major_opportunity"]["sample_stores"]) - 30} more</span>' if len(summary["major_opportunity"]["sample_stores"]) > 30 else ''}
                            </div>
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
                        <p><strong>Total Stores:</strong> {summary["good_opportunity"]["count"]} stores ({summary["good_opportunity"]["percentage"]:.1f}% of analyzed stores)</p>
                        
                        <div class="store-section">
                            <p><strong>Sample Store IDs:</strong></p>
                            <div class="store-grid">
                                {" ".join([f'<span class="store-badge">{store}</span>' for store in summary["good_opportunity"]["sample_stores"][:30]])}
                                {f'<span class="more-indicator">... and {len(summary["good_opportunity"]["sample_stores"]) - 30} more</span>' if len(summary["good_opportunity"]["sample_stores"]) > 30 else ''}
                            </div>
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
                        <p><strong>Total Stores:</strong> {summary["no_data"]["count"]} stores ({summary["no_data"]["percentage"]:.1f}% of analyzed stores)</p>
                        
                        <div class="store-section">
                            <p><strong>Sample Store IDs:</strong></p>
                            <div class="store-grid">
                                {" ".join([f'<span class="store-badge">{store}</span>' for store in summary["no_data"]["sample_stores"][:30]])}
                                {f'<span class="more-indicator">... and {len(summary["no_data"]["sample_stores"]) - 30} more</span>' if len(summary["no_data"]["sample_stores"]) > 30 else ''}
                            </div>
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
    html_content = re.sub(pattern, explanations_js, html_content, flags=re.DOTALL)
    
    # Save updated presentation
    with open('AI_Store_Planning_Executive_Presentation.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Presentation updated with correct store performance mapping")
    print("   • Removed misleading 'Top Performers' category")
    print("   • Added business context explaining Rule 12 methodology")
    print("   • Updated all percentages and store counts to match actual data")
    print("   • Included sample store IDs for each valid category")

def main():
    """Main execution function."""
    print("🔍 Fixing Store Performance Mapping in Executive Presentation")
    print("=" * 60)
    
    try:
        # Analyze the actual Rule 12 data
        analysis = analyze_rule12_data()
        
        # Save analysis for reference
        with open('store_performance_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\n💾 Analysis saved to store_performance_analysis.json")
        
        # Update presentation with correct mapping
        update_presentation_with_correct_mapping(analysis)
        
        print("\n✅ Store performance mapping correction completed!")
        print("\n📋 Summary of Changes:")
        print("   1. Corrected store counts and percentages to match Rule 12 data")
        print("   2. Replaced 'Top Performers' with 'Not Available' explanation")
        print("   3. Added business context for why no top performers exist")
        print("   4. Updated store ID samples for each category")
        print("   5. Clarified Rule 12 methodology and purpose")
        
        print(f"\n📊 Final Distribution:")
        print(f"   • Optimization Needed: {analysis['summary']['major_opportunity']['count']} stores ({analysis['summary']['major_opportunity']['percentage']:.1f}%)")
        print(f"   • Growth Opportunity: {analysis['summary']['good_opportunity']['count']} stores ({analysis['summary']['good_opportunity']['percentage']:.1f}%)")
        print(f"   • Insufficient Data: {analysis['summary']['no_data']['count']} stores ({analysis['summary']['no_data']['percentage']:.1f}%)")
        print(f"   • Top Performers: N/A (Rule 12 focuses on improvement opportunities)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    main() 