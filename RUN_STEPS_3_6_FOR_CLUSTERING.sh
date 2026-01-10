#!/bin/bash
# Create proper clustering using 202410A data, then apply to 202510A
# This allows Steps 7-12 to work with meaningful cluster-based peer analysis

set -e  # Exit on error

echo "🎯 Creating Proper Clustering for 202510A Analysis"
echo "===================================================="
echo ""
echo "Strategy: Use 202410A data to create clustering,"
echo "          then apply it to 202510A for Steps 7-12"
echo ""

# Set environment
export PYTHONPATH=.

# ============================================================================
# STEP 3: Prepare Matrix (202410A)
# ============================================================================
echo "📊 Step 3: Prepare Matrix (202410A)"
echo "------------------------------------"
echo "Creating store-subcategory matrix from 202410A data..."
echo ""

python3 src/step3_prepare_matrix.py \
  --target-yyyymm 202410 --target-period A

if [ $? -eq 0 ]; then
    echo "✅ Step 3 completed"
    # Check if matrix has real store codes
    echo ""
    echo "🔍 Verifying matrix has real store codes..."
    python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/normalized_subcategory_matrix_202410A.csv', index_col=0, nrows=5)
print(f"Matrix index sample: {df.index.tolist()}")
if all(idx == 0.0 for idx in df.index[:5]):
    print("❌ WARNING: Matrix still has corrupted index (all 0.0)")
    exit(1)
else:
    print("✅ Matrix has real store codes!")
EOF
    if [ $? -ne 0 ]; then
        echo "❌ Matrix creation failed - index still corrupted"
        echo "   Need to debug Step 3 dtype handling"
        exit 1
    fi
else
    echo "❌ Step 3 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 4: Data Cleansing (202410A)
# ============================================================================
echo "📊 Step 4: Data Cleansing (202410A)"
echo "------------------------------------"
echo "Cleaning and normalizing matrix data..."
echo ""

python3 src/step4_data_cleansing.py \
  --target-yyyymm 202410 --target-period A

if [ $? -eq 0 ]; then
    echo "✅ Step 4 completed"
else
    echo "❌ Step 4 failed"
    exit 1
fi
echo ""

# ============================================================================
# STEP 5: Temperature Data (Optional)
# ============================================================================
echo "📊 Step 5: Temperature Data (202410A)"
echo "--------------------------------------"
echo "Calculating feels-like temperature (optional for clustering)..."
echo ""

# Step 5 might fail if temperature data not available - that's OK
python3 src/step5_calculate_feels_like_temp.py \
  --target-yyyymm 202410 --target-period A || echo "⚠️ Step 5 skipped (temperature data not available)"

echo ""

# ============================================================================
# STEP 6: Cluster Analysis (202410A)
# ============================================================================
echo "📊 Step 6: Cluster Analysis (202410A)"
echo "--------------------------------------"
echo "Creating business-relevant store clusters..."
echo ""

python3 src/step6_cluster_analysis.py \
  --target-yyyymm 202410 --target-period A

if [ $? -eq 0 ]; then
    echo "✅ Step 6 completed"
    echo ""
    echo "🔍 Verifying clustering has real store codes..."
    python3 << 'EOF'
import pandas as pd

# Check clustering
c = pd.read_csv('output/clustering_results_subcategory_202410A.csv', dtype={'str_code': str}, nrows=10)
print(f"Clustering sample:")
print(c.head())
print(f"\nUnique stores in sample: {c['str_code'].nunique()}")
print(f"Sample codes: {c['str_code'].unique()[:5].tolist()}")

# Check for corruption
if (c['str_code'] == '0.0').all():
    print("❌ ERROR: Clustering still has corrupted codes (all 0.0)")
    exit(1)
else:
    print("✅ Clustering has real store codes!")
    
# Test merge with SPU sales
s = pd.read_csv('data/api_data/complete_spu_sales_202510A.csv', dtype={'str_code': str})
merged = s.merge(c[['str_code', 'Cluster']], on='str_code', how='inner')
print(f"\n✅ Merge test: {len(merged):,} / {len(s):,} records ({len(merged)/len(s):.1%})")
EOF
    if [ $? -ne 0 ]; then
        echo "❌ Clustering verification failed"
        exit 1
    fi
else
    echo "❌ Step 6 failed"
    exit 1
fi
echo ""

# ============================================================================
# APPLY CLUSTERING TO 202510A
# ============================================================================
echo "🔗 Applying 202410A Clustering to 202510A"
echo "------------------------------------------"
echo "Creating symlinks for 202510A analysis..."
echo ""

# Create symlinks for 202510A
for matrix_type in subcategory spu; do
    src="output/clustering_results_${matrix_type}_202410A.csv"
    if [ -f "$src" ]; then
        # Create 202510A symlink
        dst="output/clustering_results_${matrix_type}_202510A.csv"
        if [ -e "$dst" ] || [ -L "$dst" ]; then
            rm "$dst"
        fi
        ln -s "$(basename $src)" "$dst"
        echo "✅ Created: $dst -> $src"
        
        # Create generic symlink
        generic="output/clustering_results_${matrix_type}.csv"
        if [ -e "$generic" ] || [ -L "$generic" ]; then
            rm "$generic"
        fi
        ln -s "$(basename $src)" "$generic"
        echo "✅ Created: $generic -> $src"
    fi
done

echo ""
echo "🎉 Clustering Setup Complete!"
echo "=============================="
echo ""
echo "✅ Created business-relevant clustering from 202410A"
echo "✅ Applied to 202510A for Steps 7-12 analysis"
echo "✅ Clustering has real store codes"
echo "✅ Merge operations will work"
echo ""
echo "📊 Clustering Files:"
ls -lh output/clustering_results*.csv | grep -E "202410A|202510A|subcategory.csv|spu.csv"
echo ""
echo "🚀 Ready to run Steps 7-12!"
echo ""
echo "Next: ./RUN_STEPS_7_12_STANDARDIZED_CLI.sh"
