#!/usr/bin/env python3
"""
Pipeline Data Flow Analysis

This script analyzes the data flow between all pipeline steps to ensure proper file handoffs.
It identifies inputs, outputs, and potential missing dependencies.

Author: Data Pipeline Analysis
Date: 2025-01-02
"""

import os
import pandas as pd
from typing import Dict, List, Tuple, Set
from datetime import datetime
import glob

def log_progress(message: str) -> None:
    """Log progress with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

class PipelineStep:
    """Represents a single pipeline step with its inputs and outputs."""
    
    def __init__(self, name: str, script_path: str):
        self.name = name
        self.script_path = script_path
        self.inputs = []  # Files this step reads
        self.outputs = []  # Files this step creates
        self.optional_inputs = []  # Files this step can optionally read
        self.dependencies = []  # Other steps this depends on

def analyze_pipeline_data_flow() -> Dict[str, PipelineStep]:
    """
    Analyze the data flow for all pipeline steps.
    
    Returns:
        Dict mapping step names to PipelineStep objects
    """
    log_progress("Analyzing pipeline data flow...")
    
    steps = {}
    
    # Step 1: Download API Data
    step1 = PipelineStep("Step 1: Download API Data", "src/step1_download_api_data.py")
    step1.inputs = [
        "data/store_codes.csv"
    ]
    step1.outputs = [
        "data/api_data/store_config_202506A.csv",
        "data/api_data/store_sales_202506A.csv", 
        "data/api_data/complete_category_sales_202506A.csv",
        "data/api_data/complete_spu_sales_202506A.csv"
    ]
    steps["step1"] = step1
    
    # Step 2: Extract Coordinates
    step2 = PipelineStep("Step 2: Extract Coordinates", "src/step2_extract_coordinates.py")
    step2.inputs = [
        "data/api_data/complete_category_sales_202506A.csv",
        "data/api_data/complete_spu_sales_202506A.csv",
        "data/api_data/store_sales_202506A.csv"
    ]
    step2.outputs = [
        "data/store_coordinates_extended.csv",
        "data/spu_store_mapping.csv",
        "data/spu_metadata.csv"
    ]
    step2.dependencies = ["step1"]
    steps["step2"] = step2
    
    # Step 3: Prepare Matrix
    step3 = PipelineStep("Step 3: Prepare Matrix", "src/step3_prepare_matrix.py")
    step3.inputs = [
        "data/api_data/complete_category_sales_202506A.csv",
        "data/api_data/complete_spu_sales_202506A.csv",
        "data/store_coordinates_extended.csv"
    ]
    step3.outputs = [
        "data/store_subcategory_matrix.csv",
        "data/normalized_subcategory_matrix.csv",
        "data/store_spu_limited_matrix.csv",
        "data/normalized_spu_limited_matrix.csv",
        "data/store_category_agg_matrix.csv",
        "data/normalized_category_agg_matrix.csv",
        "data/subcategory_store_list.txt",
        "data/spu_limited_store_list.txt",
        "data/category_agg_store_list.txt",
        "data/store_list.txt",
        "data/subcategory_list.txt",
        "data/category_list.txt"
    ]
    step3.dependencies = ["step1", "step2"]
    steps["step3"] = step3
    
    # Step 4: Download Weather Data
    step4 = PipelineStep("Step 4: Download Weather Data", "src/step4_download_weather_data.py")
    step4.inputs = [
        "data/store_coordinates_extended.csv"
    ]
    step4.outputs = [
        "output/weather_data/weather_data_*.csv",  # Multiple files
        "output/store_altitudes.csv"
    ]
    step4.dependencies = ["step2"]
    steps["step4"] = step4
    
    # Step 5: Calculate Feels Like Temperature
    step5 = PipelineStep("Step 5: Calculate Feels Like Temperature", "src/step5_calculate_feels_like_temperature.py")
    step5.inputs = [
        "output/weather_data/weather_data_*.csv",
        "output/store_altitudes.csv"
    ]
    step5.outputs = [
        "output/stores_with_feels_like_temperature.csv",
        "output/temperature_bands.csv"
    ]
    step5.dependencies = ["step4"]
    steps["step5"] = step5
    
    # Step 6: Cluster Analysis
    step6 = PipelineStep("Step 6: Cluster Analysis", "src/step6_cluster_analysis.py")
    step6.inputs = [
        "data/normalized_subcategory_matrix.csv",
        "data/store_subcategory_matrix.csv"
    ]
    step6.optional_inputs = [
        "data/normalized_spu_limited_matrix.csv",
        "data/store_spu_limited_matrix.csv",
        "data/normalized_category_agg_matrix.csv", 
        "data/store_category_agg_matrix.csv",
        "output/stores_with_feels_like_temperature.csv"
    ]
    step6.outputs = [
        "output/clustering_results.csv",
        "output/clustering_results_subcategory.csv",
        "output/clustering_results_spu.csv",
        "output/clustering_results_category_agg.csv",
        "output/cluster_profiles_*.csv",
        "output/per_cluster_metrics_*.csv",
        "output/cluster_visualization_*.png"
    ]
    step6.dependencies = ["step3"]
    steps["step6"] = step6
    
    # Step 7: Missing Category Rule
    step7 = PipelineStep("Step 7: Missing Category Rule", "src/step7_missing_category_rule.py")
    step7.inputs = [
        "output/clustering_results_spu.csv",
        "data/api_data/complete_spu_sales_202506A.csv"
    ]
    step7.outputs = [
        "output/rule7_missing_spu_results.csv",
        "output/rule7_missing_spu_opportunities.csv",
        "output/rule7_missing_spu_summary.md"
    ]
    step7.dependencies = ["step6", "step1"]
    steps["step7"] = step7
    
    # Step 8: Imbalanced Rule
    step8 = PipelineStep("Step 8: Imbalanced Rule", "src/step8_imbalanced_rule.py")
    step8.inputs = [
        "output/clustering_results_spu.csv",
        "data/api_data/store_config_202506A.csv"
    ]
    step8.outputs = [
        "output/rule8_imbalanced_spu_results.csv",
        "output/rule8_imbalanced_spu_cases.csv",
        "output/rule8_imbalanced_spu_summary.md"
    ]
    step8.dependencies = ["step6", "step1"]
    steps["step8"] = step8
    
    # Step 9: Below Minimum Rule
    step9 = PipelineStep("Step 9: Below Minimum Rule", "src/step9_below_minimum_rule.py")
    step9.inputs = [
        "output/clustering_results_spu.csv",
        "data/api_data/store_config_202506A.csv"
    ]
    step9.outputs = [
        "output/rule9_below_minimum_spu_results.csv",
        "output/rule9_below_minimum_spu_cases.csv",
        "output/rule9_below_minimum_spu_summary.md"
    ]
    step9.dependencies = ["step6", "step1"]
    steps["step9"] = step9
    
    # Step 10: SPU Assortment Optimization
    step10 = PipelineStep("Step 10: SPU Assortment Optimization", "src/step10_spu_assortment_optimization.py")
    step10.inputs = [
        "output/clustering_results.csv",
        "data/api_data/store_config_202506A.csv"
    ]
    step10.outputs = [
        "output/rule10_spu_overcapacity_results.csv",
        "output/rule10_spu_overcapacity_opportunities.csv"
    ]
    step10.dependencies = ["step6", "step1"]
    steps["step10"] = step10
    
    # Step 11: Improved Category Logic
    step11 = PipelineStep("Step 11: Improved Category Logic", "src/step11_improved_category_logic.py")
    step11.inputs = [
        "output/clustering_results_spu.csv",
        "data/api_data/complete_spu_sales_202506A.csv",
        "data/api_data/store_sales_data.csv"
    ]
    step11.outputs = [
        "output/rule11_improved_missed_sales_opportunity_spu_results.csv",
        "output/rule11_improved_missed_sales_opportunity_spu_details.csv",
        "output/rule11_improved_top_performers_by_cluster_category.csv",
        "output/rule11_improved_missed_sales_opportunity_spu_summary.md"
    ]
    step11.dependencies = ["step6", "step1"]
    steps["step11"] = step11
    
    # Step 12: Sales Performance Rule
    step12 = PipelineStep("Step 12: Sales Performance Rule", "src/step12_sales_performance_rule.py")
    step12.inputs = [
        "output/clustering_results.csv",
        "data/api_data/complete_category_sales_202506A.csv"
    ]
    step12.outputs = [
        "output/rule12_sales_performance_results.csv",
        "output/rule12_sales_performance_details.csv",
        "output/rule12_sales_performance_summary.md"
    ]
    step12.dependencies = ["step6", "step1"]
    steps["step12"] = step12
    
    # Step 13: Consolidate SPU Rules
    step13 = PipelineStep("Step 13: Consolidate SPU Rules", "src/step13_consolidate_spu_rules.py")
    step13.inputs = [
        "output/clustering_results.csv",
        "output/rule7_missing_spu_results.csv",
        "output/rule8_imbalanced_spu_results.csv", 
        "output/rule9_below_minimum_spu_results.csv",
        "output/rule10_spu_overcapacity_results.csv",
        "output/rule11_improved_missed_sales_opportunity_spu_results.csv",
        "output/rule12_sales_performance_spu_results.csv"
    ]
    step13.outputs = [
        "output/consolidated_spu_rule_results.csv",
        "output/consolidated_spu_rule_summary.md"
    ]
    step13.dependencies = ["step6", "step7", "step8", "step9", "step10", "step11", "step12"]
    steps["step13"] = step13
    
    # Step 14: Global Overview Dashboard
    step14 = PipelineStep("Step 14: Global Overview Dashboard", "src/step14_global_overview_dashboard.py")
    step14.inputs = [
        "output/consolidated_spu_rule_results.csv"
    ]
    step14.outputs = [
        "output/global_overview_spu_dashboard.html"
    ]
    step14.dependencies = ["step13"]
    steps["step14"] = step14
    
    # Step 15: Interactive Map Dashboard
    step15 = PipelineStep("Step 15: Interactive Map Dashboard", "src/step15_interactive_map_dashboard.py")
    step15.inputs = [
        "output/consolidated_spu_rule_results.csv",
        "data/store_coordinates_extended.csv",
        "output/rule7_missing_spu_opportunities.csv",
        "output/rule9_below_minimum_spu_cases.csv",
        "output/rule11_improved_missed_sales_opportunity_spu_results.csv",
        "output/rule12_sales_performance_results.csv"
    ]
    step15.outputs = [
        "output/interactive_map_spu_dashboard.html"
    ]
    step15.dependencies = ["step13", "step2", "step7", "step9", "step11", "step12"]
    steps["step15"] = step15
    
    return steps

def check_file_existence(file_path: str) -> Tuple[bool, str]:
    """
    Check if a file exists, handling wildcards.
    
    Args:
        file_path: Path to check (may contain wildcards)
        
    Returns:
        Tuple of (exists, status_message)
    """
    if '*' in file_path:
        # Handle wildcard patterns
        matching_files = glob.glob(file_path)
        if matching_files:
            return True, f"Found {len(matching_files)} files matching pattern"
        else:
            return False, "No files match pattern"
    else:
        # Handle exact file paths
        if os.path.exists(file_path):
            try:
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                return True, f"Exists ({size_mb:.1f} MB)"
            except:
                return True, "Exists"
        else:
            return False, "Missing"

def validate_data_flow(steps: Dict[str, PipelineStep]) -> Dict[str, List[str]]:
    """
    Validate the data flow between pipeline steps.
    
    Args:
        steps: Dictionary of pipeline steps
        
    Returns:
        Dictionary of validation issues by step
    """
    log_progress("Validating data flow between pipeline steps...")
    
    issues = {}
    
    for step_name, step in steps.items():
        step_issues = []
        
        # Check required inputs
        for input_file in step.inputs:
            exists, status = check_file_existence(input_file)
            if not exists:
                step_issues.append(f"MISSING REQUIRED INPUT: {input_file} - {status}")
        
        # Check optional inputs (warnings only)
        for input_file in step.optional_inputs:
            exists, status = check_file_existence(input_file)
            if not exists:
                step_issues.append(f"MISSING OPTIONAL INPUT: {input_file} - {status}")
        
        # Check if outputs are being created
        for output_file in step.outputs:
            exists, status = check_file_existence(output_file)
            if not exists:
                step_issues.append(f"OUTPUT NOT FOUND: {output_file} - {status}")
        
        if step_issues:
            issues[step_name] = step_issues
    
    return issues

def generate_data_flow_report(steps: Dict[str, PipelineStep], issues: Dict[str, List[str]]) -> None:
    """
    Generate a comprehensive data flow report.
    
    Args:
        steps: Dictionary of pipeline steps
        issues: Dictionary of validation issues
    """
    log_progress("Generating data flow report...")
    
    report_content = f"""# Pipeline Data Flow Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This report analyzes the data flow between all {len(steps)} pipeline steps to ensure proper file handoffs.

