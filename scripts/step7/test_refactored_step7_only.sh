#!/bin/bash
# Quick test of refactored Step 7 only (assumes prerequisites already run)

set -e

TARGET_YYYYMM="202510"
TARGET_PERIOD="A"

echo "🧪 Testing REFACTORED Step 7"
echo "============================================================"
echo "Target: ${TARGET_YYYYMM}${TARGET_PERIOD}"
echo "============================================================"
echo ""

# Set PYTHONPATH to include current directory and src
export PYTHONPATH="$(pwd):$(pwd)/src:$PYTHONPATH"

# Run refactored Step 7
echo "📋 Running REFACTORED Step 7..."
echo "----------------------------------------"
cd src && python step7_missing_category_rule_refactored.py \
    --target-yyyymm "$TARGET_YYYYMM" \
    --target-period "$TARGET_PERIOD" \
    --verbose

echo ""
echo "============================================================"
echo "✅ TEST COMPLETE!"
echo "============================================================"
echo ""
echo "📁 Check outputs in: output/"
echo ""
echo "🔍 Look for files matching:"
echo "  - rule7_missing_category_${TARGET_YYYYMM}${TARGET_PERIOD}*.csv"
echo "  - *missing_category*${TARGET_YYYYMM}${TARGET_PERIOD}*.csv"
