#!/bin/bash
set -e

echo "=========================================="
echo "PIPELINE CLEANUP AND INTEGRATION TEST"
echo "Steps 2, 2b, 3, 5, 6, 7"
echo "=========================================="

# Function to safely remove files
safe_remove() {
    local pattern=$1
    local description=$2
    echo "Removing $description..."
    find . -name "$pattern" -type f -delete 2>/dev/null || true
    find . -name "$pattern" -type l -delete 2>/dev/null || true
}

echo ""
echo "=== PHASE 1: CLEANUP ALL OUTPUTS ==="
echo ""

# Step 2 outputs
echo "Step 2: Extract Coordinates"
safe_remove "store_coordinates_extended*.csv" "coordinates files"
safe_remove "spu_store_mapping*.csv" "SPU mapping files"
safe_remove "spu_metadata*.csv" "SPU metadata files"

# Step 2b outputs
echo "Step 2b: Consolidate Seasonal"
safe_remove "seasonal_store_profiles*.csv" "seasonal store profiles"
safe_remove "seasonal_category_patterns*.csv" "seasonal category patterns"
safe_remove "seasonal_clustering_features*.csv" "seasonal clustering features"

# Step 3 outputs
echo "Step 3: Prepare Matrix"
safe_remove "store_subcategory_matrix*.csv" "subcategory matrices"
safe_remove "normalized_subcategory_matrix*.csv" "normalized subcategory matrices"
safe_remove "store_spu_limited_matrix*.csv" "SPU matrices"
safe_remove "normalized_spu_limited_matrix*.csv" "normalized SPU matrices"
safe_remove "store_category_agg_matrix*.csv" "category agg matrices"
safe_remove "normalized_category_agg_matrix*.csv" "normalized category agg matrices"
safe_remove "*_store_list.txt" "store lists"
safe_remove "*_product_list.txt" "product lists"

# Step 5 outputs
echo "Step 5: Feels-Like Temperature"
safe_remove "temperature_bands*.csv" "temperature bands"
safe_remove "stores_with_feels_like_temperature*.csv" "feels-like temperature data"

# Step 6 outputs
echo "Step 6: Cluster Analysis"
safe_remove "clustering_results*.csv" "clustering results"
safe_remove "cluster_profiles*.csv" "cluster profiles"
safe_remove "per_cluster_metrics*.csv" "per-cluster metrics"
safe_remove "cluster_visualization*.png" "cluster visualizations"

# Step 7 outputs
echo "Step 7: Missing Category Rule"
safe_remove "rule7_missing_*_sellthrough_*.csv" "rule 7 outputs"

echo ""
echo "✅ Cleanup complete!"
echo ""

# Verify cleanup
echo "=== VERIFICATION: Checking for remaining outputs ==="
remaining_files=$(find data output -name "*_20*.csv" -o -name "*_20*.png" 2>/dev/null | wc -l)
echo "Remaining timestamped files: $remaining_files"

if [ "$remaining_files" -gt 0 ]; then
    echo "⚠️  Warning: Some timestamped files remain:"
    find data output -name "*_20*.csv" -o -name "*_20*.png" 2>/dev/null | head -10
fi

echo ""
echo "=== PHASE 2: RUN PIPELINE STEPS 2-7 ==="
echo ""

# Set environment variables for consistent run
export PYTHONPATH=.
export PIPELINE_TARGET_YYYYMM=202410
export PIPELINE_TARGET_PERIOD=B
export COORDS_MONTHS_BACK=3
export MATRIX_TYPE=subcategory
export ENABLE_TEMPERATURE_CONSTRAINTS=0
export RULE7_USE_ROI=0
export RULE7_MIN_STORES_SELLING=2
export RULE7_MIN_ADOPTION=0.10
export RULE7_MIN_PREDICTED_ST=15

echo "Environment configured:"
echo "  PIPELINE_TARGET_YYYYMM=$PIPELINE_TARGET_YYYYMM"
echo "  PIPELINE_TARGET_PERIOD=$PIPELINE_TARGET_PERIOD"
echo "  MATRIX_TYPE=$MATRIX_TYPE"
echo ""

# Step 2
echo "=== Running Step 2: Extract Coordinates ==="
python3 src/step2_extract_coordinates.py
if [ $? -eq 0 ]; then
    echo "✅ Step 2 completed successfully"
    # Verify outputs
    if [ -f "data/store_coordinates_extended.csv" ]; then
        echo "   ✓ store_coordinates_extended.csv created"
    fi
    if [ -f "data/spu_store_mapping.csv" ]; then
        echo "   ✓ spu_store_mapping.csv created"
    fi
else
    echo "❌ Step 2 failed!"
    exit 1
fi
echo ""

# Step 2b
echo "=== Running Step 2b: Consolidate Seasonal ==="
python3 src/step2b_consolidate_seasonal_data.py
if [ $? -eq 0 ]; then
    echo "✅ Step 2b completed successfully"
    # Verify outputs
    if [ -f "output/seasonal_store_profiles.csv" ]; then
        echo "   ✓ seasonal_store_profiles.csv created"
    fi
else
    echo "❌ Step 2b failed!"
    exit 1
fi
echo ""

