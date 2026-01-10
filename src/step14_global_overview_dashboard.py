#!/usr/bin/env python3
"""
Step 14: Global Overview Dashboard Generator (Enhanced for SPU-Level Analysis)

Creates a comprehensive global overview dashboard showing high-level insights
across all rules, clusters, and stores with executive-level summaries.
Now supports both subcategory and SPU-level analysis with enhanced granularity.

Features:
- Executive summary with key KPIs
- Rule violation breakdown (subcategory vs SPU-level)
- Cluster performance matrix
- Geographic distribution overview
- Opportunity prioritization matrix
- Actionable insights and recommendations
- SPU-level granular analysis capabilities

Author: Analytics Team
Date: 2025-06-15
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configuration - Enhanced for SPU-level analysis
ANALYSIS_LEVEL = "spu"  # Options: "subcategory", "spu"
# To switch to subcategory analysis, change ANALYSIS_LEVEL to "subcategory"

# File paths based on analysis level
if ANALYSIS_LEVEL == "spu":
    CONSOLIDATED_RESULTS_FILE = "output/consolidated_spu_rule_results.csv"
    RULE7_DETAILS_FILE = "output/rule7_missing_spu_results.csv"
    RULE8_DETAILS_FILE = "output/rule8_imbalanced_spu_results.csv"
    RULE9_DETAILS_FILE = "output/rule9_below_minimum_spu_results.csv"
    RULE10_DETAILS_FILE = "output/rule10_smart_overcapacity_spu_results.csv"
    RULE11_DETAILS_FILE = "output/rule11_missed_sales_opportunity_spu_results.csv"
    RULE12_DETAILS_FILE = "output/rule12_sales_performance_spu_results.csv"
    OUTPUT_FILE = "output/global_overview_spu_dashboard.html"
else:
    CONSOLIDATED_RESULTS_FILE = "output/consolidated_rule_results.csv"
    RULE7_DETAILS_FILE = "output/rule7_missing_category_results.csv"
    RULE8_DETAILS_FILE = "output/rule8_imbalanced_results.csv"
    RULE9_DETAILS_FILE = "output/rule9_below_minimum_results.csv"
    RULE10_DETAILS_FILE = "output/rule10_smart_overcapacity_results.csv"
    RULE11_DETAILS_FILE = "output/rule11_missed_sales_opportunity_results.csv"
    RULE12_DETAILS_FILE = "output/rule12_sales_performance_results.csv"
    OUTPUT_FILE = "output/global_overview_dashboard.html"

# Common files
COORDINATES_FILE = "data/store_coordinates_extended.csv"
CLUSTER_RESULTS_FILE = "pipeline/steps/output/clustering_results.csv"

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_all_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
    """
    Load all required data for the global overview.
    
    Returns:
        Tuple of (consolidated_df, coordinates_df, cluster_df, rule_details)
    """
    log_progress(f"Loading data for global overview ({ANALYSIS_LEVEL.upper()} level)...")
    
    # Load consolidated results
    consolidated_df = pd.read_csv(CONSOLIDATED_RESULTS_FILE, dtype={'str_code': str})
    log_progress(f"Loaded consolidated {ANALYSIS_LEVEL} results for {len(consolidated_df):,} stores")
    
    # Load coordinates
    coordinates_df = pd.DataFrame()
    if os.path.exists(COORDINATES_FILE):
        coordinates_df = pd.read_csv(COORDINATES_FILE, dtype={'str_code': str})
        log_progress(f"Loaded coordinates for {len(coordinates_df):,} stores")
    
    # Load cluster data (if exists)
    cluster_df = pd.DataFrame()
    if os.path.exists(CLUSTER_RESULTS_FILE):
        cluster_df = pd.read_csv(CLUSTER_RESULTS_FILE, dtype={'str_code': str})
        log_progress(f"Loaded cluster data for {len(cluster_df):,} stores")
    
    # Load detailed rule results
    rule_details = {}
    detail_files = {
        'rule7': RULE7_DETAILS_FILE,
        'rule8': RULE8_DETAILS_FILE,
        'rule9': RULE9_DETAILS_FILE,
        'rule10': RULE10_DETAILS_FILE,
        'rule11': RULE11_DETAILS_FILE,
        'rule12': RULE12_DETAILS_FILE
    }
    
    for rule_name, file_path in detail_files.items():
        if os.path.exists(file_path):
            rule_details[rule_name] = pd.read_csv(file_path, dtype={'str_code': str})
            log_progress(f"Loaded {rule_name} {ANALYSIS_LEVEL} details: {len(rule_details[rule_name]):,} stores")
    
    return consolidated_df, coordinates_df, cluster_df, rule_details

def calculate_global_metrics(consolidated_df: pd.DataFrame, rule_details: Dict) -> Dict:
    """
    Calculate global KPIs and metrics with SPU-level support.
    
    Args:
        consolidated_df: Consolidated rule results
        rule_details: Detailed rule data
        
    Returns:
        Dictionary with global metrics
    """
    log_progress(f"Calculating global metrics ({ANALYSIS_LEVEL} level)...")
    
    total_stores = len(consolidated_df)
    
    # Determine column naming based on analysis level
    if ANALYSIS_LEVEL == "spu":
        # SPU-level column names
        rule_flag_columns = {
            'rule7_missing_category': 'rule7_missing_spu',
            'rule8_imbalanced': 'rule8_imbalanced_spu', 
            'rule9_below_minimum': 'rule9_below_minimum_spu',
            'rule10_smart_overcapacity_strict': 'rule10_smart_overcapacity_strict',
            'rule10_smart_overcapacity_standard': 'rule10_smart_overcapacity_standard',
            'rule10_smart_overcapacity_lenient': 'rule10_smart_overcapacity_lenient',
            'rule11_missed_sales_opportunity': 'rule11_missed_sales_opportunity',
            'rule11_cluster_underperformance': 'rule11_cluster_relative_underperformance',
            'rule11_cluster_misjudgment': 'rule11_cluster_misjudgment',
            'rule12_sales_performance': 'rule12_sales_performance'
        }
        violation_col = 'total_spu_rule_violations'
        unreasonable_col = 'overall_spu_unreasonable'
    else:
        # Subcategory-level column names
        rule_flag_columns = {
            'rule7_missing_category': 'rule7_missing_category',
            'rule8_imbalanced': 'rule8_imbalanced',
            'rule9_below_minimum': 'rule9_below_minimum',
            'rule10_smart_overcapacity_strict': 'rule10_smart_overcapacity_strict',
            'rule10_smart_overcapacity_standard': 'rule10_smart_overcapacity_standard',
            'rule10_smart_overcapacity_lenient': 'rule10_smart_overcapacity_lenient',
            'rule11_missed_sales_opportunity': 'rule11_missed_sales_opportunity',
            'rule11_cluster_underperformance': 'rule11_cluster_relative_underperformance',
            'rule11_cluster_misjudgment': 'rule11_cluster_misjudgment',
            'rule12_sales_performance': 'rule12_sales_performance'
        }
        violation_col = 'total_rule_violations'
        unreasonable_col = 'overall_unreasonable'
    
    # Rule violation metrics with multi-profile support
    rule_counts = {}
    for rule_key, col_name in rule_flag_columns.items():
        rule_counts[rule_key] = consolidated_df[col_name].sum() if col_name in consolidated_df.columns else 0
    
    # Backward compatibility - use standard profile or legacy column for rule10
    rule_counts['rule10_smart_overcapacity'] = rule_counts['rule10_smart_overcapacity_standard'] or (
        consolidated_df['rule10_smart_overcapacity'].sum() if 'rule10_smart_overcapacity' in consolidated_df.columns else 0
    )
    
    # Overall metrics
    stores_with_violations = consolidated_df[unreasonable_col].sum() if unreasonable_col in consolidated_df.columns else 0
    total_violations = consolidated_df[violation_col].sum() if violation_col in consolidated_df.columns else 0
    avg_violations_per_store = total_violations / total_stores if total_stores > 0 else 0
    
    # Severity analysis
    violation_distribution = {}
    if violation_col in consolidated_df.columns:
        violation_distribution = consolidated_df[violation_col].value_counts().sort_index().to_dict()
    
    # Geographic clusters (if available)
    cluster_metrics = {}
    if 'Cluster' in consolidated_df.columns and violation_col in consolidated_df.columns:
        cluster_summary = consolidated_df.groupby('Cluster').agg({
            'str_code': 'count',
            violation_col: ['sum', 'mean'],
            unreasonable_col: 'sum'
        }).round(2)
        cluster_metrics = cluster_summary.to_dict()
    
    # Enhanced opportunity analysis for SPU-level
    opportunity_metrics = {}
    
    # Rule 7: Missing Categories/SPUs
    if 'rule7' in rule_details:
        if ANALYSIS_LEVEL == "spu":
            if 'missing_spu_count' in rule_details['rule7'].columns:
                opportunity_metrics['missing_category_count'] = rule_details['rule7']['missing_spu_count'].sum()
            if 'total_opportunity_value' in rule_details['rule7'].columns:
                opportunity_metrics['missing_category_value'] = rule_details['rule7']['total_opportunity_value'].sum()
        else:
            if 'missing_categories_count' in rule_details['rule7'].columns:
                opportunity_metrics['missing_category_count'] = rule_details['rule7']['missing_categories_count'].sum()
            if 'total_opportunity_value' in rule_details['rule7'].columns:
                opportunity_metrics['missing_category_value'] = rule_details['rule7']['total_opportunity_value'].sum()
    
    # Rule 8: Imbalanced Allocations
    if 'rule8' in rule_details:
        if ANALYSIS_LEVEL == "spu":
            if 'imbalanced_spu_count' in rule_details['rule8'].columns:
                opportunity_metrics['imbalanced_categories'] = rule_details['rule8']['imbalanced_spu_count'].sum()
            if 'total_adjustment_needed' in rule_details['rule8'].columns:
                opportunity_metrics['imbalanced_adjustments'] = rule_details['rule8']['total_adjustment_needed'].sum()
        else:
            if 'imbalanced_categories_count' in rule_details['rule8'].columns:
                opportunity_metrics['imbalanced_categories'] = rule_details['rule8']['imbalanced_categories_count'].sum()
            if 'total_adjustment_needed' in rule_details['rule8'].columns:
                opportunity_metrics['imbalanced_adjustments'] = rule_details['rule8']['total_adjustment_needed'].sum()
    
    # Rule 9: Below Minimum
    if 'rule9' in rule_details:
        if ANALYSIS_LEVEL == "spu":
            if 'below_minimum_spu_count' in rule_details['rule9'].columns:
                opportunity_metrics['below_minimum_count'] = rule_details['rule9']['below_minimum_spu_count'].sum()
            if 'total_increase_needed' in rule_details['rule9'].columns:
                opportunity_metrics['below_minimum_increase'] = rule_details['rule9']['total_increase_needed'].sum()
        else:
            if 'below_minimum_count' in rule_details['rule9'].columns:
                opportunity_metrics['below_minimum_count'] = rule_details['rule9']['below_minimum_count'].sum()
            if 'total_increase_needed' in rule_details['rule9'].columns:
                opportunity_metrics['below_minimum_increase'] = rule_details['rule9']['total_increase_needed'].sum()
    
    # Rule 10: Smart Overcapacity (multi-profile)
    if 'rule10' in rule_details:
        # Use standard profile for primary metrics
        if 'rule10_reallocation_suggested_standard' in rule_details['rule10'].columns:
            opportunity_metrics['overcapacity_reallocation'] = rule_details['rule10']['rule10_reallocation_suggested_standard'].sum()
            opportunity_metrics['overcapacity_opportunities'] = rule_details['rule10']['rule10_opportunities_count_standard'].sum()
        elif 'total_reallocation_suggested' in rule_details['rule10'].columns:  # Backward compatibility
            opportunity_metrics['overcapacity_reallocation'] = rule_details['rule10']['total_reallocation_suggested'].sum()
            opportunity_metrics['overcapacity_opportunities'] = rule_details['rule10']['overcapacity_opportunities_count'].sum()
    
    # Rule 11: Missed Sales Opportunity
    if 'rule11' in rule_details:
        if 'rule11_potential_sales_increase' in rule_details['rule11'].columns:
            opportunity_metrics['missed_sales_potential'] = rule_details['rule11']['rule11_potential_sales_increase'].sum()
        if 'rule11_opportunities_count' in rule_details['rule11'].columns:
            opportunity_metrics['missed_sales_opportunities'] = rule_details['rule11']['rule11_opportunities_count'].sum()
    
    # Rule 12: Sales Performance (multi-level)
    if 'rule12' in rule_details:
        # Performance level breakdown
        performance_levels = ['top_performer', 'performing_well', 'some_opportunity', 'good_opportunity', 'major_opportunity']
        performance_breakdown = {}
        for level in performance_levels:
            level_col = f'rule12_{level}'
            if level_col in rule_details['rule12'].columns:
                performance_breakdown[level] = rule_details['rule12'][level_col].sum()
        
        opportunity_metrics['sales_performance_breakdown'] = performance_breakdown
        
        # Total opportunities (good + major)
        total_opportunities = performance_breakdown.get('good_opportunity', 0) + performance_breakdown.get('major_opportunity', 0)
        opportunity_metrics['sales_performance_opportunities'] = total_opportunities
    
    return {
        'overview': {
            'total_stores': total_stores,
            'stores_with_violations': stores_with_violations,
            'violation_rate': round((stores_with_violations / total_stores) * 100, 1) if total_stores > 0 else 0,
            'total_violations': total_violations,
            'avg_violations_per_store': round(avg_violations_per_store, 2),
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'analysis_level': ANALYSIS_LEVEL.upper()
        },
        'rule_counts': rule_counts,
        'rule_percentages': {k: round((v / total_stores) * 100, 1) if total_stores > 0 else 0 for k, v in rule_counts.items()},
        'violation_distribution': violation_distribution,
        'cluster_metrics': cluster_metrics,
        'opportunity_metrics': opportunity_metrics
    }

def create_executive_summary_charts(metrics: Dict) -> List[go.Figure]:
    """Create executive summary visualizations with SPU-level enhancements."""
    log_progress("Creating executive summary charts...")
    
    charts = []
    
    # 1. Rule Violation Overview (Pie Chart)
    rule_labels = [
        f'Missing {ANALYSIS_LEVEL.title()}s (Rule 7)',
        'Imbalanced Allocations (Rule 8)', 
        'Below Minimum (Rule 9)',
        'Smart Overcapacity (Rule 10)',
        'Missed Sales Opportunities (Rule 11)',
        'Sales Performance Issues (Rule 12)'
    ]
    
    rule_values = [
        metrics['rule_counts']['rule7_missing_category'],
        metrics['rule_counts']['rule8_imbalanced'],
        metrics['rule_counts']['rule9_below_minimum'],
        metrics['rule_counts']['rule10_smart_overcapacity'],
        metrics['rule_counts']['rule11_missed_sales_opportunity'],
        metrics['rule_counts']['rule12_sales_performance']
    ]
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFA07A', '#DDA0DD']
    
    fig1 = go.Figure(data=[go.Pie(
        labels=rule_labels,
        values=rule_values,
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent+value',
        textposition='outside'
    )])
    
    fig1.update_layout(
        title=f'{ANALYSIS_LEVEL.title()}-Level Rule Violation Distribution',
        font=dict(size=12),
        showlegend=True,
        height=500
    )
    charts.append(fig1)
    
    # 2. Violation Severity Distribution (Bar Chart)
    if metrics['violation_distribution']:
        violation_counts = list(metrics['violation_distribution'].keys())
        violation_frequencies = list(metrics['violation_distribution'].values())
        
        fig2 = go.Figure(data=[go.Bar(
            x=[f'{count} Violations' for count in violation_counts],
            y=violation_frequencies,
            marker_color='#3498db',
            text=violation_frequencies,
            textposition='auto'
        )])
        
        fig2.update_layout(
            title=f'{ANALYSIS_LEVEL.title()}-Level Violation Severity Distribution',
            xaxis_title='Number of Rule Violations per Store',
            yaxis_title='Number of Stores',
            height=400
        )
        charts.append(fig2)
    
    # 3. Rule Performance Comparison (Horizontal Bar)
    rule_names = ['Rule 7', 'Rule 8', 'Rule 9', 'Rule 10', 'Rule 11', 'Rule 12']
    rule_percentages = [
        metrics['rule_percentages']['rule7_missing_category'],
        metrics['rule_percentages']['rule8_imbalanced'],
        metrics['rule_percentages']['rule9_below_minimum'],
        metrics['rule_percentages']['rule10_smart_overcapacity'],
        metrics['rule_percentages']['rule11_missed_sales_opportunity'],
        metrics['rule_percentages']['rule12_sales_performance']
    ]
    
    fig3 = go.Figure(data=[go.Bar(
        y=rule_names,
        x=rule_percentages,
        orientation='h',
        marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFA07A', '#DDA0DD'],
        text=[f'{pct}%' for pct in rule_percentages],
        textposition='auto'
    )])
    
    fig3.update_layout(
        title=f'{ANALYSIS_LEVEL.title()}-Level Rule Violation Rates',
        xaxis_title='Percentage of Stores Affected (%)',
        yaxis_title='Business Rules',
        height=400
    )
    charts.append(fig3)
    
    # 4. SPU-Level Sales Performance Breakdown (if Rule 12 data available)
    if 'sales_performance_breakdown' in metrics['opportunity_metrics']:
        performance_data = metrics['opportunity_metrics']['sales_performance_breakdown']
        
        if performance_data:
            performance_labels = [label.replace('_', ' ').title() for label in performance_data.keys()]
            performance_values = list(performance_data.values())
            
            # Color scheme for performance levels
            performance_colors = {
                'Top Performer': '#2ECC71',      # Green
                'Performing Well': '#3498DB',    # Blue  
                'Some Opportunity': '#F39C12',   # Orange
                'Good Opportunity': '#E74C3C',   # Red
                'Major Opportunity': '#8E44AD'   # Purple
            }
            
            colors = [performance_colors.get(label, '#95A5A6') for label in performance_labels]
            
            fig4 = go.Figure(data=[go.Bar(
                x=performance_labels,
                y=performance_values,
                marker_color=colors,
                text=performance_values,
                textposition='auto'
            )])
            
            fig4.update_layout(
                title=f'{ANALYSIS_LEVEL.title()}-Level Sales Performance Classification',
                xaxis_title='Performance Level',
                yaxis_title='Number of Stores',
                height=400
            )
            charts.append(fig4)
    
    return charts

def create_cluster_performance_matrix(consolidated_df: pd.DataFrame) -> Optional[go.Figure]:
    """Create cluster performance matrix with SPU-level support."""
    if 'Cluster' not in consolidated_df.columns:
        return None
    
    log_progress("Creating cluster performance matrix...")
    
    # Determine violation column based on analysis level
    violation_col = 'total_spu_rule_violations' if ANALYSIS_LEVEL == "spu" else 'total_rule_violations'
    unreasonable_col = 'overall_spu_unreasonable' if ANALYSIS_LEVEL == "spu" else 'overall_unreasonable'
    
    if violation_col not in consolidated_df.columns:
        return None
    
    # Calculate cluster metrics
    cluster_summary = consolidated_df.groupby('Cluster').agg({
        'str_code': 'count',
        violation_col: ['sum', 'mean'],
        unreasonable_col: ['sum', lambda x: (x.sum() / len(x)) * 100]
    }).round(2)
    
    cluster_summary.columns = ['store_count', 'total_violations', 'avg_violations', 'flagged_stores', 'flagged_percentage']
    cluster_summary = cluster_summary.reset_index()
    
    # Create scatter plot
    fig = go.Figure()
    
    # Add scatter points
    fig.add_trace(go.Scatter(
        x=cluster_summary['avg_violations'],
        y=cluster_summary['flagged_percentage'],
        mode='markers+text',
        marker=dict(
            size=cluster_summary['store_count'] / 2,  # Size based on store count
            color=cluster_summary['total_violations'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Total Violations")
        ),
        text=cluster_summary['Cluster'],
        textposition='middle center',
        hovertemplate='<b>Cluster %{text}</b><br>' +
                      'Stores: %{marker.size}<br>' +
                      'Avg Violations: %{x}<br>' +
                      'Flagged Rate: %{y}%<br>' +
                      '<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'{ANALYSIS_LEVEL.title()}-Level Cluster Performance Matrix',
        xaxis_title='Average Violations per Store',
        yaxis_title='Percentage of Stores Flagged (%)',
        height=500,
        showlegend=False
    )
    
    return fig

def generate_dashboard_html(metrics: Dict, charts: List[go.Figure], 
                           cluster_chart: Optional[go.Figure] = None) -> str:
    """Generate comprehensive HTML dashboard with SPU-level enhancements."""
    log_progress("Generating HTML dashboard...")
    
    # Convert charts to HTML
    chart_htmls = []
    for chart in charts:
        chart_html = chart.to_html(full_html=False, include_plotlyjs='cdn')
        chart_htmls.append(chart_html)
    
    cluster_chart_html = ""
    if cluster_chart:
        cluster_chart_html = cluster_chart.to_html(full_html=False, include_plotlyjs='cdn')
    
    # Analysis level specific content
    analysis_level_display = metrics['overview']['analysis_level']
    analysis_description = {
        'SPU': 'Individual Stock Keeping Unit (SPU) Level Analysis - Maximum Granularity',
        'SUBCATEGORY': 'Category-Level Analysis - Aggregated View'
    }.get(analysis_level_display, 'Multi-Level Analysis')
    
    # Rule 12 performance breakdown for insights
    performance_insights = ""
    if 'sales_performance_breakdown' in metrics['opportunity_metrics']:
        perf_data = metrics['opportunity_metrics']['sales_performance_breakdown']
        some_opp = perf_data.get('some_opportunity', 0)
        good_opp = perf_data.get('good_opportunity', 0)
        top_perf = perf_data.get('top_performer', 0)
        performing_well = perf_data.get('performing_well', 0)
        
        performance_insights = f"""
                <div class="insight-card">
                    <h4>🎯 {analysis_level_display}-Level Sales Performance</h4>
                    <p><strong>{some_opp:,} stores</strong> have "Some Opportunity" for improvement, while <strong>{good_opp:,} stores</strong> have "Good Opportunity". 
                    <strong>{top_perf:,} stores</strong> are top performers and <strong>{performing_well:,} stores</strong> are performing well.</p>
                </div>"""
    
    # Generate comprehensive HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{analysis_level_display}-Level Global Store Analysis Overview</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            margin-top: 20px;
            margin-bottom: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}

        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin: -20px -20px 40px -20px;
        }}

        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}

        .subtitle {{
            font-size: 1.2em;
            margin-top: 10px;
            opacity: 0.9;
        }}

        .analysis-level {{
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 20px;
            margin-top: 15px;
            font-weight: 600;
            font-size: 1.1em;
        }}

        .executive-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .kpi-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 5px solid #3498db;
        }}

        .kpi-card.primary {{ border-left-color: #3498db; }}
        .kpi-card.success {{ border-left-color: #2ecc71; }}
        .kpi-card.warning {{ border-left-color: #f39c12; }}
        .kpi-card.danger {{ border-left-color: #e74c3c; }}

        .kpi-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }}

        .kpi-label {{
            font-size: 1.1em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .section {{
            margin-bottom: 50px;
        }}

        .section h2 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}

        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}

        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}

        .insight-card {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #3498db;
        }}

        .insight-card h4 {{
            margin-top: 0;
            color: #2c3e50;
        }}

        .rule-breakdown {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .rule-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid #e9ecef;
        }}

        .rule-card.rule5 {{ border-color: #FF6B6B; }}
        .rule-card.rule6 {{ border-color: #4ECDC4; }}
        .rule-card.rule7 {{ border-color: #45B7D1; }}
        .rule-card.rule8 {{ border-color: #96CEB4; }}
        .rule-card.rule9 {{ border-color: #FFA07A; }}
        .rule-card.rule12 {{ border-color: #DDA0DD; }}
        .rule-card.supplementary {{ border-color: #9370DB; background: #f5f3ff; }}

        .rule-count {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .rule-percentage {{
            font-size: 1.2em;
            color: #7f8c8d;
            margin-bottom: 10px;
        }}

        .rule-label {{
            font-weight: 600;
            color: #2c3e50;
        }}

        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            margin-top: 40px;
            font-style: italic;
        }}

        .spu-highlight {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 Global Store Analysis Overview</h1>
            <p class="subtitle">Executive Dashboard - Comprehensive Store Performance Analysis</p>
            <div class="analysis-level">{analysis_description}</div>
            <p>Analysis Date: {metrics['overview']['analysis_date']} | Level: <span class="spu-highlight">{analysis_level_display}</span></p>
        </div>

        <!-- Executive Summary KPIs -->
        <div class="executive-summary">
            <div class="kpi-card primary">
                <div class="kpi-value">{metrics['overview']['total_stores']:,}</div>
                <div class="kpi-label">Total Stores</div>
            </div>
            <div class="kpi-card danger">
                <div class="kpi-value">{metrics['overview']['stores_with_violations']:,}</div>
                <div class="kpi-label">Stores with Violations</div>
            </div>
            <div class="kpi-card warning">
                <div class="kpi-value">{metrics['overview']['violation_rate']}%</div>
                <div class="kpi-label">Violation Rate</div>
            </div>
            <div class="kpi-card success">
                <div class="kpi-value">{metrics['overview']['avg_violations_per_store']}</div>
                <div class="kpi-label">Avg Violations/Store</div>
            </div>
        </div>

        <!-- Rule Breakdown -->
        <div class="section">
            <h2>📊 {analysis_level_display}-Level Rule Violation Breakdown</h2>
            <div class="rule-breakdown">
                <div class="rule-card rule5">
                    <div class="rule-count">{metrics['rule_counts']['rule7_missing_category']:,}</div>
                    <div class="rule-percentage">{metrics['rule_percentages']['rule7_missing_category']}%</div>
                    <div class="rule-label">Missing {'SPUs' if analysis_level_display == 'SPU' else 'Categories'}</div>
                </div>
                <div class="rule-card rule6">
                    <div class="rule-count">{metrics['rule_counts']['rule8_imbalanced']:,}</div>
                    <div class="rule-percentage">{metrics['rule_percentages']['rule8_imbalanced']}%</div>
                    <div class="rule-label">Imbalanced Allocations</div>
                </div>
                <div class="rule-card rule7">
                    <div class="rule-count">{metrics['rule_counts']['rule9_below_minimum']:,}</div>
                    <div class="rule-percentage">{metrics['rule_percentages']['rule9_below_minimum']}%</div>
                    <div class="rule-label">Below Minimum</div>
                </div>
                <div class="rule-card rule8">
                    <div class="rule-count">{metrics['rule_counts']['rule10_smart_overcapacity']:,}</div>
                    <div class="rule-percentage">{metrics['rule_percentages']['rule10_smart_overcapacity']}%</div>
                    <div class="rule-label">Smart Overcapacity</div>
                </div>
                <div class="rule-card rule9">
                    <div class="rule-count">{metrics['rule_counts']['rule11_missed_sales_opportunity']:,}</div>
                    <div class="rule-percentage">{metrics['rule_percentages']['rule11_missed_sales_opportunity']}%</div>
                    <div class="rule-label">Missed Sales Opportunities</div>
                </div>
                <div class="rule-card rule12">
                    <div class="rule-count">{metrics['rule_counts']['rule12_sales_performance']:,}</div>
                    <div class="rule-percentage">{metrics['rule_percentages']['rule12_sales_performance']}%</div>
                    <div class="rule-label">Sales Performance Issues</div>
                </div>
            </div>
            
            <!-- Supplementary Measures for Cluster Analysis -->
            <h3>🔍 Supplementary Cluster Analysis Measures</h3>
            <div class="rule-breakdown">
                <div class="rule-card supplementary">
                    <div class="rule-count">{metrics['rule_counts']['rule11_cluster_underperformance']:,}</div>
                    <div class="rule-percentage">{metrics['rule_percentages']['rule11_cluster_underperformance']}%</div>
                    <div class="rule-label">Cluster Underperformance</div>
                    <div style="font-size: 0.8em; color: #7f8c8d; margin-top: 5px;">Stores performing below cluster average</div>
                </div>
                <div class="rule-card supplementary">
                    <div class="rule-count">{metrics['rule_counts']['rule11_cluster_misjudgment']:,}</div>
                    <div class="rule-percentage">{metrics['rule_percentages']['rule11_cluster_misjudgment']}%</div>
                    <div class="rule-label">Cluster Misjudgment</div>
                    <div style="font-size: 0.8em; color: #7f8c8d; margin-top: 5px;">Stores in potentially problematic clusters</div>
                </div>
            </div>
        </div>

        <!-- Visualizations -->
        <div class="section">
            <h2>📈 Key Performance Visualizations</h2>
            
            {''.join(f'<div class="chart-container">{chart_html}</div>' for chart_html in chart_htmls)}
            
            {f'<div class="chart-container">{cluster_chart_html}</div>' if cluster_chart_html else ''}
        </div>

        <!-- Insights & Recommendations -->
        <div class="section">
            <h2>💡 Key Insights & Recommendations</h2>
            <div class="insights-grid">
                <div class="insight-card">
                    <h4>🎯 Primary Focus Areas</h4>
                    <p>Smart Overcapacity affects {metrics['rule_percentages']['rule10_smart_overcapacity']}% of stores, indicating significant optimization potential. Imbalanced allocations affect {metrics['rule_percentages']['rule8_imbalanced']}% of stores at the {analysis_level_display.lower()} level.</p>
                </div>
                <div class="insight-card">
                    <h4>🔍 Optimization Opportunities</h4>
                    <p>With {metrics['overview']['avg_violations_per_store']} average violations per store, there's substantial room for improvement through targeted {analysis_level_display.lower()}-level interventions.</p>
                </div>
                <div class="insight-card">
                    <h4>📍 Missing {'SPU' if analysis_level_display == 'SPU' else 'Category'} Impact</h4>
                    <p>{metrics['rule_percentages']['rule7_missing_category']}% of stores have missing {'SPU' if analysis_level_display == 'SPU' else 'category'} issues, suggesting {'precise product-level' if analysis_level_display == 'SPU' else 'good cluster coverage but specific'} optimization opportunities.</p>
                </div>
                <div class="insight-card">
                    <h4>⚖️ Below Minimum Threshold</h4>
                    <p>{metrics['rule_percentages']['rule9_below_minimum']}% of stores have below minimum allocations at the {analysis_level_display.lower()} level, indicating potential threshold optimization needs.</p>
                </div>
                {performance_insights}
                <div class="insight-card">
                    <h4>🔍 Cluster Analysis Insights</h4>
                    <p>{metrics['rule_percentages']['rule11_cluster_underperformance']}% of stores underperform relative to their cluster peers, while {metrics['rule_percentages']['rule11_cluster_misjudgment']}% are in potentially problematic clusters. These supplementary measures help distinguish store vs cluster issues.</p>
                </div>
                <div class="insight-card">
                    <h4>🚀 {analysis_level_display}-Level Analysis Benefits</h4>
                    <p>{'This SPU-level analysis provides granular, product-specific insights enabling precise inventory optimization and targeted promotional strategies.' if analysis_level_display == 'SPU' else 'This category-level analysis provides aggregated insights for strategic planning and broad optimization initiatives.'}</p>
                </div>
            </div>
        </div>

        <div class="timestamp">
            Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')} | Analysis Level: {analysis_level_display}
        </div>
    </div>
</body>
</html>"""
    
    return html_content

