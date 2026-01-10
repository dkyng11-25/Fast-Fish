#!/bin/bash
# Run REFACTORED Step 7 in subcategory mode for comparison

set -e

TARGET_YYYYMM="202510"
TARGET_PERIOD="A"

echo "🔧 Running REFACTORED Step 7 - SUBCATEGORY MODE"
echo "============================================================"
echo "Target: ${TARGET_YYYYMM}${TARGET_PERIOD}"
echo "Analysis Level: SUBCATEGORY (all 2,255 stores)"
echo "============================================================"
echo ""

# Set PYTHONPATH to include current directory and src
export PYTHONPATH="$(pwd):$(pwd)/src:$PYTHONPATH"

# Set environment variables for refactored version
export PIPELINE_TARGET_YYYYMM="$TARGET_YYYYMM"
export PIPELINE_TARGET_PERIOD="$TARGET_PERIOD"
export PIPELINE_MATRIX_TYPE="subcategory"

# Run refactored Step 7
echo "📋 Executing refactored Step 7..."
echo "----------------------------------------"
cd src && python step7_missing_category_rule_refactored.py \
    --target-yyyymm "$TARGET_YYYYMM" \
    --target-period "$TARGET_PERIOD" \
    --verbose

EXIT_CODE=$?

cd ..

echo ""
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Refactored Step 7 completed successfully!"
    echo ""
    echo "📁 Check outputs in: output/"
else
    echo "❌ Refactored Step 7 failed with exit code: $EXIT_CODE"
fi
echo "============================================================"

exit $EXIT_CODE
