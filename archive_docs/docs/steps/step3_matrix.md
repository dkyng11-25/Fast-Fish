# Step 3: Matrix Preparation

## Overview
This step prepares the normalized matrix for clustering analysis by processing store-subcategory sales data and applying necessary transformations.

## Functionality

### Key Features
1. Data Normalization
   - Standardizes sales data across stores
   - Handles missing values and outliers
   - Applies appropriate scaling methods

2. Matrix Construction
   - Creates store-subcategory matrix
   - Ensures data completeness
   - Optimizes matrix structure

## Input Requirements
- Store sales data from Step 1
- Category configuration data

## Output Files
1. Normalized Matrix
   - Location: data/normalized_matrix.csv
   - Contains: Normalized store-subcategory relationships
   - Format: CSV matrix with stores as rows and subcategories as columns

2. Original Matrix
   - Location: data/store_subcategory_matrix.csv
   - Contains: Raw store-subcategory relationships
   - Format: CSV matrix with original values

## Configuration
- Normalization method: Z-score standardization
- Missing value handling: Zero-filling
- Matrix format: Dense matrix with store codes as index

## Error Handling
1. Data Processing
   - Missing values
   - Invalid sales data
   - Inconsistent categories

2. Matrix Operations
   - Dimension mismatches
   - Memory constraints
   - Numerical stability

## Performance Considerations
- Efficient matrix operations
- Memory-optimized data structures
- Progress tracking for large matrices

## Dependencies
- pandas
- numpy
- scipy
- typing

## Usage
python src/step3_prepare_matrix.py

## Troubleshooting
1. Matrix Issues
   - Check matrix dimensions
   - Verify data completeness
   - Review normalization results

2. Performance
   - Monitor memory usage
   - Check processing time
   - Review matrix sparsity