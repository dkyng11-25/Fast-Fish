#!/bin/bash
# Simple Dual Output Test - Run Steps That Work
# Tests the dual output pattern on steps that have minimal dependencies

set -e

echo "🧪 Simple Dual Output Pattern Test"
echo "==================================="
echo ""

cd /Users/borislavdzodzo/Desktop/Dev/ais-129-issues-found-when-running-main

export PYTHONPATH=.
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A

echo "✅ Environment set:"
echo "   PYTHONPATH=$PYTHONPATH"
echo "   PIPELINE_TARGET_YYYYMM=$PIPELINE_TARGET_YYYYMM"
echo "   PIPELINE_TARGET_PERIOD=$PIPELINE_TARGET_PERIOD"
echo ""

# Step 6: Clustering (has dependencies but should work if data exists)
echo "▶️  Testing Step 6: Cluster Analysis"
echo "======================================"
python3 src/step6_cluster_analysis.py --target-yyyymm 202510 --target-period A
echo ""

# Check outputs
echo "📊 Checking Step 6 outputs..."
ls -lh output/clustering_*202510* 2>/dev/null || echo "⚠️  No Step 6 outputs found"
echo ""

# Verify dual output pattern
echo "🔍 Verifying dual output pattern for Step 6..."
TIMESTAMPED=$(find output/ -name "clustering_*_20*_*.csv" -type f 2>/dev/null | wc -l | tr -d ' ')
SYMLINKS=$(find output/ -name "clustering_*.csv" -type l 2>/dev/null | wc -l | tr -d ' ')

echo "  Timestamped files: $TIMESTAMPED"
echo "  Symlinks: $SYMLINKS"

if [ "$TIMESTAMPED" -gt 0 ] && [ "$SYMLINKS" -gt 0 ]; then
    echo "  ✅ Dual output pattern working!"
else
    echo "  ❌ Dual output pattern not working"
    exit 1
fi

echo ""
echo "✅ Test complete!"