### Issues Summary
- **Steps with issues:** {len(issues)}
- **Total issues:** {sum(len(issue_list) for issue_list in issues.values())}

## Detailed Analysis

"""
    
    for step_name, step in steps.items():
        report_content += f"\n### {step.name}\n"
        report_content += f"**Script:** `{step.script_path}`\n\n"
        
        if step.dependencies:
            report_content += f"**Dependencies:** {', '.join(step.dependencies)}\n\n"
        
        # Required inputs
        if step.inputs:
            report_content += "**Required Inputs:**\n"
            for input_file in step.inputs:
                exists, status = check_file_existence(input_file)
                status_icon = "✅" if exists else "❌"
                report_content += f"- {status_icon} `{input_file}` - {status}\n"
            report_content += "\n"
        
        # Optional inputs
        if step.optional_inputs:
            report_content += "**Optional Inputs:**\n"
            for input_file in step.optional_inputs:
                exists, status = check_file_existence(input_file)
                status_icon = "✅" if exists else "⚠️"
                report_content += f"- {status_icon} `{input_file}` - {status}\n"
            report_content += "\n"
        
        # Outputs
        if step.outputs:
            report_content += "**Outputs:**\n"
            for output_file in step.outputs:
                exists, status = check_file_existence(output_file)
                status_icon = "✅" if exists else "❌"
                report_content += f"- {status_icon} `{output_file}` - {status}\n"
            report_content += "\n"
        
        # Issues for this step
        if step_name in issues:
            report_content += f"**Issues ({len(issues[step_name])}):**\n"
            for issue in issues[step_name]:
                report_content += f"- ⚠️ {issue}\n"
            report_content += "\n"
        else:
            report_content += "**Status:** ✅ No issues detected\n\n"
    
    # Add recommendations
    report_content += """
