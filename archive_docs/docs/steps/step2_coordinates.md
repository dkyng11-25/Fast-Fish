# Step 2: Coordinate Extraction

## Overview
This step extracts and processes geographical coordinates for each store location, preparing the data for weather integration and spatial analysis.

## Functionality

### Key Features
1. Coordinate Processing
   - Extracts latitude and longitude from store data
   - Validates coordinate format and range
   - Handles missing or invalid coordinates

2. Data Validation
   - Ensures coordinates are within valid ranges
   - Checks for duplicate store locations
   - Validates coordinate precision

## Input Requirements
- Store configuration data from Step 1
- Store location data with coordinates

## Output Files
1. Store Coordinates
   - Location: data/store_coordinates_extended.csv
   - Contains: Store codes and their geographical coordinates
   - Format: CSV with columns: str_code, latitude, longitude

## Configuration
- Coordinate precision: 6 decimal places
- Valid latitude range: -90 to 90
- Valid longitude range: -180 to 180

## Error Handling
1. Coordinate Validation
   - Invalid coordinate formats
   - Out-of-range values
   - Missing coordinates

2. Data Processing
   - Duplicate store entries
   - Inconsistent coordinate formats
   - Missing store codes

## Performance Considerations
- Efficient coordinate validation
- Memory-optimized data processing
- Progress tracking for large datasets

## Dependencies
- pandas
- numpy
- typing

## Usage
python src/step2_extract_coordinates.py

## Troubleshooting
1. Coordinate Issues
   - Check coordinate format
   - Verify coordinate ranges
   - Review store location data

2. Data Quality
   - Validate store codes
   - Check for duplicates
   - Review coordinate precision