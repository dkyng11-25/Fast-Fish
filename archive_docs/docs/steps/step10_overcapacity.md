# Step 10: Overcapacity Rule

## Overview
This step implements the Smart Overcapacity Rule analysis, identifying stores with excess inventory capacity and optimizing stock levels.

## Functionality

### Key Features
1. Capacity Analysis
   - Calculates store capacity
   - Identifies overcapacity
   - Evaluates utilization

2. Rule Implementation
   - Applies capacity thresholds
   - Generates optimization recommendations
   - Prioritizes adjustments

## Input Requirements
- Store sales data from Step 1
- Capacity configuration
- Threshold parameters

## Output Files
1. Overcapacity Analysis
   - Location: output/overcapacity_analysis.csv
   - Contains: Overcapacity stores
   - Format: CSV with columns: str_code, category, current_capacity, optimal_capacity

2. Capacity Analysis
   - Location: output/capacity_analysis.csv
   - Contains: Capacity statistics
   - Format: CSV with capacity metrics

## Configuration
- Capacity thresholds
- Optimization criteria
- Adjustment parameters

## Error Handling
1. Analysis Issues
   - Invalid capacities
   - Missing data
   - Calculation errors

2. Rule Application
   - Threshold violations
   - Inconsistent data
   - Format issues

## Performance Considerations
- Efficient capacity calculation
- Memory optimization
- Progress tracking

## Dependencies
- pandas
- numpy
- typing

## Usage
python src/step10_smart_overcapacity_rule.py

## Troubleshooting
1. Analysis Problems
   - Check capacity calculations
   - Verify thresholds
   - Review utilization

2. Data Quality
   - Validate capacities
   - Check utilization data
   - Review recommendations