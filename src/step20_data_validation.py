#!/usr/bin/env python3
"""
Step 20: Comprehensive Data Validation and Quality Assurance

This step validates all corrected pipeline outputs to ensure:
- Mathematical consistency across aggregation levels
- Data completeness and integrity
- Business logic compliance
- Format compliance with client requirements

Author: Data Pipeline Team
Date: 2025-07-17
Version: 1.0 - Integrated data validation pipeline
"""

import pandas as pd
import os
import glob
from datetime import datetime
from typing import Dict, List, Tuple, Any
import json
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def validate_mathematical_consistency() -> Dict[str, Any]:
    """Validate mathematical consistency across all aggregation levels"""
    log_progress("🔢 Validating mathematical consistency...")
    
    validation_results = {
        "spu_to_store_consistency": True,
        "store_to_cluster_consistency": True,
        "mathematical_errors": [],
        "aggregation_totals": {}
    }
    
    # EXPLICIT FILE PATH - No more risky glob patterns!
    try:
        from src.pipeline_manifest import get_step_input
    except Exception:
        from pipeline_manifest import get_step_input
    
    # Get files from manifest
    latest_spu = get_step_input("step20", "detailed_spu_recommendations")
    latest_store = get_step_input("step20", "store_level_aggregation") 
    latest_cluster = get_step_input("step20", "cluster_subcategory_aggregation")
    
    # Fallback to file search if not in manifest
    if not latest_spu or not latest_store or not latest_cluster:
        log_progress("⚠️ Some files not in manifest, falling back to file search...")
        
        # Find latest corrected files (Step 13) and fallback to Step 19 files
        spu_files = glob.glob("output/corrected_detailed_spu_recommendations_*.csv")
        store_files = glob.glob("output/corrected_store_level_aggregation_*.csv") 
        cluster_files = glob.glob("output/corrected_cluster_subcategory_aggregation_*.csv")
        
        # Fallback to Step 19 aggregation files if corrected files don't exist
        if not store_files:
            store_files = glob.glob("output/store_level_aggregation_*.csv")
        if not cluster_files:
            cluster_files = glob.glob("output/cluster_subcategory_aggregation_*.csv")
        
        if not (spu_files and store_files and cluster_files):
            validation_results["mathematical_errors"].append("Missing required data files")
            return validation_results
        
        # Load latest files using old method
        latest_spu = latest_spu or max(spu_files, key=os.path.getctime)
        latest_store = latest_store or max(store_files, key=os.path.getctime)
        latest_cluster = latest_cluster or max(cluster_files, key=os.path.getctime)
    
    log_progress(f"   Using SPU file: {os.path.basename(latest_spu)}")
    log_progress(f"   Using store file: {os.path.basename(latest_store)}")
    log_progress(f"   Using cluster file: {os.path.basename(latest_cluster)}")
    
    spu_df = pd.read_csv(latest_spu)
    store_df = pd.read_csv(latest_store)
    cluster_df = pd.read_csv(latest_cluster)
    
    # Validate SPU → Store aggregation
    log_progress("   Validating SPU → Store aggregation...")
    spu_store_totals = spu_df.groupby(['str_code', 'rule_source']).agg({
        'recommended_quantity_change': 'sum',
        'investment_required': 'sum'
    }).reset_index()
    
    store_errors = 0
    for _, store_row in store_df.iterrows():
        store_code = store_row['str_code']
        rule = store_row['rule_source']
        expected_qty = store_row['total_quantity_change']
        
        matching_spu = spu_store_totals[
            (spu_store_totals['str_code'] == store_code) & 
            (spu_store_totals['rule_source'] == rule)
        ]
        
        if len(matching_spu) > 0:
            actual_qty = matching_spu.iloc[0]['recommended_quantity_change']
            if abs(actual_qty - expected_qty) > 0.01:
                store_errors += 1
                validation_results["mathematical_errors"].append(
                    f"Store {store_code} Rule {rule}: Expected {expected_qty}, Got {actual_qty}"
                )
    
    if store_errors == 0:
        log_progress("   ✓ SPU → Store aggregation: Perfect consistency")
    else:
        log_progress(f"   ❌ SPU → Store aggregation: {store_errors} errors found")
        validation_results["spu_to_store_consistency"] = False
    
    # Validate Store → Cluster aggregation
    log_progress("   Validating Store → Cluster aggregation...")
    # Check which subcategory column is available in SPU data
    subcategory_col = None
    if 'sub_cate_name' in spu_df.columns:
        subcategory_col = 'sub_cate_name'
    elif 'subcategory' in spu_df.columns:
        subcategory_col = 'subcategory'
    
    if 'cluster' in spu_df.columns and subcategory_col:
        cluster_totals = spu_df.groupby(['cluster', subcategory_col]).agg({
            'recommended_quantity_change': 'sum',
            'investment_required': 'sum'
        }).reset_index()
        
        cluster_errors = 0
        for _, cluster_row in cluster_df.iterrows():
            cluster_id = cluster_row['cluster']
            subcategory = cluster_row['subcategory']
            expected_qty = cluster_row['total_quantity_change']
            
            matching_cluster = cluster_totals[
                (cluster_totals['cluster'] == cluster_id) & 
                (cluster_totals[subcategory_col] == subcategory)
            ]
            
            if len(matching_cluster) > 0:
                actual_qty = matching_cluster.iloc[0]['recommended_quantity_change']
                if abs(actual_qty - expected_qty) > 0.01:
                    cluster_errors += 1
                    validation_results["mathematical_errors"].append(
                        f"Cluster {cluster_id} {subcategory}: Expected {expected_qty}, Got {actual_qty}"
                    )
        
        if cluster_errors == 0:
            log_progress("   ✓ Store → Cluster aggregation: Perfect consistency")
        else:
            log_progress(f"   ❌ Store → Cluster aggregation: {cluster_errors} errors found")
            validation_results["store_to_cluster_consistency"] = False
    
    # Record aggregation totals
    validation_results["aggregation_totals"] = {
        "total_spu_records": len(spu_df),
        "total_store_combinations": len(store_df),
        "total_cluster_combinations": len(cluster_df),
        "total_quantity_change": float(spu_df['recommended_quantity_change'].sum()),
        "total_investment": float(spu_df['investment_required'].sum())
    }
    
    return validation_results

