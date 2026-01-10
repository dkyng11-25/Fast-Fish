# Half-Month API Download Guide

## Overview

The `step1_download_api_data.py` script has been enhanced to support downloading data for specific half-month periods instead of just full months. This allows for more granular analysis and reduces data processing time.

## Key Features

### Period Support
- **First Half (A)**: Downloads data for the first half of the month (typically days 1-15)
- **Second Half (B)**: Downloads data for the second half of the month (typically days 16-31)
- **Full Month**: Downloads data for the entire month (original behavior)

### API Integration
The script now supports the `mm_type` field in the FastFish API responses:
- `5A` = May, first half
- `5B` = May, second half
- `5` = May, full month

### File Naming Convention
Output files now include period indicators:
- `complete_category_sales_202505A.csv` (first half of May 2025)
- `complete_category_sales_202505B.csv` (second half of May 2025)
- `complete_category_sales_202505.csv` (full May 2025)

## Usage Examples

### Command Line Interface

```bash
# Download first half of May 2025
python src/step1_download_api_data.py --month 202505 --period A

# Download second half of May 2025
python src/step1_download_api_data.py --month 202505 --period B

# Download full month (original behavior)
python src/step1_download_api_data.py --month 202505 --period full

# List existing data periods
python src/step1_download_api_data.py --list-periods

# Custom batch size for faster processing
python src/step1_download_api_data.py --period A --batch-size 20
```

### Configuration Options

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `--month` | Year-month in YYYYMM format | 202505 | Any valid YYYYMM |
| `--period` | Period to download | A | A, B, full |
| `--batch-size` | Stores per API call | 10 | 1-100 |
| `--list-periods` | List existing data | - | Flag only |

## API Changes

### New Functions

#### `get_period_label(yyyymm: str, period: Optional[str]) -> str`
Generates period-specific labels for file naming.

```python
get_period_label("202505", "A")    # Returns "202505A"
get_period_label("202505", "B")    # Returns "202505B"
get_period_label("202505", None)   # Returns "202505"
```

#### `get_period_description(period: Optional[str]) -> str`
Returns human-readable period descriptions.

```python
get_period_description("A")    # Returns "first half of month"
get_period_description("B")    # Returns "second half of month"
get_period_description(None)   # Returns "full month"
```

### Modified Functions

#### `fetch_store_config()` and `fetch_store_sales()`
Now accept an optional `period` parameter:

```python
# Original
config_df, stores = fetch_store_config(store_codes, "202505")

# Enhanced
config_df, stores = fetch_store_config(store_codes, "202505", "A")  # First half
config_df, stores = fetch_store_config(store_codes, "202505", "B")  # Second half
config_df, stores = fetch_store_config(store_codes, "202505", None) # Full month
```

## Output Files

### File Structure
```
data/api_data/
├── store_config_202505A.csv          # Store configuration (first half)
├── store_sales_202505A.csv           # Store sales data (first half)
├── complete_category_sales_202505A.csv # Category-level sales (first half)
├── complete_spu_sales_202505A.csv    # SPU-level sales (first half)
├── processed_stores_202505A.txt      # Processing tracking (first half)
└── notes/                            # Error logs and debugging info
```

### Data Validation
The script automatically validates that the returned data matches the requested period by checking the `mm_type` field:
- Filters data to ensure only the requested period is included
- Logs warnings if expected period data is not found
- Falls back to using all returned data if filtering fails

## Testing

### Test Script
Run the test script to verify half-month functionality:

```bash
python test_half_month_api.py
```

The test script validates:
- Period helper functions work correctly
- API calls succeed for all period types
- Data filtering by `mm_type` works as expected

### Manual Testing
1. **Test First Half**: `python src/step1_download_api_data.py --period A --batch-size 5`
2. **Test Second Half**: `python src/step1_download_api_data.py --period B --batch-size 5`
3. **Compare Results**: Check that `mm_type` values differ between periods
4. **Verify Files**: Ensure output files have correct period labels

## Integration with Pipeline

### Backward Compatibility
The enhanced script maintains full backward compatibility:
- Default behavior downloads first half of month (period A)
- Existing scripts continue to work without modification
- File naming includes period indicators for clarity

### Pipeline Integration
To use half-month data in the analysis pipeline:

1. **Update Configuration**: Modify `run_pipeline.py` to specify desired period
2. **File References**: Update downstream scripts to use period-specific filenames
3. **Batch Processing**: Consider processing both halves separately for comparison

## Troubleshooting

### Common Issues

#### Empty Data Response
```
Error: Empty data received from config API for first half of month
```
**Solution**: Check if the API supports the requested period for the specified month.

#### Missing mm_type Field
```
Warning: No data found for mm_type=5A, using all data
```
**Solution**: The API may not support half-month periods for this data. The script will use all returned data.

#### File Not Found
```
Error: Could not find store_codes.csv
```
**Solution**: Ensure the store codes file exists in the `data/` directory.

### Debug Mode
Enable debug output by checking the console logs:
- `[DEBUG]` messages show API payloads and processing details
- Error logs are saved to `data/api_data/notes/` directory
- Progress messages include period information

## Performance Considerations

### Benefits of Half-Month Downloads
- **Reduced Data Volume**: ~50% less data per download
- **Faster Processing**: Shorter API response times
- **Granular Analysis**: Better temporal resolution for trends
- **Parallel Processing**: Can download both halves simultaneously

### Optimization Tips
- Use larger batch sizes (10-20) for faster downloads
- Process both halves in parallel using separate terminal sessions
- Monitor API rate limits and adjust delays if needed

## Future Enhancements

### Potential Improvements
1. **Daily Periods**: Support for daily data downloads
2. **Date Range Queries**: Specify exact start/end dates
3. **Automatic Period Detection**: Detect optimal period based on data availability
4. **Parallel Downloads**: Built-in support for concurrent period downloads

### API Evolution
Monitor the FastFish API documentation for:
- New period parameters
- Enhanced `mm_type` values
- Additional temporal granularity options 