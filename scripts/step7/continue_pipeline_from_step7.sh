#!/bin/bash
# Continue Pipeline from Step 7
# After fixing Step 2B and data symlinks

set -e

echo "🚀 Continuing Pipeline from Step 7"
echo "===================================="
echo ""

cd /Users/borislavdzodzo/Desktop/Dev/ais-129-issues-found-when-running-main

export PYTHONPATH=.
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A

echo "✅ Environment set"
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

echo "✅ Pipeline continuation complete!"
echo ""
echo "Next: Run remaining steps 15-36 if needed"
