#!/usr/bin/env python3
"""
Simple CLI script for analyzing validation system complexity.

Usage:
    python analyze_complexity.py                    # Analyze entire system
    python analyze_complexity.py --file path/to/file.py  # Analyze specific file
    python analyze_complexity.py --threshold 15     # Set custom threshold
"""

import sys
from pathlib import Path

# Add the validation directory to the path
validation_dir = Path(__file__).parent
sys.path.insert(0, str(validation_dir))

from complexity_analyzer import ValidationComplexityAnalyzer


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze complexity of validation system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_complexity.py                    # Analyze entire system
  python analyze_complexity.py --file schemas/weather_schemas.py
  python analyze_complexity.py --threshold 15     # Custom threshold
  python analyze_complexity.py --detailed         # Show detailed analysis
        """
    )
    
    parser.add_argument(
        "--file", 
        help="Analyze specific file"
    )
    parser.add_argument(
        "--directory", 
        help="Analyze specific directory"
    )
    parser.add_argument(
        "--threshold", 
        type=int, 
        default=20, 
        help="Complexity threshold (default: 20)"
    )
    parser.add_argument(
        "--detailed", 
        action="store_true", 
        help="Show detailed analysis"
    )
    parser.add_argument(
        "--candidates-only", 
        action="store_true", 
        help="Show only refactoring candidates"
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = ValidationComplexityAnalyzer()
    analyzer.complexity_threshold = args.threshold
    
    print(f"🔍 Validation System Complexity Analyzer")
    print(f"📊 Threshold: {args.threshold}")
    print(f"📁 Root: {analyzer.validation_root}")
    print()
    
    if args.file:
        # Analyze specific file
        if args.detailed:
            analyzer.print_detailed_analysis(args.file)
        else:
            result = analyzer.analyze_file(args.file)
            if result:
                status = "🔴 NEEDS REFACTORING" if result.needs_refactoring else "✅ OK"
                print(f"File: {result.file_name}")
                print(f"Complexity: {result.overall_complexity} {status}")
                print(f"Functions: {result.function_count}")
                print(f"Size: {result.file_size:,} bytes")
                
    elif args.directory:
        # Analyze specific directory
        results = analyzer.analyze_directory(args.directory)
        if args.candidates_only:
            candidates = [r for r in results if r.needs_refactoring]
            if candidates:
                print("REFACTORING CANDIDATES:")
                for result in candidates:
                    print(f"  📁 {result.file_name} (complexity: {result.overall_complexity})")
            else:
                print("✅ No refactoring candidates found!")
        else:
            analyzer.print_summary(results)
            
    else:
        # Analyze entire system
        if args.candidates_only:
            candidates = analyzer.get_refactoring_candidates()
            if candidates:
                print("REFACTORING CANDIDATES:")
                for result in candidates:
                    print(f"  📁 {result.file_name} (complexity: {result.overall_complexity})")
            else:
                print("✅ No refactoring candidates found!")
        else:
            analyzer.analyze_validation_system()


if __name__ == "__main__":
    main()

