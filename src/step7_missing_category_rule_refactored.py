#!/usr/bin/env python3
"""
Step 7: Missing Category/SPU Rule with Sell-Through Validation (Refactored)

This is the refactored implementation of Step 7 following the 4-phase Step pattern.

Usage:
    python src/step7_missing_category_rule_refactored.py --target-yyyymm 202510 --target-period A
    python src/step7_missing_category_rule_refactored.py --target-yyyymm 202510 --target-period A --analysis-level spu
    
Environment Variables:
    ANALYSIS_LEVEL: 'subcategory' or 'spu' (default: subcategory)
    MIN_CLUSTER_STORES_SELLING: Minimum percentage of stores (default: 0.70 for subcategory, 0.80 for SPU)
    MIN_CLUSTER_SALES_THRESHOLD: Minimum sales amount (default: 100 for subcategory, 1500 for SPU)
    MIN_PREDICTED_ST: Minimum predicted sell-through (default: 0.30)
    ENABLE_SEASONAL_BLENDING: Enable seasonal data blending (default: True)
    SEASONAL_WEIGHT: Weight for seasonal data (default: 0.60)
"""

import argparse
import sys
import os
import logging
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.logger import PipelineLogger
from core.context import StepContext
from core.exceptions import DataValidationError
from components.missing_category import MissingCategoryConfig
from steps.missing_category_rule_factory import MissingCategoryRuleFactory
from repositories.csv_repository import CsvFileRepository


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Step 7: Missing Category/SPU Rule (Refactored)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Required arguments
    parser.add_argument(
        '--target-yyyymm',
        required=True,
        help='Target period in YYYYMM format (e.g., 202510)'
    )
    
    parser.add_argument(
        '--target-period',
        required=True,
        choices=['A', 'B'],
        help='Target period: A (days 1-15) or B (days 16-end)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--analysis-level',
        choices=['subcategory', 'spu'],
        default=os.getenv('ANALYSIS_LEVEL', 'subcategory'),
        help='Analysis level: subcategory or spu (default: subcategory)'
    )
    
    parser.add_argument(
        '--enable-seasonal-blending',
        action='store_true',
        default=os.getenv('ENABLE_SEASONAL_BLENDING', 'True').lower() == 'true',
        help='Enable seasonal data blending (default: True)'
    )
    
    parser.add_argument(
        '--seasonal-weight',
        type=float,
        default=float(os.getenv('SEASONAL_WEIGHT', '0.60')),
        help='Weight for seasonal data (default: 0.60)'
    )
    
    parser.add_argument(
        '--min-predicted-st',
        type=float,
        default=float(os.getenv('MIN_PREDICTED_ST', '0.30')),
        help='Minimum predicted sell-through (default: 0.30)'
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default='output',
        help='Base data directory (default: output)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory (default: output)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--disable-fastfish',
        action='store_true',
        default=os.getenv('DISABLE_FASTFISH_VALIDATION', 'False').lower() == 'true',
        help='Disable Fast Fish sell-through validation (default: False)'
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Create logger
    logger = PipelineLogger(
        name="Step7_MissingCategoryRule",
        level=logging.DEBUG if args.verbose else logging.INFO
    )
    
    logger.info("=" * 80)
    logger.info("Step 7: Missing Category/SPU Rule (Refactored)")
    logger.info("=" * 80)
    logger.info(f"Target Period: {args.target_yyyymm}{args.target_period}")
    logger.info(f"Analysis Level: {args.analysis_level}")
    logger.info(f"Seasonal Blending: {args.enable_seasonal_blending}")
    
    try:
        # Create configuration
        config = MissingCategoryConfig(
            analysis_level=args.analysis_level,
            period_label=f"{args.target_yyyymm}{args.target_period}",
            use_blended_seasonal=args.enable_seasonal_blending,
            seasonal_weight=args.seasonal_weight,
            min_predicted_st=args.min_predicted_st
        )
        
        # Create CSV repository for data loading
        csv_repo = CsvFileRepository(file_path=args.data_dir, logger=logger)
        
        # Create output repository with proper filename
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"rule7_missing_{config.analysis_level}_sellthrough_results_{config.period_label}_{timestamp}.csv"
        output_path = f"{args.output_dir}/{output_filename}"
        output_repo = CsvFileRepository(file_path=output_path, logger=logger)
        
        # Import Fast Fish validator if available and not disabled
        if args.disable_fastfish:
            logger.warning("⚠️ Fast Fish validation DISABLED by user flag")
            fastfish_validator = None
        else:
            try:
                from sell_through_validator import SellThroughValidator
                fastfish_validator = SellThroughValidator()
                logger.info("✅ Fast Fish validator loaded")
            except ImportError:
                logger.warning("⚠️ Fast Fish validator not available - validation will be skipped")
                fastfish_validator = None
        
        # Create step using factory
        step = MissingCategoryRuleFactory.create(
            csv_repo=csv_repo,
            output_repo=output_repo,
            logger=logger,
            config=config,
            fastfish_validator=fastfish_validator
        )
        
        # Create initial context
        context = StepContext()
        context.set_state('period_label', config.period_label)
        context.set_state('analysis_level', config.analysis_level)
        context.set_state('target_yyyymm', args.target_yyyymm)
        context.set_state('target_period', args.target_period)
        context.set_state('data_dir', args.data_dir)
        context.set_state('output_dir', args.output_dir)
        
        # Execute step
        logger.info("🚀 Executing Step 7...")
        final_context = step.execute(context)
        
        # Log results
        logger.info("=" * 80)
        logger.info("✅ Step 7 completed successfully")
        logger.info("=" * 80)
        
        # Print summary
        opportunities_count = final_context.get_state('opportunities_count', 0)
        stores_with_opportunities = final_context.get_state('stores_with_opportunities', 0)
        total_investment = final_context.get_state('total_investment_required', 0)
        
        print("\n" + "=" * 80)
        print("📊 STEP 7 RESULTS SUMMARY")
        print("=" * 80)
        print(f"Analysis Level: {config.analysis_level}")
        print(f"Period: {config.period_label}")
        print(f"Opportunities Found: {opportunities_count}")
        print(f"Stores with Opportunities: {stores_with_opportunities}")
        print(f"Total Investment Required: ${total_investment:,.2f}")
        print("=" * 80)
        print(f"✅ Outputs saved to: {args.output_dir}/")
        print("=" * 80 + "\n")
        
        return 0
        
    except DataValidationError as e:
        logger.error(f"❌ Validation failed: {e}")
        print(f"\n❌ Validation Error: {e}\n", file=sys.stderr)
        return 1
        
    except KeyboardInterrupt:
        logger.warning("⚠️ Interrupted by user")
        print("\n⚠️ Execution interrupted by user\n", file=sys.stderr)
        return 130
        
    except Exception as e:
        logger.error(f"❌ Execution failed: {e}")
        logger.error(traceback.format_exc())
        print(f"\n❌ Execution Error: {e}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
