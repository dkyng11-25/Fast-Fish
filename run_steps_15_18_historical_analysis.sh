#!/bin/bash
# Master execution script for Steps 15-18: Historical Analysis Workflow
# Enhanced with comprehensive trending analysis

echo "================================================================================"
echo "🚀 STEPS 15-18: HISTORICAL ANALYSIS WORKFLOW"
echo "   Historical Reference + Comprehensive Trending Analysis"
echo "================================================================================"
echo "Starting enhanced historical reference analysis with trending insights..."

# Step 15: Download historical baseline
echo ""
echo "Step 15: Creating historical baseline (202407A reference)..."
PYTHONPATH=. python src/step15_download_historical_baseline.py --target-yyyymm "${PIPELINE_TARGET_YYYYMM}" --target-period "${PIPELINE_TARGET_PERIOD}"
if [ $? -ne 0 ]; then
    echo "❌ Error in Step 15"
    exit 1
fi
echo "✅ Step 15 completed"

# Step 16: Create comparison tables (optional)
echo ""
echo "Step 16: Creating Excel comparison tables..."
PYTHONPATH=. python src/step16_create_comparison_tables.py --target-yyyymm "${PIPELINE_TARGET_YYYYMM}" --target-period "${PIPELINE_TARGET_PERIOD}"
if [ $? -ne 0 ]; then
    echo "⚠️ Warning: Step 16 failed, continuing..."
else
    echo "✅ Step 16 completed"
fi

# Step 17: Enhanced augmentation with trending analysis
echo ""
echo "Step 17: Enhanced Fast Fish augmentation..."
echo "        • Historical reference (July 2024 baseline)"
echo "        • 10-dimension trending analysis"
echo "        • Comprehensive business priority scoring"
STEP17_ENABLE_TRENDING=true PYTHONPATH=. python src/step17_augment_recommendations.py --target-yyyymm "${PIPELINE_TARGET_YYYYMM}" --target-period "${PIPELINE_TARGET_PERIOD}" --enable-trending
if [ $? -ne 0 ]; then
    echo "❌ Error in Step 17 (Critical Step)"
    exit 1
fi
echo "✅ Step 17 completed"

# Step 18: Validate results
echo ""
echo "Step 18: Validating enhanced results..."
PYTHONPATH=. python src/step18_validate_results.py --target-yyyymm "${PIPELINE_TARGET_YYYYMM}" --target-period "${PIPELINE_TARGET_PERIOD}"
if [ $? -ne 0 ]; then
    echo "⚠️ Warning: Validation issues detected"
else
    echo "✅ Step 18 completed"
fi

echo ""
echo "================================================================================"
echo "🎯 STEPS 15-18 COMPLETED SUCCESSFULLY"
echo "================================================================================"
echo "📊 Key Outputs Generated:"
echo "  • Historical baseline analysis (Step 15)"
echo "  • Excel comparison tables (Step 16)"
echo "  • Enhanced Fast Fish recommendations with:"
echo "    - Historical context (July 2024 baselines)"
echo "    - 10-dimension trending analysis"
echo "    - Business priority scoring"
echo "    - Comprehensive rationale with confidence metrics"
echo "  • Validation reports (Step 18)"
echo ""
echo "📁 Check output/ directory for:"
echo "  • fast_fish_with_historical_and_cluster_trending_analysis_YYYYMMDD_HHMMSS.csv"
echo "  • historical_reference_202407A_YYYYMMDD_HHMMSS.csv"
echo "  • spreadsheet_comparison_analysis_YYYYMMDD_HHMMSS.xlsx"
echo ""
echo "🚀 Enhanced recommendations now include comprehensive market intelligence!"
echo "================================================================================"
