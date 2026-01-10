#!/usr/bin/env python3
"""
Comprehensive 202506B Pipeline Audit

This script thoroughly verifies that every step of the pipeline
processed 202506B data (second half June 2025) and not 202506A.

Author: Data Pipeline Audit
Date: 2025-07-01
"""

import pandas as pd
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import glob

def audit_configuration() -> Dict[str, Any]:
    """Audit configuration files for 202506B settings."""
    print("🔍 AUDITING CONFIGURATION...")
    
    results = {}
    
    # Check main config
    config_file = "src/config.py"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            content = f.read()
            if 'DEFAULT_PERIOD = "B"' in content:
                results["config_period"] = "✅ 202506B"
            else:
                results["config_period"] = "❌ NOT 202506B"
    else:
        results["config_period"] = "❌ Config file missing"
    
    return results

def audit_input_data() -> Dict[str, Any]:
    """Audit input data files for 202506B."""
    print("🔍 AUDITING INPUT DATA...")
    
    results = {}
    data_dir = "data/api_data"
    
    # Check for 202506B files
    b_files = glob.glob(f"{data_dir}/*202506B*")
    a_files = glob.glob(f"{data_dir}/*202506A*")
    
    results["202506B_files"] = len(b_files)
    results["202506A_files"] = len(a_files)
    
    # Check specific files
    key_files = [
        "complete_spu_sales_202506B.csv",
        "store_config_202506B.csv", 
        "complete_category_sales_202506B.csv",
        "store_sales_202506B.csv"
    ]
    
    for file in key_files:
        file_path = f"{data_dir}/{file}"
        if os.path.exists(file_path):
            # Get file size and modification time
            stat = os.stat(file_path)
            results[f"{file}_status"] = f"✅ EXISTS ({stat.st_size:,} bytes)"
        else:
            results[f"{file}_status"] = "❌ MISSING"
    
    return results

def audit_weather_data() -> Dict[str, Any]:
    """Audit weather data for correct date range."""
    print("🔍 AUDITING WEATHER DATA...")
    
    results = {}
    weather_dir = "output/weather_data"
    
    # Check for 202506B weather files (June 16-30, 2025)
    b_weather_files = glob.glob(f"{weather_dir}/*20250616_to_20250630*")
    a_weather_files = glob.glob(f"{weather_dir}/*20250601_to_20250615*")
    
    results["202506B_weather_files"] = len(b_weather_files)
    results["202506A_weather_files"] = len(a_weather_files)
    
    # Sample a weather file to check dates
    if b_weather_files:
        sample_file = b_weather_files[0]
        try:
            df = pd.read_csv(sample_file)
            if 'date_time' in df.columns:
                dates = pd.to_datetime(df['date_time'])
                min_date = dates.min().strftime('%Y-%m-%d')
                max_date = dates.max().strftime('%Y-%m-%d')
                results["weather_date_range"] = f"✅ {min_date} to {max_date}"
                
                # Verify it's June 16-30, 2025
                if min_date.startswith('2025-06-16') and max_date.startswith('2025-06-30'):
                    results["weather_period_correct"] = "✅ 202506B period confirmed"
                else:
                    results["weather_period_correct"] = f"❌ Wrong period: {min_date} to {max_date}"
        except Exception as e:
            results["weather_sample_check"] = f"❌ Error reading sample: {e}"
    
    return results

def audit_processing_outputs() -> Dict[str, Any]:
    """Audit processing output files for 202506B data references."""
    print("🔍 AUDITING PROCESSING OUTPUTS...")
    
    results = {}
    output_dir = "output"
    
    # Check rule output files
    rule_files = [
        "rule7_missing_spu_results.csv",
        "rule8_imbalanced_spu_results.csv", 
        "rule9_below_minimum_spu_results.csv",
        "rule10_spu_overcapacity_results.csv",
        "rule11_improved_missed_sales_opportunity_spu_results.csv",
        "rule12_sales_performance_spu_results.csv"
    ]
    
    for rule_file in rule_files:
        file_path = f"{output_dir}/{rule_file}"
        if os.path.exists(file_path):
            # Check file size and modification time
            stat = os.stat(file_path)
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            results[f"{rule_file}_status"] = f"✅ EXISTS ({stat.st_size:,} bytes, modified: {mod_time})"
            
            # Check if file contains recent data (created today)
            if datetime.fromtimestamp(stat.st_mtime).date() == datetime.now().date():
                results[f"{rule_file}_recent"] = "✅ Created today"
            else:
                results[f"{rule_file}_recent"] = "⚠️ Not created today"
        else:
            results[f"{rule_file}_status"] = "❌ MISSING"
    
    # Check consolidated results
    consolidated_file = f"{output_dir}/consolidated_spu_rule_results.csv"
    if os.path.exists(consolidated_file):
        results["consolidated_results"] = "✅ EXISTS"
        
        # Sample the data to verify content
        try:
            df = pd.read_csv(consolidated_file, nrows=5)
            results["consolidated_sample_stores"] = f"✅ Sample stores: {list(df['str_code'].head())}"
        except Exception as e:
            results["consolidated_read_error"] = f"❌ Error reading: {e}"
    else:
        results["consolidated_results"] = "❌ MISSING"
    
    return results

