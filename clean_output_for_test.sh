#!/bin/bash
# Clean Output Directory for Pipeline Test
# ==========================================
# Backs up existing outputs and cleans directory for fresh pipeline run

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="output"
BACKUP_DIR="output_backup_${TIMESTAMP}"

echo "🧹 Clean Output Directory for Pipeline Test"
echo "==========================================="
echo ""

# Check if output directory exists
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "❌ Output directory not found: $OUTPUT_DIR"
    exit 1
fi

# Count files
CSV_COUNT=$(find "$OUTPUT_DIR" -name "*.csv" -type f 2>/dev/null | wc -l | tr -d ' ')
SYMLINK_COUNT=$(find "$OUTPUT_DIR" -name "*.csv" -type l 2>/dev/null | wc -l | tr -d ' ')
TOTAL=$((CSV_COUNT + SYMLINK_COUNT))

echo "📊 Current output directory status:"
echo "  CSV files: $CSV_COUNT"
echo "  Symlinks: $SYMLINK_COUNT"
echo "  Total: $TOTAL"
echo ""

if [ "$TOTAL" -eq 0 ]; then
    echo "✅ Output directory is already clean!"
    exit 0
fi

# Ask for confirmation
read -p "⚠️  This will backup and remove all $TOTAL files. Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled by user"
    exit 1
fi

echo ""
echo "📦 Creating backup..."
mkdir -p "$BACKUP_DIR"

# Copy all CSV files and symlinks
echo "  Copying files to $BACKUP_DIR..."
find "$OUTPUT_DIR" -name "*.csv" -exec cp -P {} "$BACKUP_DIR/" \; 2>/dev/null || true

BACKUP_COUNT=$(find "$BACKUP_DIR" -name "*.csv" | wc -l | tr -d ' ')
echo "  ✅ Backed up $BACKUP_COUNT files to $BACKUP_DIR/"

echo ""
echo "🗑️  Removing files from output directory..."

# Remove all CSV files (real files)
find "$OUTPUT_DIR" -name "*.csv" -type f -delete 2>/dev/null || true

# Remove all CSV symlinks
find "$OUTPUT_DIR" -name "*.csv" -type l -delete 2>/dev/null || true

# Verify cleanup
REMAINING=$(find "$OUTPUT_DIR" -name "*.csv" | wc -l | tr -d ' ')

echo ""
if [ "$REMAINING" -eq 0 ]; then
    echo "✅ Output directory cleaned successfully!"
    echo ""
    echo "Summary:"
    echo "  - Backed up: $BACKUP_COUNT files → $BACKUP_DIR/"
    echo "  - Removed: $TOTAL files from $OUTPUT_DIR/"
    echo "  - Remaining: 0 files"
    echo ""
    echo "🚀 Ready to run pipeline with fresh outputs!"
    echo ""
    echo "To restore backup:"
    echo "  cp $BACKUP_DIR/*.csv $OUTPUT_DIR/"
else
    echo "⚠️  Warning: $REMAINING files still remain in output/"
    echo "  Manual cleanup may be needed"
fi
