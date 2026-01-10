#!/usr/bin/env python3
"""
Generate all dual output pattern test files for Steps 13-36
"""

# Steps that have dual output pattern implementations
STEPS_WITH_DUAL_OUTPUT = [
    13, 14, 15, 16, 17, 18, 19, 20, 21, 22,  # Core steps
    25, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36  # Additional steps
]

# Step metadata
STEP_INFO = {
    13: {"name": "Consolidate SPU Rules", "output_file": "consolidated_spu_rule_results_detailed"},
    14: {"name": "Fast Fish Format", "output_file": "enhanced_fast_fish_format"},
    15: {"name": "Historical Baseline", "output_file": "historical_reference"},
    16: {"name": "Comparison Tables", "output_file": "spreadsheet_comparison_analysis"},
    17: {"name": "Augment Recommendations", "output_file": "fast_fish_with_historical_and_cluster_trending_analysis"},
    18: {"name": "Validate Results", "output_file": "fast_fish_with_sell_through_analysis"},
    19: {"name": "Detailed SPU Breakdown", "output_file": "detailed_spu_recommendations"},
    20: {"name": "Data Validation", "output_file": "comprehensive_validation_report"},
    21: {"name": "Label Tag Recommendations", "output_file": "D_F_Label_Tag_Recommendation_Sheet"},
    22: {"name": "Store Attribute Enrichment", "output_file": "enriched_store_attributes"},
    25: {"name": "Product Role Classifier", "output_file": "product_role_classifications"},
    26: {"name": "Price Elasticity Analyzer", "output_file": "price_band_analysis"},
    27: {"name": "Gap Matrix Generator", "output_file": "gap_analysis_detailed"},
    28: {"name": "Scenario Analyzer", "output_file": "scenario_analysis_results"},
    29: {"name": "Supply-Demand Gap Analysis", "output_file": "supply_demand_gap_analysis"},
    30: {"name": "Sell-Through Optimization", "output_file": "sellthrough_optimization_results"},
    31: {"name": "Gap Analysis Workbook", "output_file": "gap_analysis_workbook"},
    32: {"name": "Store Allocation", "output_file": "store_level_allocations"},
    33: {"name": "Store-Level Merchandising", "output_file": "store_level_merchandising_rules"},
    35: {"name": "Merchandising Strategy", "output_file": "merchandising_strategy_deployment"},
    36: {"name": "Unified Delivery Builder", "output_file": "unified_delivery"},
}

print("="*80)
print("DUAL OUTPUT PATTERN TEST GENERATION PLAN")
print("="*80)
print()
print(f"Total steps to test: {len(STEPS_WITH_DUAL_OUTPUT)}")
print()
print("Steps with dual output pattern:")
for step in STEPS_WITH_DUAL_OUTPUT:
    info = STEP_INFO.get(step, {"name": "Unknown", "output_file": "unknown"})
    print(f"  Step {step:2d}: {info['name']}")
print()
print("="*80)
print()
print("✅ Test files to create:")
for step in STEPS_WITH_DUAL_OUTPUT:
    print(f"   - test_step{step}_dual_output.py")
print()
print("Note: Steps 1-12 do NOT have dual output patterns and don't need tests")
print("="*80)
