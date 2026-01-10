#!/bin/bash
# Experiment with ULTRA LOW thresholds to get meaningful results
# Strategy: Lower thresholds progressively until we get results

set -e

echo "🧪 EXPERIMENTAL RUN: Ultra Low Thresholds"
echo "=========================================="
echo ""
echo "Goal: Get meaningful results from each step"
echo "Strategy: Aggressively lower all thresholds"
echo ""

export PYTHONPATH=.
export RECENT_MONTHS_BACK=3
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A
export PIPELINE_YYYYMM=202510
export PIPELINE_PERIOD=A

# ============================================================================
# STEP 7: Missing Category - ULTRA LOW
# ============================================================================
echo "📊 Step 7: Missing Category (ULTRA LOW THRESHOLDS)"
echo "---------------------------------------------------"
echo "Thresholds:"
echo "  - Min adoption: 0.10 (10% vs 80% default)"
echo "  - Min cluster sales: $50 (vs $1,500 default)"
echo "  - Min opportunity: $10 (vs $500 default)"
echo ""

RULE7_MIN_STORES_SELLING=1 \
RULE7_MIN_ADOPTION=0.05 \
MIN_COMPARABLES=1 \
ROI_MIN_THRESHOLD=0.05 \
MIN_MARGIN_UPLIFT=10 \
python3 src/step7_missing_category_rule.py \
  --target-yyyymm 202510 --target-period A \
  --min-adoption-rate 0.10 \
  --min-cluster-sales 50 \
  --min-opportunity-value 10 \
  2>&1 | tee step7_ultra_low.log | tail -30

echo ""
wc -l output/rule7_*_results_*.csv 2>/dev/null | tail -1
echo ""

# ============================================================================
# STEP 8: Imbalanced - ULTRA LOW
# ============================================================================
echo "📊 Step 8: Imbalanced Allocation (ULTRA LOW THRESHOLDS)"
echo "--------------------------------------------------------"
echo "Thresholds:"
echo "  - Z-score: 1.0 (vs 3.0 default)"
echo "  - Min cluster size: 1 (vs 5 default)"
echo "  - Min allocation: 0.001 (vs 0.05 default)"
echo ""

python3 src/step8_imbalanced_rule.py \
  --yyyymm 202510 --period A \
  --target-yyyymm 202510 --target-period A \
  --z-threshold 1.0 \
  --min-cluster-size 1 \
  --min-allocation-threshold 0.001 \
  --min-rebalance-qty 1.0 \
  2>&1 | tee step8_ultra_low.log | tail -30

echo ""
wc -l output/rule8_*_results_*.csv 2>/dev/null | tail -1
echo ""

# ============================================================================
# STEP 9: Below Minimum - ALREADY GOOD
# ============================================================================
echo "📊 Step 9: Below Minimum (Already producing results)"
echo "-----------------------------------------------------"
echo "Current results: 104 units, $13,297"
echo "Skipping - already working!"
echo ""

# ============================================================================
# STEP 11: Missed Sales - ULTRA LOW
# ============================================================================
echo "📊 Step 11: Missed Sales Opportunity (ULTRA LOW THRESHOLDS)"
echo "------------------------------------------------------------"
echo "Thresholds:"
echo "  - Min cluster stores: 1 (vs 8 default)"
echo "  - Min stores selling: 1 (vs 5 default)"
echo "  - Min SPU sales: $10 (vs $200 default)"
echo "  - Top performer: 50% (vs 95% default)"
echo ""

python3 src/step11_missed_sales_opportunity.py \
  --target-yyyymm 202510 --target-period A \
  --min-cluster-stores 1 \
  --min-stores-selling 1 \
  --min-spu-sales 10 \
  --top-performer-threshold 0.50 \
  2>&1 | tee step11_ultra_low.log | tail -30

echo ""
wc -l output/rule11_*_results_*.csv 2>/dev/null | tail -1
echo ""

# ============================================================================
# STEP 12: Sales Performance - ULTRA LOW
# ============================================================================
echo "📊 Step 12: Sales Performance (ULTRA LOW THRESHOLDS)"
echo "-----------------------------------------------------"
echo "Thresholds:"
echo "  - Min cluster size: 1 (vs default)"
echo "  - Min sales volume: $50 (vs $500)"
echo "  - Min opportunity score: 0.01 (vs 0.05)"
echo ""

python3 src/step12_sales_performance_rule.py \
  --target-yyyymm 202510 --target-period A \
  --min-cluster-size 1 \
  --min-sales-volume 50 \
  --min-opportunity-score 0.01 \
  --min-z 0.5 \
  2>&1 | tee step12_ultra_low.log | tail -30

echo ""
wc -l output/rule12_*_results_*.csv 2>/dev/null | tail -1
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "🎯 EXPERIMENTAL RESULTS SUMMARY"
echo "================================"
echo ""

for step in 7 8 9 11 12; do
    echo "Step $step:"
    latest=$(ls -t output/rule${step}_*_results_*.csv 2>/dev/null | head -1)
    if [ -f "$latest" ]; then
        count=$(($(wc -l < "$latest") - 1))
        echo "  Recommendations: $count"
        
        # Try to find flagged/opportunity counts
        if [ $step -eq 7 ] || [ $step -eq 8 ] || [ $step -eq 9 ]; then
            flagged=$(python3 -c "import pandas as pd; df=pd.read_csv('$latest'); print((df.iloc[:, 1] > 0).sum() if len(df.columns) > 1 else 0)" 2>/dev/null || echo "?")
            echo "  Flagged stores: $flagged"
        fi
    else
        echo "  No results file"
    fi
    echo ""
done

echo "✅ Experiment complete!"
echo ""
echo "Next: Review logs to see why results are still limited"
echo "  - step7_ultra_low.log"
echo "  - step8_ultra_low.log"
echo "  - step11_ultra_low.log"
echo "  - step12_ultra_low.log"
