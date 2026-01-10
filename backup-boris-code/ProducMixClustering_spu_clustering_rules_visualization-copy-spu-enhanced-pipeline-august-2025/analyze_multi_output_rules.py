#!/usr/bin/env python3
"""
Multi-Output SPU Rules Analysis Tool

This tool analyzes and visualizes the multi-output structure of SPU rules,
showing detailed breakdowns of which SPUs break different rule variants
(Rule 10a, 10b, 10c, etc.) and provides comprehensive insights.

Author: Data Pipeline
Date: 2025-01-27
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Configuration
CONSOLIDATED_FILE = "output/consolidated_spu_rule_results.csv"
OUTPUT_DIR = "output"
VISUALIZATION_DIR = "output/visualizations"

# Create directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(VISUALIZATION_DIR, exist_ok=True)

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_consolidated_data() -> pd.DataFrame:
    """Load consolidated SPU rule results"""
    try:
        df = pd.read_csv(CONSOLIDATED_FILE, dtype={'str_code': str})
        log_progress(f"Loaded consolidated SPU data: {len(df):,} stores")
        return df
    except Exception as e:
        log_progress(f"Error loading consolidated data: {str(e)}")
        raise

def analyze_rule10_multi_profile(df: pd.DataFrame) -> Dict:
    """Analyze Rule 10 SPU Assortment Optimization multi-profile structure"""
    log_progress("Analyzing Rule 10 multi-profile structure...")
    
    profiles = ['conservative', 'standard', 'aggressive']
    issue_types = ['over_assorted', 'under_assorted', 'inefficient_mix']
    
    analysis = {
        'profile_summary': {},
        'issue_type_breakdown': {},
        'profile_overlap': {},
        'detailed_metrics': {}
    }
    
    # Profile summary
    for profile in profiles:
        flagged = df[f'rule10_assortment_issue_{profile}'].sum()
        opportunities = df[f'rule10_opportunities_count_{profile}'].sum()
        total_value = df[f'rule10_total_opportunity_value_{profile}'].sum()
        
        analysis['profile_summary'][profile] = {
            'stores_flagged': int(flagged),
            'total_opportunities': int(opportunities),
            'total_opportunity_value': float(total_value),
            'avg_opportunities_per_store': float(opportunities / len(df)) if len(df) > 0 else 0
        }
    
    # Issue type breakdown by profile
    for profile in profiles:
        analysis['issue_type_breakdown'][profile] = {}
        for issue_type in issue_types:
            count = df[f'rule10_{issue_type}_{profile}'].sum()
            analysis['issue_type_breakdown'][profile][issue_type] = int(count)
    
    # Profile overlap analysis
    for i, profile1 in enumerate(profiles):
        for profile2 in profiles[i+1:]:
            overlap = ((df[f'rule10_assortment_issue_{profile1}'] == 1) & 
                      (df[f'rule10_assortment_issue_{profile2}'] == 1)).sum()
            analysis['profile_overlap'][f'{profile1}_vs_{profile2}'] = {
                'overlap_count': int(overlap),
                'overlap_percentage': float(overlap / len(df) * 100)
            }
    
    # Detailed metrics
    analysis['detailed_metrics'] = {
        'stores_flagged_all_profiles': int(
            ((df['rule10_assortment_issue_conservative'] == 1) & 
             (df['rule10_assortment_issue_standard'] == 1) & 
             (df['rule10_assortment_issue_aggressive'] == 1)).sum()
        ),
        'stores_flagged_conservative_only': int(
            ((df['rule10_assortment_issue_conservative'] == 1) & 
             (df['rule10_assortment_issue_standard'] == 0) & 
             (df['rule10_assortment_issue_aggressive'] == 0)).sum()
        ),
        'avg_efficiency_gaps': {
            profile: float(df[f'rule10_avg_efficiency_gap_{profile}'].mean()) 
            for profile in profiles
        }
    }
    
    return analysis

def analyze_rule11_multi_dimension(df: pd.DataFrame) -> Dict:
    """Analyze Rule 11 multi-dimensional opportunity structure"""
    log_progress("Analyzing Rule 11 multi-dimensional structure...")
    
    dimensions = {
        'cluster_relative_underperformance': 'Cluster Relative Underperformance',
        'cluster_misjudgment': 'Cluster Misjudgment',
        'missed_sales_opportunity': 'Primary Missed Sales Opportunity'
    }
    
    analysis = {
        'dimension_summary': {},
        'dimension_overlap': {},
        'performance_metrics': {}
    }
    
    # Dimension summary
    for dim_key, dim_name in dimensions.items():
        col_name = f'rule11_{dim_key}'
        if col_name in df.columns:
            flagged = df[col_name].sum()
            analysis['dimension_summary'][dim_key] = {
                'name': dim_name,
                'stores_flagged': int(flagged),
                'percentage': float(flagged / len(df) * 100)
            }
    
    # Dimension overlap
    dim_keys = list(dimensions.keys())
    for i, dim1 in enumerate(dim_keys):
        for dim2 in dim_keys[i+1:]:
            col1 = f'rule11_{dim1}'
            col2 = f'rule11_{dim2}'
            if col1 in df.columns and col2 in df.columns:
                overlap = ((df[col1] == 1) & (df[col2] == 1)).sum()
                analysis['dimension_overlap'][f'{dim1}_vs_{dim2}'] = {
                    'overlap_count': int(overlap),
                    'overlap_percentage': float(overlap / len(df) * 100)
                }
    
    # Performance metrics
    if 'rule11_avg_opportunity_gap' in df.columns:
        analysis['performance_metrics']['avg_opportunity_gap'] = float(df['rule11_avg_opportunity_gap'].mean())
    if 'rule11_potential_sales_increase' in df.columns:
        analysis['performance_metrics']['total_potential_sales'] = float(df['rule11_potential_sales_increase'].sum())
    
    return analysis

def analyze_rule12_performance_levels(df: pd.DataFrame) -> Dict:
    """Analyze Rule 12 5-level performance classification"""
    log_progress("Analyzing Rule 12 performance level structure...")
    
    performance_levels = {
        'top_performer': 'Top Performer',
        'performing_well': 'Performing Well', 
        'some_opportunity': 'Some Opportunity',
        'good_opportunity': 'Good Opportunity',
        'major_opportunity': 'Major Opportunity'
    }
    
    analysis = {
        'level_summary': {},
        'performance_distribution': {},
        'transition_analysis': {}
    }
    
    # Level summary
    total_classified = 0
    for level_key, level_name in performance_levels.items():
        col_name = f'rule12_{level_key}'
        if col_name in df.columns:
            count = df[col_name].sum()
            analysis['level_summary'][level_key] = {
                'name': level_name,
                'store_count': int(count),
                'percentage': float(count / len(df) * 100)
            }
            total_classified += count
    
    analysis['performance_distribution']['total_classified'] = int(total_classified)
    analysis['performance_distribution']['unclassified'] = int(len(df) - total_classified)
    analysis['performance_distribution']['classification_rate'] = float(total_classified / len(df) * 100)
    
    # Opportunity vs. performing breakdown
    opportunity_levels = ['some_opportunity', 'good_opportunity', 'major_opportunity']
    performing_levels = ['top_performer', 'performing_well']
    
    opportunity_count = sum(df[f'rule12_{level}'].sum() for level in opportunity_levels if f'rule12_{level}' in df.columns)
    performing_count = sum(df[f'rule12_{level}'].sum() for level in performing_levels if f'rule12_{level}' in df.columns)
    
    analysis['transition_analysis'] = {
        'stores_needing_improvement': int(opportunity_count),
        'stores_performing_adequately': int(performing_count),
        'improvement_opportunity_rate': float(opportunity_count / total_classified * 100) if total_classified > 0 else 0
    }
    
    return analysis

def create_multi_output_visualization(rule10_analysis: Dict, rule11_analysis: Dict, rule12_analysis: Dict) -> None:
    """Create comprehensive multi-output rule visualization"""
    log_progress("Creating multi-output rule visualization...")
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            'Rule 10: SPU Assortment Optimization Profiles',
            'Rule 10: Issue Type Distribution',
            'Rule 11: Multi-Dimensional Opportunities', 
            'Rule 11: Dimension Overlap',
            'Rule 12: Performance Level Distribution',
            'Rule 12: Opportunity vs Performance'
        ],
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'pie'}, {'type': 'bar'}]]
    )
    
    # Rule 10: Profile comparison
    profiles = list(rule10_analysis['profile_summary'].keys())
    stores_flagged = [rule10_analysis['profile_summary'][p]['stores_flagged'] for p in profiles]
    
    fig.add_trace(
        go.Bar(x=profiles, y=stores_flagged, name='Stores Flagged', 
               marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1']),
        row=1, col=1
    )
    
    # Rule 10: Issue type breakdown (using standard profile)
    issue_types = list(rule10_analysis['issue_type_breakdown']['standard'].keys())
    issue_counts = [rule10_analysis['issue_type_breakdown']['standard'][t] for t in issue_types]
    
    fig.add_trace(
        go.Bar(x=issue_types, y=issue_counts, name='Issue Types',
               marker_color=['#FF9999', '#FFB366', '#FFCC99']),
        row=1, col=2
    )
    
    # Rule 11: Dimension summary
    dimensions = list(rule11_analysis['dimension_summary'].keys())
    dim_counts = [rule11_analysis['dimension_summary'][d]['stores_flagged'] for d in dimensions]
    
    fig.add_trace(
        go.Bar(x=dimensions, y=dim_counts, name='Opportunity Dimensions',
               marker_color=['#96CEB4', '#FFEAA7', '#DDA0DD']),
        row=2, col=1
    )
    
    # Rule 11: Overlap analysis
    if rule11_analysis['dimension_overlap']:
        overlap_keys = list(rule11_analysis['dimension_overlap'].keys())
        overlap_counts = [rule11_analysis['dimension_overlap'][k]['overlap_count'] for k in overlap_keys]
        
        fig.add_trace(
            go.Bar(x=overlap_keys, y=overlap_counts, name='Dimension Overlaps',
                   marker_color='#B19CD9'),
            row=2, col=2
        )
    
    # Rule 12: Performance distribution (pie chart)
    perf_levels = list(rule12_analysis['level_summary'].keys())
    perf_counts = [rule12_analysis['level_summary'][p]['store_count'] for p in perf_levels]
    perf_labels = [rule12_analysis['level_summary'][p]['name'] for p in perf_levels]
    
    fig.add_trace(
        go.Pie(labels=perf_labels, values=perf_counts, name='Performance Levels',
               marker_colors=['#2ECC71', '#3498DB', '#F39C12', '#E74C3C', '#8E44AD']),
        row=3, col=1
    )
    
    # Rule 12: Opportunity vs Performance
    transition_data = rule12_analysis['transition_analysis']
    categories = ['Needing Improvement', 'Performing Adequately']
    values = [transition_data['stores_needing_improvement'], transition_data['stores_performing_adequately']]
    
    fig.add_trace(
        go.Bar(x=categories, y=values, name='Performance Categories',
               marker_color=['#E74C3C', '#2ECC71']),
        row=3, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=1200,
        title_text="SPU Multi-Output Rules Analysis Dashboard",
        title_x=0.5,
        showlegend=False
    )
    
    # Save visualization
    output_file = f"{VISUALIZATION_DIR}/multi_output_rules_analysis.html"
    fig.write_html(output_file)
    log_progress(f"Saved multi-output visualization to {output_file}")

def generate_spu_breakdown_analysis(df: pd.DataFrame) -> None:
    """Generate detailed SPU-level breakdown analysis for multi-output rules"""
    log_progress("Generating SPU breakdown analysis...")
    
    # Create comprehensive breakdown report
    report_file = f"{OUTPUT_DIR}/spu_multi_output_breakdown.md"
    
    with open(report_file, 'w') as f:
        f.write("# SPU Multi-Output Rules Breakdown Analysis\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Overview\n")
        f.write(f"- **Total stores analyzed**: {len(df):,}\n")
        f.write("- **Multi-output rules**: Rule 10 (3 profiles), Rule 11 (3 dimensions), Rule 12 (5 levels)\n")
        f.write("- **Single-output rules**: Rule 7, Rule 8, Rule 9\n\n")
        
        # Rule 10 detailed breakdown
        f.write("## Rule 10: SPU Assortment Optimization (3 Profiles)\n\n")
        f.write("### Profile Comparison\n")
        f.write("| Profile | Stores Flagged | Over-Assorted | Under-Assorted | Inefficient Mix |\n")
        f.write("|---------|---------------|---------------|----------------|----------------|\n")
        
        for profile in ['conservative', 'standard', 'aggressive']:
            flagged = df[f'rule10_assortment_issue_{profile}'].sum()
            over = df[f'rule10_over_assorted_{profile}'].sum()
            under = df[f'rule10_under_assorted_{profile}'].sum()
            inefficient = df[f'rule10_inefficient_mix_{profile}'].sum()
            f.write(f"| {profile.title()} | {flagged:,} | {over:,} | {under:,} | {inefficient:,} |\n")
        
        f.write("\n### Opportunity Value by Profile\n")
        f.write("| Profile | Total Opportunity Value | Avg per Store |\n")
        f.write("|---------|------------------------|---------------|\n")
        
        for profile in ['conservative', 'standard', 'aggressive']:
            total_value = df[f'rule10_total_opportunity_value_{profile}'].sum()
            avg_value = df[f'rule10_total_opportunity_value_{profile}'].mean()
            f.write(f"| {profile.title()} | {total_value:,.1f} | {avg_value:.1f} |\n")
        
        # Rule 11 breakdown
        f.write("\n## Rule 11: Missed Sales Opportunity (3 Dimensions)\n\n")
        f.write("| Dimension | Stores Flagged | Percentage |\n")
        f.write("|-----------|---------------|------------|\n")
        
        dimensions = [
            ('cluster_relative_underperformance', 'Cluster Relative Underperformance'),
            ('cluster_misjudgment', 'Cluster Misjudgment'),
            ('missed_sales_opportunity', 'Primary Opportunity')
        ]
        
        for dim_key, dim_name in dimensions:
            col_name = f'rule11_{dim_key}'
            if col_name in df.columns:
                flagged = df[col_name].sum()
                percentage = flagged / len(df) * 100
                f.write(f"| {dim_name} | {flagged:,} | {percentage:.1f}% |\n")
        
        # Rule 12 breakdown
        f.write("\n## Rule 12: Sales Performance (5 Levels)\n\n")
        f.write("| Performance Level | Store Count | Percentage |\n")
        f.write("|------------------|-------------|------------|\n")
        
        levels = [
            ('top_performer', 'Top Performer'),
            ('performing_well', 'Performing Well'),
            ('some_opportunity', 'Some Opportunity'),
            ('good_opportunity', 'Good Opportunity'),
            ('major_opportunity', 'Major Opportunity')
        ]
        
        for level_key, level_name in levels:
            col_name = f'rule12_{level_key}'
            if col_name in df.columns:
                count = df[col_name].sum()
                percentage = count / len(df) * 100
                f.write(f"| {level_name} | {count:,} | {percentage:.1f}% |\n")
        
        # Single-output rules summary
        f.write("\n## Single-Output Rules Summary\n\n")
        f.write("| Rule | Stores Flagged | Percentage |\n")
        f.write("|------|---------------|------------|\n")
        
        single_rules = [
            ('rule7_missing_spu', 'Rule 7: Missing SPU'),
            ('rule8_imbalanced_spu', 'Rule 8: Imbalanced'),
            ('rule9_below_minimum_spu', 'Rule 9: Below Minimum')
        ]
        
        for rule_col, rule_name in single_rules:
            if rule_col in df.columns:
                flagged = df[rule_col].sum()
                percentage = flagged / len(df) * 100
                f.write(f"| {rule_name} | {flagged:,} | {percentage:.1f}% |\n")
        
        # Profile overlap analysis
        f.write("\n## Rule 10 Profile Overlap Analysis\n\n")
        all_three = ((df['rule10_assortment_issue_conservative'] == 1) & 
                    (df['rule10_assortment_issue_standard'] == 1) & 
                    (df['rule10_assortment_issue_aggressive'] == 1)).sum()
        
        conservative_only = ((df['rule10_assortment_issue_conservative'] == 1) & 
                           (df['rule10_assortment_issue_standard'] == 0) & 
                           (df['rule10_assortment_issue_aggressive'] == 0)).sum()
        
        f.write(f"- **All three profiles flagged**: {all_three:,} stores ({all_three/len(df)*100:.1f}%)\n")
        f.write(f"- **Conservative only**: {conservative_only:,} stores ({conservative_only/len(df)*100:.1f}%)\n")
        
        # Visualization note
        f.write("\n## Visualization Files\n")
        f.write("- Multi-output analysis dashboard: `output/visualizations/multi_output_rules_analysis.html`\n")
        f.write("- Detailed opportunity files:\n")
        f.write("  - `output/rule10_spu_assortment_opportunities_conservative.csv`\n")
        f.write("  - `output/rule10_spu_assortment_opportunities_standard.csv`\n")
        f.write("  - `output/rule10_spu_assortment_opportunities_aggressive.csv`\n")
    
    log_progress(f"Saved SPU breakdown analysis to {report_file}")

def main() -> None:
    """Run comprehensive multi-output rules analysis"""
    print("\n" + "="*80)
    print("🔍 SPU MULTI-OUTPUT RULES ANALYSIS")
    print("="*80)
    
    start_time = datetime.now()
    
    try:
        # Load data
        df = load_consolidated_data()
        
        # Analyze each multi-output rule
        rule10_analysis = analyze_rule10_multi_profile(df)
        rule11_analysis = analyze_rule11_multi_dimension(df)
        rule12_analysis = analyze_rule12_performance_levels(df)
        
        # Create visualizations
        create_multi_output_visualization(rule10_analysis, rule11_analysis, rule12_analysis)
        
        # Generate detailed breakdown
        generate_spu_breakdown_analysis(df)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ MULTI-OUTPUT RULES ANALYSIS COMPLETE:")
        print(f"  • Processing time: {elapsed:.1f} seconds")
        print(f"  • Total stores analyzed: {len(df):,}")
        print(f"  • Multi-output rules analyzed: 3 (Rule 10, 11, 12)")
        
        # Summary statistics
        print(f"\n📊 KEY FINDINGS:")
        print(f"  • Rule 10 Standard Profile: {rule10_analysis['profile_summary']['standard']['stores_flagged']:,} stores flagged")
        print(f"  • Rule 11 Primary Opportunities: {rule11_analysis['dimension_summary']['missed_sales_opportunity']['stores_flagged']:,} stores")
        print(f"  • Rule 12 Performance Classification: {rule12_analysis['performance_distribution']['classification_rate']:.1f}% stores classified")
        
        print("="*80)
        
    except Exception as e:
        log_progress(f"❌ Error in multi-output analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main() 