#!/usr/bin/env python3
"""
Product Mix Clustering & Rule Analysis Pipeline - Main Execution Module

A comprehensive 15-step pipeline for retail product mix optimization through clustering
analysis and business rule validation. This pipeline processes store sales data, applies
weather-aware clustering, and identifies optimization opportunities through 6 business rules.

PIPELINE ARCHITECTURE:
=====================

19-Step Pipeline Structure:
1. Data Collection & Processing (Steps 1-3): API download → Coordinates → Matrix preparation
2. Weather Integration (Steps 4-5): Weather data → Temperature analysis  
3. Clustering Analysis (Step 6): Temperature-aware store clustering
4. Business Rules Analysis (Steps 7-12): 6 optimization rules analysis
5. Visualization & Consolidation (Steps 13-15): Consolidation → Dashboards
6. Advanced Analysis (Steps 16-19): Historical comparison, trending, validation, SPU breakdown

PIPELINE STEPS:
==============

Phase 1: Data Collection & Processing
- Step 1: API Data Download (~15 min) - Download store/sales data from API
- Step 2: Coordinate Extraction (~1 min) - Extract geographic coordinates  
- Step 3: Matrix Preparation (<1 min) - Create clustering matrices

Phase 2: Weather Integration
- Step 4: Weather Data Download (<1 min) - Load weather information
- Step 5: Temperature Calculation (~14 min) - Calculate feels-like temperatures

Phase 3: Clustering Analysis  
- Step 6: Cluster Analysis (<1 min) - Create temperature-aware store clusters

Phase 4: Business Rules Analysis
- Step 7: Missing Category Rule (~1 min) - Identify missing subcategory opportunities
- Step 8: Imbalanced Rule (~2 min) - Detect imbalanced SPU allocations
- Step 9: Below Minimum Rule (~1 min) - Find subcategories below thresholds
- Step 10: Smart Overcapacity Rule (<1 min) - Identify reallocation opportunities
- Step 11: Missed Sales Opportunity Rule (~14 min) - Detect missed sales opportunities
- Step 12: Sales Performance Rule (~22 min) - Analyze performance vs top performers

Phase 5: Consolidation & Advanced Analysis
- Step 13: Rule Consolidation (<1 min) - Consolidate all rule results
- Step 14: Fast Fish Format (<1 min) - Create client-compliant output format
- Step 15: Historical Baseline (<1 min) - Download historical comparison data
- Step 16: Comparison Tables (<1 min) - Generate Excel-compatible comparison tables
- Step 17: Augment Recommendations (~5 min) - Add historical reference and trending analysis
- Step 18: Sell-Through Analysis (<1 min) - Add client-requested sell-through rate calculations
- Step 19: Detailed SPU Breakdown (<1 min) - Generate store-SPU level breakdown and validation

Phase 6: Data Quality Assurance
- Step 20: Data Validation (<1 min) - Comprehensive validation and quality assurance

COMMAND LINE INTERFACE:
======================

Basic Usage:
    python pipeline.py --month 202506 --period A --validate-data

Step Control:
    python pipeline.py --month 202506 --period A --start-step 7 --end-step 12
    python pipeline.py --list-steps
    python pipeline.py --list-periods

Error Handling:
    python pipeline.py --month 202506 --period A --strict
    python pipeline.py --month 202506 --period A --clear-period

SYSTEM REQUIREMENTS:
===================
- Memory: 32GB+ RAM recommended
- Python: 3.12+ with dependencies
- Storage: ~2GB per analysis period  
- Network: Stable internet for API calls
- Processing Time: 60-90 minutes for complete pipeline

PERFORMANCE METRICS (Recent Execution - June 2025 First Half):
=============================================================
- Total Time: 65.2 minutes
- Success Rate: 100% (2,263 stores processed)
- Total Violations: 6,104 across 6 business rules
- Key Output: Interactive dashboards + consolidated CSV results

BUSINESS RULES SUMMARY:
======================
Rule 7: Missing Categories - 1,611 stores, 3,878 opportunities (Subcategory)
Rule 8: Imbalanced Allocation - 2,254 stores, 43,170 cases (SPU)
Rule 9: Below Minimum - 2,263 stores, 54,698 cases (Subcategory)
Rule 10: Smart Overcapacity - 601 stores, 1,219 cases (Subcategory)
Rule 11: Missed Sales - 0 stores (no issues) (SPU)
Rule 12: Sales Performance - 1,326 stores with opportunities (SPU)

KEY OUTPUT FILES:
================
- consolidated_rule_results.csv - Main analysis results (2.3MB)
- global_overview_spu_dashboard.html - Executive dashboard (11KB)
- interactive_map_spu_dashboard.html - Geographic dashboard (7.1MB)
- clustering_results.csv - Store cluster assignments (19KB)
- Individual rule result files for detailed analysis

ERROR HANDLING & DEBUGGING:
===========================
- Strict Mode: Use --strict to stop on any error for debugging
- Normal Mode: Continues on non-critical failures for production
- Data Validation: Use --validate-data for quality checks after each step
- Enhanced Logging: Timestamps, progress tracking, and context

STEP CONTROL SYSTEM:
===================
Steps are categorized by criticality:
- Critical Steps (1,2,3,6): Data Collection, Processing, Clustering - pipeline stops if these fail
- Optional Steps (4,5,7-15): Weather, Business Rules, Visualization - pipeline continues if these fail

Author: Data Pipeline Team
Date: 2025-06-16
Version: 2.0 - Complete 15-step pipeline with comprehensive documentation
"""

import os
import sys
import subprocess
import time
import signal
import argparse
import shutil
import glob
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config import (
        initialize_pipeline_config, get_current_period, set_current_period,
        get_period_label, get_period_description, get_api_data_files,
        ensure_backward_compatibility, update_legacy_file_references,
        validate_configuration, log_current_configuration,
        DATA_DIR, API_DATA_DIR, OUTPUT_DIR
    )
except ImportError:
    print("ERROR: Could not import config module. Make sure src/config.py exists.")
    sys.exit(1)

# Optional: manifest reset support for fresh runs
try:
    from pipeline_manifest import reset_manifest as reset_pipeline_manifest
except Exception:
    reset_pipeline_manifest = None

# ——— LOGGING AND UTILITIES ———

