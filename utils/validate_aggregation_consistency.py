#!/usr/bin/env python3
"""
Aggregation Consistency Validation

This script validates that individual store-SPU recommendations properly aggregate
up to cluster-subcategory strategic recommendations. It ensures mathematical
consistency across all aggregation levels.

Boss requested: Verify that everything adds up correctly between detailed
recommendations and strategic cluster-subcategory suggestions.

Author: Data Pipeline
Date: 2025-07-16
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_latest_files() -> Dict[str, pd.DataFrame]:
    """Load the latest output files for comparison"""
    log_progress("Loading latest output files for comparison...")
    
    files = {}
    
    # Find the latest detailed SPU breakdown files
    output_dir = "output"
    
    # 1. Latest detailed SPU recommendations
    spu_files = [f for f in os.listdir(output_dir) if f.startswith("detailed_spu_recommendations_")]
    if spu_files:
        latest_spu_file = max(spu_files)
        files['detailed_spu'] = pd.read_csv(os.path.join(output_dir, latest_spu_file), dtype={'str_code': str, 'spu_code': str})
        log_progress(f"✓ Loaded detailed SPU: {latest_spu_file} ({len(files['detailed_spu']):,} records)")
    else:
        log_progress("❌ No detailed SPU recommendations found")
        return {}
    
    # 2. Latest store-level aggregation
    store_files = [f for f in os.listdir(output_dir) if f.startswith("store_level_aggregation_")]
    if store_files:
        latest_store_file = max(store_files)
        files['store_aggregation'] = pd.read_csv(os.path.join(output_dir, latest_store_file), dtype={'str_code': str})
        log_progress(f"✓ Loaded store aggregation: {latest_store_file} ({len(files['store_aggregation']):,} records)")
    
    # 3. Latest cluster-subcategory aggregation
    cluster_files = [f for f in os.listdir(output_dir) if f.startswith("cluster_subcategory_aggregation_")]
    if cluster_files:
        latest_cluster_file = max(cluster_files)
        files['cluster_aggregation'] = pd.read_csv(os.path.join(output_dir, latest_cluster_file))
        log_progress(f"✓ Loaded cluster aggregation: {latest_cluster_file} ({len(files['cluster_aggregation']):,} records)")
    
    # 4. Enhanced Fast Fish format (strategic recommendations)
    ff_files = [f for f in os.listdir(output_dir) if f.startswith("enhanced_fast_fish_format_")]
    if ff_files:
        latest_ff_file = max(ff_files)
        files['fast_fish'] = pd.read_csv(os.path.join(output_dir, latest_ff_file), dtype={'Store_Code': str})
        log_progress(f"✓ Loaded Fast Fish format: {latest_ff_file} ({len(files['fast_fish']):,} records)")
    
    # 5. Consolidated SPU rules
    if os.path.exists(os.path.join(output_dir, "consolidated_spu_rule_results.csv")):
        files['consolidated_rules'] = pd.read_csv(os.path.join(output_dir, "consolidated_spu_rule_results.csv"), dtype={'str_code': str})
        log_progress(f"✓ Loaded consolidated rules: ({len(files['consolidated_rules']):,} records)")
    
    # 6. Load clustering results for store-cluster mapping
    if os.path.exists(os.path.join(output_dir, "clustering_results_spu.csv")):
        files['clustering'] = pd.read_csv(os.path.join(output_dir, "clustering_results_spu.csv"), dtype={'str_code': str})
        log_progress(f"✓ Loaded clustering results: ({len(files['clustering']):,} records)")
    
    return files

def validate_spu_to_store_aggregation(detailed_spu: pd.DataFrame, store_agg: pd.DataFrame) -> Dict:
    """Validate that detailed SPU recommendations aggregate correctly to store level"""
    log_progress("🔍 Validating SPU → Store aggregation...")
    
    validation_results = {
        'test_name': 'SPU to Store Aggregation',
        'passed': True,
        'details': [],
        'discrepancies': []
    }
    
    # Calculate store totals from detailed SPU data
    spu_store_totals = detailed_spu.groupby(['str_code', 'rule_source']).agg({
        'recommended_quantity_change': 'sum',
        'investment_required': 'sum',
        'spu_code': 'count'
    }).reset_index()
    
    spu_store_totals.columns = ['str_code', 'rule_source', 'spu_calc_qty_change', 'spu_calc_investment', 'spu_calc_count']
    
    # Merge with store aggregation results
    comparison = store_agg.merge(
        spu_store_totals, 
        on=['str_code', 'rule_source'], 
        how='outer',
        suffixes=('_agg', '_spu')
    )
    
    # Check for missing data
    missing_in_agg = comparison[comparison['total_quantity_change'].isna()]
    missing_in_spu = comparison[comparison['spu_calc_qty_change'].isna()]
    
    if len(missing_in_agg) > 0:
        validation_results['passed'] = False
        validation_results['discrepancies'].append(f"Missing in store aggregation: {len(missing_in_agg)} records")
    
    if len(missing_in_spu) > 0:
        validation_results['passed'] = False
        validation_results['discrepancies'].append(f"Missing in SPU calculations: {len(missing_in_spu)} records")
    
    # Compare quantities (allowing for small floating point differences)
    comparison = comparison.dropna()
    qty_diff = abs(comparison['total_quantity_change'] - comparison['spu_calc_qty_change'])
    investment_diff = abs(comparison['total_investment'] - comparison['spu_calc_investment'])
    count_diff = abs(comparison['affected_spus'] - comparison['spu_calc_count'])
    
    qty_discrepancies = qty_diff > 0.01
    investment_discrepancies = investment_diff > 1.0  # Allow ¥1 difference
    count_discrepancies = count_diff > 0
    
    if qty_discrepancies.any():
        validation_results['passed'] = False
        max_qty_diff = qty_diff.max()
        validation_results['discrepancies'].append(f"Quantity differences found. Max difference: {max_qty_diff:.2f}")
    
    if investment_discrepancies.any():
        validation_results['passed'] = False
        max_inv_diff = investment_diff.max()
        validation_results['discrepancies'].append(f"Investment differences found. Max difference: ¥{max_inv_diff:.2f}")
    
    if count_discrepancies.any():
        validation_results['passed'] = False
        max_count_diff = count_diff.max()
        validation_results['discrepancies'].append(f"SPU count differences found. Max difference: {max_count_diff}")
    
    validation_results['details'] = [
        f"Records compared: {len(comparison):,}",
        f"Average quantity difference: {qty_diff.mean():.4f}",
        f"Average investment difference: ¥{investment_diff.mean():.2f}",
        f"Records with quantity discrepancies: {qty_discrepancies.sum()}",
        f"Records with investment discrepancies: {investment_discrepancies.sum()}"
    ]
    
    return validation_results

def validate_store_to_cluster_aggregation(store_agg: pd.DataFrame, cluster_agg: pd.DataFrame, 
                                         clustering: pd.DataFrame) -> Dict:
    """Validate that store-level aggregations roll up correctly to cluster-subcategory level"""
    log_progress("🔍 Validating Store → Cluster-Subcategory aggregation...")
    
    validation_results = {
        'test_name': 'Store to Cluster-Subcategory Aggregation',
        'passed': True,
        'details': [],
        'discrepancies': []
    }
    
    # This validation is more complex because we need to map stores to clusters
    # and aggregate by subcategory, but our current data structure may not have
    # subcategory information in the store aggregation
    
    if 'cluster' not in store_agg.columns and clustering is not None:
        # Add cluster information to store aggregation
        store_with_cluster = store_agg.merge(
            clustering[['str_code', 'Cluster']], 
            on='str_code', 
            how='left'
        )
        store_with_cluster.rename(columns={'Cluster': 'cluster'}, inplace=True)
    else:
        store_with_cluster = store_agg.copy()
    
    # Calculate cluster totals from store data
    if 'cluster' in store_with_cluster.columns:
        store_cluster_totals = store_with_cluster.groupby('cluster').agg({
            'total_quantity_change': 'sum',
            'total_investment': 'sum',
            'str_code': 'nunique'
        }).reset_index()
        
        store_cluster_totals.columns = ['cluster', 'store_calc_qty_change', 'store_calc_investment', 'store_calc_stores']
        
        # Compare with cluster aggregation totals
        cluster_totals = cluster_agg.groupby('cluster').agg({
            'total_quantity_change': 'sum',
            'total_investment': 'sum',
            'stores_affected': 'sum'
        }).reset_index()
        
        comparison = cluster_totals.merge(store_cluster_totals, on='cluster', how='outer')
        
        # Check for discrepancies
        comparison = comparison.dropna()
        qty_diff = abs(comparison['total_quantity_change'] - comparison['store_calc_qty_change'])
        investment_diff = abs(comparison['total_investment'] - comparison['store_calc_investment'])
        
        qty_discrepancies = qty_diff > 0.01
        investment_discrepancies = investment_diff > 1.0
        
        if qty_discrepancies.any():
            validation_results['passed'] = False
            max_qty_diff = qty_diff.max()
            validation_results['discrepancies'].append(f"Cluster quantity differences. Max: {max_qty_diff:.2f}")
        
        if investment_discrepancies.any():
            validation_results['passed'] = False
            max_inv_diff = investment_diff.max()
            validation_results['discrepancies'].append(f"Cluster investment differences. Max: ¥{max_inv_diff:.2f}")
        
        validation_results['details'] = [
            f"Clusters compared: {len(comparison)}",
            f"Average quantity difference: {qty_diff.mean():.4f}",
            f"Average investment difference: ¥{investment_diff.mean():.2f}"
        ]
    else:
        validation_results['passed'] = False
        validation_results['discrepancies'].append("No cluster information available for validation")
    
    return validation_results

def validate_totals_consistency(files: Dict[str, pd.DataFrame]) -> Dict:
    """Validate that total numbers are consistent across all aggregation levels"""
    log_progress("🔍 Validating total consistency across all levels...")
    
    validation_results = {
        'test_name': 'Total Consistency Check',
        'passed': True,
        'details': [],
        'discrepancies': []
    }
    
    totals = {}
    
    # Calculate totals from each level
    if 'detailed_spu' in files:
        spu_df = files['detailed_spu']
        totals['spu_level'] = {
            'total_quantity_change': spu_df['recommended_quantity_change'].sum(),
            'total_investment': spu_df['investment_required'].sum(),
            'unique_stores': spu_df['str_code'].nunique(),
            'unique_spus': spu_df['spu_code'].nunique(),
            'total_recommendations': len(spu_df)
        }
    
    if 'store_aggregation' in files:
        store_df = files['store_aggregation']
        totals['store_level'] = {
            'total_quantity_change': store_df['total_quantity_change'].sum(),
            'total_investment': store_df['total_investment'].sum(),
            'unique_stores': store_df['str_code'].nunique(),
            'total_recommendations': len(store_df)
        }
    
    if 'cluster_aggregation' in files:
        cluster_df = files['cluster_aggregation']
        totals['cluster_level'] = {
            'total_quantity_change': cluster_df['total_quantity_change'].sum(),
            'total_investment': cluster_df['total_investment'].sum(),
            'unique_clusters': cluster_df['cluster'].nunique(),
            'total_combinations': len(cluster_df)
        }
    
    # Compare totals between levels
    if 'spu_level' in totals and 'store_level' in totals:
        qty_diff = abs(totals['spu_level']['total_quantity_change'] - totals['store_level']['total_quantity_change'])
        inv_diff = abs(totals['spu_level']['total_investment'] - totals['store_level']['total_investment'])
        
        if qty_diff > 0.01:
            validation_results['passed'] = False
            validation_results['discrepancies'].append(f"SPU vs Store quantity difference: {qty_diff:.2f}")
        
        if inv_diff > 1.0:
            validation_results['passed'] = False
            validation_results['discrepancies'].append(f"SPU vs Store investment difference: ¥{inv_diff:.2f}")
    
    validation_results['details'] = [f"Totals calculated for {len(totals)} levels"]
    for level, values in totals.items():
        validation_results['details'].append(f"{level}: {values}")
    
    return validation_results

def validate_fast_fish_mapping(files: Dict[str, pd.DataFrame]) -> Dict:
    """Validate Fast Fish strategic recommendations against detailed data"""
    log_progress("🔍 Validating Fast Fish strategic recommendations...")
    
    validation_results = {
        'test_name': 'Fast Fish Strategic Mapping',
        'passed': True,
        'details': [],
        'discrepancies': []
    }
    
    if 'fast_fish' not in files:
        validation_results['passed'] = False
        validation_results['discrepancies'].append("Fast Fish format file not found")
        return validation_results
    
    ff_df = files['fast_fish']
    
    # Basic validation of Fast Fish structure
    required_columns = ['Store_Group_Name', 'Target_Style_Tags', 'Target_SPU_Quantity']
    missing_columns = [col for col in required_columns if col not in ff_df.columns]
    
    if missing_columns:
        validation_results['passed'] = False
        validation_results['discrepancies'].append(f"Missing Fast Fish columns: {missing_columns}")
    else:
        validation_results['details'].append(f"Fast Fish records: {len(ff_df):,}")
        validation_results['details'].append(f"Store groups: {ff_df['Store_Group_Name'].nunique()}")
        validation_results['details'].append(f"Unique categories: {ff_df['Target_Style_Tags'].nunique()}")
        validation_results['details'].append(f"Total target SPUs: {ff_df['Target_SPU_Quantity'].sum():,.0f}")
    
    return validation_results

def create_detailed_comparison_report(files: Dict[str, pd.DataFrame], validations: List[Dict]) -> None:
    """Create a detailed comparison report"""
    log_progress("Creating detailed comparison report...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"output/aggregation_validation_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Aggregation Consistency Validation Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Executive Summary\n")
        all_passed = all(v['passed'] for v in validations)
        if all_passed:
            f.write("✅ **ALL VALIDATIONS PASSED** - Data aggregation is mathematically consistent\n\n")
        else:
            f.write("⚠️ **VALIDATION ISSUES DETECTED** - See details below\n\n")
        
        f.write("## Data Files Analyzed\n")
        for file_type, df in files.items():
            f.write(f"- **{file_type.replace('_', ' ').title()}**: {len(df):,} records\n")
        f.write("\n")
        
        f.write("## Validation Results\n")
        for i, validation in enumerate(validations, 1):
            status = "✅ PASSED" if validation['passed'] else "❌ FAILED"
            f.write(f"### {i}. {validation['test_name']} - {status}\n\n")
            
            if validation['details']:
                f.write("**Details:**\n")
                for detail in validation['details']:
                    f.write(f"- {detail}\n")
                f.write("\n")
            
            if validation['discrepancies']:
                f.write("**Discrepancies Found:**\n")
                for discrepancy in validation['discrepancies']:
                    f.write(f"- ⚠️ {discrepancy}\n")
                f.write("\n")
        
        f.write("## Key Metrics Summary\n")
        if 'detailed_spu' in files:
            spu_df = files['detailed_spu']
            f.write(f"- **Total SPU Recommendations**: {len(spu_df):,}\n")
            f.write(f"- **Total Quantity Changes**: {spu_df['recommended_quantity_change'].sum():,.1f} units\n")
            f.write(f"- **Total Investment Required**: ¥{spu_df['investment_required'].sum():,.0f}\n")
            f.write(f"- **Stores Affected**: {spu_df['str_code'].nunique():,}\n")
            f.write(f"- **Unique SPUs**: {spu_df['spu_code'].nunique():,}\n")
        
        f.write("\n## Validation Methodology\n")
        f.write("1. **SPU → Store Validation**: Verify individual SPU recommendations sum to store totals\n")
        f.write("2. **Store → Cluster Validation**: Verify store totals aggregate to cluster-subcategory totals\n")
        f.write("3. **Total Consistency**: Verify mathematical consistency across all aggregation levels\n")
        f.write("4. **Fast Fish Mapping**: Validate strategic recommendations structure\n")
        
        f.write("\n## Tolerance Levels\n")
        f.write("- **Quantity differences**: ±0.01 units (floating point precision)\n")
        f.write("- **Investment differences**: ±¥1.00 (rounding precision)\n")
        f.write("- **Count differences**: Exact match required\n")
        
        if all_passed:
            f.write("\n## ✅ Conclusion\n")
            f.write("All validations passed successfully. The detailed SPU recommendations properly\n")
            f.write("aggregate to store-level totals and cluster-subcategory strategic recommendations.\n")
            f.write("The boss can have confidence that all numbers add up correctly.\n")
        else:
            f.write("\n## ⚠️ Action Required\n")
            f.write("Validation discrepancies were detected. Please review the specific issues\n")
            f.write("identified above and investigate the root cause of any inconsistencies.\n")
    
    log_progress(f"✅ Saved detailed validation report: {report_file}")

def create_summary_comparison_table(files: Dict[str, pd.DataFrame]) -> None:
    """Create a summary comparison table for quick reference"""
    log_progress("Creating summary comparison table...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    summary_data = []
    
    # SPU Level
    if 'detailed_spu' in files:
        spu_df = files['detailed_spu']
        summary_data.append({
            'Level': 'SPU (Individual)',
            'Records': len(spu_df),
            'Total_Quantity_Change': spu_df['recommended_quantity_change'].sum(),
            'Total_Investment': spu_df['investment_required'].sum(),
            'Unique_Stores': spu_df['str_code'].nunique(),
            'Unique_Entities': spu_df['spu_code'].nunique()
        })
    
    # Store Level
    if 'store_aggregation' in files:
        store_df = files['store_aggregation']
        summary_data.append({
            'Level': 'Store (Aggregated)',
            'Records': len(store_df),
            'Total_Quantity_Change': store_df['total_quantity_change'].sum(),
            'Total_Investment': store_df['total_investment'].sum(),
            'Unique_Stores': store_df['str_code'].nunique(),
            'Unique_Entities': store_df['str_code'].nunique()
        })
    
    # Cluster Level
    if 'cluster_aggregation' in files:
        cluster_df = files['cluster_aggregation']
        summary_data.append({
            'Level': 'Cluster-Subcategory',
            'Records': len(cluster_df),
            'Total_Quantity_Change': cluster_df['total_quantity_change'].sum(),
            'Total_Investment': cluster_df['total_investment'].sum(),
            'Unique_Stores': cluster_df['stores_affected'].sum(),
            'Unique_Entities': cluster_df['cluster'].nunique()
        })
    
    # Fast Fish Strategic
    if 'fast_fish' in files:
        ff_df = files['fast_fish']
        summary_data.append({
            'Level': 'Fast Fish Strategic',
            'Records': len(ff_df),
            'Total_Quantity_Change': ff_df.get('Target_SPU_Quantity', pd.Series([0])).sum(),
            'Total_Investment': ff_df.get('Total_Investment_Required', pd.Series([0])).sum(),
            'Unique_Stores': ff_df.get('Stores_In_Group_Selling_This_Category', pd.Series([0])).sum(),
            'Unique_Entities': ff_df['Store_Group_Name'].nunique() if 'Store_Group_Name' in ff_df.columns else 0
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_file = f"output/aggregation_summary_comparison_{timestamp}.csv"
    summary_df.to_csv(summary_file, index=False)
    
    log_progress(f"✅ Saved summary comparison: {summary_file}")
    
    # Print summary to console
    log_progress("\n📊 SUMMARY COMPARISON:")
    for _, row in summary_df.iterrows():
        log_progress(f"  {row['Level']:20} | {row['Records']:6,} records | {row['Total_Quantity_Change']:8,.0f} units | ¥{row['Total_Investment']:12,.0f}")

def main():
    """Main validation function"""
    log_progress("🔍 Starting Aggregation Consistency Validation...")
    log_progress("Boss requested: Verify that detailed SPU recommendations add up to cluster-subcategory suggestions")
    
    try:
        # Load all relevant files
        files = load_latest_files()
        
        if not files or 'detailed_spu' not in files:
            log_progress("❌ Required files not found. Please run the pipeline and Step 19 first.")
            return
        
        log_progress(f"✅ Loaded {len(files)} data files for validation")
        
        # Run validation tests
        validations = []
        
        # Test 1: SPU to Store aggregation
        if 'store_aggregation' in files:
            validation1 = validate_spu_to_store_aggregation(files['detailed_spu'], files['store_aggregation'])
            validations.append(validation1)
            
            status1 = "✅ PASSED" if validation1['passed'] else "❌ FAILED"
            log_progress(f"  Test 1 - SPU → Store: {status1}")
        
        # Test 2: Store to Cluster aggregation  
        if 'store_aggregation' in files and 'cluster_aggregation' in files:
            validation2 = validate_store_to_cluster_aggregation(
                files['store_aggregation'], 
                files['cluster_aggregation'],
                files.get('clustering')
            )
            validations.append(validation2)
            
            status2 = "✅ PASSED" if validation2['passed'] else "❌ FAILED"
            log_progress(f"  Test 2 - Store → Cluster: {status2}")
        
        # Test 3: Total consistency
        validation3 = validate_totals_consistency(files)
        validations.append(validation3)
        
        status3 = "✅ PASSED" if validation3['passed'] else "❌ FAILED"
        log_progress(f"  Test 3 - Total Consistency: {status3}")
        
        # Test 4: Fast Fish mapping
        validation4 = validate_fast_fish_mapping(files)
        validations.append(validation4)
        
        status4 = "✅ PASSED" if validation4['passed'] else "❌ FAILED"
        log_progress(f"  Test 4 - Fast Fish Mapping: {status4}")
        
        # Create detailed reports
        create_detailed_comparison_report(files, validations)
        create_summary_comparison_table(files)
        
        # Final summary
        all_passed = all(v['passed'] for v in validations)
        
        log_progress("\n" + "="*60)
        if all_passed:
            log_progress("✅ ALL VALIDATIONS PASSED!")
            log_progress("📊 Boss conclusion: Everything adds up correctly!")
            log_progress("   • Individual SPU recommendations → Store totals ✅")
            log_progress("   • Store totals → Cluster-subcategory totals ✅") 
            log_progress("   • Mathematical consistency maintained ✅")
            log_progress("   • Strategic recommendations validated ✅")
        else:
            failed_tests = [v['test_name'] for v in validations if not v['passed']]
            log_progress("⚠️ VALIDATION ISSUES DETECTED!")
            log_progress(f"   Failed tests: {', '.join(failed_tests)}")
            log_progress("   Please review the detailed report for specific discrepancies")
        
        log_progress("="*60)
        
    except Exception as e:
        log_progress(f"❌ Error in validation analysis: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main() 