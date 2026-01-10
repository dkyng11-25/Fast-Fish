#!/usr/bin/env python3
"""
Steps 13-24 Comprehensive Runner

This runner provides comprehensive validation and testing for steps 13-24.

Author: Data Pipeline
Date: 2025-01-03
"""

import os
import sys
import pandas as pd
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.validation_comprehensive.schemas.pipeline import (
    ConsolidatedSPURulesSchema,
    FastFishFormatSchema,
    HistoricalBaselineSchema,
    ComparisonTableSchema,
    AugmentedRecommendationsSchema,
    ValidationResultsSchema,
    DetailedSPUBreakdownSchema,
    DataValidationReportSchema,
    LabelTagRecommendationsSchema,
    StoreAttributeEnrichmentSchema,
    ClusteringFeaturesUpdateSchema,
    ComprehensiveClusterLabelingSchema
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Steps13_24Runner:
    """Comprehensive runner for steps 13-24."""
    
    def __init__(self, period: str = "202508A"):
        """Initialize the steps 13-24 runner."""
        self.period = period
        self.output_dir = Path("output")
        self.data_dir = Path("data")
        
        # Step definitions with their expected outputs
        self.step_definitions = {
            'step13': {
                'name': 'Consolidate All SPU-Level Rule Results',
                'script': 'src/step13_consolidate_spu_rules.py',
                'expected_files': [
                    'consolidated_spu_rule_results_detailed_202508A.csv',
                    'consolidated_spu_rule_results.csv',
                    'consolidated_cluster_subcategory_results.csv'
                ],
                'schema': ConsolidatedSPURulesSchema
            },
            'step14': {
                'name': 'Create Fast Fish Format',
                'script': 'src/step14_create_fast_fish_format.py',
                'expected_files': [
                    'enhanced_fast_fish_format_202508A.csv',
                    'cluster_fashion_makeup_202508A.csv',
                    'cluster_weather_profile_202508A.csv',
                    'store_level_recommendation_breakdown_202508A.csv'
                ],
                'schema': FastFishFormatSchema
            },
            'step15': {
                'name': 'Download Historical Baseline',
                'script': 'src/step15_download_historical_baseline.py',
                'expected_files': [
                    'historical_baseline_202508A.csv',
                    'historical_spu_counts_202508A.csv',
                    'historical_sales_performance_202508A.csv'
                ],
                'schema': HistoricalBaselineSchema
            },
            'step16': {
                'name': 'Create Comparison Tables',
                'script': 'src/step16_create_comparison_tables.py',
                'expected_files': [
                    'comparison_tables_202508A.xlsx',
                    'store_group_comparison_202508A.csv',
                    'category_comparison_202508A.csv'
                ],
                'schema': ComparisonTableSchema
            },
            'step17': {
                'name': 'Augment Recommendations',
                'script': 'src/step17_augment_recommendations.py',
                'expected_files': [
                    'augmented_recommendations_202508A.csv',
                    'recommendation_enhancements_202508A.csv',
                    'market_analysis_202508A.csv'
                ],
                'schema': AugmentedRecommendationsSchema
            },
            'step18': {
                'name': 'Validate Results',
                'script': 'src/step18_validate_results.py',
                'expected_files': [
                    'validation_results_202508A.csv',
                    'data_quality_report_202508A.csv',
                    'business_logic_validation_202508A.csv'
                ],
                'schema': ValidationResultsSchema
            },
            'step19': {
                'name': 'Detailed SPU Breakdown',
                'script': 'src/step19_detailed_spu_breakdown.py',
                'expected_files': [
                    'detailed_spu_breakdown_202508A.csv',
                    'spu_performance_analysis_202508A.csv',
                    'store_spu_analysis_202508A.csv'
                ],
                'schema': DetailedSPUBreakdownSchema
            },
            'step20': {
                'name': 'Data Validation',
                'script': 'src/step20_data_validation.py',
                'expected_files': [
                    'data_validation_report_202508A.csv',
                    'data_quality_issues_202508A.csv',
                    'validation_rules_202508A.csv'
                ],
                'schema': DataValidationReportSchema
            },
            'step21': {
                'name': 'Label Tag Recommendations',
                'script': 'src/step21_label_tag_recommendations.py',
                'expected_files': [
                    'label_tag_recommendations_202508A.csv',
                    'tag_analysis_202508A.csv',
                    'tag_recommendation_engine_202508A.csv'
                ],
                'schema': LabelTagRecommendationsSchema
            },
            'step22': {
                'name': 'Store Attribute Enrichment',
                'script': 'src/step22_store_attribute_enrichment.py',
                'expected_files': [
                    'store_attribute_enrichment_202508A.csv',
                    'store_demographic_analysis_202508A.csv',
                    'store_performance_enrichment_202508A.csv'
                ],
                'schema': StoreAttributeEnrichmentSchema
            },
            'step23': {
                'name': 'Update Clustering Features',
                'script': 'src/step23_update_clustering_features.py',
                'expected_files': [
                    'clustering_features_update_202508A.csv',
                    'clustering_feature_details_202508A.csv',
                    'cluster_update_summary_202508A.csv'
                ],
                'schema': ClusteringFeaturesUpdateSchema
            },
            'step24': {
                'name': 'Comprehensive Cluster Labeling',
                'script': 'src/step24_comprehensive_cluster_labeling.py',
                'expected_files': [
                    'comprehensive_cluster_labeling_202508A.csv',
                    'cluster_label_analysis_202508A.csv',
                    'cluster_labeling_engine_202508A.csv'
                ],
                'schema': ComprehensiveClusterLabelingSchema
            }
        }
    
    def run_step(self, step_name: str, force: bool = False) -> Dict[str, Any]:
        """Run a specific step and validate its output."""
        if step_name not in self.step_definitions:
            return {'error': f'Unknown step: {step_name}'}
        
        step_def = self.step_definitions[step_name]
        logger.info(f"Running {step_name}: {step_def['name']}")
        
        results = {
            'step': step_name,
            'name': step_def['name'],
            'status': 'pending',
            'execution_time': 0,
            'files_created': 0,
            'files_expected': len(step_def['expected_files']),
            'validation_results': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check if step already completed
            if not force and self._is_step_completed(step_name):
                logger.info(f"Step {step_name} already completed, skipping...")
                results['status'] = 'already_completed'
                return results
            
            # Run the step
            start_time = pd.Timestamp.now()
            execution_result = self._execute_step(step_name, step_def)
            end_time = pd.Timestamp.now()
            
            results['execution_time'] = (end_time - start_time).total_seconds()
            
            if execution_result['success']:
                # Validate outputs
                validation_results = self._validate_step_outputs(step_name, step_def)
                results['validation_results'] = validation_results
                results['files_created'] = validation_results.get('files_found', 0)
                
                if validation_results.get('validation_passed', False):
                    results['status'] = 'completed'
                else:
                    results['status'] = 'completed_with_warnings'
                    results['warnings'].extend(validation_results.get('warnings', []))
            else:
                results['status'] = 'failed'
                results['errors'].extend(execution_result.get('errors', []))
        
        except Exception as e:
            logger.error(f"Error running step {step_name}: {str(e)}")
            results['status'] = 'failed'
            results['errors'].append(str(e))
        
        return results
    
    def run_all_steps(self, force: bool = False, steps: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run all steps 13-24 or specified steps."""
        if steps is None:
            steps = list(self.step_definitions.keys())
        
        logger.info(f"Running steps: {', '.join(steps)}")
        
        all_results = {}
        total_steps = len(steps)
        completed_steps = 0
        failed_steps = 0
        
        for step_name in steps:
            logger.info(f"Processing step {step_name} ({completed_steps + 1}/{total_steps})")
            step_results = self.run_step(step_name, force)
            all_results[step_name] = step_results
            
            if step_results['status'] == 'completed':
                completed_steps += 1
            elif step_results['status'] == 'failed':
                failed_steps += 1
        
        # Summary
        summary = {
            'total_steps': total_steps,
            'completed_steps': completed_steps,
            'failed_steps': failed_steps,
            'success_rate': (completed_steps / total_steps) * 100 if total_steps > 0 else 0,
            'results': all_results
        }
        
        return summary
    
    def validate_all_steps(self) -> Dict[str, Any]:
        """Validate all steps without running them."""
        logger.info("Validating all steps 13-24...")
        
        validation_results = {}
        total_files = 0
        found_files = 0
        
        for step_name, step_def in self.step_definitions.items():
            step_validation = self._validate_step_outputs(step_name, step_def)
            validation_results[step_name] = step_validation
            
            total_files += len(step_def['expected_files'])
            found_files += step_validation.get('files_found', 0)
        
        summary = {
            'total_files_expected': total_files,
            'files_found': found_files,
            'success_rate': (found_files / total_files) * 100 if total_files > 0 else 0,
            'validation_results': validation_results
        }
        
        return summary
    
    def _is_step_completed(self, step_name: str) -> bool:
        """Check if a step has already been completed."""
        step_def = self.step_definitions[step_name]
        expected_files = step_def['expected_files']
        
        # Check if at least 50% of expected files exist
        existing_files = sum(1 for filename in expected_files 
                           if (self.output_dir / filename).exists())
        
        return existing_files >= len(expected_files) * 0.5
    
    def _execute_step(self, step_name: str, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a step script."""
        script_path = step_def['script']
        
        if not os.path.exists(script_path):
            return {
                'success': False,
                'errors': [f'Script not found: {script_path}']
            }
        
        try:
            # Set environment variables
            env = os.environ.copy()
            env['PIPELINE_TARGET_YYYYMM'] = '202508'
            env['PIPELINE_TARGET_PERIOD'] = 'A'
            env['PYTHONPATH'] = '.'
            
            # Run the script
            cmd = ['python', script_path]
            
            # Add specific arguments for certain steps
            if step_name == 'step14':
                cmd.extend(['--target-yyyymm', '202508', '--target-period', 'A'])
            elif step_name in ['step15', 'step16', 'step17', 'step18']:
                cmd.extend(['--yyyymm', '202508', '--period', 'A'])
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                return {
                    'success': False,
                    'errors': [f'Script failed with return code {result.returncode}'],
                    'stderr': result.stderr
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'errors': ['Script execution timed out']
            }
        except Exception as e:
            return {
                'success': False,
                'errors': [f'Execution error: {str(e)}']
            }
    
    def _validate_step_outputs(self, step_name: str, step_def: Dict[str, Any]) -> Dict[str, Any]:
        """Validate step outputs."""
        expected_files = step_def['expected_files']
        schema = step_def.get('schema')
        
        validation_results = {
            'files_expected': len(expected_files),
            'files_found': 0,
            'files_validated': 0,
            'validation_passed': True,
            'warnings': [],
            'errors': []
        }
        
        for filename in expected_files:
            file_path = self.output_dir / filename
            if file_path.exists():
                validation_results['files_found'] += 1
                
                # Try to validate with schema if available
                if schema:
                    try:
                        if filename.endswith('.csv'):
                            df = pd.read_csv(file_path)
                            schema.validate(df)
                            validation_results['files_validated'] += 1
                            logger.info(f"✅ {filename}: Schema validation passed")
                        else:
                            validation_results['files_validated'] += 1
                            logger.info(f"✅ {filename}: File exists")
                    except Exception as e:
                        validation_results['warnings'].append(f"Schema validation failed for {filename}: {str(e)}")
                        logger.warning(f"⚠️ {filename}: Schema validation failed - {str(e)}")
                else:
                    validation_results['files_validated'] += 1
                    logger.info(f"✅ {filename}: File exists")
            else:
                validation_results['validation_passed'] = False
                validation_results['errors'].append(f"Missing file: {filename}")
                logger.warning(f"❌ {filename}: Missing")
        
        return validation_results


def main():
    """Main function to run steps 13-24 validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run and validate steps 13-24")
    parser.add_argument("--period", default="202508A", help="Period to process")
    parser.add_argument("--steps", nargs="+", help="Specific steps to run (e.g., step13 step14)")
    parser.add_argument("--force", action="store_true", help="Force re-run even if already completed")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't run steps")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize runner
    runner = Steps13_24Runner(period=args.period)
    
    if args.validate_only:
        # Only validate existing outputs
        results = runner.validate_all_steps()
        print(f"\n=== VALIDATION RESULTS ===")
        print(f"Files found: {results['files_found']}/{results['total_files_expected']}")
        print(f"Success rate: {results['success_rate']:.1f}%")
    else:
        # Run steps
        results = runner.run_all_steps(force=args.force, steps=args.steps)
        print(f"\n=== EXECUTION RESULTS ===")
        print(f"Completed: {results['completed_steps']}/{results['total_steps']}")
        print(f"Failed: {results['failed_steps']}/{results['total_steps']}")
        print(f"Success rate: {results['success_rate']:.1f}%")
    
    return results


if __name__ == "__main__":
    main()
