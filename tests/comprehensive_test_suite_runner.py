"""
Comprehensive Test Suite Runner for Steps 6-18

This test suite runner organizes and executes all comprehensive tests following USER_NOTE.md requirements:
- Tests 5 clusters with high/average consumption spread as subset
- Black-box testing with minimal assumptions
- Multiple parameter settings to capture anomalies
- Parallel execution for faster testing
- Dynamic period detection (202509A → 202508B → 202508A)
- Proper exclusion of slow steps (10 and 11)

Organization:
- tests/comprehensive/ : Main comprehensive test suite
- tests/subset_tests/ : Individual step tests
- tests/archived/ : Old test files for reference
- tests/utils/ : Test utilities and helpers
"""

import os
import sys
import subprocess
import logging
import pytest
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.periods import detect_available_period, split_period_label


class ComprehensiveTestSuiteRunner:
    """Main runner for comprehensive test suite covering Steps 6-18."""

    def __init__(self):
        """Initialize the comprehensive test suite runner."""
        self.project_root = Path(__file__).parent.parent
        self.test_root = Path(__file__).parent
        self.logger = self._setup_logger()

        # Test suite configuration following USER_NOTE.md
        self.test_config = {
            'steps': {
                6: {'name': 'Cluster Analysis', 'test_file': 'subset_tests/test_step6_subset_comprehensive.py', 'slow': False},
                7: {'name': 'Missing Category Rule', 'test_file': 'subset_tests/test_step7_subset_comprehensive.py', 'slow': False},
                8: {'name': 'Imbalanced Rule', 'test_file': 'subset_tests/test_step8_subset_comprehensive.py', 'slow': False},
                9: {'name': 'Below Minimum Rule', 'test_file': 'subset_tests/test_step9_subset_comprehensive.py', 'slow': False},
                10: {'name': 'SPU Assortment Optimization', 'test_file': 'slow_tests/test_step10_subset_comprehensive.py', 'slow': True},
                11: {'name': 'Missed Sales Opportunity', 'test_file': 'slow_tests/test_step11_subset_comprehensive.py', 'slow': True},
                12: {'name': 'Sales Performance Rule', 'test_file': 'subset_tests/test_step12_subset_comprehensive.py', 'slow': False},
                13: {'name': 'Consolidate SPU Rules', 'test_file': 'subset_tests/test_step13_subset_comprehensive.py', 'slow': False},
                14: {'name': 'Global Overview Dashboard', 'test_file': 'subset_tests/test_step14_subset_comprehensive.py', 'slow': False},
                15: {'name': 'Historical Baseline Download', 'test_file': 'subset_tests/test_step15_subset_comprehensive.py', 'slow': False},
                16: {'name': 'Create Comparison Tables', 'test_file': 'subset_tests/test_step16_subset_comprehensive.py', 'slow': False},
                17: {'name': 'Augment Recommendations', 'test_file': 'subset_tests/test_step17_subset_comprehensive.py', 'slow': False},
                18: {'name': 'Validate Results', 'test_file': 'subset_tests/test_step18_subset_comprehensive.py', 'slow': False}
            },
            'parallel_groups': {
                'fast_steps': [6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 18],  # Steps that can run in parallel
                'slow_steps': [10, 11]  # Steps marked as slow (excluded from main suite)
            },
            'execution_config': {
                'max_parallel_workers': 3,
                'timeout_per_test': 600,  # 10 minutes per test
                'retry_failed_tests': True,
                'generate_reports': True
            }
        }

        self.logger.info("Comprehensive Test Suite Runner initialized")
        self.logger.info(f"Project root: {self.project_root}")
        self.logger.info(f"Test root: {self.test_root}")

    def _setup_logger(self):
        """Set up comprehensive logging for the test suite."""
        logger = logging.getLogger("comprehensive_test_suite")
        logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create logs directory if it doesn't exist
        log_dir = self.test_root / "test_logs"
        log_dir.mkdir(exist_ok=True)

        # File handler for comprehensive test suite
        log_file = log_dir / "comprehensive_test_suite.log"
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def run_comprehensive_test_suite(self, exclude_slow_steps: bool = True, run_parallel: bool = True):
        """
        Run the comprehensive test suite for Steps 6-18.

        Args:
            exclude_slow_steps: Whether to exclude Steps 10 and 11 (default: True)
            run_parallel: Whether to run tests in parallel (default: True)
        """
        self.logger.info("Starting Comprehensive Test Suite execution")
        self.logger.info("=" * 80)

        # Get steps to run
        steps_to_run = self._get_steps_to_run(exclude_slow_steps)

        if not steps_to_run:
            self.logger.warning("No steps to run based on current configuration")
            return

        self.logger.info(f"Steps to run: {[step for step in steps_to_run]}")
        if exclude_slow_steps:
            self.logger.info(f"Excluding slow steps: {[step for step in self.test_config['parallel_groups']['slow_steps']]}")

        # Detect available periods
        available_period = detect_available_period(self.project_root)
        if available_period:
            period_parts = split_period_label(available_period)
            self.logger.info(f"Detected available period: {available_period} ({period_parts[0]} {period_parts[1]})")
        else:
            self.logger.warning("No valid data period found - tests may fail due to missing data")
            available_period = "202509A"  # Fallback

        # Set environment variables for tests
        os.environ['COMPREHENSIVE_TEST_PERIOD'] = available_period
        os.environ['COMPREHENSIVE_TEST_MODE'] = 'true'

        # Run tests
        if run_parallel:
            self._run_tests_parallel(steps_to_run)
        else:
            self._run_tests_sequential(steps_to_run)

        # Generate test report
        self._generate_comprehensive_report(steps_to_run)

        self.logger.info("=" * 80)
        self.logger.info("Comprehensive Test Suite execution completed")

    def _get_steps_to_run(self, exclude_slow_steps: bool) -> List[int]:
        """Get list of steps to run based on configuration."""
        all_steps = list(self.test_config['steps'].keys())

        if exclude_slow_steps:
            slow_steps = self.test_config['parallel_groups']['slow_steps']
            steps_to_run = [step for step in all_steps if step not in slow_steps]
        else:
            steps_to_run = all_steps

        return sorted(steps_to_run)

    def _run_tests_sequential(self, steps_to_run: List[int]):
        """Run tests sequentially."""
        self.logger.info("Running tests sequentially...")

        for step in steps_to_run:
            step_config = self.test_config['steps'][step]
            test_file = step_config['test_file']

            self.logger.info(f"Running Step {step}: {step_config['name']}")
            self.logger.info(f"Test file: {test_file}")

            # Run individual test
            result = self._run_single_step_test(step, test_file)

            if result['success']:
                self.logger.info(f"✓ Step {step} completed successfully")
            else:
                self.logger.error(f"✗ Step {step} failed: {result['error']}")

            # Small delay between tests to avoid resource conflicts
            time.sleep(2)

    def _run_tests_parallel(self, steps_to_run: List[int]):
        """Run tests in parallel using ThreadPoolExecutor."""
        self.logger.info("Running tests in parallel...")

        # Group steps for parallel execution
        fast_steps = [step for step in steps_to_run if step in self.test_config['parallel_groups']['fast_steps']]

        self.logger.info(f"Running {len(fast_steps)} steps in parallel...")

        # Run tests in parallel
        with ThreadPoolExecutor(max_workers=self.test_config['execution_config']['max_parallel_workers']) as executor:
            future_to_step = {}

            for step in fast_steps:
                step_config = self.test_config['steps'][step]
                test_file = step_config['test_file']

                future = executor.submit(self._run_single_step_test, step, test_file)
                future_to_step[future] = step

            # Collect results as they complete
            for future in as_completed(future_to_step):
                step = future_to_step[future]
                try:
                    result = future.result()
                    if result['success']:
                        self.logger.info(f"✓ Step {step} completed successfully")
                    else:
                        self.logger.error(f"✗ Step {step} failed: {result['error']}")
                except Exception as e:
                    step = future_to_step[future]
                    self.logger.error(f"✗ Step {step} encountered exception: {e}")

    def _run_single_step_test(self, step: int, test_file: str) -> Dict[str, Any]:
        """Run a single step test."""
        test_path = self.test_root / test_file

        if not test_path.exists():
            return {
                'success': False,
                'error': f'Test file not found: {test_file}',
                'step': step
            }

        try:
            # Run pytest for the specific test file
            cmd = [
                sys.executable, '-m', 'pytest',
                str(test_path),
                '-v', '--tb=short',
                '--durations=10'  # Show slowest 10 tests
            ]

            self.logger.info(f"Running command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.test_config['execution_config']['timeout_per_test']
            )

            return {
                'success': result.returncode == 0,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'step': step
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Test timed out after {self.test_config["execution_config"]["timeout_per_test"]} seconds',
                'step': step
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception during test execution: {e}',
                'step': step
            }

    def _generate_comprehensive_report(self, steps_run: List[int]):
        """Generate a comprehensive test report."""
        self.logger.info("Generating comprehensive test report...")

        report_data = {
            'execution_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'steps_executed': steps_run,
            'steps_skipped': [step for step in self.test_config['steps'].keys() if step not in steps_run],
            'test_configuration': self.test_config,
            'summary': {
                'total_steps': len(steps_run),
                'fast_steps': len([s for s in steps_run if s in self.test_config['parallel_groups']['fast_steps']]),
                'slow_steps': len([s for s in steps_run if s in self.test_config['parallel_groups']['slow_steps']])
            }
        }

        # Save report to JSON
        report_file = self.test_root / "test_logs" / "comprehensive_test_suite_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        self.logger.info(f"Comprehensive test report saved to: {report_file}")

        # Log summary
        self.logger.info("Test Suite Summary:")
        self.logger.info(f"  - Steps executed: {len(steps_run)}")
        self.logger.info(f"  - Steps skipped: {len(report_data['steps_skipped'])}")
        self.logger.info(f"  - Report location: {report_file}")

    def run_specific_step(self, step: int, verbose: bool = True):
        """Run a specific step test."""
        if step not in self.test_config['steps']:
            self.logger.error(f"Step {step} not found in test configuration")
            return False

        step_config = self.test_config['steps'][step]
        test_file = step_config['test_file']

        if verbose:
            self.logger.info(f"Running Step {step}: {step_config['name']}")
            self.logger.info(f"Test file: {test_file}")
            if step_config['slow']:
                self.logger.warning(f"Note: Step {step} is marked as slow")

        result = self._run_single_step_test(step, test_file)

        if result['success']:
            self.logger.info(f"✓ Step {step} completed successfully")
            return True
        else:
            error_msg = result.get('error', f"Test failed with return code {result.get('return_code', 'unknown')}")
            self.logger.error(f"✗ Step {step} failed: {error_msg}")
            if result.get('stderr'):
                self.logger.error(f"Error details: {result['stderr']}")
            return False

    def get_test_status(self) -> Dict[str, Any]:
        """Get comprehensive test status."""
        status = {
            'available_steps': list(self.test_config['steps'].keys()),
            'fast_steps': self.test_config['parallel_groups']['fast_steps'],
            'slow_steps': self.test_config['parallel_groups']['slow_steps'],
            'test_files_status': {}
        }

        # Check which test files exist
        for step, config in self.test_config['steps'].items():
            test_file = self.test_root / config['test_file']
            status['test_files_status'][step] = {
                'exists': test_file.exists(),
                'path': config['test_file'],
                'slow': config['slow']
            }

        return status