## Recommendations

### Critical Issues to Fix:
1. **Missing Required Inputs**: These will cause pipeline steps to fail
2. **Missing Outputs**: Previous steps may not have run successfully

### File Naming Consistency:
- Some steps use different naming conventions (e.g., `202505` vs `202506A`)
- Consider standardizing period labels across all steps

### Dependency Management:
- Run steps in the correct order based on dependencies
- Consider creating a master pipeline script to orchestrate execution

## Next Steps

1. **Fix Critical Issues**: Address all missing required inputs first
2. **Run Missing Steps**: Execute steps that haven't produced their expected outputs
3. **Validate Outputs**: Ensure all output files contain expected data
4. **Test End-to-End**: Run the complete pipeline to verify data flow

"""
    
    # Save the report
    report_file = "pipeline_data_flow_report.md"
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    log_progress(f"Saved data flow report to {report_file}")

def create_execution_order_guide(steps: Dict[str, PipelineStep]) -> None:
    """
    Create a guide showing the proper execution order.
    
    Args:
        steps: Dictionary of pipeline steps
    """
    log_progress("Creating execution order guide...")
    
    # Topological sort to determine execution order
    execution_order = []
    remaining_steps = set(steps.keys())
    
    while remaining_steps:
        # Find steps with no remaining dependencies
        ready_steps = []
        for step_name in remaining_steps:
            step = steps[step_name]
            if not step.dependencies or all(dep not in remaining_steps for dep in step.dependencies):
                ready_steps.append(step_name)
        
        if not ready_steps:
            # Circular dependency or missing step
            break
        
        # Add ready steps to execution order
        ready_steps.sort()  # Sort for consistent ordering
        execution_order.extend(ready_steps)
        remaining_steps -= set(ready_steps)
    
    # Create execution guide
    guide_content = f"""# Pipeline Execution Order Guide

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Recommended Execution Order

