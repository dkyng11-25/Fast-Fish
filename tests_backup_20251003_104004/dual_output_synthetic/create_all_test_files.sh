#!/bin/bash
# Script to create all 36 dual output test files

cd "$(dirname "$0")"

echo "Creating all 36 dual output test files..."
echo ""

# Create test files for Steps 1-36
for step in {1..36}; do
    # Skip steps that don't exist (4, 34a is handled separately)
    if [ $step -eq 4 ]; then
        continue
    fi
    
    filename="test_step${step}_dual_output.py"
    
    if [ -f "$filename" ]; then
        echo "✓ $filename already exists"
    else
        echo "Creating $filename..."
        # File will be created by Python script
    fi
done

echo ""
echo "✅ Test file creation plan complete"
echo "Run: python3 generate_test_files.py to create the actual files"