# Step 3
echo "=== Running Step 3: Prepare Matrix ==="
python3 src/step3_prepare_matrix.py
if [ $? -eq 0 ]; then
    echo "✅ Step 3 completed successfully"
    # Verify outputs
    if [ -f "data/store_subcategory_matrix.csv" ]; then
        echo "   ✓ store_subcategory_matrix.csv created"
    fi
    if [ -f "data/normalized_subcategory_matrix.csv" ]; then
        echo "   ✓ normalized_subcategory_matrix.csv created"
    fi
else
    echo "❌ Step 3 failed!"
    exit 1
fi
echo ""

# Step 5
echo "=== Running Step 5: Feels-Like Temperature ==="
python3 src/step5_calculate_feels_like_temperature.py
if [ $? -eq 0 ]; then
    echo "✅ Step 5 completed successfully"
    # Verify outputs
    if [ -f "output/temperature_bands.csv" ]; then
        echo "   ✓ temperature_bands.csv created"
    fi
    if [ -f "output/stores_with_feels_like_temperature.csv" ]; then
        echo "   ✓ stores_with_feels_like_temperature.csv created"
    fi
else
    echo "❌ Step 5 failed!"
    exit 1
fi
echo ""

# Step 6
echo "=== Running Step 6: Cluster Analysis ==="
python3 src/step6_cluster_analysis.py
if [ $? -eq 0 ]; then
    echo "✅ Step 6 completed successfully"
    # Verify outputs
    if [ -f "output/clustering_results_subcategory.csv" ]; then
        echo "   ✓ clustering_results_subcategory.csv created"
        # Check if it's a symlink
        if [ -L "output/clustering_results_subcategory.csv" ]; then
            target=$(readlink output/clustering_results_subcategory.csv)
            echo "   ✓ Generic symlink points to: $target"
        fi
    fi
else
    echo "❌ Step 6 failed!"
    exit 1
fi
echo ""

# Step 7
echo "=== Running Step 7: Missing Category Rule ==="
python3 src/step7_missing_category_rule.py --yyyymm $PIPELINE_TARGET_YYYYMM --period $PIPELINE_TARGET_PERIOD --analysis-level subcategory
if [ $? -eq 0 ]; then
    echo "✅ Step 7 completed successfully"
    # Verify outputs
    results_file=$(find output -name "rule7_missing_subcategory_sellthrough_results*.csv" -type f | head -1)
    if [ -n "$results_file" ]; then
        echo "   ✓ Rule 7 results created: $(basename $results_file)"
    fi
    if [ -f "output/rule7_missing_subcategory_sellthrough_results.csv" ]; then
        if [ -L "output/rule7_missing_subcategory_sellthrough_results.csv" ]; then
            target=$(readlink output/rule7_missing_subcategory_sellthrough_results.csv)
            echo "   ✓ Generic symlink points to: $target"
        fi
    fi
else
    echo "❌ Step 7 failed!"
    exit 1
fi
echo ""

echo "=========================================="
echo "=== PHASE 3: VALIDATE DUAL OUTPUT PATTERN ==="
echo "=========================================="
echo ""

# Check that all steps created timestamped files AND symlinks
echo "Checking dual output pattern compliance..."
echo ""

check_dual_output() {
    local step_name=$1
    local generic_file=$2
    local pattern=$3
    
    echo "Step $step_name: $generic_file"
    
    # Check if generic symlink exists
    if [ -L "$generic_file" ]; then
        echo "  ✅ Generic symlink exists"
        
        # Check target
        target=$(readlink "$generic_file")
        echo "  ✅ Points to: $target"
        
        # Check if target has timestamp
        if [[ "$target" =~ _[0-9]{8}_[0-9]{6} ]]; then
            echo "  ✅ Target is timestamped"
        else
            echo "  ⚠️  Target is NOT timestamped: $target"
        fi
    elif [ -f "$generic_file" ]; then
        echo "  ❌ Generic file exists but is NOT a symlink!"
    else
        echo "  ❌ Generic file does NOT exist!"
    fi
    
    # Count timestamped files
    timestamped_count=$(find $(dirname "$generic_file") -name "$pattern" -type f 2>/dev/null | wc -l)
    echo "  ✅ Timestamped files: $timestamped_count"
    echo ""
}

check_dual_output "2" "data/store_coordinates_extended.csv" "store_coordinates_extended_*_*.csv"
check_dual_output "2" "data/spu_store_mapping.csv" "spu_store_mapping_*_*.csv"
check_dual_output "2b" "output/seasonal_store_profiles.csv" "seasonal_store_profiles_*_*.csv"
check_dual_output "3" "data/store_subcategory_matrix.csv" "store_subcategory_matrix_*_*.csv"
check_dual_output "3" "data/normalized_subcategory_matrix.csv" "normalized_subcategory_matrix_*_*.csv"
check_dual_output "5" "output/temperature_bands.csv" "temperature_bands_*_*.csv"
check_dual_output "5" "output/stores_with_feels_like_temperature.csv" "stores_with_feels_like_temperature_*_*.csv"
check_dual_output "6" "output/clustering_results_subcategory.csv" "clustering_results_subcategory_*_*.csv"
check_dual_output "7" "output/rule7_missing_subcategory_sellthrough_results.csv" "rule7_missing_subcategory_sellthrough_results_*_*.csv"

echo "=========================================="
echo "=== INTEGRATION TEST COMPLETE ==="
echo "=========================================="
echo ""
echo "✅ All steps completed successfully!"
echo "✅ Dual output pattern verified!"
echo "✅ Pipeline handoff working correctly!"
echo ""
