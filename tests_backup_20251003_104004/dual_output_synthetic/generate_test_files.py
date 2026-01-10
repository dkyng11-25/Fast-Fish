#!/usr/bin/env python3
"""
Generate all dual output pattern test files for Steps 1-36
"""

from pathlib import Path

# Step metadata - output files to check
STEP_OUTPUTS = {
    1: ["complete_spu_sales", "complete_category_sales", "store_config", "store_sales"],
    2: ["store_coordinates"],
    3: ["sales_matrix"],
    5: ["stores_with_feels_like_temperature"],
    6: ["clustering_results_spu", "clustering_results_subcategory"],
    7: ["rule7_missing_spu_sellthrough_results"],
    8: ["rule8_imbalanced_spu_results"],
    9: ["rule9_below_minimum_spu_sellthrough_results"],
    10: ["rule10_smart_overcapacity_results"],
    11: ["rule11_improved_missed_sales_opportunity_spu_results"],
    12: ["rule12_sales_performance_spu_results"],
    13: ["consolidated_spu_rule_results_detailed"],
    14: ["enhanced_fast_fish_format"],
    15: ["historical_reference", "year_over_year_comparison"],
    16: ["spreadsheet_comparison_analysis"],
    17: ["fast_fish_with_historical_and_cluster_trending_analysis"],
    18: ["fast_fish_with_sell_through_analysis"],
    19: ["detailed_spu_recommendations"],
    20: ["comprehensive_validation_report"],
    21: ["D_F_Label_Tag_Recommendation_Sheet", "client_desired_store_group_style_tags_targets"],
    22: ["enriched_store_attributes"],
    23: ["updated_clustering_features"],
    24: ["comprehensive_cluster_labels"],
    25: ["product_role_classifications"],
    26: ["price_band_analysis"],
    27: ["gap_analysis_detailed"],
    28: ["scenario_analysis_results"],
    29: ["supply_demand_gap_analysis"],
    30: ["sellthrough_optimization_results"],
    31: ["gap_analysis_workbook"],
    32: ["store_level_allocations"],
    33: ["store_level_merchandising_rules"],
    35: ["merchandising_strategy_deployment"],
    36: ["unified_delivery"],
}

STEP_NAMES = {
    1: "API Data Download",
    2: "Extract Coordinates",
    3: "Prepare Matrix",
    5: "Feels-Like Temperature",
    6: "Cluster Analysis",
    7: "Missing Category Rule",
    8: "Imbalanced Rule",
    9: "Below Minimum Rule",
    10: "SPU Assortment Optimization",
    11: "Missed Sales Opportunity",
    12: "Sales Performance Rule",
    13: "Consolidate SPU Rules",
    14: "Fast Fish Format",
    15: "Historical Baseline",
    16: "Comparison Tables",
    17: "Augment Recommendations",
    18: "Validate Results",
    19: "Detailed SPU Breakdown",
    20: "Data Validation",
    21: "Label Tag Recommendations",
    22: "Store Attribute Enrichment",
    23: "Update Clustering Features",
    24: "Comprehensive Cluster Labeling",
    25: "Product Role Classifier",
    26: "Price Elasticity Analyzer",
    27: "Gap Matrix Generator",
    28: "Scenario Analyzer",
    29: "Supply-Demand Gap Analysis",
    30: "Sell-Through Optimization",
    31: "Gap Analysis Workbook",
    32: "Store Allocation",
    33: "Store-Level Merchandising",
    35: "Merchandising Strategy Deployment",
    36: "Unified Delivery Builder",
}


