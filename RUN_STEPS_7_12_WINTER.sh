#!/bin/bash
# Execute Steps 7-12 for Winter 202510A Allocation
# Focus: Winter items using YoY October 2024 data

set -e  # Exit on error

echo "🎯 Steps 7-12 Execution: Winter 202510A Allocation"
echo "=================================================="
echo ""

# Set environment variables
export RECENT_MONTHS_BACK=3
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A
export PYTHONPATH=.

echo "✅ Environment configured:"
echo "   RECENT_MONTHS_BACK=$RECENT_MONTHS_BACK"
echo "   PIPELINE_TARGET_YYYYMM=$PIPELINE_TARGET_YYYYMM"
echo "   PIPELINE_TARGET_PERIOD=$PIPELINE_TARGET_PERIOD"
echo ""

# ============================================================================
# STEP 0: Data Preparation
# ============================================================================
echo "📋 Step 0: Data Preparation"
echo "----------------------------"

# Check if 202510A data exists, if not create symlinks from YoY 202410A
if [ ! -f "data/api_data/store_config_202510A.csv" ]; then
    echo "⚠️  202510A data not found, creating symlinks from YoY 202410A..."
    
    if [ -f "data/api_data/store_config_202410A.csv" ]; then
        ln -sf store_config_202410A.csv data/api_data/store_config_202510A.csv
        echo "   ✅ Created store_config_202510A.csv -> store_config_202410A.csv"
    else
        echo "   ❌ ERROR: 202410A data not found either!"
        exit 1
    fi
    
    if [ -f "data/api_data/complete_spu_sales_202410A.csv" ]; then
        ln -sf complete_spu_sales_202410A.csv data/api_data/complete_spu_sales_202510A.csv
        echo "   ✅ Created complete_spu_sales_202510A.csv -> complete_spu_sales_202410A.csv"
    fi
    
    if [ -f "data/api_data/complete_category_sales_202410A.csv" ]; then
        ln -sf complete_category_sales_202410A.csv data/api_data/complete_category_sales_202510A.csv
        echo "   ✅ Created complete_category_sales_202510A.csv -> complete_category_sales_202410A.csv"
    fi
else
    echo "   ✅ 202510A data already exists"
fi

# Check if clustering results exist
if [ ! -f "output/clustering_results_spu.csv" ]; then
    echo "⚠️  Clustering results not found"
    echo "   You need to run Step 6 first, or create symlink from existing clustering"
    echo "   Example: ln -sf clustering_results_spu_202410A.csv output/clustering_results_spu.csv"
    echo ""
    echo "   Available clustering files:"
    ls -1 output/clustering_results_spu*.csv 2>/dev/null || echo "   None found"
    echo ""
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "   ✅ Clustering results found"
fi

echo ""

# ============================================================================
# STEP 7: Missing Category Rule
# ============================================================================
echo "📊 Step 7: Missing Category Rule"
echo "---------------------------------"
python3 src/step7_missing_category_rule.py \
    --target-yyyymm 202510 \
    --target-period A

if [ $? -eq 0 ]; then
    echo "✅ Step 7 completed successfully"
    ls -lh output/rule7_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 7 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 8: Imbalanced Allocation Rule
# ============================================================================
echo "📊 Step 8: Imbalanced Allocation Rule"
echo "--------------------------------------"
python3 src/step8_imbalanced_rule.py \
    --target-yyyymm 202510 \
    --target-period A

if [ $? -eq 0 ]; then
    echo "✅ Step 8 completed successfully"
    ls -lh output/rule8_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 8 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 9: Below Minimum Quantity Rule
# ============================================================================
echo "📊 Step 9: Below Minimum Quantity Rule"
echo "---------------------------------------"
python3 src/step9_below_minimum_rule.py \
    --target-yyyymm 202510 \
    --target-period A

if [ $? -eq 0 ]; then
    echo "✅ Step 9 completed successfully"
    ls -lh output/rule9_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 9 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 10: SPU Assortment Optimization (Overcapacity)
# ============================================================================
echo "📊 Step 10: SPU Assortment Optimization"
echo "----------------------------------------"
python3 src/step10_spu_assortment_optimization.py \
    --target-yyyymm 202510 \
    --target-period A

if [ $? -eq 0 ]; then
    echo "✅ Step 10 completed successfully"
    ls -lh output/rule10_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 10 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 11: Missed Sales Opportunity
# ============================================================================
echo "📊 Step 11: Missed Sales Opportunity"
echo "-------------------------------------"
python3 src/step11_missed_sales_opportunity.py \
    --target-yyyymm 202510 \
    --target-period A

if [ $? -eq 0 ]; then
    echo "✅ Step 11 completed successfully"
    ls -lh output/rule11_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 11 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 12: Sales Performance Rule (Performance Deviation)
# ============================================================================
echo "📊 Step 12: Sales Performance Rule"
echo "-----------------------------------"
python3 src/step12_sales_performance_rule.py \
    --target-yyyymm 202510 \
    --target-period A

if [ $? -eq 0 ]; then
    echo "✅ Step 12 completed successfully"
    ls -lh output/rule12_*_results_*.csv 2>/dev/null | tail -1
else
    echo "❌ Step 12 failed"
    exit 1
fi
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "🎉 All Steps 7-12 Completed Successfully!"
echo "=========================================="
echo ""
echo "📊 Generated Output Files:"
echo "--------------------------"
ls -lh output/rule*_*_results_*.csv 2>/dev/null | tail -6
echo ""
echo "📈 Record Counts:"
echo "-----------------"
for file in output/rule{7,8,9,10,11,12}_*_results_*.csv; do
    if [ -f "$file" ]; then
        count=$(wc -l < "$file")
        echo "   $(basename $file): $count records"
    fi
done
echo ""
echo "✅ Ready for Step 13 (Consolidation)"
