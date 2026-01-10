# Data Management Strategy

## Overview
This repository uses Git LFS (Large File Storage) to handle large CSV files while keeping the repository manageable.

## Large Files Included
The following large files (>10MB) are tracked with Git LFS:

### API Data Files (data/api_data/)
- `store_config_*.csv` - Store configuration data (35-54MB each)
- `complete_spu_sales_*.csv` - SPU sales data (13-52MB each)  
- `complete_category_sales_*.csv` - Category sales data (13-30MB each)

### Core Data Files
- `data/spu_store_mapping.csv` - SPU-store mapping (26MB)
- `data/normalized_spu_limited_matrix.csv` - Normalized matrix (16MB)

### Output Files
- `output/complete_category_sales_*.csv` - Processed category sales (16-19MB each)
- `output/store_config_*.csv` - Processed store configs (34-36MB each)
- `output/complete_spu_sales_*.csv` - Processed SPU sales (34MB each)

## Files Excluded
- Temporary/processed data files
- Large model files (*.pickle, *.pkl)
- Log files and temporary outputs
- Sensitive configuration files

## Total Repository Size
- Data files: ~1.9GB
- Output files: ~1.8GB
- Total: ~3.7GB

## Benefits of This Approach
1. **Preserves all API data** - Complete dataset available for analysis
2. **Manages repository size** - LFS handles large files efficiently
3. **Maintains functionality** - All pipeline inputs/outputs included
4. **Enables collaboration** - Others can clone and run the system

## For Contributors
- Install Git LFS: `git lfs install`
- Large files will be automatically handled
- Clone with: `git lfs clone <repository-url>`

## Alternative: Data-Only Repository
If the main repository becomes too large, consider:
1. Creating a separate `data-only` repository
2. Using data versioning tools (DVC, Git LFS)
3. Hosting data on cloud storage (AWS S3, Google Cloud)
