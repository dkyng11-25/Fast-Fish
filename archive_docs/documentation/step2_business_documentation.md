# Step 2: Extract Store Coordinates and Create SPU Mappings

## 1. Identification

**Name / Path:** `/src/step2_extract_coordinates.py`

**Component:** Data Preparation

**Owner:** Data Engineering Team

**Last Updated:** 2025-07-20

## 2. Purpose & Business Value

Extracts geographic coordinates for all retail stores and creates comprehensive SPU (Stock Keeping Unit) mappings from multi-period data. This step enables spatial analysis and ensures complete product coverage for downstream optimization. The system intelligently scans multiple periods to maximize store and product coverage, creating robust mappings for both current and historical analysis.

## 3. Inputs

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| Store Sales Data | CSV Files | Sales data with store coordinates from multiple periods | Output of Step 1 (API data) |
| Category Sales Data | CSV Files | Category-level sales data from multiple periods | Output of Step 1 (API data) |
| SPU Sales Data | CSV Files | SPU-level sales data from multiple periods | Output of Step 1 (API data) |
| Store Codes | List[str] | Unique identifiers for all retail stores | `data/store_codes.csv` |

## 4. Transformation Overview

The script performs comprehensive data extraction and mapping with the following key processes:

1. **Multi-Period Scanning**: Scans all available periods (current and historical) to find the most complete coordinate data
2. **Coordinate Extraction**: Parses geographic coordinates from the "long_lat" field in store sales data
3. **SPU Mapping Creation**: Creates comprehensive SPU-to-store mappings across all periods
4. **SPU Metadata Generation**: Aggregates sales statistics and category information for each SPU
5. **Data Validation**: Ensures coordinate coverage for all stores with sales data
6. **Fallback Handling**: Provides default coordinates when geographic data is missing

## 5. Outputs & Consumers

**Format / Schema:** CSV files with the following outputs:
- `data/store_coordinates_extended.csv` - Store coordinates with latitude/longitude
- `data/spu_store_mapping.csv` - Comprehensive SPU-to-store mappings
- `data/spu_metadata.csv` - SPU metadata with sales statistics and category information

**Primary Consumers:** Steps 3 (Prepare Matrix), 6 (Clustering), and all business rule steps

**Business Use:** Enables spatial clustering, distance-based analysis, and complete product coverage for optimization recommendations

## 6. Success Metrics & KPIs

- Store coordinate coverage ≥ 95% of stores with sales data
- SPU mapping completeness ≥ 99% of unique SPU-store combinations
- Metadata quality with comprehensive sales statistics
- Execution time ≤ 5 minutes for 2,000+ stores
- Zero missing store codes in final mappings

## 7. Performance & Cost Notes

- Processes multi-period data efficiently with minimal memory overhead
- Uses optimized pandas operations for data aggregation
- Implements progress tracking for large datasets
- Handles up to 12 periods of historical data
- Memory-efficient processing with chunked data handling

## 8. Dependencies & Risks

**Upstream Data / Services:**
- Step 1 output files (store sales, category sales, SPU sales)
- `data/store_codes.csv` file

**External Libraries / APIs:**
- pandas, tqdm

**Risk Mitigation:**
- Fallback to default coordinates when geographic data is missing
- Comprehensive error handling and logging
- Data validation with coverage reporting
- Graceful degradation when some periods are missing

## 9. Pipeline Integration

**Upstream Step(s):** Step 1 (Download API Data)

**Downstream Step(s):** Step 3 (Prepare Matrix)

**Failure Impact:** Blocks spatial analysis and distance-based clustering; affects SPU-level optimization rules

## 10. Future Improvements

- Add support for external geocoding services for missing coordinates
- Implement coordinate validation with map boundary checks
- Enhance SPU metadata with seasonal trend analysis
- Add data quality scoring for coordinate accuracy
- Support for real-time coordinate updates
- Integration with external store attribute databases
- Enhanced progress tracking with detailed statistics
