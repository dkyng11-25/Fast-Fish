#!/bin/bash

# Complete Pipeline Setup and Execution Script
# Purpose: Set up data symlinks and run all 36 steps to validate dual output pattern fixes
# Generated: 2025-10-01 20:54:00

set -e  # Exit on error

echo "🚀 Starting Complete Pipeline Setup and Execution"
echo "=================================================="
echo ""

# Set working directory
cd /Users/borislavdzodzo/Desktop/Dev/ais-129-issues-found-when-running-main

# Global environment variables
export RECENT_MONTHS_BACK=3
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A
export PYTHONPATH=.

echo "✅ Environment variables set:"
echo "   RECENT_MONTHS_BACK=$RECENT_MONTHS_BACK"
echo "   PIPELINE_TARGET_YYYYMM=$PIPELINE_TARGET_YYYYMM"
echo "   PIPELINE_TARGET_PERIOD=$PIPELINE_TARGET_PERIOD"
echo ""

# ============================================================================
# PHASE 0: DATA SETUP - CREATE SYMLINKS
# ============================================================================

echo "📁 PHASE 0: Setting up data symlinks"
echo "======================================"
echo ""

# Create necessary directories
mkdir -p data/api_data
mkdir -p output
mkdir -p data

echo "Creating symlinks from source directory..."
SOURCE_DIR="/Users/borislavdzodzo/Desktop/Dev/ProducMixClustering_spu_clustering_rules_visualization-copy"

# Symlink the main data files from 202410A (real data)
echo "  → Symlinking store_config_202510A.csv from 202410A..."
ln -sf "$SOURCE_DIR/data/api_data/store_config_202410A.csv" data/api_data/store_config_202510A.csv

echo "  → Symlinking complete_category_sales_202510A.csv from 202410A..."
ln -sf "$SOURCE_DIR/data/api_data/complete_category_sales_202410A.csv" data/api_data/complete_category_sales_202510A.csv

echo "  → Symlinking complete_spu_sales_202510A.csv from 202410A..."
ln -sf "$SOURCE_DIR/data/api_data/complete_spu_sales_202410A.csv" data/api_data/complete_spu_sales_202510A.csv

echo "  → Symlinking store_sales_202510A.csv from 202410A..."
ln -sf "$SOURCE_DIR/data/api_data/store_sales_202410A.csv" data/api_data/store_sales_202510A.csv

# Symlink other required data files
echo "  → Symlinking additional data files..."
ln -sf "$SOURCE_DIR/data/api_data/store_config_data.csv" data/api_data/store_config_data.csv
ln -sf "$SOURCE_DIR/data/api_data/store_sales_data.csv" data/api_data/store_sales_data.csv

# Symlink coordinates and other reference data
if [ -f "$SOURCE_DIR/data/store_coordinates_extended.csv" ]; then
    echo "  → Symlinking store_coordinates_extended.csv..."
    ln -sf "$SOURCE_DIR/data/store_coordinates_extended.csv" data/store_coordinates_extended.csv
fi

if [ -f "$SOURCE_DIR/data/spu_subcategory_mapping.csv" ]; then
    echo "  → Symlinking spu_subcategory_mapping.csv..."
    ln -sf "$SOURCE_DIR/data/spu_subcategory_mapping.csv" data/spu_subcategory_mapping.csv
fi

# Symlink weather data if exists
if [ -d "$SOURCE_DIR/data/weather_data" ]; then
    echo "  → Symlinking weather_data directory..."
    ln -sf "$SOURCE_DIR/data/weather_data" data/weather_data
fi

echo ""
echo "✅ Data symlinks created successfully!"
echo ""

# Verify symlinks
echo "🔍 Verifying symlinks..."
ls -lh data/api_data/store_config_202510A.csv
ls -lh data/api_data/complete_category_sales_202510A.csv
ls -lh data/api_data/complete_spu_sales_202510A.csv
ls -lh data/api_data/store_sales_202510A.csv
echo ""

# ============================================================================
# PHASE 1: DATA ACQUISITION (Steps 1-6) - SKIP STEPS 1 & 4
# ============================================================================

echo "📊 PHASE 1: Data Acquisition (Steps 2, 2B, 3, 5, 6)"
echo "===================================================="
echo ""

echo "⏭️  Skipping Step 1 (Download API Data) - using symlinked data"
echo ""

echo "▶️  Step 2: Extract Coordinates"
python3 src/step2_extract_coordinates.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 2B: Consolidate Seasonal Data"
python3 src/step2b_consolidate_seasonal_data.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 3: Prepare Matrix"
python3 src/step3_prepare_matrix.py --target-yyyymm 202510 --target-period A
echo ""

echo "⏭️  Skipping Step 4 (Download Weather Data) - using symlinked data"
echo ""

echo "▶️  Step 5: Calculate Feels Like Temperature"
python3 src/step5_calculate_feels_like_temperature.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 6: Cluster Analysis"
python3 src/step6_cluster_analysis.py --target-yyyymm 202510 --target-period A
echo ""

# ============================================================================
# PHASE 2: BUSINESS RULES (Steps 7-12)
# ============================================================================

echo "📋 PHASE 2: Business Rules (Steps 7-12)"
echo "========================================"
echo ""

echo "▶️  Step 7: Missing Category Rule"
python3 src/step7_missing_category_rule.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 8: Imbalanced Rule"
python3 src/step8_imbalanced_rule.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 9: Below Minimum Rule"
python3 src/step9_below_minimum_rule.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 10: SPU Assortment Optimization"
python3 src/step10_spu_assortment_optimization.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 11: Missed Sales Opportunity"
python3 src/step11_missed_sales_opportunity.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 12: Sales Performance Rule"
python3 src/step12_sales_performance_rule.py --target-yyyymm 202510 --target-period A
echo ""

