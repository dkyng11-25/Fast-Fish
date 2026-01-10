#!/bin/bash
# Complete test script for Step 7 refactoring
# Runs legacy Step 7, backs up results, runs refactored Step 7, compares

set -e

TARGET_YYYYMM="202510"
TARGET_PERIOD="A"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🧪 STEP 7 REFACTORING TEST"
echo "============================================================"
echo "Target: ${TARGET_YYYYMM}${TARGET_PERIOD}"
echo "Timestamp: $TIMESTAMP"
echo "============================================================"
echo ""

# Step 1: Run prerequisite steps (2, 3, 5, 6)
echo "📋 Phase 1: Running prerequisite steps..."
echo "----------------------------------------"
chmod +x run_legacy_steps_2_to_6.sh
./run_legacy_steps_2_to_6.sh
echo ""

# Step 2: Run legacy Step 7
echo "📋 Phase 2: Running LEGACY Step 7..."
echo "----------------------------------------"
python -m src.step7_missing_category_rule \
    --target-yyyymm "$TARGET_YYYYMM" \
    --target-period "$TARGET_PERIOD"
echo "✅ Legacy Step 7 complete"
echo ""

# Step 3: Backup legacy results
echo "📋 Phase 3: Backing up legacy results..."
echo "----------------------------------------"
BACKUP_DIR="output/step7_legacy_backup_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

# Find and copy legacy Step 7 outputs
find output/ -name "*rule7*" -o -name "*missing_category*" | while read file; do
    if [ -f "$file" ]; then
        cp -v "$file" "$BACKUP_DIR/"
    fi
done

echo "✅ Legacy results backed up to: $BACKUP_DIR"
echo ""

# Step 4: Run refactored Step 7
echo "📋 Phase 4: Running REFACTORED Step 7..."
echo "----------------------------------------"
python src/step7_missing_category_rule_refactored.py \
    --target-yyyymm "$TARGET_YYYYMM" \
    --target-period "$TARGET_PERIOD" \
    --verbose
echo "✅ Refactored Step 7 complete"
echo ""

# Step 5: Compare results
echo "📋 Phase 5: Comparing results..."
echo "----------------------------------------"

# Find the output files
LEGACY_FILE=$(find "$BACKUP_DIR" -name "*.csv" | head -1)
REFACTORED_FILE=$(find output/ -name "*rule7*${TARGET_YYYYMM}${TARGET_PERIOD}*.csv" -o -name "*missing_category*${TARGET_YYYYMM}${TARGET_PERIOD}*.csv" | grep -v backup | head -1)

if [ -f "$LEGACY_FILE" ] && [ -f "$REFACTORED_FILE" ]; then
    echo "Legacy file: $LEGACY_FILE"
    echo "Refactored file: $REFACTORED_FILE"
    echo ""
    
    # Compare file sizes
    LEGACY_SIZE=$(wc -l < "$LEGACY_FILE")
    REFACTORED_SIZE=$(wc -l < "$REFACTORED_FILE")
    
    echo "📊 Row counts:"
    echo "  Legacy:     $LEGACY_SIZE rows"
    echo "  Refactored: $REFACTORED_SIZE rows"
    echo ""
    
    # Compare column headers
    echo "📊 Column comparison:"
    echo "  Legacy columns:"
    head -1 "$LEGACY_FILE" | tr ',' '\n' | nl
    echo ""
    echo "  Refactored columns:"
    head -1 "$REFACTORED_FILE" | tr ',' '\n' | nl
    echo ""
    
    # Show first few rows
    echo "📊 First 3 data rows (legacy):"
    head -4 "$LEGACY_FILE" | tail -3
    echo ""
    echo "📊 First 3 data rows (refactored):"
    head -4 "$REFACTORED_FILE" | tail -3
    echo ""
else
    echo "⚠️  Could not find output files for comparison"
fi

echo "============================================================"
echo "✅ TEST COMPLETE!"
echo "============================================================"
echo ""
echo "📁 Results locations:"
echo "  Legacy backup:  $BACKUP_DIR"
echo "  Refactored:     output/"
echo ""
echo "🔍 Manual review recommended:"
echo "  1. Check row counts match"
echo "  2. Verify column names are consistent"
echo "  3. Compare business logic outputs"
echo "  4. Validate seasonal blending (if enabled)"