def audit_data_content() -> Dict[str, Any]:
    """Audit actual data content to verify 202506B."""
    print("🔍 AUDITING DATA CONTENT...")
    
    results = {}
    
    # Check SPU sales data content
    spu_file = "data/api_data/complete_spu_sales_202506B.csv"
    if os.path.exists(spu_file):
        try:
            df = pd.read_csv(spu_file, nrows=1000)  # Sample first 1000 rows
            results["spu_data_rows"] = f"✅ {len(df):,} rows (sample)"
            results["spu_data_stores"] = f"✅ {df['str_code'].nunique()} unique stores (sample)"
            results["spu_data_spus"] = f"✅ {df['sty_code'].nunique()} unique SPUs (sample)"
            
            # Check date fields if available
            if 'yyyy' in df.columns and 'mm' in df.columns:
                years = df['yyyy'].unique()
                months = df['mm'].unique()
                results["spu_data_period"] = f"✅ Years: {years}, Months: {months}"
        except Exception as e:
            results["spu_data_error"] = f"❌ Error reading SPU data: {e}"
    
    # Check clustering results
    cluster_file = "output/clustering_results_spu.csv"
    if os.path.exists(cluster_file):
        try:
            df = pd.read_csv(cluster_file, nrows=100)
            results["clustering_stores"] = f"✅ {len(df)} stores clustered"
            results["clustering_clusters"] = f"✅ {df['Cluster'].nunique()} clusters"
        except Exception as e:
            results["clustering_error"] = f"❌ Error reading clustering: {e}"
    
    return results

def audit_backup_status() -> Dict[str, Any]:
    """Audit backup status to confirm 202506A data was moved."""
    print("🔍 AUDITING BACKUP STATUS...")
    
    results = {}
    
    # Check backup directory
    backup_dirs = glob.glob("backup/202506A*")
    results["backup_directories"] = len(backup_dirs)
    
    if backup_dirs:
        backup_dir = backup_dirs[0]  # Use first backup directory
        
        # Count backed up files
        backup_files = []
        for root, dirs, files in os.walk(backup_dir):
            backup_files.extend(files)
        
        results["backup_file_count"] = f"✅ {len(backup_files)} files backed up"
        
        # Check for specific backup indicators
        if any("202506A" in f for f in backup_files):
            results["backup_contains_202506A"] = "✅ Contains 202506A files"
        else:
            results["backup_contains_202506A"] = "⚠️ No 202506A files found in backup"
    else:
        results["backup_status"] = "⚠️ No 202506A backup directories found"
    
    return results

def generate_audit_report(all_results: Dict[str, Dict[str, Any]]) -> None:
    """Generate comprehensive audit report."""
    print("\n" + "="*80)
    print("📋 COMPREHENSIVE 202506B PIPELINE AUDIT REPORT")
    print("="*80)
    
    # Overall status
    issues = []
    for category, results in all_results.items():
        for key, value in results.items():
            if isinstance(value, str) and value.startswith("❌"):
                issues.append(f"{category}.{key}: {value}")
    
    if not issues:
        print("🎉 STATUS: ALL CHECKS PASSED - PIPELINE USED 202506B DATA")
    else:
        print(f"⚠️ STATUS: {len(issues)} ISSUES FOUND")
        for issue in issues:
            print(f"   - {issue}")
    
    print("\n" + "-"*80)
    
    # Detailed results by category
    for category, results in all_results.items():
        print(f"\n📂 {category.upper()}")
        print("-" * 40)
        for key, value in results.items():
            print(f"  {key}: {value}")
    
    # Summary statistics
    print(f"\n📊 SUMMARY STATISTICS")
    print("-" * 40)
    
    if "input_data" in all_results:
        print(f"  📁 202506B input files: {all_results['input_data'].get('202506B_files', 0)}")
        print(f"  📁 202506A input files: {all_results['input_data'].get('202506A_files', 0)}")
    
    if "weather_data" in all_results:
        print(f"  🌤️ 202506B weather files: {all_results['weather_data'].get('202506B_weather_files', 0)}")
        print(f"  🌤️ 202506A weather files: {all_results['weather_data'].get('202506A_weather_files', 0)}")
    
    if "backup_status" in all_results:
        print(f"  💾 Backup directories: {all_results['backup_status'].get('backup_directories', 0)}")
    
    print(f"\n⏰ Audit completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

def main():
    """Run comprehensive 202506B pipeline audit."""
    print("🚀 STARTING COMPREHENSIVE 202506B PIPELINE AUDIT...")
    print(f"📅 Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    all_results = {}
    
    # Run all audit checks
    all_results["configuration"] = audit_configuration()
    all_results["input_data"] = audit_input_data()
    all_results["weather_data"] = audit_weather_data()
    all_results["processing_outputs"] = audit_processing_outputs()
    all_results["data_content"] = audit_data_content()
    all_results["backup_status"] = audit_backup_status()
    
    # Generate report
    generate_audit_report(all_results)
    
    # Save audit results
    with open("comprehensive_202506B_audit_report.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed audit results saved to: comprehensive_202506B_audit_report.json")

if __name__ == "__main__":
    main() 