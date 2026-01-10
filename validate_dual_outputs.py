#!/usr/bin/env python3
"""
Dual Output Pattern Validation Script

Purpose: Verify that all fixed steps produce both timestamped and generic output files
Author: Pipeline Validation Team
Date: 2025-10-01
"""

import os
import glob
from datetime import datetime
from typing import Dict, List, Tuple

def check_dual_outputs() -> Dict[str, Dict]:
    """Check for dual output pattern across all fixed steps"""
    
    results = {}
    period_label = "202510A"
    
    # Define expected dual outputs for each fixed step
    expected_outputs = {
        "Step 13": [
            ("output/granular_trend_data_preserved.csv", "output/granular_trend_data_preserved_*.csv"),
            ("output/corrected_detailed_spu_recommendations_202510A.csv", "output/corrected_detailed_spu_recommendations_*.csv"),
        ],
        "Step 14": [
            (f"output/step14_rule_integration_reconciliation_{period_label}.csv", f"output/step14_rule_integration_reconciliation_{period_label}_*.csv"),
            (f"output/enhanced_fast_fish_dim_mismatches_{period_label}.csv", f"output/enhanced_fast_fish_dim_mismatches_{period_label}_*.csv"),
            (f"output/enhanced_fast_fish_validation_{period_label}.json", f"output/enhanced_fast_fish_validation_{period_label}_*.json"),
        ],
        "Step 15": [
            (f"output/historical_reference_202410A.csv", "output/historical_reference_202410A_*.csv"),
            (f"output/year_over_year_comparison_202410A.csv", "output/year_over_year_comparison_202410A_*.csv"),
            (f"output/historical_insights_202410A.json", "output/historical_insights_202410A_*.json"),
        ],
        "Step 16": [
            (f"output/spreadsheet_comparison_analysis_{period_label}.xlsx", f"output/spreadsheet_comparison_analysis_{period_label}_*.xlsx"),
        ],
        "Step 17": [
            (f"output/fast_fish_with_historical_and_cluster_trending_analysis_{period_label}.csv", 
             f"output/fast_fish_with_historical_and_cluster_trending_analysis_{period_label}_*.csv"),
        ],
        "Step 18": [
            (f"output/fast_fish_with_sell_through_analysis_{period_label}.csv",
             f"output/fast_fish_with_sell_through_analysis_{period_label}_*.csv"),
        ],
        "Step 19": [
            (f"output/detailed_spu_recommendations_{period_label}.csv", f"output/detailed_spu_recommendations_{period_label}_*.csv"),
            (f"output/store_level_aggregation_{period_label}.csv", f"output/store_level_aggregation_{period_label}_*.csv"),
            (f"output/cluster_subcategory_aggregation_{period_label}.csv", f"output/cluster_subcategory_aggregation_{period_label}_*.csv"),
            (f"output/spu_breakdown_summary_{period_label}.md", f"output/spu_breakdown_summary_{period_label}_*.md"),
        ],
        "Step 20": [
            ("output/comprehensive_validation_report.json", "output/comprehensive_validation_report_*.json"),
        ],
        "Step 21": [
            (f"output/D_F_Label_Tag_Recommendation_Sheet_{period_label}.xlsx", 
             f"output/D_F_Label_Tag_Recommendation_Sheet_{period_label}_*.xlsx"),
            (f"output/client_desired_store_group_style_tags_targets_{period_label}.csv",
             f"output/client_desired_store_group_style_tags_targets_{period_label}_*.csv"),
        ],
        "Step 22": [
            ("output/enriched_store_attributes.csv", f"output/enriched_store_attributes_{period_label}_*.csv"),
            ("output/store_type_analysis_report.md", f"output/store_type_analysis_report_{period_label}_*.md"),
        ],
    }
    
    print("🔍 Validating Dual Output Pattern Implementation")
    print("=" * 80)
    print()
    
    total_checks = 0
    passed_checks = 0
    failed_checks = 0
    
    for step_name, file_pairs in expected_outputs.items():
        print(f"📋 {step_name}")
        print("-" * 80)
        
        step_results = {
            "generic_files": [],
            "timestamped_files": [],
            "missing_generic": [],
            "missing_timestamped": [],
            "size_matches": [],
            "size_mismatches": []
        }
        
        for generic_file, timestamped_pattern in file_pairs:
            total_checks += 1
            
            # Check generic file
            generic_exists = os.path.exists(generic_file)
            generic_size = os.path.getsize(generic_file) if generic_exists else 0
            
            # Check timestamped files
            timestamped_files = glob.glob(timestamped_pattern)
            timestamped_exists = len(timestamped_files) > 0
            
            if generic_exists and timestamped_exists:
                # Compare sizes
                timestamped_file = timestamped_files[-1]  # Get most recent
                timestamped_size = os.path.getsize(timestamped_file)
                
                if abs(generic_size - timestamped_size) < 100:  # Allow small differences
                    print(f"  ✅ {os.path.basename(generic_file)}")
                    print(f"     Generic: {generic_size:,} bytes")
                    print(f"     Timestamped: {timestamped_size:,} bytes ({len(timestamped_files)} versions)")
                    step_results["size_matches"].append(generic_file)
                    passed_checks += 1
                else:
                    print(f"  ⚠️  {os.path.basename(generic_file)} - SIZE MISMATCH")
                    print(f"     Generic: {generic_size:,} bytes")
                    print(f"     Timestamped: {timestamped_size:,} bytes")
                    step_results["size_mismatches"].append(generic_file)
                    failed_checks += 1
                    
            elif generic_exists and not timestamped_exists:
                print(f"  ⚠️  {os.path.basename(generic_file)} - MISSING TIMESTAMPED VERSION")
                step_results["missing_timestamped"].append(generic_file)
                failed_checks += 1
                
            elif not generic_exists and timestamped_exists:
                print(f"  ⚠️  {os.path.basename(generic_file)} - MISSING GENERIC VERSION")
                print(f"     Found {len(timestamped_files)} timestamped version(s)")
                step_results["missing_generic"].append(generic_file)
                failed_checks += 1
                
            else:
                print(f"  ❌ {os.path.basename(generic_file)} - BOTH VERSIONS MISSING")
                step_results["missing_generic"].append(generic_file)
                step_results["missing_timestamped"].append(generic_file)
                failed_checks += 1
        
        print()
        results[step_name] = step_results
    
    # Print summary
    print("=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Checks: {total_checks}")
    print(f"✅ Passed: {passed_checks} ({passed_checks/total_checks*100:.1f}%)")
    print(f"❌ Failed: {failed_checks} ({failed_checks/total_checks*100:.1f}%)")
    print()
    
    if failed_checks == 0:
        print("🎉 SUCCESS: All dual output patterns validated!")
        print("   - All generic files exist")
        print("   - All timestamped files exist")
        print("   - File sizes match between versions")
    else:
        print("⚠️  ISSUES FOUND: Some dual output patterns incomplete")
        print("   Review the details above for specific missing files")
    
    print()
    return results

def check_pipeline_manifest():
    """Check if pipeline manifest has been updated"""
    manifest_file = "pipeline_manifest.json"
    
    print("📋 Checking Pipeline Manifest")
    print("=" * 80)
    
    if os.path.exists(manifest_file):
        import json
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        print(f"✅ Manifest exists: {manifest_file}")
        print(f"   Steps registered: {len(manifest.get('steps', {}))}")
        
        # Check for our fixed steps
        fixed_steps = ['step13', 'step14', 'step15', 'step16', 'step17', 'step18', 
                      'step19', 'step20', 'step21', 'step22']
        
        for step in fixed_steps:
            if step in manifest.get('steps', {}):
                outputs = manifest['steps'][step].get('outputs', {})
                print(f"   {step}: {len(outputs)} outputs registered")
            else:
                print(f"   {step}: ⚠️  Not registered")
    else:
        print(f"⚠️  Manifest not found: {manifest_file}")
    
    print()

if __name__ == "__main__":
    print()
    print("🔍 DUAL OUTPUT PATTERN VALIDATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {os.getcwd()}")
    print()
    
    # Run validation
    results = check_dual_outputs()
    
    # Check manifest
    check_pipeline_manifest()
    
    print("✅ Validation complete!")
    print()
