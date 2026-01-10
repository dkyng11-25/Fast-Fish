# Step 12: Sales Performance Rule

## Overview
This step implements the Sales Performance Rule analysis, evaluating store performance against benchmarks and identifying areas for improvement.

## Functionality

### Key Features
1. Performance Analysis
   - Calculates performance metrics
   - Identifies underperforming areas
   - Evaluates against benchmarks

2. Rule Implementation
   - Applies performance thresholds
   - Generates improvement recommendations
   - Prioritizes actions

## Input Requirements
- Store sales data from Step 1
- Performance benchmarks
- Evaluation parameters

## Output Files
1. Performance Analysis
   - Location: output/performance_analysis.csv
   - Contains: Store performance metrics
   - Format: CSV with columns: str_code, category, performance_score, benchmark

2. Benchmark Analysis
   - Location: output/benchmark_analysis.csv
   - Contains: Benchmark statistics
   - Format: CSV with benchmark metrics

## Configuration
- Performance thresholds
- Benchmark criteria
- Action parameters

## Error Handling
1. Analysis Issues
   - Invalid performance metrics
   - Missing data
   - Calculation errors

2. Rule Application
   - Threshold violations
   - Inconsistent data
   - Format issues

## Performance Considerations
- Efficient metric calculation
- Memory optimization
- Progress tracking

## Dependencies
- pandas
- numpy
- typing

## Usage
python src/step12_sales_performance_rule.py

## Troubleshooting
1. Analysis Problems
   - Check performance calculations
   - Verify benchmarks
   - Review metrics

2. Data Quality
   - Validate performance data
   - Check benchmarks
   - Review recommendations