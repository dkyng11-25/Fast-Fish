#!/usr/bin/env python3
"""
Comprehensive Validation Main Runner

This script provides a unified interface for running validation across all pipeline steps.
It uses the comprehensive validation system for consistent and reusable validation.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
import argparse
import sys
import os

# Add the tests directory to the path so we can import validation modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation_comprehensive.runners import (
    run_step1_validation,
    run_step2_validation,
    run_step2b_validation,
    run_step3_validation,
    run_step4_validation,
    run_step5_validation,
    run_step6_validation,
    run_step7_validation,
    run_step8_validation,
    run_step9_validation,
    run_step10_validation,
    run_step11_validation,
    run_step12_validation,
    run_step13_validation,
    run_step14_validation,
    run_comprehensive_validation,
    ComprehensiveTestRunner
)

# Import advanced step validators
from validation_comprehensive.runners.steps_15_36_runner import (
    validate_step15_historical_baseline,
    validate_step16_comparison_tables,
    validate_step17_augment_recommendations,
    validate_step18_validate_results,
    validate_step19_detailed_spu_breakdown,
    validate_step20_data_validation,
    validate_steps_21_24_labeling_analysis,
    validate_steps_25_29_analysis_optimization,
    validate_steps_30_36_merchandising_delivery,
    run_steps_15_36_validation
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main validation runner."""
    parser = argparse.ArgumentParser(description='Comprehensive validation runner for pipeline data')
    
        # Step selection
    parser.add_argument('--step', choices=[
        '1', '2', '2b', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14',
        '15', '16', '17', '18', '19', '20', '21-24', '25-29', '30-36',
        'all', 'comprehensive', 'advanced', 'eda'
    ], default='all',
                       help='Which step to validate (1-14, 15-36, all, comprehensive, advanced, or eda)')
    
    # Step 1 options
    parser.add_argument('--period', type=str, help='Period to validate (e.g., 202401)')
    parser.add_argument('--periods', nargs='+', help='Multiple periods to validate')
    parser.add_argument('--comprehensive', action='store_true', 
                       help='Run comprehensive validation on key periods')
    
    # Step 4 options
    parser.add_argument('--sample-size', type=int, default=5, 
                       help='Number of weather files to sample for validation')
    parser.add_argument('--weather-period', type=str, 
                       help='Specific weather period to validate (e.g., 202408)')
    
    # Step 5 options
    parser.add_argument('--include-quality', action='store_true', default=True,
                       help='Include quality validation checks for Step 5')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.step == '1':
            run_step1_validation(
                period=args.period,
                periods=args.periods,
                comprehensive=args.comprehensive
            )
        elif args.step == '2':
            run_step2_validation()
        elif args.step == '2b':
            run_step2b_validation()
        elif args.step == '3':
            run_step3_validation()
        elif args.step == '4':
            run_step4_validation(
                sample_size=args.sample_size,
                period=args.weather_period
            )
        elif args.step == '5':
            run_step5_validation(
                include_quality=args.include_quality
            )
        elif args.step == '6':
            run_step6_validation()
        elif args.step == '7':
            run_step7_validation()
        elif args.step == '8':
            run_step8_validation()
        elif args.step == '9':
            run_step9_validation()
        elif args.step == '10':
            run_step10_validation(period=args.period or "202508A")
        elif args.step == '11':
            run_step11_validation()
        elif args.step == '12':
            run_step12_validation(period=args.period or "202508A")
        elif args.step == '13':
            run_step13_validation()
        elif args.step == '14':
            run_step14_validation()
        elif args.step == '15':
            result = validate_step15_historical_baseline(period=args.period or "202508A")
            logger.info(f"Step 15 validation: {result['status']}")
        elif args.step == '16':
            result = validate_step16_comparison_tables(period=args.period or "202508A")
            logger.info(f"Step 16 validation: {result['status']}")
        elif args.step == '17':
            result = validate_step17_augment_recommendations(period=args.period or "202508A")
            logger.info(f"Step 17 validation: {result['status']}")
        elif args.step == '18':
            result = validate_step18_validate_results(period=args.period or "202508A")
            logger.info(f"Step 18 validation: {result['status']}")
        elif args.step == '19':
            result = validate_step19_detailed_spu_breakdown(period=args.period or "202508A")
            logger.info(f"Step 19 validation: {result['status']}")
        elif args.step == '20':
            result = validate_step20_data_validation(period=args.period or "202508A")
            logger.info(f"Step 20 validation: {result['status']}")
        elif args.step == '21-24':
            result = validate_steps_21_24_labeling_analysis(period=args.period or "202508A")
            logger.info(f"Steps 21-24 validation: {result['status']}")
        elif args.step == '25-29':
            result = validate_steps_25_29_analysis_optimization(period=args.period or "202508A")
            logger.info(f"Steps 25-29 validation: {result['status']}")
        elif args.step == '30-36':
            result = validate_steps_30_36_merchandising_delivery(period=args.period or "202508A")
            logger.info(f"Steps 30-36 validation: {result['status']}")
        elif args.step == 'all':
            run_comprehensive_validation()
        elif args.step == 'comprehensive':
            runner = ComprehensiveTestRunner(period=args.period or "202508A")
            results = runner.run_all_steps_validation()
            logger.info(f"Comprehensive testing completed. Results: {results['summary']}")
        elif args.step == 'advanced':
            result = run_steps_15_36_validation(period=args.period or "202508A")
            logger.info(f"Advanced steps validation completed: {result['summary']['success_rate']:.1f}% success rate")
        elif args.step == 'eda':
            from validation_comprehensive.runners.comprehensive_runner import ComprehensiveValidationRunner
            runner = ComprehensiveValidationRunner()
            results = runner.run_eda_analysis()
            logger.info(f"EDA analysis complete. Results saved to {runner.eda_results_path}")

        logger.info("\n✅ Validation completed successfully!")

    except Exception as e:
        logger.error(f"\n❌ Validation failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