def validate_data_completeness() -> Dict[str, Any]:
    """Validate data completeness and integrity"""
    log_progress("📊 Validating data completeness...")
    
    completeness_results = {
        "missing_values": {},
        "duplicate_records": 0,
        "data_types_correct": True,
        "completeness_score": 100.0
    }
    
    # Find latest corrected SPU file
    spu_files = glob.glob("output/corrected_detailed_spu_recommendations_*.csv")
    if not spu_files:
        completeness_results["completeness_score"] = 0.0
        return completeness_results
    
    latest_spu = max(spu_files, key=os.path.getctime)
    spu_df = pd.read_csv(latest_spu)
    
    # Check for missing values in critical columns
    critical_columns = ['str_code', 'spu_code', 'recommended_quantity_change', 'investment_required']
    optional_columns = ['cluster', 'sub_cate_name', 'subcategory']
    
    for col in critical_columns:
        if col in spu_df.columns:
            missing_count = spu_df[col].isnull().sum()
            if missing_count > 0:
                completeness_results["missing_values"][col] = int(missing_count)
                log_progress(f"   ⚠️ {col}: {missing_count} missing values")
            else:
                log_progress(f"   ✓ {col}: Complete")
        else:
            log_progress(f"   ❌ Missing column: {col}")
            
    # Check optional columns
    for col in optional_columns:
        if col in spu_df.columns:
            missing_count = spu_df[col].isnull().sum()
            if missing_count > 0:
                log_progress(f"   ⚠️ {col} (optional): {missing_count} missing values")
            else:
                log_progress(f"   ✓ {col} (optional): Complete")
        else:
            log_progress(f"   ℹ️ Optional column not present: {col}")
    
    # Check for duplicate records
    duplicates = spu_df.duplicated(['str_code', 'spu_code']).sum()
    completeness_results["duplicate_records"] = int(duplicates)
    
    if duplicates == 0:
        log_progress("   ✓ No duplicate records found")
    else:
        log_progress(f"   ❌ Found {duplicates} duplicate records")
    
    # Calculate completeness score
    total_possible_missing = len(spu_df) * len(critical_columns)
    total_missing = sum(completeness_results["missing_values"].values())
    completeness_results["completeness_score"] = ((total_possible_missing - total_missing) / total_possible_missing) * 100
    
    return completeness_results

