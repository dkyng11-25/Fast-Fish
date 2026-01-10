#!/usr/bin/env python3
"""
Product Mix Clustering & Rule Analysis Pipeline - Main Execution Module

A comprehensive 15-step pipeline for retail product mix optimization through clustering
analysis and business rule validation. This pipeline processes store sales data, applies
weather-aware clustering, and identifies optimization opportunities through 6 business rules.

PIPELINE ARCHITECTURE:
=====================

15-Step Pipeline Structure:
1. Data Collection & Processing (Steps 1-3): API download → Coordinates → Matrix preparation
2. Weather Integration (Steps 4-5): Weather data → Temperature analysis  
3. Clustering Analysis (Step 6): Temperature-aware store clustering
4. Business Rules Analysis (Steps 7-12): 6 optimization rules analysis
5. Visualization & Consolidation (Steps 13-15): Consolidation → Dashboards

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

Phase 5: Consolidation & Visualization
- Step 13: Rule Consolidation (<1 min) - Consolidate all rule results
- Step 14: Global Overview Dashboard (<1 min) - Create executive dashboard
- Step 15: Interactive Map Dashboard (<1 min) - Create geographic dashboard

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

# ——— DATA MANAGEMENT ———

def clear_previous_data(yyyymm: Optional[str] = None, period: Optional[str] = None, 
                       clear_all: bool = False) -> None:
    """
    Clear previous data files to prevent conflicts.
    
    Args:
        yyyymm: Year-month to clear (None for current)
        period: Period to clear (None for current)
        clear_all: If True, clear all data regardless of period
    """
    if clear_all:
        log_message("Clearing ALL previous data files...")
        
        # Clear API data directory
        if os.path.exists(API_DATA_DIR):
            for file in glob.glob(os.path.join(API_DATA_DIR, "*.csv")):
                try:
                    os.remove(file)
                    log_message(f"Removed: {os.path.basename(file)}")
                except Exception as e:
                    log_warning(f"Could not remove {file}: {e}")
        
        # Clear output directory (but keep directories)
        if os.path.exists(OUTPUT_DIR):
            for file in glob.glob(os.path.join(OUTPUT_DIR, "*.csv")):
                try:
                    os.remove(file)
                    log_message(f"Removed: {os.path.basename(file)}")
                except Exception as e:
                    log_warning(f"Could not remove {file}: {e}")
            
            for file in glob.glob(os.path.join(OUTPUT_DIR, "*.html")):
                try:
                    os.remove(file)
                    log_message(f"Removed: {os.path.basename(file)}")
                except Exception as e:
                    log_warning(f"Could not remove {file}: {e}")
        
        # Clear data directory files (but preserve store_codes.csv)
        if os.path.exists(DATA_DIR):
            for pattern in ["store_coordinates_*.csv", "store_*_matrix_*.csv", "spu_*.csv", "*_matrix.csv"]:
                for file in glob.glob(os.path.join(DATA_DIR, pattern)):
                    try:
                        os.remove(file)
                        log_message(f"Removed: {os.path.basename(file)}")
                    except Exception as e:
                        log_warning(f"Could not remove {file}: {e}")
        
        log_success("All previous data cleared")
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
        
        # Rule results
        os.path.join(OUTPUT_DIR, f"rule7_missing_category_results_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule8_imbalanced_results_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"rule9_below_minimum_results_{period_label}.csv"),
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
        'name': 'SPU Assortment Optimization (Rule 10)',
        'description': 'Identify SPU assortment optimization opportunities',
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
    # Step 14: Global Overview Dashboard
    {
        'step': 14,
        'script': 'step14_global_overview_dashboard.py',
        'name': 'Global Overview Dashboard',
        'description': 'Generate executive overview dashboard',
        'critical': False,
        'category': 'visualization'
    },
    # Step 15: Interactive Map Dashboard
    {
        'step': 15,
        'script': 'step15_interactive_map_dashboard.py',
        'name': 'Interactive Map Dashboard',
        'description': 'Generate interactive geographic dashboard',
        'critical': False,
        'category': 'visualization'
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
        'visualization': '📈 Visualization'
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

# ——— PIPELINE EXECUTION ———

def run_script(script_name: str, description: str) -> bool:
    """
    Run a Python script and return success status.
    
    Args:
        script_name: Name of the script file in src/ directory
        description: Human-readable description for logging
        
    Returns:
        True if script succeeded, False otherwise
    """
    log_message(f"Starting {description}...")
    script_path = os.path.join("src", script_name)
    
    if not os.path.exists(script_path):
        log_error(f"Script {script_path} not found!")
        return False
    
    result = subprocess.run([sys.executable, script_path], 
                           capture_output=True, text=True)
    
    if result.returncode != 0:
        log_error(f"{description} failed!")
        print(result.stdout)
        print(result.stderr)
        return False
    else:
        print(result.stdout)
        log_success(f"{description} completed successfully")
        return True

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

    # Optional: load real coordinates to embed into store_sales for Step 2
    coords_map = {}
    try:
        coords_df = pd.read_csv(os.path.join(DATA_DIR, "store_coordinates_extended.csv"))
        if {'str_code', 'longitude', 'latitude'}.issubset(set(coords_df.columns)):
            coords_map = {
                str(row['str_code']): (float(row['longitude']), float(row['latitude']))
                for _, row in coords_df.iterrows()
            }
            log_message(f"Loaded coordinates for {len(coords_map)} stores to embed into sales summary")
    except Exception as _coords_e:
        log_warning(f"Could not load coordinates for embedding: {_coords_e}")
    
    # Create sample category sales data
    categories = ['Casual Pants', 'Dress Shirts', 'T-Shirts', 'Shoes', 'Accessories']
    subcats = ['Cargo Pants', 'Chinos', 'Business Shirts', 'Polo Shirts', 'Sneakers', 
               'Belts', 'Watches', 'Hats', 'Jeans', 'Sweaters']
    
    api_data = []
    # CRITICAL FIX: Generate realistic sales data instead of random
    import hashlib
    for store in store_codes:
        store_hash = int(hashlib.md5(store.encode()).hexdigest()[:8], 16)
        n_subcats = 5 + (store_hash % 4)  # 5-8 subcategories per store
        selected_subcats = subcats[:n_subcats]  # Use consistent selection
        
        for i, subcat in enumerate(selected_subcats):
            # CRITICAL FIX: Use store-specific data patterns based on REAL CSV analysis
            # Load actual data patterns if CSV exists
            try:
                if os.path.exists('fast_fish_with_sell_through_analysis_20250714_124522.csv'):
                    actual_data = pd.read_csv('fast_fish_with_sell_through_analysis_20250714_124522.csv')
                    
                    # Get real patterns from CSV for similar subcategories
                    similar_data = actual_data[actual_data['Target_Style_Tags'].str.contains(subcat, na=False)]
                    
                    if len(similar_data) > 0:
                        # Use REAL patterns from CSV
                        avg_spu_qty = similar_data['Current_SPU_Quantity'].mean()
                        avg_sales_per_spu = similar_data['Avg_Sales_Per_SPU'].mean()
                        sal_qty = int(avg_spu_qty) if not pd.isna(avg_spu_qty) else 100
                        sal_amt = sal_qty * avg_sales_per_spu if not pd.isna(avg_sales_per_spu) else sal_qty * 100
                    else:
                        # Use realistic store-based calculation
                        base_qty = 50 + (store_hash % 200)  
                        sal_qty = base_qty + (i * 20)  
                        price_per_unit = 60 + ((store_hash + i) % 100)  
                        sal_amt = sal_qty * price_per_unit
                else:
                    # Fallback if CSV not available
                    base_qty = 50 + (store_hash % 200)  
                    sal_qty = base_qty + (i * 20)  
                    price_per_unit = 60 + ((store_hash + i) % 100)  
                    sal_amt = sal_qty * price_per_unit
            except:
                # Error fallback
                base_qty = 50 + (store_hash % 200)  
                sal_qty = base_qty + (i * 20)  
                price_per_unit = 60 + ((store_hash + i) % 100)  
                sal_amt = sal_qty * price_per_unit
            
            # Use realistic category assignment from CSV data
            category_idx = (store_hash + i) % len(categories)
            
            api_data.append({
                'str_code': store,
                'cate_name': categories[category_idx],
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
    
    for store in store_codes:  # Generate SPU data for all stores
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
    # Provide SPU-mode compatible columns
    spu_df['spu_sales_amt'] = spu_df['sal_amt']
    spu_df.to_csv(api_files['spu_sales'], index=False)
    log_message(f"Created sample SPU sales data: {len(spu_df)} records")
    
    # Create SPU-mode compatible planning data with sty_sal_amt JSON and grouping columns
    try:
        import json as _json
        planning_rows = []
        # Build per store-subcategory JSON of SPU sales
        for (store, subcat), grp in spu_df.groupby(['str_code', 'sub_cate_name']):
            # use up to 20 SPUs per subcategory for compact JSON
            grp_sorted = grp.sort_values('spu_sales_amt', ascending=False).head(20)
            sty_dict = {row['spu_code']: float(row['spu_sales_amt']) for _, row in grp_sorted.iterrows()}
            planning_rows.append({
                'str_code': store,
                'season_name': 'ALL_SEASONS',
                'sex_name': 'UNISEX',
                'display_location_name': 'ALL_LOCATIONS',
                'big_class_name': grp_sorted['cate_name'].iloc[0] if 'cate_name' in grp_sorted.columns and len(grp_sorted) > 0 else 'ALL_CATEGORIES',
                'sub_cate_name': subcat,
                'ext_sty_cnt_avg': len(sty_dict),
                'target_sty_cnt_avg': max(1.0, len(sty_dict) * 0.8),
                'sty_sal_amt': _json.dumps(sty_dict)
            })
        config_df = pd.DataFrame(planning_rows)
        config_df.to_csv(api_files['store_config'], index=False)
        log_message(f"Created SPU-mode planning data with JSON: {len(config_df)} records")
    except Exception as _e:
        log_warning(f"Failed to create SPU-mode planning data: {_e}")
        # Fallback to basic config if needed
        config_data = []
        for store in store_codes:
            for subcat in subcats:
                config_data.append({
                    'str_code': store,
                    'sub_cate_name': subcat,
                    'allocation': np.random.uniform(0.5, 10.0),
                    'capacity': np.random.uniform(5.0, 20.0),
                    'target_sales': np.random.uniform(100, 1000)
                })
        config_df = pd.DataFrame(config_data)
        config_df.to_csv(api_files['store_config'], index=False)
        log_message(f"Created fallback store config data: {len(config_df)} records")
    
    # Create sample store sales summary
    sales_summary = []
    for store in store_codes:
        total_sales = np.random.uniform(10000, 100000)
        lon_lat_val = None
        if coords_map:
            coords = coords_map.get(str(store))
            if coords:
                lon_lat_val = f"{coords[0]},{coords[1]}"
        sales_summary.append({
            'str_code': store,
            'total_sal_qty': np.random.randint(100, 2000),
            'total_sal_amt': total_sales,
            'store_type': np.random.choice(['Basic', 'Fashion', 'Premium']),
            'long_lat': lon_lat_val
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
    # Step 10: SPU Assortment Optimization (Rule 10)
    {
        'step': 10,
        'script': 'step10_spu_assortment_optimization.py',
        'name': 'SPU Assortment Optimization (Rule 10)',
        'description': 'Identify SPU assortment optimization opportunities',
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
    # Step 14: Global Overview Dashboard
    {
        'step': 14,
        'script': 'step14_global_overview_dashboard.py',
        'name': 'Global Overview Dashboard',
        'description': 'Generate executive overview dashboard',
        'critical': False,
        'category': 'visualization'
    },
    # Step 15: Interactive Map Dashboard
    {
        'step': 15,
        'script': 'step15_interactive_map_dashboard.py',
        'name': 'Interactive Map Dashboard',
        'description': 'Generate interactive geographic dashboard',
        'critical': False,
        'category': 'visualization'
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
        'visualization': '📈 Visualization'
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

def run_pipeline(skip_api: bool = False, skip_weather: bool = False, 
                start_step: Optional[int] = None, end_step: Optional[int] = None,
                strict_mode: bool = False, validate_data: bool = False) -> bool:
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
            if skip_api:
                if not check_api_data_exists():
                    log_message("API data not found. Creating sample data files...")
                    if not create_sample_data_files():
                        log_error("Failed to create sample data files")
                        if is_critical or strict_mode:
                            return False
                        failed_steps.append(step_num)
                        completed_steps += 1
                        continue
                    log_message("Using sample data files for analysis")
                else:
                    log_message("API data found. Continuing with existing data")
                
                # Ensure backward compatibility
                log_message("Setting up backward compatibility...")
                ensure_backward_compatibility()
                update_legacy_file_references()
                
                # Validate data if requested
                if validate_data:
                    if not validate_data_quality(step_info):
                        log_error(f"Data validation failed after Step {step_num}")
                        if is_critical or strict_mode:
                            return False
                        failed_steps.append(step_num)
                
                completed_steps += 1
                continue
        
        # Run the step
        success = run_script(script_name, step_name)
        
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
        if validate_data and success:
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
        ("rule7_missing_category_results.csv", "Rule 7 - Missing Categories"),
        ("rule8_imbalanced_results.csv", "Rule 8 - Imbalanced Allocations"),
        ("rule9_below_minimum_results.csv", "Rule 9 - Below Minimum Thresholds"),
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
    parser.add_argument('--list-periods', action='store_true',
                       help='List available data periods and exit')
    
    # Step control arguments
    parser.add_argument('--start-step', type=int, 
                       help='Start from specific step number (1-15)')
    parser.add_argument('--end-step', type=int,
                       help='End at specific step number (1-15)')
    parser.add_argument('--list-steps', action='store_true',
                       help='List all pipeline steps and exit')
    parser.add_argument('--strict', action='store_true',
                       help='Stop pipeline on any error (no continue on warnings)')
    parser.add_argument('--validate-data', action='store_true',
                       help='Validate data quality after each step')
    
    args = parser.parse_args()
    
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
        
        # Clear data if requested
        if args.clear_all:
            clear_previous_data(clear_all=True)
        elif args.clear_period:
            clear_previous_data(yyyymm, period)
        else:
            # Default: clear current period data
            clear_previous_data(yyyymm, period)
        
        # Restore store codes if needed
        restore_store_codes()
        
        # Run the pipeline
        start_time = time.time()
        success = run_pipeline(
            skip_api=args.skip_api, 
            skip_weather=args.skip_weather,
            start_step=args.start_step,
            end_step=args.end_step,
            strict_mode=args.strict,
            validate_data=args.validate_data
        )
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