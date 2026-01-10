#!/usr/bin/env python3
"""
SPU Rule Variant Breakdown Tool

This tool provides detailed SPU-level analysis showing which specific SPUs
break different rule variants (10a, 10b, 10c, etc.) with actionable insights.

Author: Data Pipeline
Date: 2025-01-27
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json

# Configuration
RULE10_OPPORTUNITY_FILES = {
    'conservative': 'output/rule10_spu_assortment_opportunities_conservative.csv',
    'standard': 'output/rule10_spu_assortment_opportunities_standard.csv', 
    'aggressive': 'output/rule10_spu_assortment_opportunities_aggressive.csv'
}
CONSOLIDATED_FILE = 'output/consolidated_spu_rule_results.csv'
OUTPUT_DIR = 'output'

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_rule10_opportunities() -> Dict[str, pd.DataFrame]:
    """Load detailed Rule 10 opportunity files for all profiles"""
    log_progress("Loading Rule 10 SPU-level opportunity data...")
    
    opportunities = {}
    for profile, file_path in RULE10_OPPORTUNITY_FILES.items():
        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, dtype={'str_code': str})
                opportunities[profile] = df
                log_progress(f"Loaded {profile} profile: {len(df):,} SPU opportunities")
            else:
                log_progress(f"File not found: {file_path}")
        except Exception as e:
            log_progress(f"Error loading {profile} opportunities: {str(e)}")
    
    return opportunities

def analyze_spu_rule_variants(opportunities: Dict[str, pd.DataFrame]) -> Dict:
    """Analyze which SPUs break different Rule 10 variants"""
    log_progress("Analyzing SPU-level rule variant breakdowns...")
    
    analysis = {
        'rule10a_conservative': {},
        'rule10b_standard': {},
        'rule10c_aggressive': {},
        'cross_profile_analysis': {},
        'spu_specific_insights': {}
    }
    
    # Define rule variants
    rule_variants = {
        'rule10a_conservative': {
            'profile': 'conservative',
            'description': 'Conservative Assortment Optimization (±1 variety, 80% efficiency)',
            'data': opportunities.get('conservative', pd.DataFrame())
        },
        'rule10b_standard': {
            'profile': 'standard', 
            'description': 'Standard Assortment Optimization (±2 varieties, 70% efficiency)',
            'data': opportunities.get('standard', pd.DataFrame())
        },
        'rule10c_aggressive': {
            'profile': 'aggressive',
            'description': 'Aggressive Assortment Optimization (±3 varieties, 60% efficiency)',
            'data': opportunities.get('aggressive', pd.DataFrame())
        }
    }
    
    # Analyze each variant
    for variant_key, variant_info in rule_variants.items():
        df = variant_info['data']
        if len(df) == 0:
            continue
            
        variant_analysis = {
            'total_opportunities': len(df),
            'unique_stores': df['str_code'].nunique(),
            'unique_subcategories': df['sub_cate_name'].nunique(),
            'issue_type_breakdown': {},
            'top_subcategories': {},
            'priority_breakdown': {},
            'opportunity_value_stats': {}
        }
        
        # Issue type breakdown
        if 'primary_issue' in df.columns:
            issue_counts = df['primary_issue'].value_counts()
            variant_analysis['issue_type_breakdown'] = {
                'over_assorted': int(issue_counts.get('over_assorted', 0)),
                'under_assorted': int(issue_counts.get('under_assorted', 0)),
                'inefficient_mix': int(issue_counts.get('inefficient_mix', 0))
            }
        
        # Top subcategories with issues
        if 'sub_cate_name' in df.columns and 'opportunity_value' in df.columns:
            top_subcats = df.groupby('sub_cate_name').agg({
                'opportunity_value': 'sum',
                'str_code': 'nunique',
                'primary_issue': lambda x: x.mode()[0] if len(x) > 0 else 'unknown'
            }).sort_values('opportunity_value', ascending=False).head(10)
            
            variant_analysis['top_subcategories'] = {}
            for subcat, data in top_subcats.iterrows():
                variant_analysis['top_subcategories'][subcat] = {
                    'opportunity_value': float(data['opportunity_value']),
                    'stores_affected': int(data['str_code']),
                    'primary_issue': str(data['primary_issue'])
                }
        
        # Priority breakdown
        if 'priority_level' in df.columns:
            priority_counts = df['priority_level'].value_counts()
            variant_analysis['priority_breakdown'] = {
                'high': int(priority_counts.get('high', 0)),
                'medium': int(priority_counts.get('medium', 0)),
                'low': int(priority_counts.get('low', 0))
            }
        
        # Opportunity value statistics
        if 'opportunity_value' in df.columns:
            variant_analysis['opportunity_value_stats'] = {
                'total': float(df['opportunity_value'].sum()),
                'mean': float(df['opportunity_value'].mean()),
                'median': float(df['opportunity_value'].median()),
                'std': float(df['opportunity_value'].std())
            }
        
        analysis[variant_key] = variant_analysis
    
    # Cross-profile analysis
    if all(profile in opportunities for profile in ['conservative', 'standard', 'aggressive']):
        analysis['cross_profile_analysis'] = analyze_cross_profile_patterns(opportunities)
    
    return analysis

def analyze_cross_profile_patterns(opportunities: Dict[str, pd.DataFrame]) -> Dict:
    """Analyze patterns across different Rule 10 profiles"""
    log_progress("Analyzing cross-profile patterns...")
    
    # Merge all profiles to find overlaps
    conservative = opportunities['conservative'][['str_code', 'sub_cate_name', 'primary_issue', 'opportunity_value']].copy()
    standard = opportunities['standard'][['str_code', 'sub_cate_name', 'primary_issue', 'opportunity_value']].copy()
    aggressive = opportunities['aggressive'][['str_code', 'sub_cate_name', 'primary_issue', 'opportunity_value']].copy()
    
    conservative['profile'] = 'conservative'
    standard['profile'] = 'standard'
    aggressive['profile'] = 'aggressive'
    
    # Create composite key for store-subcategory combinations
    for df in [conservative, standard, aggressive]:
        df['store_subcat_key'] = df['str_code'] + '|' + df['sub_cate_name']
    
    # Find overlaps
    conservative_keys = set(conservative['store_subcat_key'])
    standard_keys = set(standard['store_subcat_key'])
    aggressive_keys = set(aggressive['store_subcat_key'])
    
    cross_analysis = {
        'all_three_profiles': len(conservative_keys & standard_keys & aggressive_keys),
        'conservative_and_standard_only': len((conservative_keys & standard_keys) - aggressive_keys),
        'conservative_only': len(conservative_keys - standard_keys - aggressive_keys),
        'standard_only': len(standard_keys - conservative_keys - aggressive_keys),
        'aggressive_only': len(aggressive_keys - conservative_keys - standard_keys),
        'profile_escalation_analysis': {}
    }
    
    # Analyze profile escalation (issues that appear in more restrictive profiles)
    all_data = pd.concat([conservative, standard, aggressive])
    
    # Group by store-subcategory and see which profiles flag it
    escalation_analysis = all_data.groupby('store_subcat_key').agg({
        'profile': lambda x: list(x),
        'primary_issue': lambda x: list(x),
        'opportunity_value': 'mean'
    }).reset_index()
    
    # Categorize escalation patterns
    escalation_patterns = {
        'conservative_escalation': 0,  # Only flagged in conservative
        'standard_escalation': 0,     # Flagged in conservative + standard
        'full_escalation': 0          # Flagged in all three
    }
    
    for _, row in escalation_analysis.iterrows():
        profiles = row['profile']
        if len(profiles) == 1 and 'conservative' in profiles:
            escalation_patterns['conservative_escalation'] += 1
        elif len(profiles) == 2 and 'conservative' in profiles and 'standard' in profiles:
            escalation_patterns['standard_escalation'] += 1
        elif len(profiles) == 3:
            escalation_patterns['full_escalation'] += 1
    
    cross_analysis['profile_escalation_analysis'] = escalation_patterns
    
    return cross_analysis

def generate_spu_variant_report(analysis: Dict) -> None:
    """Generate comprehensive SPU rule variant report"""
    log_progress("Generating SPU rule variant report...")
    
    report_file = f"{OUTPUT_DIR}/spu_rule_variant_breakdown.md"
    
    with open(report_file, 'w') as f:
        f.write("# SPU Rule Variant Breakdown Analysis\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Rule 10 Variant Analysis\n\n")
        f.write("This analysis shows which specific SPUs break different Rule 10 variants:\n")
        f.write("- **Rule 10a (Conservative)**: Strict assortment optimization\n")
        f.write("- **Rule 10b (Standard)**: Balanced assortment optimization\n") 
        f.write("- **Rule 10c (Aggressive)**: Flexible assortment optimization\n\n")
        
        # Rule variant details
        variant_names = {
            'rule10a_conservative': 'Rule 10a: Conservative Profile',
            'rule10b_standard': 'Rule 10b: Standard Profile',
            'rule10c_aggressive': 'Rule 10c: Aggressive Profile'
        }
        
        for variant_key, variant_name in variant_names.items():
            if variant_key in analysis and analysis[variant_key]:
                variant_data = analysis[variant_key]
                
                f.write(f"### {variant_name}\n\n")
                f.write(f"- **Total SPU opportunities**: {variant_data['total_opportunities']:,}\n")
                f.write(f"- **Stores affected**: {variant_data['unique_stores']:,}\n")
                f.write(f"- **Subcategories affected**: {variant_data['unique_subcategories']:,}\n")
                
                # Issue type breakdown
                if 'issue_type_breakdown' in variant_data:
                    issues = variant_data['issue_type_breakdown']
                    f.write(f"- **Over-assorted issues**: {issues.get('over_assorted', 0):,}\n")
                    f.write(f"- **Under-assorted issues**: {issues.get('under_assorted', 0):,}\n")
                    f.write(f"- **Inefficient mix issues**: {issues.get('inefficient_mix', 0):,}\n")
                
                # Opportunity value stats
                if 'opportunity_value_stats' in variant_data:
                    stats = variant_data['opportunity_value_stats']
                    f.write(f"- **Total opportunity value**: {stats['total']:,.1f}\n")
                    f.write(f"- **Average opportunity per case**: {stats['mean']:.1f}\n")
                
                # Priority breakdown
                if 'priority_breakdown' in variant_data:
                    priority = variant_data['priority_breakdown']
                    f.write(f"- **High priority cases**: {priority.get('high', 0):,}\n")
                    f.write(f"- **Medium priority cases**: {priority.get('medium', 0):,}\n")
                    f.write(f"- **Low priority cases**: {priority.get('low', 0):,}\n")
                
                # Top subcategories
                if 'top_subcategories' in variant_data and variant_data['top_subcategories']:
                    f.write(f"\n#### Top Subcategories for {variant_name}\n")
                    f.write("| Subcategory | Opportunity Value | Stores | Primary Issue |\n")
                    f.write("|-------------|------------------|---------|---------------|\n")
                    
                    for subcat, data in list(variant_data['top_subcategories'].items())[:5]:
                        f.write(f"| {subcat} | {data['opportunity_value']:,.1f} | {data['stores_affected']} | {data['primary_issue']} |\n")
                
                f.write("\n")
        
        # Cross-profile analysis
        if 'cross_profile_analysis' in analysis:
            cross_data = analysis['cross_profile_analysis']
            f.write("## Cross-Profile Pattern Analysis\n\n")
            f.write("This shows how SPU issues escalate across different rule variants:\n\n")
            
            f.write("### Profile Overlap Summary\n")
            f.write(f"- **All three profiles (10a+10b+10c)**: {cross_data['all_three_profiles']:,} SPU cases\n")
            f.write(f"- **Conservative + Standard only**: {cross_data['conservative_and_standard_only']:,} SPU cases\n")
            f.write(f"- **Conservative only**: {cross_data['conservative_only']:,} SPU cases\n")
            f.write(f"- **Standard only**: {cross_data['standard_only']:,} SPU cases\n")
            f.write(f"- **Aggressive only**: {cross_data['aggressive_only']:,} SPU cases\n")
            
            if 'profile_escalation_analysis' in cross_data:
                escalation = cross_data['profile_escalation_analysis']
                f.write("\n### Escalation Pattern Analysis\n")
                f.write(f"- **Conservative escalation**: {escalation['conservative_escalation']:,} cases (most restrictive)\n")
                f.write(f"- **Standard escalation**: {escalation['standard_escalation']:,} cases (moderate)\n")
                f.write(f"- **Full escalation**: {escalation['full_escalation']:,} cases (flagged by all profiles)\n")
        
        # Actionable insights
        f.write("\n## Actionable Insights\n\n")
        f.write("### Rule Variant Selection Guide\n")
        f.write("- **Use Rule 10a (Conservative)** for: High-confidence optimization, minimal disruption\n")
        f.write("- **Use Rule 10b (Standard)** for: Balanced optimization, moderate changes\n")
        f.write("- **Use Rule 10c (Aggressive)** for: Maximum optimization, bold restructuring\n\n")
        
        f.write("### Implementation Priority\n")
        f.write("1. **Start with Rule 10c cases**: Easiest wins, flexible thresholds\n")
        f.write("2. **Progress to Rule 10b cases**: Moderate complexity, good ROI\n")
        f.write("3. **Consider Rule 10a cases**: High-precision, strategic importance\n\n")
        
        f.write("### Data Files for Detailed Analysis\n")
        f.write("- Conservative profile details: `output/rule10_spu_assortment_opportunities_conservative.csv`\n")
        f.write("- Standard profile details: `output/rule10_spu_assortment_opportunities_standard.csv`\n")
        f.write("- Aggressive profile details: `output/rule10_spu_assortment_opportunities_aggressive.csv`\n")
    
    log_progress(f"Saved SPU rule variant report to {report_file}")

def create_spu_sample_analysis(opportunities: Dict[str, pd.DataFrame]) -> None:
    """Create sample analysis showing specific SPU cases"""
    log_progress("Creating SPU sample analysis...")
    
    sample_file = f"{OUTPUT_DIR}/spu_rule_variant_samples.csv"
    
    # Collect sample cases from each profile
    samples = []
    
    for profile, df in opportunities.items():
        if len(df) == 0:
            continue
            
        # Get top 10 cases by opportunity value for each issue type
        for issue_type in ['over_assorted', 'under_assorted', 'inefficient_mix']:
            issue_cases = df[df['primary_issue'] == issue_type].nlargest(10, 'opportunity_value')
            
            for _, row in issue_cases.iterrows():
                sample = {
                    'rule_variant': f'Rule10_{profile[0].upper()}',  # Rule10_C, Rule10_S, Rule10_A
                    'profile': profile,
                    'store_code': row['str_code'],
                    'subcategory': row['sub_cate_name'],
                    'issue_type': row['primary_issue'],
                    'priority_level': row.get('priority_level', 'unknown'),
                    'current_varieties': row.get('current_spu_varieties', 0),
                    'target_varieties': row.get('target_spu_varieties', 0),
                    'variety_gap': row.get('variety_gap', 0),
                    'suggested_adds': row.get('suggested_adds', 0),
                    'suggested_removes': row.get('suggested_removes', 0),
                    'opportunity_value': row.get('opportunity_value', 0),
                    'efficiency_gap': row.get('efficiency_gap', 0),
                    'cluster_id': row.get('cluster_id', 'unknown')
                }
                samples.append(sample)
    
    # Create DataFrame and save
    if samples:
        samples_df = pd.DataFrame(samples)
        samples_df = samples_df.sort_values(['opportunity_value'], ascending=False)
        samples_df.to_csv(sample_file, index=False)
        log_progress(f"Saved {len(samples_df):,} SPU sample cases to {sample_file}")
    else:
        log_progress("No sample cases found")

def main() -> None:
    """Run SPU rule variant breakdown analysis"""
    print("\n" + "="*80)
    print("🔍 SPU RULE VARIANT BREAKDOWN ANALYSIS")
    print("="*80)
    
    start_time = datetime.now()
    
    try:
        # Load Rule 10 opportunity data
        opportunities = load_rule10_opportunities()
        
        if not opportunities:
            log_progress("No Rule 10 opportunity files found. Please run Rule 10 analysis first.")
            return
        
        # Analyze rule variants
        analysis = analyze_spu_rule_variants(opportunities)
        
        # Generate reports
        generate_spu_variant_report(analysis)
        create_spu_sample_analysis(opportunities)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ SPU RULE VARIANT ANALYSIS COMPLETE:")
        print(f"  • Processing time: {elapsed:.1f} seconds")
        
        # Summary statistics
        for profile in ['conservative', 'standard', 'aggressive']:
            if profile in opportunities:
                df = opportunities[profile]
                variant_key = f'rule10{"abc"[["conservative", "standard", "aggressive"].index(profile)]}_' + profile
                print(f"  • Rule 10{'abc'[['conservative', 'standard', 'aggressive'].index(profile)].upper()} ({profile.title()}): {len(df):,} SPU opportunities")
        
        if 'cross_profile_analysis' in analysis:
            cross_data = analysis['cross_profile_analysis']
            print(f"  • Cross-profile overlaps: {cross_data['all_three_profiles']:,} cases flagged by all variants")
        
        print("="*80)
        
    except Exception as e:
        log_progress(f"❌ Error in SPU variant analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main() 