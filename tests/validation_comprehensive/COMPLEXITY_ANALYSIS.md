# Complexity Analysis Tools

This directory contains integrated complexity analysis tools for the validation system, making it easy to identify files that need refactoring.

## Quick Start

### Analyze Entire System
```bash
# From the validation directory
python analyze_complexity.py

# Or on Windows
analyze_complexity.bat
```

### Analyze Specific File
```bash
python analyze_complexity.py --file schemas/weather_schemas.py
```

### Show Only Refactoring Candidates
```bash
python analyze_complexity.py --candidates-only
```

### Custom Complexity Threshold
```bash
python analyze_complexity.py --threshold 15
```

## Available Tools

### 1. `complexity_analyzer.py`
The main complexity analysis module with the `ValidationComplexityAnalyzer` class.

**Features:**
- Analyze individual files or entire directories
- Configurable complexity threshold
- Detailed function-level analysis
- Refactoring recommendations
- Integration with the validation system

### 2. `analyze_complexity.py`
Simple CLI script for easy command-line usage.

**Usage:**
```bash
python analyze_complexity.py [options]
```

**Options:**
- `--file FILE`: Analyze specific file
- `--directory DIR`: Analyze specific directory
- `--threshold N`: Set complexity threshold (default: 20)
- `--detailed`: Show detailed analysis
- `--candidates-only`: Show only refactoring candidates

### 3. `analyze_complexity.bat`
Windows batch script for easy execution.

## Programmatic Usage

```python
from tests.validation_comprehensive import ValidationComplexityAnalyzer

# Initialize analyzer
analyzer = ValidationComplexityAnalyzer()

# Analyze entire system
analyzer.analyze_validation_system()

# Analyze specific file
result = analyzer.analyze_file("schemas/weather_schemas.py")
print(f"Complexity: {result.overall_complexity}")

# Get refactoring candidates
candidates = analyzer.get_refactoring_candidates()
for candidate in candidates:
    print(f"Refactor: {candidate.file_name}")
```

## Complexity Thresholds

- **0-10**: Excellent - Simple, easy to understand
- **11-20**: Good - Acceptable complexity
- **21-30**: Moderate - Consider refactoring
- **31+**: High - Definitely needs refactoring

## Refactoring Recommendations

When files exceed the complexity threshold, consider:

1. **Split into smaller modules** - Break large files into focused components
2. **Extract functions** - Move complex logic into separate functions
3. **Reduce nesting** - Simplify conditional and loop structures
4. **Use composition** - Combine smaller, simpler components
5. **Apply design patterns** - Use appropriate patterns to reduce complexity

## Integration with Validation System

The complexity analyzer is fully integrated with the validation system:

```python
# Import from main validation package
from tests.validation_comprehensive import ValidationComplexityAnalyzer

# Use in validation workflows
analyzer = ValidationComplexityAnalyzer()
results = analyzer.analyze_directory("schemas/")
```

## Examples

### Check if refactoring is needed
```bash
python analyze_complexity.py --candidates-only
```

### Detailed analysis of a specific file
```bash
python analyze_complexity.py --file schemas/pipeline_schemas.py --detailed
```

### Analyze with custom threshold
```bash
python analyze_complexity.py --threshold 15
```

## Dependencies

- `complexipy`: For complexity analysis
- `pathlib`: For file system operations
- `dataclasses`: For result objects

Install dependencies:
```bash
pip install complexipy
```