Run the pipeline steps in this order to ensure proper data flow:

"""
    
    for i, step_name in enumerate(execution_order, 1):
        step = steps[step_name]
        guide_content += f"\n### {i}. {step.name}\n"
        guide_content += f"```bash\npython {step.script_path}\n```\n"
        
        if step.dependencies:
            guide_content += f"**Requires:** {', '.join([steps[dep].name for dep in step.dependencies])}\n"
        
        # Show key outputs
        if step.outputs:
            key_outputs = [output for output in step.outputs if not output.endswith('*.csv') and not output.endswith('*.png')][:3]
            if key_outputs:
                guide_content += f"**Key Outputs:** {', '.join([f'`{output}`' for output in key_outputs])}\n"
    
    if remaining_steps:
        guide_content += f"\n## Warning: Unresolved Dependencies\n"
        guide_content += f"The following steps have unresolved dependencies: {', '.join(remaining_steps)}\n"
    
    guide_content += """
## Quick Start Commands

Run all steps in sequence:
```bash
# Core data preparation
python src/step1_download_api_data.py
python src/step2_extract_coordinates.py
python src/step3_prepare_matrix.py

# Weather data (optional but recommended)
python src/step4_download_weather_data.py
python src/step5_calculate_feels_like_temperature.py

# Clustering analysis
python src/step6_cluster_analysis.py

# Business rules analysis
python src/step7_missing_category_rule.py
python src/step8_imbalanced_rule.py
python src/step9_below_minimum_rule.py
python src/step10_spu_assortment_optimization.py
python src/step11_improved_category_logic.py
python src/step12_sales_performance_rule.py

# Consolidation and dashboards
python src/step13_consolidate_spu_rules.py
python src/step14_global_overview_dashboard.py
python src/step15_interactive_map_dashboard.py
```

