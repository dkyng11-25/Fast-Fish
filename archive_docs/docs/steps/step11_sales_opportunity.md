# Step 11: Sales Opportunity Rule

## Overview
This step implements the Missed Sales Opportunity Rule analysis, identifying potential sales opportunities based on market conditions and store performance.

## Functionality

### Key Features
1. Opportunity Analysis
   - Calculates potential sales
   - Identifies missed opportunities
   - Evaluates market conditions

2. Rule Implementation
   - Applies opportunity thresholds
   - Generates growth recommendations
   - Prioritizes actions

## Input Requirements
- Store sales data from Step 1
- Market condition data
- Opportunity parameters

## Output Files
1. Opportunity Analysis
   - Location: output/opportunity_analysis.csv
   - Contains: Sales opportunities
   - Format: CSV with columns: str_code, category, potential_sales, missed_opportunity

2. Market Analysis
   - Location: output/market_analysis.csv
   - Contains: Market condition statistics
   - Format: CSV with market metrics

## Configuration
- Opportunity thresholds
- Market criteria
- Action parameters

## Error Handling
1. Analysis Issues
   - Invalid opportunities
   - Missing data
   - Calculation errors

2. Rule Application
   - Threshold violations
   - Inconsistent data
   - Format issues

## Performance Considerations
- Efficient opportunity calculation
- Memory optimization
- Progress tracking

## Dependencies
- pandas
- numpy
- typing

## Usage
python src/step11_missed_sales_opportunity_rule.py

## Troubleshooting
1. Analysis Problems
   - Check opportunity calculations
   - Verify thresholds
   - Review market conditions

2. Data Quality
   - Validate opportunities
   - Check market data
   - Review recommendations