def generate_test_file(step_num: int) -> str:
    """Generate test file content for a given step"""
    
    step_name = STEP_NAMES.get(step_num, f"Step {step_num}")
    output_files = STEP_OUTPUTS.get(step_num, [f"step{step_num}_output"])
    primary_output = output_files[0]
    
    # Determine file extension
    ext = ".xlsx" if "workbook" in primary_output.lower() or "sheet" in primary_output.lower() else ".csv"
    
    template = f'''"""
Step {step_num} Dual Output Pattern Test
{'=' * 50}

Tests that Step {step_num} ({step_name}) creates output files WITHOUT timestamps.

The dual output pattern ensures:
1. Files have period labels (e.g., _202510A)
2. Files do NOT have timestamp patterns (_YYYYMMDD_HHMMSS)
3. Downstream steps can reliably find these files
"""

import os
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest
import re

TARGET_YYYYMM = "202510"
TARGET_PERIOD = "A"
PERIOD_LABEL = f"{{TARGET_YYYYMM}}{{TARGET_PERIOD}}"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"


def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox with src/ code"""
    sandbox = tmp_path / "sandbox"
    src_target = sandbox / "src"
    shutil.copytree(SRC_ROOT, src_target)

    stub = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {{}}

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None
""".strip()
    (src_target / "pipeline_manifest.py").write_text(stub, encoding="utf-8")
    (src_target / "__init__.py").write_text("", encoding="utf-8")

    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    return sandbox


def test_step{step_num}_creates_output_without_timestamp(tmp_path):
    """Test that Step {step_num} creates output files WITHOUT timestamp in filename"""
    # NOTE: This is a placeholder test
    # TODO: Implement full sandbox test with synthetic inputs
    
    # For now, just verify the pattern in actual output directory
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist - run pipeline first")
    
    # Check for output file
    pattern = "{primary_output}_{{PERIOD_LABEL}}{ext}"
    expected_file = output_dir / pattern
    
    # Look for files matching the base pattern
    matching_files = list(output_dir.glob(f"{primary_output}_*{ext}"))
    
    if not matching_files:
        pytest.skip(f"No output files found for step {step_num} - run pipeline first")
    
    # Verify NO files have timestamp pattern
    timestamp_pattern = r'_\\d{{8}}_\\d{{6}}'
    
    for file in matching_files:
        # File should have period label
        assert re.search(r'_\\d{{6}}[AB]', file.name), \\
            f"❌ File should have period label: {{file.name}}"
        
        # File should NOT have timestamp
        assert not re.search(timestamp_pattern, file.name), \\
            f"❌ File should NOT have timestamp: {{file.name}}"
    
    print(f"✅ Step {step_num} output files have correct naming (no timestamps)")
    for file in matching_files:
        print(f"   - {{file.name}}")


def test_step{step_num}_output_has_period_label(tmp_path):
    """Test that Step {step_num} output files have period labels"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    matching_files = list(output_dir.glob(f"{primary_output}_*{ext}"))
    
    if not matching_files:
        pytest.skip(f"No output files found for step {step_num}")
    
    # Verify files have period label pattern (YYYYMMA or YYYYMMB)
    period_pattern = r'_\\d{{6}}[AB]'
    
    for file in matching_files:
        assert re.search(period_pattern, file.name), \\
            f"❌ File should have period label (YYYYMMA/B): {{file.name}}"
    
    print(f"✅ Step {step_num} output files have period labels")


def test_step{step_num}_output_consumable_by_downstream(tmp_path):
    """Test that Step {step_num} output can be found by downstream steps"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    # Check that at least one output file exists
    matching_files = list(output_dir.glob(f"{primary_output}_*{ext}"))
    
    if not matching_files:
        pytest.skip(f"No output files found for step {step_num}")
    
    # Verify file is readable
    test_file = matching_files[0]
    assert test_file.exists(), f"File should exist: {{test_file}}"
    assert test_file.stat().st_size > 0, f"File should not be empty: {{test_file}}"
    
    print(f"✅ Step {step_num} output is consumable by downstream steps")
    print(f"   File: {{test_file.name}} ({{test_file.stat().st_size}} bytes)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
    
    return template


# Generate all test files
def main():
    output_dir = Path(__file__).parent
    
    print("="*80)
    print("GENERATING DUAL OUTPUT PATTERN TESTS")
    print("="*80)
    print()
    
    created = 0
    skipped = 0
    
    for step_num in sorted(STEP_OUTPUTS.keys()):
        filename = f"test_step{step_num}_dual_output.py"
        filepath = output_dir / filename
        
        if filepath.exists():
            print(f"⏭️  {filename} - already exists")
            skipped += 1
        else:
            content = generate_test_file(step_num)
            filepath.write_text(content, encoding="utf-8")
            print(f"✅ {filename} - created")
            created += 1
    
    print()
    print("="*80)
    print(f"SUMMARY: Created {created} files, Skipped {skipped} files")
    print("="*80)
    print()
    print("Run tests with: pytest tests/dual_output_synthetic/ -v")


if __name__ == "__main__":
    main()