def log_message(message: str) -> None:
    """Log a message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def log_section(title: str) -> None:
    """Log a section header"""
    print("\n" + "="*80)
    print(f"🔧 {title}")
    print("="*80)

def log_success(message: str) -> None:
    """Log a success message"""
    log_message(f"✅ {message}")

def log_warning(message: str) -> None:
    """Log a warning message"""
    log_message(f"⚠️  {message}")

def log_error(message: str) -> None:
    """Log an error message"""
    log_message(f"❌ {message}")

# ——— HELPERS ———

def choose_existing_file(candidate_paths: List[str]) -> Optional[str]:
    """Return the first existing path from candidates, or None if none exist."""
    for path in candidate_paths:
        if path and os.path.exists(path):
            return path
    return None

# ——— DATA MANAGEMENT ———

def clear_previous_data(yyyymm: Optional[str] = None, period: Optional[str] = None, 
                       clear_all: bool = False,
                       clear_api_data: Optional[bool] = None) -> None:
    """
    Clear previous data files to prevent conflicts.
    
    Args:
        yyyymm: Year-month to clear (None for current)
        period: Period to clear (None for current)
        clear_all: If True, clear all data regardless of period
        clear_api_data: If True, also clear raw API data in API_DATA_DIR. If False, preserve it.
                         If None (default), use legacy behavior (clear API data when clear_all is True).
    """
    if clear_all:
        log_message("Clearing ALL previous data files...")

        # Determine whether to clear raw API data (default legacy behavior: True when unspecified)
        if clear_api_data is None:
            clear_api_data = True

        # Clear or preserve API data directory
        if clear_api_data:
            # Clear API data directory (raw API will be re-downloaded in Step 1)
            if os.path.exists(API_DATA_DIR):
                for pattern in ("*.csv", "*.json", "*.xlsx", "*.xls", "*.parquet", "*.feather", "*.pkl", "*.txt", "*.log", "*.gz", "*.zip"):
                    for file in glob.glob(os.path.join(API_DATA_DIR, pattern)):
                        try:
                            os.remove(file)
                            log_message(f"Removed: {os.path.basename(file)}")
                        except Exception as e:
                            log_warning(f"Could not remove {file}: {e}")
        else:
            log_message("Preserving raw API data in API_DATA_DIR (use --fresh-repull-api to force re-download)")

        # Helper to remove generated files recursively by extensions
        def _recursive_remove(dir_path: str, exts: List[str], allow_filenames: List[str] = None):
            allow_filenames = allow_filenames or []
            if not os.path.exists(dir_path):
                return 0
            removed = 0
            for root, _, files in os.walk(dir_path):
                for fname in files:
                    if fname in allow_filenames:
                        continue
                    lower = fname.lower()
                    if any(lower.endswith(ext) for ext in exts):
                        fpath = os.path.join(root, fname)
                        try:
                            os.remove(fpath)
                            removed += 1
                            log_message(f"Removed: {os.path.relpath(fpath, dir_path)}")
                        except Exception as e:
                            log_warning(f"Could not remove {fpath}: {e}")
            return removed

        # Clear output directory recursively: all generated artifacts
        removed_out = _recursive_remove(
            OUTPUT_DIR,
            exts=[".csv", ".html", ".md", ".json", ".xlsx", ".xls", ".parquet", ".feather", ".pkl", ".txt", ".log", ".gz", ".zip"]
        )
        if removed_out:
            log_message(f"Removed {removed_out} files from output directory")

        # Clear data directory recursively but preserve store_codes.* mapping
        data_allow = ["store_codes.csv", "store_codes.csv.backup"]
        removed_data = _recursive_remove(
            DATA_DIR,
            exts=[".csv", ".md", ".json", ".xlsx", ".xls", ".parquet", ".feather", ".pkl", ".txt", ".log", ".gz", ".zip"],
            allow_filenames=data_allow,
        )
        if removed_data:
            log_message(f"Removed {removed_data} files from data directory (preserved store_codes mapping)")

        # Clear src/output directory recursively (module/local outputs)
        src_output_dir = os.path.join("src", "output")
        removed_src_out = _recursive_remove(
            src_output_dir,
            exts=[".csv", ".html", ".md", ".json", ".xlsx", ".xls", ".parquet", ".feather", ".pkl", ".txt", ".log", ".gz", ".zip"],
        )
        if removed_src_out:
            log_message(f"Removed {removed_src_out} files from src/output directory")

        log_success("All previous generated data cleared (strict)")
        return
    
    # Clear period-specific data
    current_yyyymm, current_period = get_current_period()
    target_yyyymm = yyyymm or current_yyyymm
    target_period = period if period is not None else current_period
    
    period_label = get_period_label(target_yyyymm, target_period)
    log_message(f"Clearing previous data for period: {period_label}")
    
    # Get files to clear
    api_files = get_api_data_files(target_yyyymm, target_period)
    
    files_to_clear = [
        # API data files
        api_files['store_config'],
        api_files['store_sales'], 
        api_files['category_sales'],
        api_files['spu_sales'],
        api_files['processed_stores'],
        
        # Data files
        os.path.join(DATA_DIR, f"store_coordinates_extended_{period_label}.csv"),
        os.path.join(DATA_DIR, f"spu_store_mapping_{period_label}.csv"),
        os.path.join(DATA_DIR, f"spu_metadata_{period_label}.csv"),
        os.path.join(DATA_DIR, f"store_subcategory_matrix_{period_label}.csv"),
        os.path.join(DATA_DIR, f"store_spu_matrix_{period_label}.csv"),
        
        # Output files
        os.path.join(OUTPUT_DIR, f"clustering_results_subcategory_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"clustering_results_spu_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"cluster_profiles_subcategory_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"cluster_profiles_spu_{period_label}.csv"),
        
        # Rule results (modern names)
        # Step 7
        os.path.join(OUTPUT_DIR, f"rule7_missing_spu_sellthrough_results_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule7_missing_subcategory_sellthrough_results_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule7_missing_spu_sellthrough_opportunities_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule7_missing_subcategory_sellthrough_opportunities_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule7_missing_spu_sellthrough_summary_{period_label}.md"),
        os.path.join(OUTPUT_DIR, f"rule7_missing_subcategory_sellthrough_summary_{period_label}.md"),
        # Step 8
        os.path.join(OUTPUT_DIR, f"rule8_imbalanced_spu_results_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule8_imbalanced_subcategory_results_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule8_imbalanced_spu_cases_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule8_imbalanced_spu_z_score_analysis_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule8_imbalanced_spu_summary_{period_label}.md"),
        os.path.join(OUTPUT_DIR, f"rule8_imbalanced_subcategory_summary_{period_label}.md"),
        # Step 9
        os.path.join(OUTPUT_DIR, f"rule9_below_minimum_spu_sellthrough_results_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule9_below_minimum_spu_sellthrough_opportunities_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule9_below_minimum_spu_sellthrough_summary_{period_label}.md"),
        os.path.join(OUTPUT_DIR, f"rule10_smart_overcapacity_results_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule11_missed_sales_opportunity_results_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule12_sales_performance_results_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"consolidated_rule_results_{period_label}.csv"),
        
        # Legacy compatibility files
        os.path.join(API_DATA_DIR, "complete_category_sales_202505.csv"),
        os.path.join(API_DATA_DIR, "complete_spu_sales_202505.csv"),
        os.path.join(API_DATA_DIR, "store_config_data.csv"),
        os.path.join(API_DATA_DIR, "store_sales_data.csv"),
        os.path.join(OUTPUT_DIR, "clustering_results.csv"),
        os.path.join(DATA_DIR, "store_coordinates_extended.csv"),
        os.path.join(OUTPUT_DIR, "rule7_missing_category_results.csv"),
        os.path.join(OUTPUT_DIR, "rule8_imbalanced_results.csv"),
        os.path.join(OUTPUT_DIR, "rule9_below_minimum_spu_sellthrough_results.csv"),
        os.path.join(OUTPUT_DIR, "rule9_below_minimum_spu_sellthrough_opportunities.csv"),
    ]
    
    cleared_count = 0
    for file_path in files_to_clear:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                log_message(f"Removed: {os.path.basename(file_path)}")
                cleared_count += 1
            except Exception as e:
                log_warning(f"Could not remove {file_path}: {e}")
    
    # Generic sweep: remove any files in OUTPUT/DATA that include period label (unknown names)
    try:
        for dir_path in [OUTPUT_DIR, DATA_DIR]:
            if not os.path.exists(dir_path):
                continue
            for root, _, files in os.walk(dir_path):
                for fname in files:
                    if period_label not in fname:
                        continue
                    # Preserve store mapping
                    if fname in ("store_codes.csv", "store_codes.csv.backup"):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        os.remove(fpath)
                        cleared_count += 1
                        log_message(f"Removed: {os.path.relpath(fpath, dir_path)}")
                    except Exception as e:
                        log_warning(f"Could not remove {fpath}: {e}")
    except Exception as e:
        log_warning(f"Generic sweep failed: {e}")

    log_success(f"Cleared {cleared_count} files for period {period_label}")

def backup_store_codes() -> None:
    """Backup the store_codes.csv file to prevent accidental deletion"""
    store_codes_paths = [
        os.path.join(DATA_DIR, "store_codes.csv"),
        os.path.join("..", DATA_DIR, "store_codes.csv")
    ]
    
    for path in store_codes_paths:
        if os.path.exists(path):
            backup_path = f"{path}.backup"
            shutil.copy2(path, backup_path)
            log_message(f"Backed up store codes file: {os.path.basename(path)}")
            return
    
    log_warning("store_codes.csv not found for backup")

def restore_store_codes() -> bool:
    """Restore store_codes.csv from backup if needed"""
    store_codes_path = os.path.join(DATA_DIR, "store_codes.csv")
    backup_path = f"{store_codes_path}.backup"
    
    if not os.path.exists(store_codes_path) and os.path.exists(backup_path):
        shutil.copy2(backup_path, store_codes_path)
        log_message("Restored store_codes.csv from backup")
        return True
    return False

def list_available_periods() -> None:
    """List all available data periods"""
    print("\n📅 Available Data Periods:")
    
    # Check API data directory
    if os.path.exists(API_DATA_DIR):
        category_files = glob.glob(os.path.join(API_DATA_DIR, "complete_category_sales_*.csv"))
        if category_files:
            periods = []
            for file in category_files:
                basename = os.path.basename(file)
                period_label = basename.replace('complete_category_sales_', '').replace('.csv', '')
                
                # Parse period info
                if period_label.endswith('A'):
                    yyyymm = period_label[:-1]
                    desc = f"{yyyymm} (first half)"
                elif period_label.endswith('B'):
                    yyyymm = period_label[:-1]
                    desc = f"{yyyymm} (second half)"
                else:
                    yyyymm = period_label
                    desc = f"{yyyymm} (full month)"
                
                # Check file size
                file_size = os.path.getsize(file) / (1024 * 1024)  # MB
                periods.append((period_label, desc, file_size))
            
            # Sort by period label
            periods.sort(key=lambda x: x[0])
            
            for period_label, desc, file_size in periods:
                print(f"  • {desc} - {file_size:.1f} MB (label: {period_label})")
        else:
            print("  No API data files found")
    else:
        print("  API data directory does not exist")
    
    # Check output directory for results
    if os.path.exists(OUTPUT_DIR):
        result_files = glob.glob(os.path.join(OUTPUT_DIR, "consolidated_rule_results_*.csv"))
        if result_files:
            print("\n📊 Available Analysis Results:")
            for file in sorted(result_files):
                basename = os.path.basename(file)
                period_label = basename.replace('consolidated_rule_results_', '').replace('.csv', '')
                file_size = os.path.getsize(file) / (1024 * 1024)  # MB
                print(f"  • {period_label} - {file_size:.1f} MB")

# ——— PIPELINE STEP DEFINITIONS ———

PIPELINE_STEPS = [
    # Step 1: API Data Download
    {
        'step': 1,
        'script': 'step1_download_api_data.py',
        'name': 'API Data Download',
        'description': 'Download store sales data from FastFish API',
        'critical': True,
        'category': 'data_collection'
    },
    # Step 2: Coordinate Extraction
    {
        'step': 2,
        'script': 'step2_extract_coordinates.py',
        'name': 'Coordinate Extraction',
        'description': 'Extract store coordinates and create SPU mappings',
        'critical': True,
        'category': 'data_processing'
    },
    # Step 3: Matrix Preparation
    {
        'step': 3,
        'script': 'step3_prepare_matrix.py',
        'name': 'Matrix Preparation',
        'description': 'Prepare clustering matrices for analysis',
        'critical': True,
        'category': 'data_processing'
    },
    # Step 4: Weather Data Download
    {
        'step': 4,
        'script': 'step4_download_weather_data.py',
        'name': 'Weather Data Download',
        'description': 'Download weather data for store locations',
        'critical': False,
        'category': 'weather'
    },
    # Step 5: Feels-like Temperature
    {
        'step': 5,
        'script': 'step5_calculate_feels_like_temperature.py',
        'name': 'Feels-like Temperature Calculation',
        'description': 'Calculate feels-like temperature metrics',
        'critical': False,
        'category': 'weather'
    },
    # Step 6: Cluster Analysis
    {
        'step': 6,
        'script': 'step6_cluster_analysis.py',
        'name': 'Cluster Analysis',
        'description': 'Perform store clustering analysis',
        'critical': True,
        'category': 'clustering'
    },
    # Step 7: Missing Category Rule
    {
        'step': 7,
        'script': 'step7_missing_category_rule.py',
        'name': 'Missing Category Rule (Rule 7)',
        'description': 'Identify missing category opportunities',
        'critical': False,
        'category': 'business_rules'
    },
    # Step 8: Imbalanced Rule
    {
        'step': 8,
        'script': 'step8_imbalanced_rule.py',
        'name': 'Imbalanced Rule (Rule 8)',
        'description': 'Analyze imbalanced inventory allocations',
        'critical': False,
        'category': 'business_rules'
    },
    # Step 9: Below Minimum Rule
    {
        'step': 9,
        'script': 'step9_below_minimum_rule.py',
        'name': 'Below Minimum Rule (Rule 9)',
        'description': 'Detect below minimum threshold allocations',
        'critical': False,
        'category': 'business_rules'
    },
    # Step 10: Smart Overcapacity Rule
    {
        'step': 10,
        'script': 'step10_spu_assortment_optimization.py',
        'name': 'Smart Overcapacity Rule (Rule 10)',
        'description': 'Identify smart overcapacity optimization opportunities',
        'critical': False,
        'category': 'business_rules'
    },
    # Step 11: Missed Sales Opportunity Rule
    {
        'step': 11,
        'script': 'step11_missed_sales_opportunity.py',
        'name': 'Missed Sales Opportunity Rule (Rule 11)',
        'description': 'Analyze missed sales opportunities',
        'critical': False,
        'category': 'business_rules'
    },
    # Step 12: Sales Performance Rule
    {
        'step': 12,
        'script': 'step12_sales_performance_rule.py',
        'name': 'Sales Performance Rule (Rule 12)',
        'description': 'Classify sales performance levels',
        'critical': False,
        'category': 'business_rules'
    },
    # Step 13: Rule Consolidation
    {
        'step': 13,
        'script': 'step13_consolidate_spu_rules.py',
        'name': 'Rule Consolidation',
        'description': 'Consolidate all business rule results',
        'critical': False,
        'category': 'consolidation'
    },
    # Step 14: Create Fast Fish Format
    {
        'step': 14,
        'script': 'step14_create_fast_fish_format.py',
        'name': 'Create Fast Fish Format',
        'description': 'Generate client-compliant Fast Fish output format',
        'critical': False,
        'category': 'consolidation'
    },
    # Step 15: Download Historical Baseline
    {
        'step': 15,
        'script': 'step15_download_historical_baseline.py',
        'name': 'Download Historical Baseline',
        'description': 'Download historical data for comparison analysis',
        'critical': False,
        'category': 'data_collection'
    },
    # Step 16: Create Comparison Tables
    {
        'step': 16,
        'script': 'step16_create_comparison_tables.py',
        'name': 'Create Comparison Tables',
        'description': 'Generate Excel-compatible historical vs current comparison tables',
        'critical': False,
        'category': 'analysis'
    },
    # Step 17: Augment Recommendations
    {
        'step': 17,
        'script': 'step17_augment_recommendations.py',
        'name': 'Augment Recommendations with Historical & Trending',
        'description': 'Add historical reference and comprehensive trending analysis to Fast Fish format',
        'critical': False,
        'category': 'analysis'
    },
    # Step 18: Validate Results
    {
        'step': 18,
        'script': 'step18_validate_results.py',
        'name': 'Add Sell-Through Rate Analysis',
        'description': 'Add client-requested sell-through rate calculations and validation',
        'critical': False,
        'category': 'analysis'
    },
    # Step 19: Detailed SPU Breakdown Analysis
    {
        'step': 19,
        'script': 'step19_detailed_spu_breakdown.py',
        'name': 'Detailed SPU Breakdown Analysis',
        'description': 'Generate detailed store-SPU level breakdown and aggregation validation',
        'critical': False,
        'category': 'analysis'
    },
    # Step 20: Comprehensive Data Validation
    {
        'step': 20,
        'script': 'step20_data_validation.py',
        'name': 'Comprehensive Data Validation',
        'description': 'Validate mathematical consistency, data completeness, and business logic compliance',
        'critical': True,
        'category': 'validation'
    },
    # Step 21: Label/Tag Recommendations
    {
        'step': 21,
        'script': 'step21_label_tag_recommendations.py',
        'name': 'Label/Tag Recommendations',
        'description': 'Generate label/tag recommendation sheets with bilingual outputs',
        'critical': False,
        'category': 'analysis'
    },
    # Step 22: Store Attribute Enrichment
    {
        'step': 22,
        'script': 'step22_store_attribute_enrichment.py',
        'name': 'Store Attribute Enrichment',
        'description': 'Enrich store attributes with real sales data and capacity tiers',
        'critical': False,
        'category': 'analysis'
    }
]

def list_pipeline_steps() -> None:
    """List all pipeline steps with details"""
    print("\n📋 Pipeline Steps:")
    print("=" * 80)
    
    categories = {}
    for step in PIPELINE_STEPS:
        category = step['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(step)
    
    category_names = {
        'data_collection': '📥 Data Collection',
        'data_processing': '⚙️  Data Processing', 
        'weather': '🌤️  Weather Analysis',
        'clustering': '🔍 Clustering Analysis',
        'business_rules': '📊 Business Rules',
        'consolidation': '📋 Consolidation',
        'visualization': '📈 Visualization',
        'analysis': '🔬 Advanced Analysis'
    }
    
    for category, steps in categories.items():
        print(f"\n{category_names.get(category, category.title())}:")
        for step in steps:
            critical_marker = "🔴" if step['critical'] else "🟡"
            print(f"  {critical_marker} Step {step['step']:2d}: {step['name']}")
            print(f"      {step['description']}")
    
    print(f"\n🔴 Critical steps (pipeline stops if these fail)")
    print(f"🟡 Optional steps (pipeline continues if these fail)")

def validate_step_range(start_step: Optional[int], end_step: Optional[int]) -> tuple[int, int]:
    """Validate and normalize step range"""
    min_step = 1
    max_step = len(PIPELINE_STEPS)
    
    if start_step is not None and (start_step < min_step or start_step > max_step):
        raise ValueError(f"Start step must be between {min_step} and {max_step}")
    
    if end_step is not None and (end_step < min_step or end_step > max_step):
        raise ValueError(f"End step must be between {min_step} and {max_step}")
    
    if start_step is not None and end_step is not None and start_step > end_step:
        raise ValueError("Start step cannot be greater than end step")
    
    actual_start = start_step or min_step
    actual_end = end_step or max_step
    
    return actual_start, actual_end

def validate_data_quality(step_info: Dict[str, Any]) -> bool:
    """Validate data quality after a step"""
    step_num = step_info['step']
    log_message(f"🔍 Validating data quality after Step {step_num}...")
    
    # Basic file existence checks based on step
    if step_num == 1:  # API Download
        current_yyyymm, current_period = get_current_period()
        api_files = get_api_data_files(current_yyyymm, current_period)
        
        required_files = [api_files['category_sales']]
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            log_error(f"Missing required files after Step {step_num}: {missing_files}")
            return False
        
        # Check file sizes
        for file_path in required_files:
            if os.path.getsize(file_path) < 1000:  # Less than 1KB
                log_error(f"File too small (likely empty): {file_path}")
                return False
        
        log_success(f"Data validation passed for Step {step_num}")
        return True
    
    elif step_num == 2:  # Coordinate Extraction
        coord_file = os.path.join(DATA_DIR, "store_coordinates_extended.csv")
        if not os.path.exists(coord_file):
            log_error(f"Missing coordinates file: {coord_file}")
            return False
        
        # Check coordinate file has data
        try:
            import pandas as pd
            df = pd.read_csv(coord_file)
            if len(df) == 0:
                log_error("Coordinates file is empty")
                return False
            log_success(f"Data validation passed for Step {step_num} - {len(df)} stores with coordinates")
            return True
        except Exception as e:
            log_error(f"Error reading coordinates file: {e}")
            return False
    
    elif step_num == 3:  # Matrix Preparation
        matrix_files = [
            os.path.join(DATA_DIR, "store_subcategory_matrix.csv"),
            os.path.join(DATA_DIR, "normalized_subcategory_matrix.csv")
        ]
        
        missing_files = [f for f in matrix_files if not os.path.exists(f)]
        if missing_files:
            log_error(f"Missing matrix files after Step {step_num}: {missing_files}")
            return False
        
        log_success(f"Data validation passed for Step {step_num}")
        return True
    
    elif step_num == 6:  # Clustering
        # Accept any of the clustering result variants written by Step 6
        candidate_paths = [
            os.path.join(OUTPUT_DIR, "clustering_results_spu.csv"),
            os.path.join(OUTPUT_DIR, "clustering_results_subcategory.csv"),
            os.path.join(OUTPUT_DIR, "clustering_results_category_agg.csv"),
            os.path.join(OUTPUT_DIR, "clustering_results.csv"),  # legacy
        ]
        cluster_file = choose_existing_file(candidate_paths)
        if not cluster_file:
            log_error(
                "Missing clustering results. Checked: "
                + ", ".join(os.path.basename(p) for p in candidate_paths)
            )
            return False
        
        try:
            import pandas as pd
            df = pd.read_csv(cluster_file)
            if len(df) == 0:
                log_error("Clustering results file is empty")
                return False
            
            unique_clusters = df['Cluster'].nunique() if 'Cluster' in df.columns else 0
            log_success(f"Data validation passed for Step {step_num} - {len(df)} stores in {unique_clusters} clusters")
            return True
        except Exception as e:
            log_error(f"Error reading clustering results from {os.path.basename(cluster_file)}: {e}")
            return False

    elif step_num in {7, 8, 9}:  # Business rule outputs
        # Check for presence of expected rule output files (period-aware and legacy)
        current_yyyymm, current_period = get_current_period()
        period_label = get_period_label(current_yyyymm, current_period)

        if step_num == 7:
            candidate_paths = [
                # Primary (current) filenames
                os.path.join(OUTPUT_DIR, f"rule7_missing_spu_sellthrough_results_{period_label}.csv"),
                os.path.join(OUTPUT_DIR, "rule7_missing_spu_sellthrough_results.csv"),
                # Legacy/alternate fallback filenames
                os.path.join(OUTPUT_DIR, f"rule7_missing_category_results_{period_label}.csv"),
                os.path.join(OUTPUT_DIR, "rule7_missing_category_results.csv"),
            ]
        elif step_num == 8:
            candidate_paths = [
                # Primary (current) filenames
                os.path.join(OUTPUT_DIR, f"rule8_imbalanced_spu_results_{period_label}.csv"),
                os.path.join(OUTPUT_DIR, "rule8_imbalanced_spu_results.csv"),
                # Legacy/alternate fallback filenames
                os.path.join(OUTPUT_DIR, f"rule8_imbalanced_results_{period_label}.csv"),
                os.path.join(OUTPUT_DIR, "rule8_imbalanced_results.csv"),
                # Observed alternate naming in repository artifacts
                os.path.join(OUTPUT_DIR, f"rule8_imbalanced_spu_cases_{period_label}.csv"),
                os.path.join(OUTPUT_DIR, "rule8_imbalanced_spu_cases.csv"),
            ]
        else:  # step 9
            candidate_paths = [
                # Primary (current) filenames
                os.path.join(OUTPUT_DIR, f"rule9_below_minimum_spu_sellthrough_results_{period_label}.csv"),
                os.path.join(OUTPUT_DIR, "rule9_below_minimum_spu_sellthrough_results.csv"),
                # Legacy/alternate fallback filenames
                os.path.join(OUTPUT_DIR, f"rule9_below_minimum_results_{period_label}.csv"),
                os.path.join(OUTPUT_DIR, "rule9_below_minimum_results.csv"),
            ]

        found_file = choose_existing_file(candidate_paths)
        if not found_file:
            log_error(
                f"Missing expected output for Step {step_num}. Checked: "
                + ", ".join(os.path.basename(p) for p in candidate_paths)
            )
            return False
        
        # Basic sanity: file non-empty and has at least header row
        try:
            import pandas as pd
            df = pd.read_csv(found_file)
            if df.empty:
                log_error(f"Output file for Step {step_num} is empty: {os.path.basename(found_file)}")
                return False
            log_success(f"Data validation passed for Step {step_num} - {os.path.basename(found_file)} rows: {len(df)}")
            return True
        except Exception as e:
            log_error(f"Error reading output for Step {step_num} from {os.path.basename(found_file)}: {e}")
            return False
    
    # For other steps, just log that validation was requested
    log_message(f"Data validation not implemented for Step {step_num} (skipping)")
    return True

# ——— PIPELINE EXECUTION ———

def run_script(script_name: str, description: str, extra_args: list = None, timeout_minutes: Optional[int] = None, env: Optional[dict] = None) -> bool:
    """
    Run a Python script and return success status.
    
    Args:
        script_name: Name of the script file in src/ directory
        description: Human-readable description for logging
        extra_args: List of additional arguments to pass to the script
        timeout_minutes: If provided, abort the step after this many minutes
        
    Returns:
        True if script succeeded, False otherwise
    """
    log_message(f"Starting {description}...")
    script_path = os.path.join("src", script_name)
    
    if not os.path.exists(script_path):
        log_error(f"Script {script_path} not found!")
        return False
    
    # Build command with extra arguments if provided
    cmd = [sys.executable, script_path]
    if extra_args:
        cmd.extend(extra_args)
    
    # Log the full command for traceability
    log_message("Command: " + " ".join(cmd))
    if timeout_minutes:
        log_message(f"Timeout set: {timeout_minutes} minute(s)")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60 if timeout_minutes else None
    try:
        # Start child in its own process group so we can terminate the whole group on timeout
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid,
            env=(env or os.environ),
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            log_error(f"{description} timed out after {elapsed/60:.1f} minutes (limit={timeout_minutes}m). Terminating process group...")
            # Kill the entire process group
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception as kill_err:
                log_warning(f"Failed to kill process group directly: {kill_err}. Killing main process...")
                try:
                    proc.kill()
                except Exception:
                    pass
            # Collect any remaining output
            stdout, stderr = proc.communicate()
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
            return False

        elapsed = time.time() - start_time
        if proc.returncode != 0:
            log_error(f"{description} failed (exit code {proc.returncode}) after {elapsed/60:.1f} minutes")
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
            return False
        else:
            if stdout:
                print(stdout)
            log_success(f"{description} completed successfully in {elapsed/60:.1f} minutes")
            return True

    except Exception as e:
        elapsed = time.time() - start_time
        log_error(f"{description} crashed after {elapsed/60:.1f} minutes: {e}")
        return False

def create_sample_data_files() -> bool:
    """Create sample data files for demonstration when API data doesn't exist"""
    log_message("Creating sample data files for demonstration...")
    
    # Ensure directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(API_DATA_DIR, exist_ok=True)
    
    # Check if store_codes.csv exists, if not create it
    store_codes_path = os.path.join(DATA_DIR, "store_codes.csv")
    if not os.path.exists(store_codes_path):
        log_message("Creating default store_codes.csv file...")
        store_codes = [f"STORE{i:04d}" for i in range(100)]
        pd.DataFrame({"str_code": store_codes}).to_csv(store_codes_path, index=False)
        log_message(f"Created store_codes.csv with {len(store_codes)} stores")
    
    # Create sample API data
    current_yyyymm, current_period = get_current_period()
    api_files = get_api_data_files(current_yyyymm, current_period)
    
    # Sample store data
    store_codes = pd.read_csv(store_codes_path)['str_code'].tolist()
    
    # Create sample category sales data
    categories = ['Casual Pants', 'Dress Shirts', 'T-Shirts', 'Shoes', 'Accessories']
    subcats = ['Cargo Pants', 'Chinos', 'Business Shirts', 'Polo Shirts', 'Sneakers', 
               'Belts', 'Watches', 'Hats', 'Jeans', 'Sweaters']
    
    api_data = []
    for store in store_codes:
        n_subcats = np.random.randint(5, 9)
        selected_subcats = np.random.choice(subcats, n_subcats, replace=False)
        
        for subcat in selected_subcats:
            sal_qty = np.random.randint(10, 500)
            sal_amt = sal_qty * np.random.uniform(20, 200)  # Random price per unit
            api_data.append({
                'str_code': store,
                'cate_name': np.random.choice(categories),
                'sub_cate_name': subcat,
                'sal_qty': sal_qty,
                'sal_amt': sal_amt
            })
    
    api_df = pd.DataFrame(api_data)
    api_df.to_csv(api_files['category_sales'], index=False)
    log_message(f"Created sample category sales data: {len(api_df)} records")
    
    # Create sample SPU sales data
    spu_data = []
    spus = [f"SPU{i:05d}" for i in range(1000)]  # 1000 sample SPUs
    
    for store in store_codes[:100]:  # Limit to first 100 stores for sample
        n_spus = np.random.randint(50, 200)  # Each store has 50-200 SPUs
        selected_spus = np.random.choice(spus, n_spus, replace=False)
        
        for spu in selected_spus:
            sal_qty = np.random.randint(1, 50)
            sal_amt = sal_qty * np.random.uniform(10, 500)
            spu_data.append({
                'str_code': store,
                'spu_code': spu,
                'cate_name': np.random.choice(categories),
                'sub_cate_name': np.random.choice(subcats),
                'sal_qty': sal_qty,
                'sal_amt': sal_amt
            })
    
    spu_df = pd.DataFrame(spu_data)
    spu_df.to_csv(api_files['spu_sales'], index=False)
    log_message(f"Created sample SPU sales data: {len(spu_df)} records")
    
    # Create sample store config data (needed for business rules)
    config_data = []
    for store in store_codes:
        for subcat in subcats:
            # Random allocation data
            config_data.append({
                'str_code': store,
                'sub_cate_name': subcat,
                'allocation': np.random.uniform(0.5, 10.0),  # Allocation amount
                'capacity': np.random.uniform(5.0, 20.0),    # Store capacity
                'target_sales': np.random.uniform(100, 1000) # Target sales
            })
    
    config_df = pd.DataFrame(config_data)
    config_df.to_csv(api_files['store_config'], index=False)
    log_message(f"Created sample store config data: {len(config_df)} records")
    
    # Create sample store sales summary
    sales_summary = []
    for store in store_codes:
        total_sales = np.random.uniform(10000, 100000)
        sales_summary.append({
            'str_code': store,
            'total_sal_qty': np.random.randint(100, 2000),
            'total_sal_amt': total_sales,
            'store_type': np.random.choice(['Basic', 'Fashion', 'Premium'])
        })
    
    sales_df = pd.DataFrame(sales_summary)
    sales_df.to_csv(api_files['store_sales'], index=False)
    log_message(f"Created sample store sales summary: {len(sales_df)} records")
    
    log_success("Sample data files created successfully")
    return True

