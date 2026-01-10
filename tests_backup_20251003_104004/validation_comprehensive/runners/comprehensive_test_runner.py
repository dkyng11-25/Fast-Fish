#!/usr/bin/env python3
"""
Comprehensive Test Runner for All Pipeline Steps

This module provides comprehensive validation for all pipeline steps (1-37)
including both basic and advanced validation capabilities.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

# Import individual step runners
from .step1_runner import run_step1_validation
from .step2_runner import run_step2_validation
from .step3_runner import run_step3_validation
from .step4_runner import run_step4_validation
from .step5_runner import run_step5_validation
from .step6_runner import run_step6_validation
from .step7_runner import run_step7_validation
from .step8_runner import run_step8_validation
from .step9_runner import run_step9_validation
from .step10_runner import run_step10_validation
from .step11_runner import run_step11_validation
from .step12_runner import run_step12_validation
from .step13_runner import run_step13_validation
from .step14_runner import run_step14_validation
from .step15_runner import run_step15_validation
from .step16_runner import run_step16_validation
from .step17_runner import run_step17_validation
from .step18_runner import run_step18_validation
from .step19_runner import run_step19_validation
from .step20_runner import run_step20_validation
from .step21_runner import run_step21_validation
from .step22_runner import run_step22_validation
from .step23_runner import run_step23_validation
from .step24_runner import run_step24_validation
from .step25_runner import run_step25_validation
from .step26_runner import run_step26_validation
from .step27_runner import run_step27_validation
from .step28_runner import run_step28_validation
from .step29_runner import run_step29_validation
from .step30_runner import run_step30_validation
from .step31_runner import run_step31_validation
from .step32_runner import run_step32_validation
from .step33_runner import run_step33_validation
from .step34_runner import run_step34_validation
from .step35_runner import run_step35_validation
from .step36_runner import run_step36_validation
from .step37_runner import run_step37_validation

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComprehensiveTestRunner:
    """Comprehensive test runner for all pipeline steps (1-37)."""
    
    def __init__(self, period: str = "202508A", output_dir: str = "../../output"):
        """Initialize the comprehensive test runner."""
        self.period = period
        self.output_dir = Path(output_dir)
        self.results = {}
        
        # Define all step validators
        self.step_validators = {
            1: run_step1_validation,
            2: run_step2_validation,
            3: run_step3_validation,
            4: run_step4_validation,
            5: run_step5_validation,
            6: run_step6_validation,
            7: run_step7_validation,
            8: run_step8_validation,
            9: run_step9_validation,
            10: run_step10_validation,
            11: run_step11_validation,
            12: run_step12_validation,
            13: run_step13_validation,
            14: run_step14_validation,
            15: run_step15_validation,
            16: run_step16_validation,
            17: run_step17_validation,
            18: run_step18_validation,
            19: run_step19_validation,
            20: run_step20_validation,
            21: run_step21_validation,
            22: run_step22_validation,
            23: run_step23_validation,
            24: run_step24_validation,
            25: run_step25_validation,
            26: run_step26_validation,
            27: run_step27_validation,
            28: run_step28_validation,
            29: run_step29_validation,
            30: run_step30_validation,
            31: run_step31_validation,
            32: run_step32_validation,
            33: run_step33_validation,
            34: run_step34_validation,
            35: run_step35_validation,
            36: run_step36_validation,
            37: run_step37_validation
        }
    
    def run_validation(self, steps: Optional[List[int]] = None, 
                      include_quality: bool = True) -> Dict[str, Any]:
        """
        Run validation for specified steps or all steps.
        
        Args:
            steps: List of step numbers to validate (None for all steps)
            include_quality: Whether to include quality validation
            
        Returns:
            Dictionary with comprehensive validation results
        """
        logger.info(f"Starting comprehensive validation for period {self.period}")
        
        if steps is None:
            steps = list(self.step_validators.keys())
        
        results = {
            'period': self.period,
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'summary': {},
            'overall_status': 'pending'
        }
        
        total_steps = len(steps)
        passed_steps = 0
        failed_steps = 0
        skipped_steps = 0
        
        for step_num in sorted(steps):
            if step_num not in self.step_validators:
                logger.warning(f"No validator found for step {step_num}, skipping")
                skipped_steps += 1
                continue
                
            logger.info(f"Validating step {step_num} ({steps.index(step_num) + 1}/{total_steps})")
            
            try:
                step_result = self.step_validators[step_num](self.period)
                results['steps'][f'step{step_num}'] = step_result
                
                if step_result.get('validation_passed', False):
                    passed_steps += 1
                    logger.info(f"✅ Step {step_num} validation passed")
                else:
                    failed_steps += 1
                    logger.warning(f"❌ Step {step_num} validation failed")
                    
            except Exception as e:
                logger.error(f"Error validating step {step_num}: {str(e)}")
                results['steps'][f'step{step_num}'] = {
                    'validation_passed': False,
                    'errors': [str(e)],
                    'warnings': []
                }
                failed_steps += 1
        
        # Generate summary
        results['summary'] = {
            'total_steps': total_steps,
            'passed_steps': passed_steps,
            'failed_steps': failed_steps,
            'skipped_steps': skipped_steps,
            'success_rate': (passed_steps / total_steps) * 100 if total_steps > 0 else 0,
            'overall_status': 'passed' if failed_steps == 0 else 'failed'
        }
        
        results['overall_status'] = results['summary']['overall_status']
        
        logger.info(f"Comprehensive validation completed: {results['summary']['success_rate']:.1f}% success rate")
        return results
    
    def run_basic_validation(self, steps: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Run basic validation for specified steps.
        
        Args:
            steps: List of step numbers to validate (None for all steps)
            
        Returns:
            Dictionary with basic validation results
        """
        return self.run_validation(steps, include_quality=False)
    
    def run_quality_validation(self, steps: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Run quality validation for specified steps.
        
        Args:
            steps: List of step numbers to validate (None for all steps)
            
        Returns:
            Dictionary with quality validation results
        """
        return self.run_validation(steps, include_quality=True)
    
    def run_critical_steps_validation(self) -> Dict[str, Any]:
        """
        Run validation for critical pipeline steps only.
        
        Returns:
            Dictionary with critical steps validation results
        """
        critical_steps = [1, 2, 3, 4, 5, 6, 13, 14, 36, 37]  # Define critical steps
        return self.run_validation(critical_steps)
    
    def run_data_download_steps_validation(self) -> Dict[str, Any]:
        """
        Run validation for data download steps only.
        
        Returns:
            Dictionary with data download steps validation results
        """
        data_download_steps = [1, 4, 15]  # Define data download steps
        return self.run_validation(data_download_steps)
    
    def run_analysis_steps_validation(self) -> Dict[str, Any]:
        """
        Run validation for analysis steps only.
        
        Returns:
            Dictionary with analysis steps validation results
        """
        analysis_steps = [5, 6, 7, 8, 9, 10, 11, 12, 25, 26, 27, 28, 29]  # Define analysis steps
        return self.run_validation(analysis_steps)
    
    def run_merchandising_steps_validation(self) -> Dict[str, Any]:
        """
        Run validation for merchandising steps only.
        
        Returns:
            Dictionary with merchandising steps validation results
        """
        merchandising_steps = [30, 31, 32, 33, 34, 35]  # Define merchandising steps
        return self.run_validation(merchandising_steps)
    
    def run_delivery_steps_validation(self) -> Dict[str, Any]:
        """
        Run validation for delivery steps only.
        
        Returns:
            Dictionary with delivery steps validation results
        """
        delivery_steps = [36, 37]  # Define delivery steps
        return self.run_validation(delivery_steps)
    
    def save_results(self, results: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Save validation results to file.
        
        Args:
            results: Validation results dictionary
            filename: Optional filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"comprehensive_validation_results_{self.period}_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Validation results saved to {filepath}")
        return str(filepath)
    
    def print_summary(self, results: Dict[str, Any]):
        """Print validation summary."""
        summary = results['summary']
        
        print("\n" + "="*80)
        print("COMPREHENSIVE VALIDATION RESULTS")
        print("="*80)
        print(f"Period: {results['period']}")
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Steps: {summary['total_steps']}")
        print(f"Passed: {summary['passed_steps']}")
        print(f"Failed: {summary['failed_steps']}")
        print(f"Skipped: {summary['skipped_steps']}")
        print("="*80)
        
        # Print step details
        print(f"\nStep Details:")
        for step_name, step_result in results['steps'].items():
            status_icon = "✅" if step_result.get('validation_passed', False) else "❌"
            print(f"  {status_icon} {step_name}: {'PASSED' if step_result.get('validation_passed', False) else 'FAILED'}")
            
            if step_result.get('errors'):
                for error in step_result['errors'][:2]:  # Show first 2 errors
                    print(f"    - {error}")
                if len(step_result['errors']) > 2:
                    print(f"    ... and {len(step_result['errors']) - 2} more errors")


def run_comprehensive_validation(period: str = "202508A", 
                                steps: Optional[List[int]] = None,
                                include_quality: bool = True) -> Dict[str, Any]:
    """
    Run comprehensive validation for all or specified pipeline steps.
    
    Args:
        period: Period label for validation
        steps: List of step numbers to validate (None for all steps)
        include_quality: Whether to include quality validation
        
    Returns:
        Dictionary with comprehensive validation results
    """
    runner = ComprehensiveTestRunner(period)
    return runner.run_validation(steps, include_quality)


def run_critical_validation(period: str = "202508A") -> Dict[str, Any]:
    """
    Run validation for critical pipeline steps only.
    
    Args:
        period: Period label for validation
        
    Returns:
        Dictionary with critical steps validation results
    """
    runner = ComprehensiveTestRunner(period)
    return runner.run_critical_steps_validation()


def run_analysis_validation(period: str = "202508A") -> Dict[str, Any]:
    """
    Run validation for analysis steps only.
    
    Args:
        period: Period label for validation
        
    Returns:
        Dictionary with analysis steps validation results
    """
    runner = ComprehensiveTestRunner(period)
    return runner.run_analysis_steps_validation()


def run_merchandising_validation(period: str = "202508A") -> Dict[str, Any]:
    """
    Run validation for merchandising steps only.
    
    Args:
        period: Period label for validation
        
    Returns:
        Dictionary with merchandising steps validation results
    """
    runner = ComprehensiveTestRunner(period)
    return runner.run_merchandising_steps_validation()


def run_delivery_validation(period: str = "202508A") -> Dict[str, Any]:
    """
    Run validation for delivery steps only.
    
    Args:
        period: Period label for validation
        
    Returns:
        Dictionary with delivery steps validation results
    """
    runner = ComprehensiveTestRunner(period)
    return runner.run_delivery_steps_validation()


if __name__ == "__main__":
    # Run validation when script is executed directly
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive validation for pipeline steps")
    parser.add_argument("--period", default="202508A", help="Period to validate")
    parser.add_argument("--steps", nargs="+", type=int, help="Specific steps to validate")
    parser.add_argument("--critical", action="store_true", help="Run only critical steps")
    parser.add_argument("--analysis", action="store_true", help="Run only analysis steps")
    parser.add_argument("--merchandising", action="store_true", help="Run only merchandising steps")
    parser.add_argument("--delivery", action="store_true", help="Run only delivery steps")
    parser.add_argument("--no-quality", action="store_true", help="Skip quality validation")
    parser.add_argument("--save", help="Save results to specified file")
    
    args = parser.parse_args()
    
    # Determine which validation to run
    if args.critical:
        results = run_critical_validation(args.period)
    elif args.analysis:
        results = run_analysis_validation(args.period)
    elif args.merchandising:
        results = run_merchandising_validation(args.period)
    elif args.delivery:
        results = run_delivery_validation(args.period)
    else:
        results = run_comprehensive_validation(
            args.period, 
            args.steps, 
            not args.no_quality
        )
    
    # Print summary
    runner = ComprehensiveTestRunner(args.period)
    runner.print_summary(results)
    
    # Save results if requested
    if args.save:
        runner.save_results(results, args.save)
    
    # Return appropriate exit code
    if results['summary']['overall_status'] == 'passed':
        sys.exit(0)
    else:
        sys.exit(1)