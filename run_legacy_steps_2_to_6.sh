#!/bin/bash
# Run legacy steps 2, 3, 5, 6 to prepare for Step 7 testing

set -e

TARGET_YYYYMM="202510"
TARGET_PERIOD="A"

echo "🚀 Running legacy steps 2-6 for ${TARGET_YYYYMM}${TARGET_PERIOD}"
echo "============================================================"
echo ""

# Step 2: Extract Coordinates
echo "📍 Step 2: Extract Coordinates"
echo "----------------------------------------"
python src/step2_extract_coordinates.py \
    --target-yyyymm "$TARGET_YYYYMM" \
    --target-period "$TARGET_PERIOD"
echo "✅ Step 2 complete"
echo ""

# Step 3: Prepare Matrix
echo "📊 Step 3: Prepare Matrix"
echo "----------------------------------------"
python src/step3_prepare_matrix.py \
    --target-yyyymm "$TARGET_YYYYMM" \
    --target-period "$TARGET_PERIOD"
echo "✅ Step 3 complete"
echo ""

# Step 5: Calculate Feels Like Temperature
echo "🌡️  Step 5: Calculate Feels Like Temperature"
echo "----------------------------------------"
python src/step5_calculate_feels_like_temperature.py \
    --target-yyyymm "$TARGET_YYYYMM" \
    --target-period "$TARGET_PERIOD"
echo "✅ Step 5 complete"
echo ""

# Step 6: Cluster Analysis
echo "🔍 Step 6: Cluster Analysis"
echo "----------------------------------------"
python src/step6_cluster_analysis.py \
    --target-yyyymm "$TARGET_YYYYMM" \
    --target-period "$TARGET_PERIOD"
echo "✅ Step 6 complete"
echo ""

echo "============================================================"
echo "✅ All prerequisite steps (2, 3, 5, 6) completed successfully!"
echo ""
echo "🎯 Next: Run Step 7 (legacy and refactored)"
