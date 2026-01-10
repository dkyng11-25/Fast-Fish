#!/bin/bash
# Test Cleanup Script
# Removes superseded tests and organizes test directory

set -e

echo "🧹 Test Cleanup Script"
echo "====================="
echo ""

# Create archived directory
echo "📁 Creating archived directory..."
mkdir -p tests/archived

# Delete superseded dual output tests
echo "❌ Deleting superseded dual output tests..."
rm -f tests/step7_synthetic/test_step7_dual_output.py
rm -f tests/step8_synthetic/test_step8_dual_output.py
rm -f tests/step13_synthetic/test_step13_dual_output.py

# Rename integration test
echo "🔄 Renaming integration test..."
if [ -f tests/test_dual_output_validation.py ]; then
    mv tests/test_dual_output_validation.py tests/test_dual_output_integration.py
    echo "  ✅ Renamed: test_dual_output_validation.py → test_dual_output_integration.py"
fi

# Archive timestamp tests (optional - uncomment to archive)
# echo "📦 Archiving timestamp tests..."
# mv tests/test_timestamp_format.py tests/archived/
# mv tests/test_steps_10_to_15.py tests/archived/

# Archive subset tests (optional - uncomment to archive)
# echo "📦 Archiving subset tests..."
# mv tests/subset_tests tests/archived/

# Archive validation comprehensive (optional - uncomment to archive)
# echo "📦 Archiving validation comprehensive..."
# mv tests/validation_comprehensive tests/archived/

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Summary:"
echo "  ✅ Deleted 3 superseded dual output tests"
echo "  ✅ Renamed integration test"
echo "  ✅ Created archived directory"
echo ""
echo "Remaining tests:"
echo "  - 36 isolated dual output tests (test_step*_dual_output_isolated.py)"
echo "  - 1 integration test (test_dual_output_integration.py)"
echo "  - ~20 business logic tests (step*_synthetic/)"
echo "  - ~5 step-specific tests (step*/)"
echo ""
echo "To archive additional tests, uncomment lines in this script."
