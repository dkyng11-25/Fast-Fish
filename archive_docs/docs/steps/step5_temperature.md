# Step 5: Temperature Analysis

## Overview
This step calculates the feels-like temperature for each store location, combining temperature, humidity, and wind speed data to create a more accurate representation of weather impact.

## Functionality

### Key Features
1. Temperature Calculation
   - Computes feels-like temperature
   - Handles multiple weather parameters
   - Applies appropriate formulas

2. Data Processing
   - Validates input parameters
   - Handles missing data
   - Ensures calculation accuracy

## Input Requirements
- Weather data from Step 4
- Temperature calculation parameters

## Output Files
1. Feels-like Temperature Data
   - Location: data/feels_like_temperature.csv
   - Contains: Calculated feels-like temperatures
   - Format: CSV with columns: str_code, date, feels_like_temp

2. Temperature Analysis
   - Location: data/temperature_analysis.csv
   - Contains: Detailed temperature metrics
   - Format: CSV with temperature statistics

## Configuration
- Temperature calculation formula
- Parameter thresholds
- Data validation rules

## Error Handling
1. Calculation Issues
   - Invalid input parameters
   - Missing weather data
   - Calculation errors

2. Data Validation
   - Out-of-range values
   - Inconsistent data
   - Format issues

## Performance Considerations
- Efficient calculations
- Memory-optimized processing
- Progress tracking

## Dependencies
- pandas
- numpy
- scipy
- typing

## Usage
python src/step5_calculate_feels_like_temperature.py

## Troubleshooting
1. Calculation Problems
   - Check input parameters
   - Verify calculation formula
   - Review temperature ranges

2. Data Quality
   - Validate weather data
   - Check calculation results
   - Review temperature distribution