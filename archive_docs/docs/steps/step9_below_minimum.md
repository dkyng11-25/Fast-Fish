# Step 9: Below Minimum Rule

## Overview
This step implements the Below Minimum Rule analysis, identifying stores with category sales below minimum thresholds.

## Functionality

### Key Features
1. Threshold Analysis
   - Calculates minimum thresholds
   - Identifies below-minimum categories
   - Evaluates performance gaps

2. Rule Implementation
   - Applies minimum thresholds
   - Generates improvement recommendations
   - Prioritizes actions

## Input Requirements
- Store sales data from Step 1
- Category configuration
- Minimum threshold parameters

## Output Files
1. Below Minimum Analysis
   - Location: output/below_minimum_analysis.csv
   - Contains: Below-minimum categories
   - Format: CSV with columns: str_code, category, current_sales, minimum_threshold

2. Threshold Analysis
   - Location: output/threshold_analysis.csv
   - Contains: Threshold statistics
   - Format: CSV with threshold metrics

## Configuration
- Minimum thresholds
- Performance criteria
- Action parameters

## Error Handling
1. Analysis Issues
   - Invalid thresholds
   - Missing data
   - Calculation errors

2. Rule Application
   - Threshold violations
   - Inconsistent data
   - Format issues

## Performance Considerations
- Efficient threshold calculation
- Memory optimization
- Progress tracking

## Dependencies
- pandas
- numpy
- typing

## Usage
python src/step9_below_minimum_rule.py

## Troubleshooting
1. Analysis Problems
   - Check threshold calculations
   - Verify minimums
   - Review performance

2. Data Quality
   - Validate thresholds
   - Check sales data
   - Review recommendations