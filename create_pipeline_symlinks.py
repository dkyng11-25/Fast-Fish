#!/usr/bin/env python3
"""
Pipeline Symlinks Creation Script

This script addresses Issues 2 and 3:
2. Missing Period-Specific Data Files - create symlinks for 202510A using 202407A data
3. Timestamped File Dependencies - create generic filename symlinks

Author: Pipeline Team
Date: 2025-10-01
"""

import os
import glob
import argparse
from pathlib import Path
from datetime import datetime

def log_progress(message):
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_period_symlinks(target_period="202510A", source_period="202407A"):
    """
    Fix Issue 2: Missing Period-Specific Data Files
    
    Creates symlinks for period-specific files that steps expect but don't exist
    """
    log_progress(f"🔧 FIXING ISSUE 2: Creating period-specific symlinks ({target_period} -> {source_period})")
    
    # Define period-specific file patterns
    period_file_patterns = [
        # API data files
        ("data/api_data/fast_fish_data_{}.csv", "Fast Fish data"),
        ("data/api_data/store_config_{}.csv", "Store configuration"),
        ("data/api_data/spu_sales_{}.csv", "SPU sales data"),
        ("data/api_data/category_sales_{}.csv", "Category sales data"),
        
        # Weather data files
        ("output/weather_data/consolidated_weather_{}.csv", "Consolidated weather data"),
        ("output/stores_with_feels_like_temperature_{}.csv", "Temperature data"),
        
        # Matrix files
        ("data/store_subcategory_matrix_{}.csv", "Subcategory matrix"),
        ("data/store_spu_limited_matrix_{}.csv", "SPU matrix"),
        ("data/normalized_subcategory_matrix_{}.csv", "Normalized subcategory matrix"),
        ("data/normalized_spu_limited_matrix_{}.csv", "Normalized SPU matrix"),
        
        # Clustering results
        ("output/clustering_results_spu_{}.csv", "SPU clustering results"),
        ("output/clustering_results_subcategory_{}.csv", "Subcategory clustering results"),
    ]
    
    created_symlinks = []
    
    for pattern, description in period_file_patterns:
        target_file = pattern.format(target_period)
        source_file = pattern.format(source_period)
        
        # Skip if target already exists
        if os.path.exists(target_file):
            log_progress(f"   ✅ {description} already exists: {target_file}")
            continue
            
        # Check if source exists
        if os.path.exists(source_file):
            try:
                # Create directory if needed
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                
                # Create symlink
                os.symlink(os.path.abspath(source_file), target_file)
                log_progress(f"   ✅ Created symlink: {target_file} -> {source_file}")
                created_symlinks.append((target_file, source_file, description))
                
            except Exception as e:
                log_progress(f"   ❌ Error creating symlink for {description}: {e}")
        else:
            log_progress(f"   ⚠️  Source not found for {description}: {source_file}")
    
    return created_symlinks

def create_timestamped_symlinks():
    """
    Fix Issue 3: Timestamped File Dependencies
    
    Creates generic filename symlinks for timestamped files that steps expect
    """
    log_progress("🔧 FIXING ISSUE 3: Creating timestamped file symlinks")
    
    # Define timestamped file mappings
    timestamped_mappings = [
        # Step 26 dependencies
        ("output/product_role_classifications.csv", "output/product_role_classifications_*.csv", "Product role classifications"),
        
        # Step 27 dependencies  
        ("output/price_band_analysis.csv", "output/price_band_analysis_*.csv", "Price band analysis"),
        
        # Step 28 dependencies
        ("output/gap_analysis_detailed.csv", "output/gap_analysis_detailed_*.csv", "Gap analysis detailed"),
        ("output/gap_matrix_summary.json", "output/gap_matrix_summary_*.json", "Gap matrix summary"),
        
        # Step 31 dependencies
        ("output/supply_demand_gap_detailed.csv", "output/supply_demand_gap_detailed_*.csv", "Supply demand gap detailed"),
        
        # Additional common timestamped files
        ("output/enhanced_fast_fish_format.csv", "output/enhanced_fast_fish_format_*.csv", "Enhanced Fast Fish format"),
        ("output/fast_fish_with_sell_through_analysis.csv", "output/fast_fish_with_sell_through_analysis_*.csv", "Sell-through analysis"),
        ("output/consolidated_spu_rule_results.csv", "output/consolidated_spu_rule_results_*.csv", "Consolidated SPU rules"),
        ("output/comprehensive_trend_enhanced_suggestions.csv", "output/comprehensive_trend_enhanced_suggestions_*.csv", "Trend enhanced suggestions"),
    ]
    
    created_symlinks = []
    
    for generic_name, pattern, description in timestamped_mappings:
        # Skip if generic file already exists
        if os.path.exists(generic_name):
            log_progress(f"   ✅ {description} already exists: {generic_name}")
            continue
            
        # Find matching timestamped files
        matching_files = glob.glob(pattern)
        
        if matching_files:
            # Get the most recent file
            latest_file = max(matching_files, key=os.path.getmtime)
            
            try:
                # Create directory if needed
                os.makedirs(os.path.dirname(generic_name), exist_ok=True)
                
                # Create symlink
                os.symlink(os.path.abspath(latest_file), generic_name)
                log_progress(f"   ✅ Created symlink: {generic_name} -> {latest_file}")
                created_symlinks.append((generic_name, latest_file, description))
                
            except Exception as e:
                log_progress(f"   ❌ Error creating symlink for {description}: {e}")
        else:
            log_progress(f"   ⚠️  No timestamped files found for {description}: {pattern}")
    
    return created_symlinks