## Troubleshooting

If a step fails:
1. Check the previous step completed successfully
2. Verify all required input files exist
3. Check the step's specific error messages
4. Ensure sufficient disk space and memory

"""
    
    # Save the guide
    guide_file = "pipeline_execution_guide.md"
    with open(guide_file, 'w') as f:
        f.write(guide_content)
    
    log_progress(f"Saved execution order guide to {guide_file}")

def main() -> None:
    """Main function to analyze pipeline data flow."""
    start_time = datetime.now()
    log_progress("Starting Pipeline Data Flow Analysis...")
    
    try:
        # Analyze pipeline steps
        steps = analyze_pipeline_data_flow()
        
        # Validate data flow
        issues = validate_data_flow(steps)
        
        # Generate comprehensive report
        generate_data_flow_report(steps, issues)
        
        # Create execution order guide
        create_execution_order_guide(steps)
        
        # Summary
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress(f"\n{'='*70}")
        log_progress("PIPELINE DATA FLOW ANALYSIS COMPLETE")
        log_progress(f"{'='*70}")
        log_progress(f"Analysis completed in {execution_time:.1f} seconds")
        log_progress(f"✓ Steps analyzed: {len(steps)}")
        log_progress(f"✓ Steps with issues: {len(issues)}")
        log_progress(f"✓ Total issues found: {sum(len(issue_list) for issue_list in issues.values())}")
        
        if issues:
            log_progress(f"\n⚠️  CRITICAL ISSUES FOUND:")
            for step_name, step_issues in issues.items():
                critical_issues = [issue for issue in step_issues if "MISSING REQUIRED INPUT" in issue]
                if critical_issues:
                    log_progress(f"   {step_name}: {len(critical_issues)} critical issues")
        else:
            log_progress(f"\n✅ No critical issues found - pipeline data flow is healthy!")
        
        log_progress(f"\nGenerated files:")
        log_progress(f"  • pipeline_data_flow_report.md - Detailed analysis report")
        log_progress(f"  • pipeline_execution_guide.md - Step-by-step execution guide")
        
    except Exception as e:
        log_progress(f"Error in pipeline data flow analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main() 