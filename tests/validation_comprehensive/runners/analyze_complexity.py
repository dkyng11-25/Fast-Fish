#!/usr/bin/env python3
"""
Complexity Analyzer for Pipeline Code

This module provides comprehensive complexity analysis for the pipeline codebase,
including cyclomatic complexity, maintainability index, and code quality metrics.

Author: Data Pipeline
Date: 2025-01-03
"""

import os
import sys
import ast
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import subprocess
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplexityAnalyzer:
    """Analyzer for code complexity metrics."""
    
    def __init__(self, src_dir: str = "src"):
        """Initialize the complexity analyzer."""
        self.src_dir = Path(src_dir)
        self.results = {}
    
    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze the entire codebase for complexity."""
        logger.info("Analyzing codebase complexity...")
        
        results = {
            'overall_metrics': {},
            'file_metrics': {},
            'step_metrics': {},
            'complexity_distribution': {},
            'recommendations': []
        }
        
        try:
            # Analyze all Python files in src directory
            python_files = list(self.src_dir.glob("*.py"))
            
            total_files = len(python_files)
            total_complexity = 0
            total_lines = 0
            total_functions = 0
            total_classes = 0
            
            file_metrics = {}
            
            for file_path in python_files:
                if file_path.name.startswith('__'):
                    continue
                
                file_metrics[file_path.name] = self.analyze_file(str(file_path))
                
                total_complexity += file_metrics[file_path.name].get('cyclomatic_complexity', 0)
                total_lines += file_metrics[file_path.name].get('lines_of_code', 0)
                total_functions += file_metrics[file_path.name].get('function_count', 0)
                total_classes += file_metrics[file_path.name].get('class_count', 0)
            
            # Calculate overall metrics
            results['overall_metrics'] = {
                'total_files': total_files,
                'total_complexity': total_complexity,
                'average_complexity': total_complexity / total_files if total_files > 0 else 0,
                'total_lines': total_lines,
                'average_lines_per_file': total_lines / total_files if total_files > 0 else 0,
                'total_functions': total_functions,
                'total_classes': total_classes,
                'functions_per_file': total_functions / total_files if total_files > 0 else 0,
                'classes_per_file': total_classes / total_files if total_files > 0 else 0
            }
            
            results['file_metrics'] = file_metrics
            
            # Analyze step-specific metrics
            results['step_metrics'] = self._analyze_step_metrics(file_metrics)
            
            # Calculate complexity distribution
            results['complexity_distribution'] = self._calculate_complexity_distribution(file_metrics)
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(file_metrics)
            
            logger.info("Codebase complexity analysis completed")
            
        except Exception as e:
            logger.error(f"Error analyzing codebase complexity: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single Python file for complexity."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            metrics = {
                'file_path': file_path,
                'lines_of_code': len(content.splitlines()),
                'cyclomatic_complexity': 0,
                'function_count': 0,
                'class_count': 0,
                'max_function_complexity': 0,
                'max_class_complexity': 0,
                'maintainability_index': 0,
                'duplicate_lines': 0,
                'longest_function': 0,
                'longest_class': 0,
                'import_count': 0,
                'comment_ratio': 0
            }
            
            # Count imports
            metrics['import_count'] = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
            
            # Count comments
            comment_lines = sum(1 for line in content.splitlines() if line.strip().startswith('#'))
            metrics['comment_ratio'] = comment_lines / metrics['lines_of_code'] if metrics['lines_of_code'] > 0 else 0
            
            # Analyze functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics['function_count'] += 1
                    func_complexity = self._calculate_cyclomatic_complexity(node)
                    metrics['cyclomatic_complexity'] += func_complexity
                    metrics['max_function_complexity'] = max(metrics['max_function_complexity'], func_complexity)
                    
                    # Calculate function length
                    func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 1
                    metrics['longest_function'] = max(metrics['longest_function'], func_lines)
                
                elif isinstance(node, ast.ClassDef):
                    metrics['class_count'] += 1
                    class_complexity = self._calculate_class_complexity(node)
                    metrics['max_class_complexity'] = max(metrics['max_class_complexity'], class_complexity)
                    
                    # Calculate class length
                    class_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 1
                    metrics['longest_class'] = max(metrics['longest_class'], class_lines)
            
            # Calculate maintainability index
            metrics['maintainability_index'] = self._calculate_maintainability_index(metrics)
            
            # Check for duplicate lines (simplified)
            metrics['duplicate_lines'] = self._count_duplicate_lines(content)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            return {'error': str(e), 'file_path': file_path}
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_class_complexity(self, node: ast.ClassDef) -> int:
        """Calculate complexity for a class."""
        complexity = 0
        
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                complexity += self._calculate_cyclomatic_complexity(child)
        
        return complexity
    
    def _calculate_maintainability_index(self, metrics: Dict[str, Any]) -> float:
        """Calculate maintainability index (simplified version)."""
        try:
            # Simplified maintainability index calculation
            # Based on: MI = 171 - 5.2 * ln(aveV) - 0.23 * aveC - 16.2 * ln(aveLOC)
            # Where aveV = average Halstead volume, aveC = average cyclomatic complexity, aveLOC = average lines of code
            
            loc = metrics['lines_of_code']
            complexity = metrics['cyclomatic_complexity']
            functions = metrics['function_count']
            
            if functions == 0:
                return 100.0
            
            ave_complexity = complexity / functions
            ave_loc = loc / functions if functions > 0 else loc
            
            # Simplified calculation (without Halstead volume)
            mi = 171 - 0.23 * ave_complexity - 16.2 * (ave_loc ** 0.5)
            
            # Ensure MI is between 0 and 100
            return max(0, min(100, mi))
            
        except (ValueError, ZeroDivisionError):
            return 50.0  # Default value
    
    def _count_duplicate_lines(self, content: str) -> int:
        """Count duplicate lines in the content (simplified)."""
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith('#')]
        
        line_counts = {}
        for line in lines:
            line_counts[line] = line_counts.get(line, 0) + 1
        
        duplicates = sum(count - 1 for count in line_counts.values() if count > 1)
        return duplicates
    
    def _analyze_step_metrics(self, file_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze metrics for pipeline steps."""
        step_metrics = {}
        
        for filename, metrics in file_metrics.items():
            if filename.startswith('step') and filename.endswith('.py'):
                step_name = filename.replace('.py', '')
                step_metrics[step_name] = {
                    'complexity': metrics.get('cyclomatic_complexity', 0),
                    'lines_of_code': metrics.get('lines_of_code', 0),
                    'functions': metrics.get('function_count', 0),
                    'classes': metrics.get('class_count', 0),
                    'maintainability': metrics.get('maintainability_index', 0),
                    'max_function_complexity': metrics.get('max_function_complexity', 0),
                    'comment_ratio': metrics.get('comment_ratio', 0)
                }
        
        return step_metrics
    
    def _calculate_complexity_distribution(self, file_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate complexity distribution across files."""
        complexities = [metrics.get('cyclomatic_complexity', 0) for metrics in file_metrics.values()]
        
        if not complexities:
            return {}
        
        complexities.sort()
        n = len(complexities)
        
        return {
            'min': min(complexities),
            'max': max(complexities),
            'mean': sum(complexities) / n,
            'median': complexities[n // 2],
            'q1': complexities[n // 4],
            'q3': complexities[3 * n // 4],
            'high_complexity_files': len([c for c in complexities if c > 20]),
            'very_high_complexity_files': len([c for c in complexities if c > 50])
        }
    
    def _generate_recommendations(self, file_metrics: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on complexity analysis."""
        recommendations = []
        
        # Check for high complexity files
        high_complexity_files = [
            (filename, metrics.get('cyclomatic_complexity', 0))
            for filename, metrics in file_metrics.items()
            if metrics.get('cyclomatic_complexity', 0) > 20
        ]
        
        if high_complexity_files:
            recommendations.append(
                f"Consider refactoring {len(high_complexity_files)} files with high complexity: "
                f"{', '.join([f'{f} ({c})' for f, c in high_complexity_files[:5]])}"
            )
        
        # Check for low maintainability
        low_maintainability_files = [
            (filename, metrics.get('maintainability_index', 100))
            for filename, metrics in file_metrics.items()
            if metrics.get('maintainability_index', 100) < 30
        ]
        
        if low_maintainability_files:
            recommendations.append(
                f"Improve maintainability for {len(low_maintainability_files)} files: "
                f"{', '.join([f'{f} ({m:.1f})' for f, m in low_maintainability_files[:5]])}"
            )
        
        # Check for long functions
        long_function_files = [
            (filename, metrics.get('longest_function', 0))
            for filename, metrics in file_metrics.items()
            if metrics.get('longest_function', 0) > 100
        ]
        
        if long_function_files:
            recommendations.append(
                f"Break down long functions in {len(long_function_files)} files: "
                f"{', '.join([f'{f} ({l} lines)' for f, l in long_function_files[:5]])}"
            )
        
        # Check for low comment ratio
        low_comment_files = [
            (filename, metrics.get('comment_ratio', 0))
            for filename, metrics in file_metrics.items()
            if metrics.get('comment_ratio', 0) < 0.1
        ]
        
        if low_comment_files:
            recommendations.append(
                f"Add more comments to {len(low_comment_files)} files: "
                f"{', '.join([f'{f} ({r:.1%})' for f, r in low_comment_files[:5]])}"
            )
        
        return recommendations
    
    def run_radon_analysis(self) -> Dict[str, Any]:
        """Run radon complexity analysis if available."""
        try:
            # Check if radon is available
            result = subprocess.run(['radon', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return {'error': 'radon not available'}
            
            # Run radon analysis
            result = subprocess.run(
                ['radon', 'cc', '-a', '-j', str(self.src_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {'error': f'radon analysis failed: {result.stderr}'}
                
        except FileNotFoundError:
            return {'error': 'radon not installed'}
        except Exception as e:
            return {'error': f'Error running radon: {str(e)}'}
    
    def run_pylint_analysis(self) -> Dict[str, Any]:
        """Run pylint analysis if available."""
        try:
            # Run pylint on the src directory
            result = subprocess.run(
                ['pylint', '--output-format=json', str(self.src_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode in [0, 4, 8, 16]:  # Valid pylint exit codes
                return json.loads(result.stdout)
            else:
                return {'error': f'pylint analysis failed: {result.stderr}'}
                
        except FileNotFoundError:
            return {'error': 'pylint not installed'}
        except Exception as e:
            return {'error': f'Error running pylint: {str(e)}'}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze code complexity")
    parser.add_argument("--src-dir", default="src", help="Source directory to analyze")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--include-radon", action="store_true", help="Include radon analysis")
    parser.add_argument("--include-pylint", action="store_true", help="Include pylint analysis")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize analyzer
    analyzer = ComplexityAnalyzer(src_dir=args.src_dir)
    
    # Run analysis
    results = analyzer.analyze_codebase()
    
    # Add additional analyses if requested
    if args.include_radon:
        results['radon_analysis'] = analyzer.run_radon_analysis()
    
    if args.include_pylint:
        results['pylint_analysis'] = analyzer.run_pylint_analysis()
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2, default=str))






