# Step 8: Imbalanced Rule

## Overview
This step implements the Imbalanced Rule analysis, identifying stores with imbalanced category distributions using Z-score analysis.

## Functionality

### Key Features
1. Z-Score Analysis
   - Calculates category Z-scores
   - Identifies imbalances
   - Evaluates distribution patterns

2. Rule Implementation
   - Applies Z-score thresholds
   - Generates balance recommendations
   - Prioritizes adjustments

## Input Requirements
- Store sales data from Step 1
- Category configuration
- Z-score parameters

## Output Files
1. Imbalance Analysis
   - Location: output/imbalance_analysis.csv
   - Contains: Store category imbalances
   - Format: CSV with columns: str_code, category, z_score, imbalance_level

2. Z-Score Distribution
   - Location: output/zscore_distribution.csv
   - Contains: Z-score statistics
   - Format: CSV with distribution metrics

## Configuration
- Z-score thresholds
- Imbalance criteria
- Adjustment parameters

## Error Handling
1. Analysis Issues
   - Invalid Z-scores
   - Missing data
   - Calculation errors

2. Rule Application
   - Threshold violations
   - Inconsistent data
   - Format issues

## Performance Considerations
- Efficient Z-score calculation
- Memory optimization
- Progress tracking

## Dependencies
- pandas
- numpy
- scipy
- typing

## Usage
python src/step8_imbalanced_rule.py

## Troubleshooting
1. Analysis Problems
   - Check Z-score calculations
   - Verify thresholds
   - Review imbalances

2. Data Quality
   - Validate distributions
   - Check Z-scores
   - Review recommendations