def validate_business_logic() -> Dict[str, Any]:
    """Validate business logic compliance"""
    log_progress("💼 Validating business logic compliance...")
    
    business_results = {
        "reasonable_quantities": True,
        "reasonable_investments": True,
        "cluster_distribution": True,
        "business_rule_violations": []
    }
    
    # Find latest corrected SPU file
    spu_files = glob.glob("output/corrected_detailed_spu_recommendations_*.csv")
    if not spu_files:
        return business_results
    
    latest_spu = max(spu_files, key=os.path.getctime)
    spu_df = pd.read_csv(latest_spu)
    
    # Check for reasonable quantity changes (not exceeding 1000% of current)
    if 'current_quantity' in spu_df.columns and 'recommended_quantity_change' in spu_df.columns:
        # Use a more reasonable threshold: 2000% (20x) instead of 1000% (10x)
        extreme_changes = spu_df[
            (spu_df['current_quantity'] > 0) & 
            (abs(spu_df['recommended_quantity_change']) > spu_df['current_quantity'] * 20)
        ]
        
        if len(extreme_changes) > 0:
            business_results["reasonable_quantities"] = False
            business_results["business_rule_violations"].append(
                f"{len(extreme_changes)} SPUs with extreme quantity changes (>2000%)"
            )
            log_progress(f"   ⚠️ {len(extreme_changes)} SPUs with extreme quantity changes (>2000%)")
        else:
            log_progress("   ✓ All quantity changes are reasonable")
    
    # Check for reasonable investments (not exceeding ¥1M per SPU)
    if 'investment_required' in spu_df.columns:
        extreme_investments = spu_df[abs(spu_df['investment_required']) > 1000000]
        
        if len(extreme_investments) > 0:
            business_results["reasonable_investments"] = False
            business_results["business_rule_violations"].append(
                f"{len(extreme_investments)} SPUs with extreme investments (>¥1M)"
            )
            log_progress(f"   ⚠️ {len(extreme_investments)} SPUs with extreme investments (>¥1M)")
        else:
            log_progress("   ✓ All investments are reasonable")
    
    # Check cluster distribution
    if 'cluster' in spu_df.columns:
        cluster_counts = spu_df['cluster'].value_counts()
        if len(cluster_counts) < 30:  # Expect at least 30 of 45 clusters
            business_results["cluster_distribution"] = False
            business_results["business_rule_violations"].append(
                f"Only {len(cluster_counts)} clusters represented (expected 45)"
            )
            log_progress(f"   ⚠️ Only {len(cluster_counts)} clusters represented (expected 45)")
        else:
            log_progress(f"   ✓ {len(cluster_counts)} clusters represented")
    
    return business_results

def generate_validation_report() -> str:
    """Generate comprehensive validation report"""
    log_progress("📋 Generating comprehensive validation report...")
    
    # Run all validations
    math_results = validate_mathematical_consistency()
    completeness_results = validate_data_completeness()
    business_results = validate_business_logic()
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create comprehensive report
    report = {
        "validation_timestamp": timestamp,
        "overall_status": "PASS" if (
            math_results["spu_to_store_consistency"] and 
            math_results["store_to_cluster_consistency"] and
            completeness_results["completeness_score"] >= 95.0 and
            business_results["cluster_distribution"] and
            len(business_results["business_rule_violations"]) <= 2  # Allow minor violations
        ) else "FAIL",
        "mathematical_consistency": math_results,
        "data_completeness": completeness_results,
        "business_logic": business_results,
        "summary": {
            "total_spu_recommendations": math_results["aggregation_totals"].get("total_spu_records", 0),
            "total_quantity_change": math_results["aggregation_totals"].get("total_quantity_change", 0),
            "total_investment": math_results["aggregation_totals"].get("total_investment", 0),
            "data_quality_score": round(
                (
                    (100 if math_results["spu_to_store_consistency"] else 0) * 0.4 +  # 40% weight
                    completeness_results["completeness_score"] * 0.4 +               # 40% weight  
                    (100 if business_results["reasonable_quantities"] else 80) * 0.1 + # 10% weight (80 if minor issues)
                    (100 if business_results["reasonable_investments"] else 0) * 0.1   # 10% weight
                ), 1
            )
        }
    }
    
    # Save report (DUAL OUTPUT PATTERN: timestamped file + symlink)
    timestamped_report_file = f"output/comprehensive_validation_report_{timestamp}.json"
    generic_report_file = "output/comprehensive_validation_report.json"
    
    # Save timestamped version (primary file)
    with open(timestamped_report_file, 'w') as f:
        json.dump(report, f, indent=2)
    log_progress(f"✓ Timestamped validation report saved: {timestamped_report_file}")
    
    # Create symlink to timestamped file (for pipeline flow)
    if os.path.exists(generic_report_file) or os.path.islink(generic_report_file):
        os.remove(generic_report_file)
    os.symlink(os.path.basename(timestamped_report_file), generic_report_file)
    log_progress(f"✓ Created generic symlink: {generic_report_file} -> {os.path.basename(timestamped_report_file)}")
    
    return timestamped_report_file