def check_api_data_exists() -> bool:
    """Check if API data exists for the current period"""
    current_yyyymm, current_period = get_current_period()
    api_files = get_api_data_files(current_yyyymm, current_period)
    
    required_files = [api_files['category_sales']]
    return all(os.path.exists(file) for file in required_files)



def _legacy_validate_step_range(start_step: Optional[int], end_step: Optional[int]) -> tuple[int, int]:
    """Validate and normalize step range"""
    min_step = 1
    max_step = len(PIPELINE_STEPS)
    
    if start_step is not None and (start_step < min_step or start_step > max_step):
        raise ValueError(f"Start step must be between {min_step} and {max_step}")
    
    if end_step is not None and (end_step < min_step or end_step > max_step):
        raise ValueError(f"End step must be between {min_step} and {max_step}")
    
    if start_step is not None and end_step is not None and start_step > end_step:
        raise ValueError("Start step cannot be greater than end step")
    
    actual_start = start_step or min_step
    actual_end = end_step or max_step
    
    return actual_start, actual_end

def _legacy_validate_data_quality(step_info: Dict[str, Any]) -> bool:
    """Validate data quality after a step"""
    step_num = step_info['step']
    log_message(f"🔍 Validating data quality after Step {step_num}...")
    
    # Basic file existence checks based on step
    if step_num == 1:  # API Download
        current_yyyymm, current_period = get_current_period()
        api_files = get_api_data_files(current_yyyymm, current_period)
        
        required_files = [api_files['category_sales']]
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            log_error(f"Missing required files after Step {step_num}: {missing_files}")
            return False
        
        # Check file sizes
        for file_path in required_files:
            if os.path.getsize(file_path) < 1000:  # Less than 1KB
                log_error(f"File too small (likely empty): {file_path}")
                return False
        
        log_success(f"Data validation passed for Step {step_num}")
        return True
    
    elif step_num == 2:  # Coordinate Extraction
        coord_file = os.path.join(DATA_DIR, "store_coordinates_extended.csv")
        if not os.path.exists(coord_file):
            log_error(f"Missing coordinates file: {coord_file}")
            return False
        
        # Check coordinate file has data
        try:
            import pandas as pd
            df = pd.read_csv(coord_file)
            if len(df) == 0:
                log_error("Coordinates file is empty")
                return False
            log_success(f"Data validation passed for Step {step_num} - {len(df)} stores with coordinates")
            return True
        except Exception as e:
            log_error(f"Error reading coordinates file: {e}")
            return False
    
    elif step_num == 3:  # Matrix Preparation
        matrix_files = [
            os.path.join(DATA_DIR, "store_subcategory_matrix.csv"),
            os.path.join(DATA_DIR, "normalized_subcategory_matrix.csv")
        ]
        
        missing_files = [f for f in matrix_files if not os.path.exists(f)]
        if missing_files:
            log_error(f"Missing matrix files after Step {step_num}: {missing_files}")
            return False
        
        log_success(f"Data validation passed for Step {step_num}")
        return True
    
    elif step_num == 6:  # Clustering
        cluster_file = os.path.join(OUTPUT_DIR, "clustering_results.csv")
        if not os.path.exists(cluster_file):
            log_error(f"Missing clustering results: {cluster_file}")
            return False
        
        try:
            import pandas as pd
            df = pd.read_csv(cluster_file)
            if len(df) == 0:
                log_error("Clustering results file is empty")
                return False
            
            unique_clusters = df['Cluster'].nunique() if 'Cluster' in df.columns else 0
            log_success(f"Data validation passed for Step {step_num} - {len(df)} stores in {unique_clusters} clusters")
            return True
        except Exception as e:
            log_error(f"Error reading clustering results: {e}")
            return False
    
    # For other steps, just log that validation was requested
    log_message(f"Data validation not implemented for Step {step_num} (skipping)")
    return True

