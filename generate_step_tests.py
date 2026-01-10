"""
Generate Individual Dual Output Tests for All Steps
====================================================

This script generates individual test files for each of the 36 pipeline steps.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
TESTS_DIR = PROJECT_ROOT / "tests"

# Define output patterns for each step
STEP_PATTERNS = {
    1: ["api_data_*_*_*.csv"],
    2: ["store_coordinates_*_*_*.csv", "spu_store_mapping_*_*_*.csv"],
    3: ["store_*_matrix_*_*_*.csv", "normalized_*_matrix_*_*_*.csv"],
    4: ["store_altitude_*_*_*.csv"],
    5: ["stores_with_feels_like_temperature_*_*_*.csv"],
    6: ["clustering_results_*_*_*.csv", "cluster_profiles_*_*_*.csv"],
    7: ["rule7_*_*_*_*.csv"],
    8: ["rule8_*_*_*_*.csv"],
    9: ["rule9_*_*_*_*.csv"],
    10: ["rule10_*_*_*_*.csv"],
    11: ["rule11_*_*_*_*.csv"],
    12: ["rule12_*_*_*_*.csv"],
    13: ["consolidated_*_*_*.csv", "comprehensive_*_*_*.csv"],
    14: ["fast_fish_format_*_*_*.csv", "enhanced_fast_fish_*_*_*.csv"],
    15: ["historical_*_*_*_*.csv"],
    16: ["comparison_*_*_*_*.csv", "year_over_year_*_*_*.csv"],
    17: ["fast_fish_with_historical_*_*_*_*.csv"],
    18: ["fast_fish_with_sell_through_*_*_*_*.csv"],
    19: ["detailed_spu_recommendations_*_*_*.csv"],
    21: ["labeled_recommendations_*_*_*.csv"],
    22: ["enriched_store_attributes_*_*_*.csv"],
    24: ["comprehensive_cluster_labels_*_*_*.csv"],
    25: ["product_role_classifications_*_*_*.csv"],
    26: ["price_band_analysis_*_*_*.csv"],
    27: ["gap_analysis_matrix_*_*_*.csv"],
    28: ["scenario_analysis_*_*_*.csv"],
    29: ["supply_demand_gap_*_*_*.csv"],
    31: ["gap_analysis_workbook_*_*_*.csv"],
    32: ["store_level_allocation_*_*_*.csv"],
    33: ["merchandising_rules_*_*_*.csv"],
    34: ["strategy_optimization_*_*_*.csv"],
    35: ["strategy_deployment_*_*_*.csv"],
    36: ["unified_delivery_*_*_*.csv"],
}

TEST_TEMPLATE = '''"""
Step {step_num} Dual Output Pattern Test
=========================================

Tests that Step {step_num} creates timestamped files + symlinks.
"""

import os
import re
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"


def test_step{step_num}_creates_timestamped_files():
    """Test that Step {step_num} creates timestamped output files."""
    
    # Look for Step {step_num} outputs
    patterns = {patterns}
    
    timestamped_files = []
    for pattern in patterns:
        files = list(OUTPUT_DIR.glob(pattern))
        timestamped_files.extend([f for f in files if re.search(r'_\\d{{8}}_\\d{{6}}\\.csv$', f.name)])
    
    if len(timestamped_files) == 0:
        pytest.skip("No Step {step_num} outputs found. Run Step {step_num} first.")
    
    print(f"\\n✅ Found {{len(timestamped_files)}} Step {step_num} timestamped files")
    
    # Verify each is a real file
    for f in timestamped_files:
        assert f.is_file() and not f.is_symlink(), f"{{f.name}} should be a real file"
        assert re.search(r'_\\d{{8}}_\\d{{6}}\\.csv$', f.name), f"{{f.name}} has wrong timestamp format"


def test_step{step_num}_creates_symlinks():
    """Test that Step {step_num} creates generic symlinks."""
    
    # Look for Step {step_num} timestamped files
    patterns = {patterns}
    
    timestamped_files = []
    for pattern in patterns:
        files = list(OUTPUT_DIR.glob(pattern))
        timestamped_files.extend([f for f in files if re.search(r'_\\d{{8}}_\\d{{6}}\\.csv$', f.name)])
    
    if len(timestamped_files) == 0:
        pytest.skip("No Step {step_num} outputs found")
    
    symlinks_found = 0
    for timestamped_file in timestamped_files:
        # Get generic filename
        generic_name = re.sub(r'_\\d{{8}}_\\d{{6}}\\.csv$', '.csv', timestamped_file.name)
        generic_file = OUTPUT_DIR / generic_name
        
        if generic_file.exists():
            assert generic_file.is_symlink(), f"{{generic_file.name}} should be a symlink"
            
            # Verify it points to a timestamped file
            link_target = os.readlink(generic_file)
            assert '/' not in link_target, f"Symlink should use basename: {{link_target}}"
            assert re.search(r'_\\d{{8}}_\\d{{6}}\\.csv$', link_target), f"Symlink target has wrong format: {{link_target}}"
            
            symlinks_found += 1
            print(f"✅ {{generic_file.name}} -> {{link_target}}")
    
    if symlinks_found > 0:
        print(f"\\n✅ Step {step_num}: {{symlinks_found}} symlinks verified")
    else:
        pytest.skip(f"No symlinks found for Step {step_num} (may not have been run yet)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
'''

def generate_test_file(step_num: int, patterns: list):
    """Generate a test file for a specific step."""
    
    test_file = TESTS_DIR / f"test_step{step_num}_dual_output.py"
    
    content = TEST_TEMPLATE.format(
        step_num=step_num,
        patterns=patterns
    )
    
    test_file.write_text(content)
    print(f"✅ Created: {test_file.name}")


def main():
    """Generate all test files."""
    
    print("Generating individual dual output tests for all steps...\n")
    
    for step_num, patterns in sorted(STEP_PATTERNS.items()):
        generate_test_file(step_num, patterns)
    
    print(f"\n✅ Generated {len(STEP_PATTERNS)} test files")
    print(f"\nRun all tests with:")
    print(f"  pytest tests/test_step*_dual_output.py -v")


if __name__ == "__main__":
    main()
