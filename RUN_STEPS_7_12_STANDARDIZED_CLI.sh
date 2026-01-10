#!/bin/bash
# Execute Steps 7-12 for Winter 202510A with STANDARDIZED CLI ARGUMENTS
# All thresholds now configurable via CLI (no hardcoded values!)

set -e  # Exit on error

echo "🎯 Steps 7-12 Execution: Winter 202510A (STANDARDIZED CLI)"
echo "==========================================================="
echo ""
echo "📊 Dataset: 2,255 stores, 46 clusters (avg 49 stores/cluster)"
echo "⚙️  All thresholds: Configurable via CLI arguments"
echo "✅ No hardcoded values - full flexibility!"
echo ""

# Set base environment variables
export RECENT_MONTHS_BACK=3
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A
export PIPELINE_YYYYMM=202510
export PIPELINE_PERIOD=A
export PYTHONPATH=.

echo "✅ Environment configured"
echo ""

# ============================================================================
# STEP 7: Missing Category Rule (NOW WITH CLI ARGS!)
# ============================================================================
echo "📊 Step 7: Missing Category Rule (CLI STANDARDIZED)"
echo "----------------------------------------------------"
echo "   NEW CLI Arguments:"
echo "   - --min-adoption-rate: 0.80 → 0.30"
echo "   - --min-cluster-sales: 1500 → 500"
echo "   - --min-opportunity-value: 500 → 200"
echo "   - --max-missing-per-store: 5 (keeping default)"
echo ""

python3 src/step7_missing_category_rule.py \
  --target-yyyymm 202510 --target-period A \
  --min-adoption-rate 0.30 \
  --min-cluster-sales 500 \
  --min-opportunity-value 200 \
  --max-missing-per-store 5

if [ $? -eq 0 ]; then
    echo "✅ Step 7 completed"
    wc -l output/rule7_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 7 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 8: Imbalanced Allocation Rule (NOW WITH CLI ARGS!)
# ============================================================================
echo "📊 Step 8: Imbalanced Allocation Rule (CLI STANDARDIZED)"
echo "---------------------------------------------------------"
echo "   NEW CLI Arguments:"
echo "   - --z-threshold: 3.0 → 2.0"
echo "   - --min-cluster-size: 5 → 2"
echo "   - --min-allocation-threshold: 0.05 → 0.03"
echo "   - --min-rebalance-qty: 5.0 → 3.0"
echo ""

python3 src/step8_imbalanced_rule.py \
  --yyyymm 202510 --period A \
  --target-yyyymm 202510 --target-period A \
  --z-threshold 2.0 \
  --min-cluster-size 2 \
  --min-allocation-threshold 0.03 \
  --min-rebalance-qty 3.0

if [ $? -eq 0 ]; then
    echo "✅ Step 8 completed"
    wc -l output/rule8_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 8 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 9: Below Minimum Quantity Rule (EXISTING CLI ARGS)
# ============================================================================
echo "📊 Step 9: Below Minimum Quantity Rule (CLI ADJUSTED)"
echo "------------------------------------------------------"
echo "   CLI Arguments:"
echo "   - --min-threshold: 0.03 → 0.01"
echo "   - --min-boost: 0.5 → 0.3"
echo ""

python3 src/step9_below_minimum_rule.py \
  --target-yyyymm 202510 --target-period A \
  --min-threshold 0.01 \
  --min-boost 0.3

if [ $? -eq 0 ]; then
    echo "✅ Step 9 completed"
    wc -l output/rule9_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 9 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 10: SPU Assortment Optimization (NO ADJUSTMENTS NEEDED)
# ============================================================================
echo "📊 Step 10: SPU Assortment Optimization (DEFAULT)"
echo "--------------------------------------------------"
echo "   No adjustments needed - already producing good results!"
echo ""

python3 src/step10_spu_assortment_optimization.py \
  --yyyymm 202510 --period A \
  --target-yyyymm 202510 --target-period A

if [ $? -eq 0 ]; then
    echo "✅ Step 10 completed"
    wc -l output/rule10_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 10 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 11: Missed Sales Opportunity (EXISTING CLI ARGS)
# ============================================================================
echo "📊 Step 11: Missed Sales Opportunity (CLI ADJUSTED)"
echo "----------------------------------------------------"
echo "   CLI Arguments:"
echo "   - --min-cluster-stores: 8 → 3"
echo "   - --min-stores-selling: 5 → 2"
echo "   - --min-spu-sales: 200 → 100"
echo "   - --top-performer-threshold: 0.95 → 0.80"
echo ""

python3 src/step11_missed_sales_opportunity.py \
  --target-yyyymm 202510 --target-period A \
  --min-cluster-stores 3 \
  --min-stores-selling 2 \
  --min-spu-sales 100 \
  --top-performer-threshold 0.80

if [ $? -eq 0 ]; then
    echo "✅ Step 11 completed"
    wc -l output/rule11_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 11 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 12: Sales Performance Rule (EXISTING CLI ARGS)
# ============================================================================
echo "📊 Step 12: Sales Performance Rule (CLI ADJUSTED)"
echo "--------------------------------------------------"
echo "   CLI Arguments:"
echo "   - --min-cluster-size: default → 3"
echo "   - --min-sales-volume: default → 500"
echo "   - --min-opportunity-score: 0.05 → 0.03"
echo ""

python3 src/step12_sales_performance_rule.py \
  --target-yyyymm 202510 --target-period A \
  --min-cluster-size 3 \
  --min-sales-volume 500 \
  --min-opportunity-score 0.03

if [ $? -eq 0 ]; then
    echo "✅ Step 12 completed"
    wc -l output/rule12_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 12 failed"
    exit 1
fi
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "🎉 All Steps 7-12 Completed with Standardized CLI!"
echo "==================================================="
echo ""
echo "📊 Results Summary:"
echo "-------------------"
for step in 7 8 9 10 11 12; do
    latest=$(ls -t output/rule${step}_*_results_*.csv 2>/dev/null | head -1)
    if [ -f "$latest" ]; then
        count=$(($(wc -l < "$latest") - 1))  # Subtract header
        echo "   Step $step: $count recommendations"
    else
        echo "   Step $step: No results file found"
    fi
done
echo ""
echo "✅ Key Achievement: ALL thresholds now configurable via CLI!"
echo "📁 Output files in: output/"
echo "🚀 Ready for Step 13 (Consolidation)"