def run_pipeline(start_step: Optional[int] = None, end_step: Optional[int] = None,
                strict_mode: bool = False, validate_data_flag: bool = False,
                clear_all: bool = False, clear_period: bool = False,
                allow_sample_data: bool = False,
                skip_api: bool = False, skip_weather: bool = False,
                enable_trending: bool = False, enable_trend_utils: bool = False,
                run_2b: bool = False,
                zscore_output_limit: Optional[int] = None, skip_zscore_output: bool = False,
                step_timeout_minutes: Optional[int] = None,
                fresh_run: bool = False,
                seasonal_look_back: int = 6) -> bool:
    """
    Run the complete analysis pipeline with step control.
    
    Args:
        skip_api: Skip API data download step
        skip_weather: Skip weather-related steps
        start_step: Start from specific step number
        end_step: End at specific step number
        strict_mode: Stop on any error (no continue on warnings)
        validate_data: Validate data quality after each step
        
    Returns:
        True if pipeline succeeded, False otherwise
    """
    log_section("PRODUCT MIX CLUSTERING & RULE ANALYSIS PIPELINE")
    if fresh_run:
        log_message("Fresh run mode enabled: all steps will execute from scratch (no skipping)")
    
    # Validate step range
    try:
        actual_start, actual_end = validate_step_range(start_step, end_step)
        if start_step or end_step:
            log_message(f"Running steps {actual_start} to {actual_end}")
    except ValueError as e:
        log_error(str(e))
        return False
    
    log_message("Pipeline includes: Data Collection → Weather Integration → Clustering → Business Rules → Dashboards")
    
    # Backup store codes
    backup_store_codes()
    
    # Track pipeline progress
    total_steps = actual_end - actual_start + 1
    completed_steps = 0
    failed_steps = []
    skipped_steps = []
    
    # Track optional step execution state
    ran_2b = False
    
    # Execute steps in range
    for step_info in PIPELINE_STEPS:
        step_num = step_info['step']
        
        # Skip steps outside range
        if step_num < actual_start or step_num > actual_end:
            continue
        
        script_name = step_info['script']
        step_name = step_info['name']
        is_critical = step_info['critical']
        category = step_info['category']
        
        # Handle special skip conditions
        should_skip = False
        skip_reason = ""

        # In fresh-run mode, never skip steps due to skip flags
        if not fresh_run:
            # Don't skip step 1 if we need to create sample data
            if skip_api and step_num == 1:
                # Check if we need to create sample data
                if not check_api_data_exists():
                    should_skip = False  # Don't skip, we need to create sample data
                else:
                    should_skip = True
                    skip_reason = "--skip-api flag provided (data exists)"
            elif skip_weather and category == 'weather':
                should_skip = True
                skip_reason = "--skip-weather flag provided"
        
        # Optional Step 2B: run before Step 6 if requested and not yet executed
        if step_num == 6 and run_2b and not ran_2b:
            log_message("Running optional Step 2B (Seasonal Data Consolidation) before Step 6...")
            current_yyyymm, current_period = get_current_period()
            extra_2b_args = []
            if current_yyyymm and current_period:
                extra_2b_args.extend(['--target-yyyymm', current_yyyymm, '--target-period', current_period])
            # Pass seasonal look-back to Step 2B
            if seasonal_look_back:
                extra_2b_args.extend(['--seasonal-look-back', str(seasonal_look_back)])
            child_env_2b = os.environ.copy()
            if fresh_run:
                child_env_2b['PIPELINE_FRESH_RUN'] = '1'
            success_2b = run_script('step2b_consolidate_seasonal_data.py', 'Seasonal Data Consolidation (2B)', extra_2b_args, timeout_minutes=step_timeout_minutes, env=child_env_2b)
            ran_2b = True
            if not success_2b:
                if strict_mode:
                    log_error("Step 2B failed and --strict is set. Stopping pipeline.")
                    return False
                else:
                    log_warning("Step 2B failed (continuing to Step 6).")
        
        # Log step start
        progress = f"({completed_steps + 1}/{total_steps})"
        log_message(f"Starting Step {step_num} {progress}: {step_name}...")
        
        if should_skip:
            log_message(f"Skipping Step {step_num}: {skip_reason}")
            skipped_steps.append(step_num)
            completed_steps += 1
            continue
        
        # Special handling for Step 1 (API download)
        if step_num == 1:
            if skip_api and not fresh_run:
                if not check_api_data_exists():
                    if allow_sample_data:
                        log_message("API data not found. Creating sample data files (allowed by flag)...")
                        if not create_sample_data_files():
                            log_error("Failed to create sample data files")
                            if is_critical or strict_mode:
                                return False
                            failed_steps.append(step_num)
                            completed_steps += 1
                            continue
                        log_message("Using sample data files for analysis")
                    else:
                        log_error("API data missing and --allow-sample-data not set. Do not use --skip-api in production without data.")
                        if is_critical or strict_mode:
                            return False
                        failed_steps.append(step_num)
                        completed_steps += 1
                        continue
                else:
                    log_message("API data found. Continuing with existing data")
                
                # Ensure backward compatibility
                log_message("Setting up backward compatibility...")
                ensure_backward_compatibility()
                update_legacy_file_references()
                
                # Validate data if requested
                if validate_data_flag:
                    if not validate_data_quality(step_info):
                        log_error(f"Data validation failed after Step {step_num}")
                        if is_critical or strict_mode:
                            return False
                        failed_steps.append(step_num)
                
                completed_steps += 1
                continue
        
        # Run the step
        # Build extra arguments for specific steps
        extra_args = []
        if step_num == 13 and enable_trend_utils:
            extra_args.extend(['--enable-trend-utils', '--fast-mode'])
        elif step_num == 17 and enable_trending:
            extra_args.append('--enable-trending')
        elif step_num == 8:
            # Step 8 output control flags
            if zscore_output_limit is not None:
                extra_args.extend(['--zscore-output-limit', str(zscore_output_limit)])
            if skip_zscore_output:
                extra_args.append('--skip-zscore-output')
        
        # Add period arguments (Step 1 expects --month/--period; modern steps accept --target-yyyymm/--target-period)
        current_yyyymm, current_period = get_current_period()
        if current_yyyymm and (current_period is not None):
            if step_num == 1:
                # Step 1 legacy CLI
                extra_args.extend(['--month', current_yyyymm, '--period', current_period or 'full'])
            else:
                extra_args.extend(['--target-yyyymm', current_yyyymm, '--target-period', current_period])
        
        child_env = os.environ.copy()
        if fresh_run:
            child_env['PIPELINE_FRESH_RUN'] = '1'
        success = run_script(script_name, step_name, extra_args, timeout_minutes=step_timeout_minutes, env=child_env)
        
        if not success:
            failed_steps.append(step_num)
            
            if is_critical:
                log_error(f"Critical step {step_num} failed: {step_name}")
                if strict_mode:
                    log_error("Stopping pipeline due to critical step failure (strict mode)")
                    return False
                else:
                    log_error("Stopping pipeline due to critical step failure")
                    return False
            else:
                if strict_mode:
                    log_error(f"Step {step_num} failed: {step_name} (stopping due to strict mode)")
                    return False
                else:
                    log_warning(f"Step {step_num} failed: {step_name} (continuing...)")
        
        # Validate data quality if requested
        if validate_data_flag and success:
            if not validate_data_quality(step_info):
                log_error(f"Data validation failed after Step {step_num}")
                if is_critical or strict_mode:
                    return False
                failed_steps.append(step_num)
        
        completed_steps += 1
    
    # Log pipeline summary
    log_section("PIPELINE EXECUTION SUMMARY")
    log_message(f"Steps executed: {completed_steps}/{total_steps}")
    
    if skipped_steps:
        log_message(f"Steps skipped: {skipped_steps}")
    
    if failed_steps:
        log_warning(f"Steps failed: {failed_steps}")
        
        # Check if any critical steps failed
        critical_failures = []
        for step_num in failed_steps:
            step_info = next((s for s in PIPELINE_STEPS if s['step'] == step_num), None)
            if step_info and step_info['critical']:
                critical_failures.append(step_num)
        
        if critical_failures:
            log_error(f"Critical steps failed: {critical_failures}")
            return False
        else:
            log_warning("Only non-critical steps failed - pipeline considered successful")
    
    if not failed_steps:
        log_success("All executed steps completed successfully!")
    
    return True

