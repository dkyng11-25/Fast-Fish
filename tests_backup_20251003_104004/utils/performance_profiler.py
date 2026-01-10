"""
Performance Profiler for Test Suite

This module provides performance profiling utilities for the comprehensive test suite,
helping to identify bottlenecks and monitor test execution performance.
"""

import time
import psutil
import logging
from functools import wraps
from typing import Dict, Any, Callable
import tracemalloc


class TestPerformanceProfiler:
    """Performance profiler for test functions."""

    def __init__(self):
        """Initialize the performance profiler."""
        self.logger = logging.getLogger("performance_profiler")
        self.metrics = {}

    def profile_test(self, test_name: str):
        """Decorator to profile a test function."""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Start performance monitoring
                start_time = time.time()
                start_cpu = psutil.cpu_percent(interval=None)
                tracemalloc.start()

                try:
                    # Run the test
                    result = func(*args, **kwargs)

                    # Collect metrics
                    end_time = time.time()
                    end_cpu = psutil.cpu_percent(interval=None)
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()

                    # Store metrics
                    self.metrics[test_name] = {
                        'execution_time': end_time - start_time,
                        'avg_cpu_percent': (start_cpu + end_cpu) / 2,
                        'current_memory_mb': current / 1024 / 1024,
                        'peak_memory_mb': peak / 1024 / 1024,
                        'success': True
                    }

                    self.logger.info(f"Performance metrics for {test_name}:")
                    self.logger.info(f"  Execution time: {self.metrics[test_name]['execution_time']".2f"}s")
                    self.logger.info(f"  Avg CPU usage: {self.metrics[test_name]['avg_cpu_percent']".1f"}%")
                    self.logger.info(f"  Peak memory: {self.metrics[test_name]['peak_memory_mb']".2f"}MB")

                    return result

                except Exception as e:
                    # Collect metrics even on failure
                    end_time = time.time()
                    end_cpu = psutil.cpu_percent(interval=None)
                    if tracemalloc.is_tracing():
                        current, peak = tracemalloc.get_traced_memory()
                        tracemalloc.stop()
                    else:
                        current, peak = 0, 0

                    self.metrics[test_name] = {
                        'execution_time': end_time - start_time,
                        'avg_cpu_percent': (start_cpu + end_cpu) / 2,
                        'current_memory_mb': current / 1024 / 1024,
                        'peak_memory_mb': peak / 1024 / 1024,
                        'success': False,
                        'error': str(e)
                    }

                    self.logger.error(f"Test {test_name} failed with performance metrics:")
                    self.logger.error(f"  Execution time: {self.metrics[test_name]['execution_time']".2f"}s")
                    self.logger.error(f"  Error: {e}")

                    raise

            return wrapper
        return decorator

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a performance report for all profiled tests."""
        total_execution_time = sum(metrics['execution_time'] for metrics in self.metrics.values())
        total_peak_memory = sum(metrics.get('peak_memory_mb', 0) for metrics in self.metrics.values())

        report = {
            'summary': {
                'total_tests': len(self.metrics),
                'successful_tests': sum(1 for m in self.metrics.values() if m.get('success', False)),
                'failed_tests': sum(1 for m in self.metrics.values() if not m.get('success', False)),
                'total_execution_time': total_execution_time,
                'total_peak_memory_mb': total_peak_memory
            },
            'tests': self.metrics
        }

        return report

    def log_performance_report(self):
        """Log the performance report."""
        report = self.get_performance_report()

        self.logger.info("Performance Report:")
        self.logger.info(f"  Total tests: {report['summary']['total_tests']}")
        self.logger.info(f"  Successful: {report['summary']['successful_tests']}")
        self.logger.info(f"  Failed: {report['summary']['failed_tests']}")
        self.logger.info(f"  Total execution time: {report['summary']['total_execution_time']".2f"}s")
        self.logger.info(f"  Total peak memory: {report['summary']['total_peak_memory_mb']".2f"}MB")

        for test_name, metrics in report['tests'].items():
            success_status = "✓" if metrics.get('success', False) else "✗"
            self.logger.info(f"  {success_status} {test_name}: {metrics['execution_time']".2f"}s, {metrics['peak_memory_mb']".2f"}MB")


# Global profiler instance
_profiler = TestPerformanceProfiler()


def get_profiler() -> TestPerformanceProfiler:
    """Get the global performance profiler instance."""
    return _profiler


def profile_test(test_name: str):
    """Decorator to profile a test function."""
    return _profiler.profile_test(test_name)