def generate_enhanced_dashboard_with_trendiness():
    """Add trendiness to the global overview dashboard"""
    
    # Import the production integration
    import sys
    sys.path.insert(0, '.')
    from production_trendiness_integration import create_production_dashboard_with_trendiness
    
    # Generate enhanced dashboard
    enhanced_dashboard = create_production_dashboard_with_trendiness()
    
    if enhanced_dashboard:
        print(f"✅ Enhanced dashboard with trendiness: {enhanced_dashboard}")
    
    return enhanced_dashboard

def main() -> None:
    """Main function to generate global overview dashboard with SPU-level support."""
    log_progress(f"Starting Global Overview Dashboard generation ({ANALYSIS_LEVEL.upper()} level)...")
    
    try:
        # Load data
        consolidated_df, coordinates_df, cluster_df, rule_details = load_all_data()
        
        # Merge with cluster data if available
        if not cluster_df.empty:
            consolidated_df = consolidated_df.merge(cluster_df, on='str_code', how='left')
        
        # Calculate metrics
        metrics = calculate_global_metrics(consolidated_df, rule_details)
        
        # Create visualizations
        charts = create_executive_summary_charts(metrics)
        cluster_chart = create_cluster_performance_matrix(consolidated_df)
        
        # Generate dashboard
        html_content = generate_dashboard_html(metrics, charts, cluster_chart)
        
        # Save dashboard
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        log_progress(f"✅ {ANALYSIS_LEVEL.upper()}-Level Global Overview Dashboard saved to {OUTPUT_FILE}")
        log_progress(f"📊 Dashboard includes:")
        log_progress(f"   • Executive KPIs for {metrics['overview']['total_stores']:,} stores")
        log_progress(f"   • {ANALYSIS_LEVEL.upper()}-level rule violation analysis across 6 rules + supplementary measures") 
        log_progress(f"   • {len(charts)} interactive visualizations")
        if cluster_chart:
            log_progress(f"   • {ANALYSIS_LEVEL.upper()}-level cluster performance matrix")
        log_progress(f"   • Strategic insights and recommendations")
        log_progress(f"   • Analysis Level: {ANALYSIS_LEVEL.upper()} (granular {'product-specific' if ANALYSIS_LEVEL == 'spu' else 'category-level'} insights)")
        
        # NEW: Add trendiness enhancement
        generate_enhanced_dashboard_with_trendiness()
        
    except Exception as e:
        log_progress(f"❌ Error generating dashboard: {str(e)}")
        raise

if __name__ == "__main__":
    main() 