def log_final_results() -> None:
    """Log final pipeline results and file locations"""
    log_section("PIPELINE RESULTS")
    
    current_yyyymm, current_period = get_current_period()
    period_label = get_period_label(current_yyyymm, current_period)
    
    # Check for consolidated results
    results_file = os.path.join(OUTPUT_DIR, f"consolidated_rule_results_{period_label}.csv")
    if not os.path.exists(results_file):
        # Try legacy filename
        results_file = os.path.join(OUTPUT_DIR, "consolidated_rule_results.csv")
    
    if os.path.exists(results_file):
        try:
            results_df = pd.read_csv(results_file)
            log_success(f"Analysis completed for period: {period_label}")
            log_message(f"Total stores analyzed: {len(results_df):,}")
            
            if 'total_rule_violations' in results_df.columns:
                flagged_stores = results_df['total_rule_violations'].gt(0).sum()
                log_message(f"Stores with rule violations: {flagged_stores:,} ({flagged_stores/len(results_df)*100:.1f}%)")
                log_message(f"Total rule violations: {results_df['total_rule_violations'].sum():,}")
        except Exception as e:
            log_warning(f"Could not read final results: {e}")
    
    # Log key output files
    log_message("📋 Key Output Files:")
    
    output_files = [
        ("consolidated_rule_results.csv", "Main results with all rule violations"),
        ("consolidated_rule_summary.md", "Executive summary report"),
        ("clustering_results.csv", "Store cluster assignments"),
        ("global_overview_dashboard.html", "Executive dashboard (open in browser)"),
        ("interactive_map_dashboard.html", "Geographic analysis dashboard"),
    ]
    
    for filename, description in output_files:
        file_path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024  # KB
            log_message(f"   ✓ {filename} - {description} ({file_size:.1f} KB)")
        else:
            log_message(f"   ✗ {filename} - {description} (not found)")
    
    log_message("📊 Individual Rule Results:")
    rule_files = [
        ("rule7_missing_spu_sellthrough_results.csv", "Rule 7 - Missing Categories"),
        ("rule8_imbalanced_spu_results.csv", "Rule 8 - Imbalanced Allocations"),
        ("rule9_below_minimum_spu_sellthrough_results.csv", "Rule 9 - Below Minimum Thresholds"),
        ("rule10_smart_overcapacity_results.csv", "Rule 10 - Smart Overcapacity"),
        ("rule11_missed_sales_opportunity_results.csv", "Rule 11 - Missed Opportunities"),
        ("rule12_sales_performance_results.csv", "Rule 12 - Sales Performance"),
    ]
    
    for filename, description in rule_files:
        file_path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(file_path):
            log_message(f"   ✓ {filename} - {description}")