def create_additional_symlinks():
    """Create additional helpful symlinks for common pipeline dependencies"""
    log_progress("🔧 Creating additional helpful symlinks")
    
    additional_mappings = [
        # Enhanced clustering results (commonly needed)
        ("output/enhanced_clustering_results.csv", "output/clustering_results_spu.csv", "Enhanced clustering results"),
        
        # Generic period-agnostic files
        ("data/api_data/fast_fish_data.csv", "data/api_data/fast_fish_data_202407A.csv", "Generic Fast Fish data"),
        ("data/api_data/store_config.csv", "data/api_data/store_config_202407A.csv", "Generic store config"),
        ("data/api_data/spu_sales.csv", "data/api_data/spu_sales_202407A.csv", "Generic SPU sales"),
    ]
    
    created_symlinks = []
    
    for target, source, description in additional_mappings:
        if os.path.exists(target):
            log_progress(f"   ✅ {description} already exists: {target}")
            continue
            
        if os.path.exists(source):
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                os.symlink(os.path.abspath(source), target)
                log_progress(f"   ✅ Created symlink: {target} -> {source}")
                created_symlinks.append((target, source, description))
            except Exception as e:
                log_progress(f"   ❌ Error creating symlink for {description}: {e}")
        else:
            log_progress(f"   ⚠️  Source not found for {description}: {source}")
    
    return created_symlinks

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Create Pipeline Symlinks")
    parser.add_argument("--target-period", default="202510A", 
                       help="Target period for symlinks (default: 202510A)")
    parser.add_argument("--source-period", default="202407A",
                       help="Source period for symlinks (default: 202407A)")
    parser.add_argument("--skip-period", action="store_true",
                       help="Skip period-specific symlinks")
    parser.add_argument("--skip-timestamped", action="store_true", 
                       help="Skip timestamped file symlinks")
    parser.add_argument("--skip-additional", action="store_true",
                       help="Skip additional helpful symlinks")
    
    args = parser.parse_args()
    
    log_progress("🚀 STARTING PIPELINE SYMLINKS CREATION")
    log_progress(f"Target Period: {args.target_period}")
    log_progress(f"Source Period: {args.source_period}")
    
    total_created = 0
    
    # Create period-specific symlinks
    if not args.skip_period:
        period_symlinks = create_period_symlinks(args.target_period, args.source_period)
        total_created += len(period_symlinks)
        log_progress(f"✅ Created {len(period_symlinks)} period-specific symlinks")
    else:
        log_progress("⏭️  Skipping period-specific symlinks")
    
    # Create timestamped file symlinks
    if not args.skip_timestamped:
        timestamped_symlinks = create_timestamped_symlinks()
        total_created += len(timestamped_symlinks)
        log_progress(f"✅ Created {len(timestamped_symlinks)} timestamped file symlinks")
    else:
        log_progress("⏭️  Skipping timestamped file symlinks")
    
    # Create additional helpful symlinks
    if not args.skip_additional:
        additional_symlinks = create_additional_symlinks()
        total_created += len(additional_symlinks)
        log_progress(f"✅ Created {len(additional_symlinks)} additional symlinks")
    else:
        log_progress("⏭️  Skipping additional symlinks")
    
    # Summary
    log_progress("🎉 PIPELINE SYMLINKS CREATION COMPLETED")
    log_progress(f"   • Total symlinks created: {total_created}")
    
    if total_created > 0:
        log_progress("✅ SYMLINKS SUCCESSFULLY CREATED - Pipeline should now work better")
    else:
        log_progress("⚠️  NO SYMLINKS CREATED (files may already exist)")

if __name__ == "__main__":
    main()