def main():
    """Main function to run the comprehensive test suite."""
    import argparse

    parser = argparse.ArgumentParser(description='Comprehensive Test Suite Runner for Steps 6-18')
    parser.add_argument('--exclude-slow', action='store_true', default=True,
                       help='Exclude slow steps (10 and 11) from execution')
    parser.add_argument('--sequential', action='store_true', default=False,
                       help='Run tests sequentially instead of in parallel')
    parser.add_argument('--step', type=int, help='Run specific step only')
    parser.add_argument('--status', action='store_true', default=False,
                       help='Show test suite status without running tests')
    parser.add_argument('--verbose', '-v', action='store_true', default=True,
                       help='Verbose output')

    args = parser.parse_args()

    # Set up logging level
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    # Create test suite runner
    runner = ComprehensiveTestSuiteRunner()

    if args.status:
        # Show test suite status
        status = runner.get_test_status()
        print("\nComprehensive Test Suite Status:")
        print("=" * 50)
        print(f"Available steps: {status['available_steps']}")
        print(f"Fast steps: {status['fast_steps']}")
        print(f"Slow steps: {status['slow_steps']}")
        print("\nTest Files Status:")
        for step, info in status['test_files_status'].items():
            status_symbol = "✓" if info['exists'] else "✗"
            slow_marker = " (SLOW)" if info['slow'] else ""
            print(f"  Step {step:2d}: {status_symbol} {info['path']}{slow_marker}")
        return

    if args.step:
        # Run specific step
        success = runner.run_specific_step(args.step, args.verbose)
        sys.exit(0 if success else 1)

    # Run comprehensive test suite
    runner.run_comprehensive_test_suite(
        exclude_slow_steps=args.exclude_slow,
        run_parallel=not args.sequential
    )


if __name__ == "__main__":
    main()
