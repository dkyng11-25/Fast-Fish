# Step 15: Interactive Map

## Overview
This step creates an interactive map visualization that displays store locations, clusters, and performance metrics, enabling geographical analysis of the results.

## Functionality

### Key Features
1. Map Creation
   - Generates interactive map
   - Displays store locations
   - Shows cluster boundaries

2. Data Visualization
   - Store markers
   - Cluster regions
   - Performance indicators

## Input Requirements
- Store coordinates from Step 2
- Clustering results from Step 6
- Performance data from Step 13

## Output Files
1. Interactive Map
   - Location: output/interactive_map.html
   - Contains: Interactive map visualization
   - Format: HTML with embedded map

2. Map Assets
   - Location: output/map_assets/
   - Contains: Supporting files
   - Format: Various (CSS, JS, images)

## Configuration
- Map settings
- Visualization parameters
- Interactive features

## Error Handling
1. Map Issues
   - Coordinate errors
   - Missing data
   - Rendering problems

2. Visualization Issues
   - Marker conflicts
   - Performance issues
   - Browser compatibility

## Performance Considerations
- Efficient rendering
- Asset optimization
- Loading performance

## Dependencies
- folium
- pandas
- numpy
- typing

## Usage
python src/step15_interactive_map_dashboard.py

## Troubleshooting
1. Map Problems
   - Check coordinates
   - Verify markers
   - Review rendering

2. Visualization Issues
   - Validate layers
   - Check performance
   - Review compatibility