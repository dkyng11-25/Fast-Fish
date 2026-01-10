#!/usr/bin/env python3
"""
Complexity Analysis Module for Validation System

This module provides easy-to-use complexity analysis tools for the validation system.
It integrates complexipy functionality and provides convenient analysis methods.

Author: Data Pipeline
Date: 2025-01-03
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

try:
    from complexipy import file_complexity
except ImportError:
    print("Warning: complexipy not installed. Install with: pip install complexipy")
    file_complexity = None


@dataclass
class ComplexityResult:
    """Data class for complexity analysis results."""
    file_path: str
    file_name: str
    overall_complexity: int
    function_count: int
    functions: List[Dict]
    file_size: int
    needs_refactoring: bool = False


class ValidationComplexityAnalyzer:
    """Complexity analyzer specifically for the validation system."""
    
    def __init__(self, validation_root: str = None):
        """
        Initialize the complexity analyzer.
        
        Args:
            validation_root: Root directory of the validation system (defaults to current directory)
        """
        if validation_root is None:
            # Default to current directory if no path specified
            self.validation_root = Path.cwd()
        else:
            self.validation_root = Path(validation_root)
        self.complexity_threshold = 20  # Files above this need refactoring
        
    def analyze_file(self, file_path: str) -> Optional[ComplexityResult]:
        """
        Analyze complexity of a single file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            ComplexityResult or None if analysis fails
        """
        if file_complexity is None:
            print("complexipy not available for analysis")
            return None
            
        try:
            complexity = file_complexity(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Extract function information
            functions = []
            for func in complexity.functions:
                functions.append({
                    'name': func.name,
                    'complexity': func.complexity,
                    'line_number': getattr(func, 'line_number', 'unknown')
                })
            
            result = ComplexityResult(
                file_path=file_path,
                file_name=complexity.file_name,
                overall_complexity=complexity.complexity,
                function_count=len(complexity.functions),
                functions=functions,
                file_size=file_size,
                needs_refactoring=complexity.complexity > self.complexity_threshold
            )
            
            return result
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def analyze_directory(self, directory: str = None) -> List[ComplexityResult]:
        """
        Analyze all Python files in a directory.
        
        Args:
            directory: Directory to analyze (defaults to validation_root)
            
        Returns:
            List of ComplexityResult objects
        """
        if directory is None:
            directory = self.validation_root
        else:
            directory = Path(directory)
            
        results = []
        
        # Find all Python files
        for py_file in directory.rglob("*.py"):
            result = self.analyze_file(str(py_file))
            if result:
                results.append(result)
        
        return results
    
    def get_refactoring_candidates(self, directory: str = None) -> List[ComplexityResult]:
        """
        Get files that need refactoring based on complexity threshold.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            List of files that need refactoring
        """
        all_results = self.analyze_directory(directory)
        return [r for r in all_results if r.needs_refactoring]
    
    def print_summary(self, results: List[ComplexityResult]):
        """
        Print a summary of complexity analysis results.
        
        Args:
            results: List of ComplexityResult objects
        """
        if not results:
            print("No files analyzed.")
            return
            
        print(f"\n{'='*80}")
        print(f"COMPLEXITY ANALYSIS SUMMARY")
        print(f"{'='*80}")
        print(f"Total files analyzed: {len(results)}")
        print(f"Complexity threshold: {self.complexity_threshold}")
        
        # Sort by complexity (highest first)
        sorted_results = sorted(results, key=lambda x: x.overall_complexity, reverse=True)
        
        # Files needing refactoring
        refactoring_candidates = [r for r in sorted_results if r.needs_refactoring]
        print(f"Files needing refactoring: {len(refactoring_candidates)}")
        
        if refactoring_candidates:
            print(f"\n{'='*50}")
            print("REFACTORING CANDIDATES (Complexity > {})".format(self.complexity_threshold))
            print(f"{'='*50}")
            for result in refactoring_candidates:
                # Convert absolute path to relative path
                try:
                    rel_path = os.path.relpath(result.file_path, start=os.getcwd())
                except ValueError:
                    rel_path = result.file_path
                print(f"📁 {result.file_name}")
                print(f"   Path: {rel_path}")
                print(f"   Complexity: {result.overall_complexity}")
                print(f"   Functions: {result.function_count}")
                print(f"   Size: {result.file_size:,} bytes")
                print()
        
        # Top 10 most complex files
        print(f"\n{'='*50}")
        print("TOP 10 MOST COMPLEX FILES")
        print(f"{'='*50}")
        for i, result in enumerate(sorted_results[:10], 1):
            status = "🔴 NEEDS REFACTORING" if result.needs_refactoring else "✅ OK"
            print(f"{i:2d}. {result.file_name:<40} {result.overall_complexity:3d} {status}")
    
    def print_detailed_analysis(self, file_path: str):
        """
        Print detailed analysis for a specific file.
        
        Args:
            file_path: Path to the file to analyze
        """
        result = self.analyze_file(file_path)
        if not result:
            print(f"Could not analyze {file_path}")
            return
            
        # Convert absolute path to relative path
        try:
            rel_path = os.path.relpath(result.file_path, start=os.getcwd())
        except ValueError:
            rel_path = result.file_path
            
        print(f"\n{'='*60}")
        print(f"DETAILED ANALYSIS: {result.file_name}")
        print(f"{'='*60}")
        print(f"File Path: {rel_path}")
        print(f"Overall Complexity: {result.overall_complexity}")
        print(f"Function Count: {result.function_count}")
        print(f"File Size: {result.file_size:,} bytes")
        print(f"Needs Refactoring: {'Yes' if result.needs_refactoring else 'No'}")
        
        if result.functions:
            print(f"\nFunction Details:")
            print(f"{'Function Name':<30} {'Complexity':<10} {'Line':<8}")
            print(f"{'-'*50}")
            for func in result.functions:
                print(f"{func['name']:<30} {func['complexity']:<10} {func['line_number']:<8}")
    
    def analyze_validation_system(self):
        """
        Analyze the entire validation system and provide recommendations.
        """
        print("🔍 Analyzing Validation System Complexity...")
        
        results = self.analyze_directory()
        self.print_summary(results)
        
        # Provide recommendations
        refactoring_candidates = self.get_refactoring_candidates()
        
        if refactoring_candidates:
            print(f"\n{'='*50}")
            print("REFACTORING RECOMMENDATIONS")
            print(f"{'='*50}")
            print("The following files should be considered for refactoring:")
            print()
            
            for result in refactoring_candidates:
                print(f"📁 {result.file_name}")
                print(f"   Current complexity: {result.overall_complexity}")
                print(f"   Target complexity: < {self.complexity_threshold}")
                print(f"   Suggested actions:")
                print(f"   - Split into smaller, focused modules")
                print(f"   - Extract complex functions into separate files")
                print(f"   - Reduce nested conditions and loops")
                print()
        else:
            print(f"\n✅ All files are within acceptable complexity limits!")
            if results:
                print(f"   Maximum complexity found: {max(r.overall_complexity for r in results)}")
            else:
                print(f"   No Python files found to analyze")
            print(f"   Threshold: {self.complexity_threshold}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze complexity of validation system")
    parser.add_argument("--file", help="Analyze specific file")
    parser.add_argument("--directory", help="Analyze specific directory")
    parser.add_argument("--threshold", type=int, default=20, help="Complexity threshold")
    parser.add_argument("--detailed", action="store_true", help="Show detailed analysis")
    
    args = parser.parse_args()
    
    analyzer = ValidationComplexityAnalyzer()
    analyzer.complexity_threshold = args.threshold
    
    if args.file:
        if args.detailed:
            analyzer.print_detailed_analysis(args.file)
        else:
            result = analyzer.analyze_file(args.file)
            if result:
                print(f"File: {result.file_name}")
                print(f"Complexity: {result.overall_complexity}")
                print(f"Functions: {result.function_count}")
                print(f"Needs refactoring: {result.needs_refactoring}")
    elif args.directory:
        results = analyzer.analyze_directory(args.directory)
        analyzer.print_summary(results)
    else:
        analyzer.analyze_validation_system()


if __name__ == "__main__":
    main()