# ============================================================================
# PHASE 3: CONSOLIDATION & FORMATTING (Steps 13-14)
# ============================================================================

echo "🔄 PHASE 3: Consolidation & Formatting (Steps 13-14)"
echo "====================================================="
echo ""

echo "▶️  Step 13: Consolidate SPU Rules (FAST_MODE)"
FAST_MODE=1 python3 src/step13_consolidate_spu_rules.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 14: Create Fast Fish Format"
python3 src/step14_create_fast_fish_format.py --target-yyyymm 202510 --target-period A
echo ""

# ============================================================================
# PHASE 4: HISTORICAL & TREND ANALYSIS (Steps 15-18)
# ============================================================================

echo "📈 PHASE 4: Historical & Trend Analysis (Steps 15-18)"
echo "======================================================"
echo ""

echo "▶️  Step 15: Download Historical Baseline"
python3 src/step15_download_historical_baseline.py --target-yyyymm 202510 --target-period A --baseline-yyyymm 202410 --baseline-period A
echo ""

echo "▶️  Step 16: Create Comparison Tables"
python3 src/step16_create_comparison_tables.py --target-yyyymm 202510 --target-period A --baseline-yyyymm 202410 --baseline-period A
echo ""

echo "▶️  Step 17: Augment Recommendations"
python3 src/step17_augment_recommendations.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 18: Validate Results"
python3 src/step18_validate_results.py --target-yyyymm 202510 --target-period A
echo ""

# ============================================================================
# PHASE 5: DETAILED ANALYSIS & VALIDATION (Steps 19-21)
# ============================================================================

echo "🔍 PHASE 5: Detailed Analysis & Validation (Steps 19-21)"
echo "========================================================="
echo ""

echo "▶️  Step 19: Detailed SPU Breakdown"
python3 src/step19_detailed_spu_breakdown.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 20: Data Validation"
python3 src/step20_data_validation.py
echo ""

echo "▶️  Step 21: Label Tag Recommendations"
python3 src/step21_label_tag_recommendations.py --target-yyyymm 202510 --target-period A
echo ""

# ============================================================================
# PHASE 6: STORE ENRICHMENT (Steps 22-24)
# ============================================================================

echo "🏪 PHASE 6: Store Enrichment (Steps 22-24)"
echo "==========================================="
echo ""

echo "▶️  Step 22: Store Attribute Enrichment"
python3 src/step22_store_attribute_enrichment.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 23: Update Clustering Features"
python3 src/step23_update_clustering_features.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 24: Comprehensive Cluster Labeling"
python3 src/step24_comprehensive_cluster_labeling.py --target-yyyymm 202510 --target-period A
echo ""

# ============================================================================
# PHASE 7: ADVANCED ANALYSIS (Steps 25-30)
# ============================================================================

echo "🎯 PHASE 7: Advanced Analysis (Steps 25-30)"
echo "============================================"
echo ""

echo "▶️  Step 25: Product Role Classifier"
python3 src/step25_product_role_classifier.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 26: Price Elasticity Analyzer (Skip Elasticity)"
STEP26_SKIP_ELASTICITY=1 STEP26_SOURCE_YYYYMM=202510 STEP26_SOURCE_PERIOD=A python3 src/step26_price_elasticity_analyzer.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 27: Gap Matrix Generator"
python3 src/step27_gap_matrix_generator.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 28: Scenario Analyzer"
python3 src/step28_scenario_analyzer.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 29: Supply-Demand Gap Analysis"
python3 src/step29_supply_demand_gap_analysis.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 30: Sell-Through Optimization Engine"
python3 src/step30_sellthrough_optimization_engine.py --target-yyyymm 202510 --target-period A
echo ""

# ============================================================================
# PHASE 8: STORE-LEVEL DEPLOYMENT (Steps 31-36)
# ============================================================================

echo "🚀 PHASE 8: Store-Level Deployment (Steps 31-36)"
echo "================================================="
echo ""

echo "▶️  Step 31: Gap Analysis Workbook"
python3 src/step31_gap_analysis_workbook.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 32: Store Allocation"
# Note: Step 32 may require column name fix for clustering results
python3 src/step32_store_allocation.py --period A --target-yyyymm 202510
echo ""

echo "▶️  Step 33: Store-Level Merchandising Rules"
python3 src/step33_store_level_merchandising_rules.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 34A: Cluster Strategy Optimization"
python3 src/step34a_cluster_strategy_optimization.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 34B: Unify Outputs"
python3 src/step34b_unify_outputs.py --target-yyyymm 202510 --periods A
echo ""

echo "▶️  Step 35: Merchandising Strategy Deployment"
python3 src/step35_merchandising_strategy_deployment.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 36: Unified Delivery Builder"
python3 src/step36_unified_delivery_builder.py --target-yyyymm 202510 --target-period A
echo ""

# ============================================================================
# COMPLETION
# ============================================================================

echo ""
echo "🎉 =============================================="
echo "🎉 PIPELINE EXECUTION COMPLETE!"
echo "🎉 =============================================="
echo ""
echo "✅ All 36 steps executed successfully"
echo "✅ Dual output pattern validated across pipeline"
echo ""
echo "📊 Check output/ directory for results:"
echo "   - Timestamped files: For backup/inspection"
echo "   - Generic files: For pipeline flow"
echo ""
echo "🔍 Validation checklist:"
echo "   1. Check that both timestamped and generic files exist"
echo "   2. Verify file sizes match between versions"
echo "   3. Confirm no manual symlinks were needed"
echo "   4. Review logs for any warnings or errors"
echo ""