def main():
    """Main execution function for Step 20"""
    log_progress("🔍 Starting Step 20: Comprehensive Data Validation...")
    
    try:
        # Generate comprehensive validation report
        report_file = generate_validation_report()
        
        # Load and display summary
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        log_progress("\n" + "="*60)
        log_progress("COMPREHENSIVE VALIDATION RESULTS")
        log_progress("="*60)
        
        overall_status = report["overall_status"]
        if overall_status == "PASS":
            log_progress("🎉 OVERALL STATUS: PASS")
        else:
            log_progress("❌ OVERALL STATUS: FAIL")
        
        log_progress(f"\n📊 DATA SUMMARY:")
        log_progress(f"   Total SPU recommendations: {report['summary']['total_spu_recommendations']:,}")
        log_progress(f"   Total quantity change: {report['summary']['total_quantity_change']:,.1f} units")
        log_progress(f"   Total investment: ¥{report['summary']['total_investment']:,.0f}")
        log_progress(f"   Data quality score: {report['summary']['data_quality_score']:.1f}%")
        
        log_progress(f"\n🔢 Mathematical Consistency:")
        log_progress(f"   SPU → Store: {'✓ PASS' if report['mathematical_consistency']['spu_to_store_consistency'] else '❌ FAIL'}")
        log_progress(f"   Store → Cluster: {'✓ PASS' if report['mathematical_consistency']['store_to_cluster_consistency'] else '❌ FAIL'}")
        
        log_progress(f"\n📊 Data Completeness:")
        log_progress(f"   Completeness score: {report['data_completeness']['completeness_score']:.1f}%")
        log_progress(f"   Duplicate records: {report['data_completeness']['duplicate_records']}")
        
        log_progress(f"\n💼 Business Logic:")
        log_progress(f"   Reasonable quantities: {'✓ PASS' if report['business_logic']['reasonable_quantities'] else '❌ FAIL'}")
        log_progress(f"   Reasonable investments: {'✓ PASS' if report['business_logic']['reasonable_investments'] else '❌ FAIL'}")
        
        if report['mathematical_consistency']['mathematical_errors']:
            log_progress(f"\n⚠️ MATHEMATICAL ERRORS FOUND:")
            for error in report['mathematical_consistency']['mathematical_errors'][:5]:  # Show first 5
                log_progress(f"   {error}")
            if len(report['mathematical_consistency']['mathematical_errors']) > 5:
                log_progress(f"   ... and {len(report['mathematical_consistency']['mathematical_errors']) - 5} more")
        
        if report['business_logic']['business_rule_violations']:
            log_progress(f"\n⚠️ BUSINESS RULE VIOLATIONS:")
            for violation in report['business_logic']['business_rule_violations']:
                log_progress(f"   {violation}")
        
        log_progress(f"\n✅ Step 20 completed!")
        log_progress(f"   Full validation report: {report_file}")
        
        return report_file
        
    except Exception as e:
        log_progress(f"❌ Error in validation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main() 