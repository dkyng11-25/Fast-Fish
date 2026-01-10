#!/bin/bash

# Continue Pipeline from Step 13 (Critical Dual Output Validation Steps)

set -e

cd /Users/borislavdzodzo/Desktop/Dev/ais-129-issues-found-when-running-main

export RECENT_MONTHS_BACK=3
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A
export PYTHONPATH=.

echo "🔄 Continuing Pipeline from Step 13..."
echo "Note: Steps 10-12 may have issues, focusing on dual output validation"
echo ""

# Step 13: Consolidate (FAST_MODE) - FIRST DUAL OUTPUT FIX
echo "▶️  Step 13: Consolidate SPU Rules (FAST_MODE) ⭐ DUAL OUTPUT FIX"
FAST_MODE=1 python3 src/step13_consolidate_spu_rules.py --target-yyyymm 202510 --target-period A
echo ""

# Step 14: Fast Fish Format - DUAL OUTPUT FIX
echo "▶️  Step 14: Create Fast Fish Format ⭐ DUAL OUTPUT FIX"
python3 src/step14_create_fast_fish_format.py --target-yyyymm 202510 --target-period A
echo ""

# Steps 15-18: Historical & Trend Analysis - CRITICAL DUAL OUTPUT FIXES
echo "📈 PHASE 4: Historical & Trend Analysis (Steps 15-18)"
echo ""

echo "▶️  Step 15: Download Historical Baseline ⭐ DUAL OUTPUT FIX"
python3 src/step15_download_historical_baseline.py --target-yyyymm 202510 --target-period A --baseline-yyyymm 202410 --baseline-period A
echo ""

echo "▶️  Step 16: Create Comparison Tables ⭐ DUAL OUTPUT FIX"
python3 src/step16_create_comparison_tables.py --target-yyyymm 202510 --target-period A --baseline-yyyymm 202410 --baseline-period A
echo ""

echo "▶️  Step 17: Augment Recommendations ⭐ DUAL OUTPUT FIX"
python3 src/step17_augment_recommendations.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 18: Validate Results ⭐ DUAL OUTPUT FIX"
python3 src/step18_validate_results.py --target-yyyymm 202510 --target-period A
echo ""

# Steps 19-21: Detailed Analysis - DUAL OUTPUT FIXES
echo "🔍 PHASE 5: Detailed Analysis & Validation (Steps 19-21)"
echo ""

echo "▶️  Step 19: Detailed SPU Breakdown ⭐ DUAL OUTPUT FIX"
python3 src/step19_detailed_spu_breakdown.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 20: Data Validation ⭐ DUAL OUTPUT FIX"
python3 src/step20_data_validation.py
echo ""

echo "▶️  Step 21: Label Tag Recommendations ⭐ DUAL OUTPUT FIX"
python3 src/step21_label_tag_recommendations.py --target-yyyymm 202510 --target-period A
echo ""

# Step 22: Store Enrichment - DUAL OUTPUT FIX
echo "🏪 PHASE 6: Store Enrichment (Step 22)"
echo ""

echo "▶️  Step 22: Store Attribute Enrichment ⭐ DUAL OUTPUT FIX"
python3 src/step22_store_attribute_enrichment.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 23: Update Clustering Features"
python3 src/step23_update_clustering_features.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 24: Comprehensive Cluster Labeling"
python3 src/step24_comprehensive_cluster_labeling.py --target-yyyymm 202510 --target-period A
echo ""

# Steps 25-30: Advanced Analysis
echo "🎯 PHASE 7: Advanced Analysis (Steps 25-30)"
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

# Steps 31-36: Store-Level Deployment
echo "🚀 PHASE 8: Store-Level Deployment (Steps 31-36)"
echo ""

echo "▶️  Step 31: Gap Analysis Workbook"
python3 src/step31_gap_analysis_workbook.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 32: Store Allocation"
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

echo "🎉 =============================================="
echo "🎉 DUAL OUTPUT VALIDATION COMPLETE!"
echo "🎉 =============================================="
echo ""
echo "Now run: python3 validate_dual_outputs.py"
