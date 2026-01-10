#!/bin/bash
# Run Pipeline from Step 3 onwards
# Steps 2 and 2B already completed

set -e

echo "🚀 Running Pipeline from Step 3"
echo "================================"
echo ""

cd /Users/borislavdzodzo/Desktop/Dev/ais-129-issues-found-when-running-main

export PYTHONPATH=.
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A

echo "✅ Environment set:"
echo "   PYTHONPATH=$PYTHONPATH"
echo "   PIPELINE_TARGET_YYYYMM=$PIPELINE_TARGET_YYYYMM"
echo "   PIPELINE_TARGET_PERIOD=$PIPELINE_TARGET_PERIOD"
echo ""

# ============================================================================
# PHASE 1: DATA ACQUISITION (Steps 3, 5, 6)
# ============================================================================

echo "📊 PHASE 1: Data Acquisition (Steps 3, 5, 6)"
echo "=============================================="
echo ""

echo "▶️  Step 3: Prepare Matrix"
python3 src/step3_prepare_matrix.py --target-yyyymm 202510 --target-period A
echo ""

echo "⏭️  Skipping Step 4 (Download Weather Data) - using existing data"
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
PIPELINE_YYYYMM=202510 PIPELINE_PERIOD=A python3 src/step10_spu_assortment_optimization.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 11: Missed Sales Opportunity"
python3 src/step11_missed_sales_opportunity.py --target-yyyymm 202510 --target-period A
echo ""
{{ ... }}
echo "▶️  Step 12: Sales Performance Rule"
python3 src/step12_sales_performance_rule.py --target-yyyymm 202510 --target-period A
echo ""

# ============================================================================
# PHASE 3: CONSOLIDATION (Steps 13-14)
# ============================================================================

echo "🔄 PHASE 3: Consolidation (Steps 13-14)"
echo "========================================"
echo ""

echo "▶️  Step 13: Consolidate SPU Rules (FAST_MODE)"
FAST_MODE=1 python3 src/step13_consolidate_spu_rules.py --target-yyyymm 202510 --target-period A
echo ""

echo "▶️  Step 14: Create Fast Fish Format"
python3 src/step14_create_fast_fish_format.py --target-yyyymm 202510 --target-period A
echo ""

echo "✅ Pipeline Steps 3-14 complete!"
echo ""
echo "Check output/ directory for dual output files"
