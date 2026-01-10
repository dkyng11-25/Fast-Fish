#!/bin/bash
# Run legacy Step 7 in SUBCATEGORY mode (all 2,255 stores)

set -e

TARGET_YYYYMM="202510"
TARGET_PERIOD="A"

echo "🔧 Running LEGACY Step 7 - SUBCATEGORY MODE"
echo "============================================================"
echo "Target: ${TARGET_YYYYMM}${TARGET_PERIOD}"
echo "Analysis Level: SUBCATEGORY (all 2,255 stores)"
echo "============================================================"
echo ""

# Set PYTHONPATH to include current directory and src
export PYTHONPATH="$(pwd):$(pwd)/src:$PYTHONPATH"

# Set analysis level to subcategory
export ANALYSIS_LEVEL="subcategory"

# Run legacy Step 7 as a module
echo "📋 Executing legacy Step 7 in subcategory mode..."
echo "----------------------------------------"
python -m src.step7_missing_category_rule \
    --target-yyyymm "$TARGET_YYYYMM" \
    --target-period "$TARGET_PERIOD"

EXIT_CODE=$?

echo ""
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Legacy Step 7 (subcategory mode) completed successfully!"
    echo ""
    echo "📁 Check outputs in: output/"
    echo ""
    echo "🔍 Look for files:"
    find output/ -name "*rule7*${TARGET_YYYYMM}${TARGET_PERIOD}*" -o -name "*missing*${TARGET_YYYYMM}${TARGET_PERIOD}*" 2>/dev/null | grep -v spu | head -10
else
    echo "❌ Legacy Step 7 failed with exit code: $EXIT_CODE"
fi
echo "============================================================"

exit $EXIT_CODE
