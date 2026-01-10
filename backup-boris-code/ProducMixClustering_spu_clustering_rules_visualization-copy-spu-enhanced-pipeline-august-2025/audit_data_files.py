#!/usr/bin/env python3
"""
Comprehensive Data File Audit for Product Mix Clustering Pipeline

This script audits all data files required by the pipeline steps to ensure
they exist and are accessible. It identifies missing files and provides
a summary of the data availability.

Author: Data Pipeline
Date: 2025-01-02
"""

import os
import sys
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import pandas as pd

def check_file_exists(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a file exists and return status with file size info.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        Tuple of (exists, size_info)
    """
    try:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if size > 1024 * 1024:  # > 1MB
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:  # > 1KB
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} bytes"
            return True, size_str
        else:
            return False, None
    except Exception as e:
        return False, f"Error: {str(e)}"

def audit_step_files() -> Dict[str, Dict[str, Tuple[bool, Optional[str]]]]:
    """
    Audit all files required by pipeline steps.
    
    Returns:
        Dictionary mapping step names to file status
    """
    
    # Define all files required by each step
    step_files = {
        "Step 1 - API Data Download": {
            "Input Files": {
                "data/store_codes.csv": "Store codes for API calls"
            },
            "Output Files": {
                "data/api_data/complete_spu_sales_202505.csv": "SPU sales data (May 2025)",
                "data/api_data/complete_spu_sales_202506A.csv": "SPU sales data (June 2025A)",
                "data/api_data/complete_category_sales_202505.csv": "Category sales data (May 2025)",
                "data/api_data/complete_category_sales_202506A.csv": "Category sales data (June 2025A)",
                "data/api_data/store_config_202506A.csv": "Store configuration data",
                "data/api_data/store_sales_202506A.csv": "Store sales summary data",
                "data/api_data/store_config_data.csv": "Legacy store config (compatibility)",
                "data/api_data/store_sales_data.csv": "Legacy store sales (compatibility)"
            }
        },
        
        "Step 2 - Coordinate Extraction": {
            "Input Files": {
                "data/api_data/store_config_data.csv": "Store configuration data",
                "data/api_data/store_sales_data.csv": "Store sales data",
                "data/api_data/complete_category_sales_202505.csv": "Category sales (fallback)",
                "data/store_codes.csv": "Store codes"
            },
            "Output Files": {
                "data/store_coordinates_extended.csv": "Store coordinates with metadata",
                "data/spu_store_mapping.csv": "SPU to store mapping",
                "data/spu_metadata.csv": "SPU metadata"
            }
        },
        
        "Step 3 - Matrix Preparation": {
            "Input Files": {
                "data/store_coordinates_extended.csv": "Store coordinates",
                "data/api_data/complete_category_sales_202505.csv": "Category sales data",
                "data/api_data/complete_spu_sales_202505.csv": "SPU sales data"
            },
            "Output Files": {
                "data/store_subcategory_matrix.csv": "Subcategory matrix (original)",
                "data/normalized_subcategory_matrix.csv": "Subcategory matrix (normalized)",
                "data/store_spu_limited_matrix.csv": "SPU matrix (original)",
                "data/normalized_spu_limited_matrix.csv": "SPU matrix (normalized)",
                "data/store_category_agg_matrix.csv": "Category matrix (original)",
                "data/normalized_category_agg_matrix.csv": "Category matrix (normalized)"
            }
        },
        
        "Step 4 - Weather Data": {
            "Input Files": {
                "data/store_coordinates_extended.csv": "Store coordinates"
            },
            "Output Files": {
                "output/store_altitudes.csv": "Store altitude data"
            }
        },
        
        "Step 5 - Temperature Calculation": {
            "Input Files": {
                "output/store_altitudes.csv": "Store altitude data"
            },
            "Output Files": {
                "output/stores_with_feels_like_temperature.csv": "Temperature data",
                "output/temperature_bands.csv": "Temperature bands"
            }
        },
        
        "Step 6 - Clustering Analysis": {
            "Input Files": {
                "data/normalized_subcategory_matrix.csv": "Normalized subcategory matrix",
                "data/normalized_spu_limited_matrix.csv": "Normalized SPU matrix",
                "data/normalized_category_agg_matrix.csv": "Normalized category matrix",
                "output/stores_with_feels_like_temperature.csv": "Temperature data"
            },
            "Output Files": {
                "output/clustering_results_subcategory.csv": "Subcategory clustering results",
                "output/clustering_results_spu.csv": "SPU clustering results",
                "output/clustering_results.csv": "Legacy clustering results",
                "output/cluster_profiles_subcategory.csv": "Subcategory cluster profiles",
                "output/cluster_profiles_spu.csv": "SPU cluster profiles"
            }
        },
        
        "Step 7 - Missing Category Rule": {
            "Input Files": {
                "output/clustering_results_subcategory.csv": "Subcategory clustering",
                "output/clustering_results_spu.csv": "SPU clustering",
                "data/api_data/complete_category_sales_202505.csv": "Category sales",
                "data/api_data/complete_spu_sales_202505.csv": "SPU sales"
            },
            "Output Files": {
                "output/rule7_missing_subcategory_results.csv": "Missing subcategory results",
                "output/rule7_missing_spu_results.csv": "Missing SPU results",
                "output/rule7_missing_subcategory_opportunities.csv": "Subcategory opportunities",
                "output/rule7_missing_spu_opportunities.csv": "SPU opportunities"
            }
        },
        
        "Step 8 - Imbalanced Rule": {
            "Input Files": {
                "output/clustering_results_subcategory.csv": "Subcategory clustering",
                "output/clustering_results_spu.csv": "SPU clustering",
                "data/api_data/store_config_data.csv": "Store configuration"
            },
            "Output Files": {
                "output/rule8_imbalanced_subcategory_results.csv": "Imbalanced subcategory results",
                "output/rule8_imbalanced_spu_results.csv": "Imbalanced SPU results",
                "output/rule8_imbalanced_subcategory_cases.csv": "Subcategory cases",
                "output/rule8_imbalanced_spu_cases.csv": "SPU cases"
            }
        },
        
        "Step 9 - Below Minimum Rule": {
            "Input Files": {
                "output/clustering_results_subcategory.csv": "Subcategory clustering",
                "output/clustering_results_spu.csv": "SPU clustering",
                "data/api_data/store_config_data.csv": "Store configuration"
            },
            "Output Files": {
                "output/rule9_below_minimum_subcategory_results.csv": "Below minimum subcategory results",
                "output/rule9_below_minimum_spu_results.csv": "Below minimum SPU results",
                "output/rule9_below_minimum_subcategory_cases.csv": "Subcategory cases",
                "output/rule9_below_minimum_spu_cases.csv": "SPU cases"
            }
        },
        
        "Step 10 - SPU Assortment Optimization": {
            "Input Files": {
                "output/clustering_results.csv": "Clustering results",
                "data/api_data/store_config_data.csv": "Store configuration"
            },
            "Output Files": {
                "output/rule10_spu_overcapacity_results.csv": "Overcapacity results",
                "output/rule10_spu_overcapacity_opportunities.csv": "Overcapacity opportunities"
            }
        },
        
        "Step 11 - Improved Category Logic (Rule 11)": {
            "Input Files": {
                "output/clustering_results_spu.csv": "SPU clustering results",
                "data/api_data/complete_spu_sales_202505.csv": "SPU sales data",
                "data/api_data/store_sales_data.csv": "Store quantity data"
            },
            "Output Files": {
                "output/rule11_improved_missed_sales_opportunity_spu_results.csv": "Rule 11 results",
                "output/rule11_improved_missed_sales_opportunity_spu_details.csv": "Rule 11 details",
                "output/rule11_improved_top_performers_by_cluster_category.csv": "Top performers"
            }
        },
        
        "Step 12 - Sales Performance Rule": {
            "Input Files": {
                "output/clustering_results.csv": "Clustering results",
                "data/api_data/complete_category_sales_202505.csv": "Category sales",
                "data/api_data/store_config_data.csv": "Store configuration"
            },
            "Output Files": {
                "output/rule12_sales_performance_subcategory_results.csv": "Performance results",
                "output/rule12_sales_performance_subcategory_details.csv": "Performance details"
            }
        },
        
        "Step 13 - Consolidation": {
            "Input Files": {
                "output/clustering_results.csv": "Clustering results",
                "output/rule7_missing_spu_results.csv": "Rule 7 results",
                "output/rule8_imbalanced_spu_results.csv": "Rule 8 results",
                "output/rule9_below_minimum_spu_results.csv": "Rule 9 results",
                "output/rule10_spu_overcapacity_results.csv": "Rule 10 results",
                "output/rule11_improved_missed_sales_opportunity_spu_results.csv": "Rule 11 results",
                "output/rule12_sales_performance_spu_results.csv": "Rule 12 results"
            },
            "Output Files": {
                "output/consolidated_spu_rule_results.csv": "Consolidated SPU results",
                "output/consolidated_rule_results.csv": "Consolidated legacy results"
            }
        },
        
        "Step 14 - Global Dashboard": {
            "Input Files": {
                "output/consolidated_spu_rule_results.csv": "Consolidated results"
            },
            "Output Files": {
                "Dashboard HTML files": "Generated dashboards"
            }
        },
        
        "Step 15 - Interactive Map Dashboard": {
            "Input Files": {
                "output/rule7_missing_spu_opportunities.csv": "Rule 7 opportunities",
                "output/rule8_imbalanced_spu_cases.csv": "Rule 8 cases",
                "output/rule9_below_minimum_spu_cases.csv": "Rule 9 cases",
                "output/rule10_spu_overcapacity_opportunities.csv": "Rule 10 opportunities",
                "output/rule11_improved_missed_sales_opportunity_spu_details.csv": "Rule 11 details",
                "output/rule12_sales_performance_spu_details.csv": "Rule 12 details",
                "data/store_coordinates_extended.csv": "Store coordinates"
            },
            "Output Files": {
                "Interactive map HTML": "Generated map dashboard"
            }
        }
    }
    
    # Check all files
    audit_results = {}
    
    for step_name, file_categories in step_files.items():
        audit_results[step_name] = {}
        
        for category, files in file_categories.items():
            audit_results[step_name][category] = {}
            
            for file_path, description in files.items():
                if file_path.endswith('.csv') or file_path.endswith('.txt'):
                    exists, info = check_file_exists(file_path)
                    audit_results[step_name][category][file_path] = (exists, info, description)
    
    return audit_results

def print_audit_summary(audit_results: Dict) -> None:
    """
    Print a comprehensive audit summary.
    
    Args:
        audit_results: Results from audit_step_files()
    """
    
    print("=" * 80)
    print("📊 COMPREHENSIVE DATA FILE AUDIT FOR PRODUCT MIX CLUSTERING PIPELINE")
    print("=" * 80)
    print()
    
    total_files = 0
    missing_files = 0
    existing_files = 0
    
    critical_missing = []
    
    for step_name, categories in audit_results.items():
        print(f"🔍 {step_name}")
        print("-" * len(step_name) + "---")
        
        step_total = 0
        step_missing = 0
        step_existing = 0
        
        for category, files in categories.items():
            if not files:
                continue
                
            print(f"\n  📁 {category}:")
            
            for file_path, (exists, info, description) in files.items():
                step_total += 1
                total_files += 1
                
                if exists:
                    step_existing += 1
                    existing_files += 1
                    print(f"    ✅ {file_path} ({info})")
                    print(f"       └─ {description}")
                else:
                    step_missing += 1
                    missing_files += 1
                    print(f"    ❌ {file_path} - MISSING")
                    print(f"       └─ {description}")
                    
                    # Mark critical files
                    if category == "Input Files" and any(critical in file_path for critical in [
                        'store_codes.csv', 'complete_spu_sales', 'complete_category_sales', 
                        'store_config_data.csv', 'store_sales_data.csv'
                    ]):
                        critical_missing.append((step_name, file_path, description))
        
        # Step summary
        if step_total > 0:
            success_rate = (step_existing / step_total) * 100
            print(f"\n  📈 Step Summary: {step_existing}/{step_total} files present ({success_rate:.1f}%)")
        
        print()
    
    # Overall summary
    print("=" * 80)
    print("📋 OVERALL AUDIT SUMMARY")
    print("=" * 80)
    
    if total_files > 0:
        success_rate = (existing_files / total_files) * 100
        print(f"📊 Total Files Checked: {total_files}")
        print(f"✅ Files Present: {existing_files}")
        print(f"❌ Files Missing: {missing_files}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
    else:
        print("⚠️  No files found to audit")
    
    # Critical missing files
    if critical_missing:
        print(f"\n🚨 CRITICAL MISSING FILES ({len(critical_missing)}):")
        print("These files are essential for pipeline execution:")
        for step, file_path, description in critical_missing:
            print(f"  ❌ {file_path}")
            print(f"     └─ Required by: {step}")
            print(f"     └─ Purpose: {description}")
    
    # Weather data check
    weather_dir = "output/weather_data"
    if os.path.exists(weather_dir):
        weather_files = len([f for f in os.listdir(weather_dir) if f.endswith('.csv')])
        print(f"\n🌤️  Weather Data: {weather_files} weather CSV files found in {weather_dir}/")
    else:
        print(f"\n❌ Weather Data Directory Missing: {weather_dir}/")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    if missing_files == 0:
        print("🎉 All required files are present! The pipeline should run successfully.")
    elif critical_missing:
        print("⚠️  Critical files are missing. Please:")
        print("   1. Run Step 1 (API data download) to generate core data files")
        print("   2. Ensure store_codes.csv is present in the data/ directory")
        print("   3. Check network connectivity for API calls")
    else:
        print("ℹ️  Some output files are missing, which is expected if:")
        print("   1. The pipeline hasn't been run yet")
        print("   2. Some steps have been skipped")
        print("   3. The pipeline was interrupted")
        print("\n   Run the pipeline from the beginning to generate all files.")
    
    print("\n📝 To resolve missing files:")
    print("   • Run: python pipeline.py")
    print("   • Or run individual steps: python src/stepXX_*.py")
    print()

def check_data_integrity() -> None:
    """
    Perform additional data integrity checks on key files.
    """
    
    print("=" * 80)
    print("🔍 DATA INTEGRITY CHECKS")
    print("=" * 80)
    
    key_files = [
        ("data/store_codes.csv", "Store codes"),
        ("data/api_data/store_sales_data.csv", "Store sales data"),
        ("data/api_data/complete_spu_sales_202505.csv", "SPU sales data"),
        ("output/clustering_results_spu.csv", "SPU clustering results")
    ]
    
    for file_path, description in key_files:
        print(f"\n📄 {description}: {file_path}")
        
        if not os.path.exists(file_path):
            print("   ❌ File not found")
            continue
        
        try:
            df = pd.read_csv(file_path, nrows=5)  # Read first 5 rows only
            print(f"   ✅ Readable CSV with {len(df.columns)} columns")
            print(f"   📊 Columns: {', '.join(df.columns.tolist()[:5])}{'...' if len(df.columns) > 5 else ''}")
            
            # Check for str_code column (critical for joins)
            if 'str_code' in df.columns:
                print("   ✅ Contains 'str_code' column (required for joins)")
            else:
                print("   ⚠️  Missing 'str_code' column")
                
        except Exception as e:
            print(f"   ❌ Error reading file: {str(e)}")

def main():
    """Main audit function."""
    
    print("Starting comprehensive data file audit...")
    print()
    
    # Perform file existence audit
    audit_results = audit_step_files()
    print_audit_summary(audit_results)
    
    # Perform data integrity checks
    check_data_integrity()
    
    print("=" * 80)
    print("✅ AUDIT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main() 