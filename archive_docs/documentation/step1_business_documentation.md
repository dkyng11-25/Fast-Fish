# Step 1: Download API Data

## 1. Identification

**Name / Path:** `/src/step1_download_api_data.py`

**Component:** Data Ingestion

**Owner:** Data Engineering Team

**Last Updated:** 2025-08-06

## 2. Purpose & Business Value

Downloads store configuration and sales data from the FastFish API for retail product mix optimization analysis. This step automates what was previously a manual 4-hour data collection process and ensures data consistency across all pipeline steps. The system intelligently handles partial downloads, retries failed requests, and validates data completeness to ensure reliable downstream processing.

## 3. Inputs

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| Store Codes | List[str] | Unique identifiers for all retail stores to analyze | `data/store_codes.csv` |
| API Endpoints | URLs | FastFish API endpoints for store configuration and sales data | FastFish API (https://fdapidb.fastfish.com:8089/api/sale) |
| Target Period | String | Analysis period in YYYYMM format with optional A/B indicator | Configuration parameters |
| Batch Size | Integer | Number of stores to process per API call (default: 10) | Configuration parameter |

## 4. Transformation Overview

The script performs intelligent data collection with the following key processes:

1. **Smart Downloading**: Checks existing data and only downloads missing stores/periods
2. **Batch Processing**: Processes stores in configurable batches to optimize API performance
3. **Error Handling**: Implements retry logic with exponential backoff for failed requests
4. **Data Validation**: Validates completeness and creates detailed error reports
5. **Recovery Support**: Handles interrupted downloads by consolidating partial files
6. **Multi-Period Support**: Can download current and historical data for seasonal analysis
7. **Real Quantity Calculation**: Converts sales amounts to realistic quantities using category-based unit price estimation

## 5. Outputs & Consumers

**Format / Schema:** CSV files with the following outputs:
- `store_config_{period}.csv` - Store configuration data
- `store_sales_{period}.csv` - Raw store sales data
- `complete_category_sales_{period}.csv` - Category-level aggregated sales
- `complete_spu_sales_{period}.csv` - SPU (Stock Keeping Unit)-level sales with real quantities

**Primary Consumers:** Steps 2-3 in the pipeline, clustering analysis, business rules engine

**Business Use:** Provides the foundational data for all downstream retail optimization analysis, enabling accurate demand forecasting and inventory recommendations

## 6. Success Metrics & KPIs

- Data completeness ≥ 95% of expected stores
- Runtime ≤ 30 minutes for 2,000+ stores
- Zero synthetic/fake data (no $1.00 unit prices)
- Recovery success rate ≥ 90% for interrupted downloads
- API error rate ≤ 5%

## 7. Performance & Cost Notes

- Processes 2,000+ stores in approximately 15-30 minutes
- Implements rate limiting to prevent API throttling
- Memory-efficient batch processing with intermediate file saving
- Supports parallel processing through batch distribution
- Minimal external dependencies (only requires requests, pandas, tqdm)

## 8. Dependencies & Risks

**Upstream Data / Services:**
- FastFish API availability and authentication
- `data/store_codes.csv` file with valid store identifiers

**External Libraries / APIs:**
- requests, pandas, tqdm, urllib3
- FastFish API endpoints (requires network connectivity)

**Risk Mitigation:**
- Retry logic with exponential backoff for API failures
- Partial download recovery mechanism
- Smart incremental downloading to avoid reprocessing
- Detailed error logging and validation reports
- Graceful degradation for missing data

## 9. Pipeline Integration

**Upstream Step(s):** None (starting point of pipeline)

**Downstream Step(s):** Steps 2 (Extract Coordinates) and 3 (Prepare Matrix)

**Failure Impact:** Complete pipeline halt; no downstream analysis possible without foundational data

## 10. Future Improvements

- Implement parallel processing for faster downloads
- Add support for additional API endpoints
- Enhance data validation with business rule checks
- Implement real-time progress tracking dashboard
- Add data quality scoring and anomaly detection
- Support for incremental data updates
- Enhanced retry strategies with intelligent backoff
- Integration with data lineage tracking system