# ——— MAIN FUNCTION ———

def main() -> None:
    """Main entry point for the pipeline"""
    parser = argparse.ArgumentParser(
        description='Product Mix Clustering Pipeline Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py                           # Use default period (202506A)
  python pipeline.py --month 202507 --period A # July 2025, first half
  python pipeline.py --month 202507 --period B # July 2025, second half  
  python pipeline.py --month 202507            # July 2025, full month
  python pipeline.py --skip-api                # Skip API download
  python pipeline.py --clear-all               # Clear all previous data
  python pipeline.py --list-periods            # List available periods
  
Step Control (for debugging):
  python pipeline.py --start-step 2 --end-step 6    # Run steps 2-6 only
  python pipeline.py --start-step 7             # Run from step 7 to end
  python pipeline.py --end-step 3               # Run from start to step 3
  python pipeline.py --list-steps               # List all pipeline steps
  python pipeline.py --strict                   # Stop on any error (no continue)
        """
    )
    
    parser.add_argument('--month', type=str, 
                       help='Year-month in YYYYMM format (e.g., 202507)')
    parser.add_argument('--period', type=str, choices=['A', 'B', 'full'],
                       help='Period: A=first half, B=second half, full=entire month')
    parser.add_argument('--skip-api', action='store_true',
                       help='Skip API data download, use existing data')
    parser.add_argument('--skip-weather', action='store_true',
                       help='Skip weather data download and processing')
    parser.add_argument('--clear-all', action='store_true',
                       help='Clear all previous data files before running')
    parser.add_argument('--clear-period', action='store_true',
                       help='Clear data for the specified period only')
    parser.add_argument('--fresh-run', action='store_true',
                       help='Force a complete rerun: clear ALL cached data and reset pipeline manifest; run all steps from scratch')
    parser.add_argument('--fresh-repull-api', action='store_true',
                       help='When used with --fresh-run, also delete raw API data to force a complete re-download (otherwise preserved by default)')
    parser.add_argument('--list-periods', action='store_true',
                       help='List available data periods and exit')
    
    # Step control arguments
    parser.add_argument('--start-step', type=int, 
                       help='Start from specific step number (1-22)')
    parser.add_argument('--end-step', type=int,
                       help='End at specific step number (1-22)')
    parser.add_argument('--list-steps', action='store_true',
                       help='List all pipeline steps and exit')
    parser.add_argument('--strict', action='store_true',
                       help='Stop pipeline on any error (no continue on warnings)')
    parser.add_argument('--validate-data', action='store_true',
                       help='Validate data quality after each step')
    parser.add_argument('--allow-sample-data', action='store_true',
                       help='Allow creation of synthetic sample data only when API data is missing and --skip-api is used (not for production)')
    parser.add_argument('--no-clear', action='store_true',
                       help='Do not clear any data before running (overrides default clear)')
    
    parser.add_argument('--enable-trending', action='store_true',
                       help='Enable trending analysis in Step 17')
    parser.add_argument('--enable-trend-utils', action='store_true',
                       help='Enable trend utilities in Step 13')
    parser.add_argument('--run-2b', action='store_true',
                       help='Run Step 2B seasonal consolidation before clustering (runs just before Step 6)')
    parser.add_argument('--step-timeout-minutes', type=int,
                       help='Abort any individual step if it exceeds this many minutes (detects and prevents hangs)')
    parser.add_argument('--seasonal-look-back', type=int, default=6,
                       help='Number of half-month periods for Step 2B seasonal consolidation (default: 6)')
    # Step 8 specific output controls
    parser.add_argument('--zscore-output-limit', type=int,
                       help='Limit rows saved in Step 8 z-score analysis CSV (top-|z|). Omit for all.')
    parser.add_argument('--skip-zscore-output', action='store_true',
                       help='Skip detailed Step 8 z-score analysis file; write headers only.')
    
    args = parser.parse_args()

    # Determine if API repull is requested via CLI or environment variable
    env_fresh_repull = os.getenv('PIPELINE_FRESH_REPULL_API', '').strip().lower()
    fresh_repull_api = bool(args.fresh_repull_api or env_fresh_repull in ('1', 'true', 'yes', 'on'))
    
    # Handle list commands
    if args.list_periods:
        list_available_periods()
        return
    
    if args.list_steps:
        list_pipeline_steps()
        return
    
    # Set up period configuration
    yyyymm = args.month
    period = args.period if args.period != 'full' else None
    
    try:
        # Initialize pipeline configuration
        initialize_pipeline_config(yyyymm, period)
        
        # Log current configuration
        log_current_configuration()
        
        # Fresh run: always clear everything and reset manifest
        if args.fresh_run:
            log_section("FRESH RUN INITIALIZATION")
            if fresh_repull_api:
                log_message("--fresh-run specified: clearing ALL cached data including raw API data (forced re-download) and resetting manifest")
            else:
                log_message("--fresh-run specified: clearing ALL cached data but preserving raw API data; use --fresh-repull-api to force API re-download")

            # Set environment variable for child steps
            os.environ['PIPELINE_FRESH_REPULL_API'] = '1' if fresh_repull_api else '0'

            # Clear data with explicit API data policy
            clear_previous_data(clear_all=True, clear_api_data=fresh_repull_api)
            if reset_pipeline_manifest is not None:
                try:
                    reset_pipeline_manifest(delete_file=True)
                except Exception as e:
                    log_warning(f"Manifest reset failed (continuing anyway): {e}")
            else:
                log_warning("Manifest module not available; skipping manifest reset")
        else:
            # Clear data if requested (respects --no-clear)
            if not args.no_clear:
                if args.clear_all:
                    clear_previous_data(clear_all=True)
                elif args.clear_period:
                    clear_previous_data(yyyymm, period)
                else:
                    # Default: clear current period data
                    clear_previous_data(yyyymm, period)
            else:
                log_message("Skipping data clear due to --no-clear flag")
        
        # Restore store codes if needed
        restore_store_codes()
        
        # Run the pipeline
        start_time = time.time()
        success = run_pipeline(
            start_step=args.start_step,
            end_step=args.end_step,
            strict_mode=args.strict,
            validate_data_flag=args.validate_data,
            clear_all=args.clear_all,
            clear_period=args.clear_period,
            allow_sample_data=args.allow_sample_data,
            skip_api=args.skip_api,
            skip_weather=args.skip_weather,
            enable_trending=args.enable_trending,
            enable_trend_utils=args.enable_trend_utils,
            run_2b=args.run_2b,
            zscore_output_limit=args.zscore_output_limit,
            skip_zscore_output=args.skip_zscore_output,
            step_timeout_minutes=args.step_timeout_minutes,
            fresh_run=args.fresh_run,
            seasonal_look_back=args.seasonal_look_back)
        elapsed_time = time.time() - start_time
        
        if success:
            log_success(f"Pipeline completed successfully in {elapsed_time/60:.1f} minutes!")
            log_final_results()
        else:
            log_error("Pipeline failed. Check error messages above.")
            sys.exit(1)
            
    except Exception as e:
        log_error(f"Pipeline initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()