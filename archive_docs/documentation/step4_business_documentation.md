# Step 4: Download Weather Data for Store Locations

## 1. Identification

**Name / Path:** `/src/step4_download_weather_data.py`

**Component:** Data Enrichment

**Owner:** Data Engineering Team

**Last Updated:** 2025-07-21

## 2. Purpose & Business Value

Downloads historical weather data for each store location using geographic coordinates for all 12 year-over-year periods. This step enables weather-aware clustering and business rules by providing environmental context for store performance analysis. The system implements robust VPN switching support to handle API access restrictions and ensures comprehensive data coverage across seasonal variations.

## 3. Inputs

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| Store Coordinates | CSV File | Geographic coordinates (latitude/longitude) for all stores | Output of Step 2 |
| Time Periods | List[Dict] | 12 year-over-year periods (6 current + 6 historical) | Configuration |
| Open-Meteo API | External API | Historical weather data API | Open-Meteo API (archive-api.open-meteo.com) |

## 4. Transformation Overview

The script performs comprehensive weather data collection with the following key processes:

1. **Multi-Period Download**: Collects weather data for 12 year-over-year periods to capture seasonal variations
2. **VPN Switching Support**: Automatically detects API blocking and prompts for VPN location changes
3. **Resume Capability**: Saves progress and can resume interrupted downloads from the last successful point
4. **Rate Limit Management**: Implements intelligent backoff and retry logic for API rate limits
5. **Altitude Collection**: Gathers elevation data for all store locations to enhance weather accuracy
6. **Data Validation**: Ensures complete weather data coverage for each store and period
7. **Failure Handling**: Tracks failed downloads and provides detailed error reporting

## 5. Outputs & Consumers

**Format / Schema:** CSV files with the following outputs:
- `data/weather_data_{store_code}_{longitude}_{latitude}_{period}.csv` - Hourly weather data for each store
- `data/store_altitudes.csv` - Elevation data for all store locations
- `data/download_progress.json` - Progress tracking for resume capability
- `data/download_failed.csv` - List of failed downloads with error details

**Primary Consumers:** Steps 5 (Calculate Feels-Like Temperature) and 6 (Cluster Analysis)

**Business Use:** Provides environmental context for weather-aware clustering and business rules that consider seasonal and climatic factors

## 6. Success Metrics & KPIs

- Weather data completeness ≥ 95% of stores across all periods
- Altitude data coverage 100% of stores
- API success rate ≥ 90% with proper rate limit handling
- Resume capability working correctly after interruptions
- Execution time ≤ 2 hours for 2,000+ stores across 12 periods

## 7. Performance & Cost Notes

- Implements intelligent rate limiting to optimize API usage
- Uses batch processing with configurable delays between requests
- Supports parallel processing through VPN switching workflow
- Memory-efficient processing with file-based storage
- Handles up to 12 periods of historical weather data

## 8. Dependencies & Risks

**Upstream Data / Services:**
- Step 2 output (store coordinates)
- Open-Meteo API availability and rate limits

**External Libraries / APIs:**
- requests, pandas, Open-Meteo Archive API

**Risk Mitigation:**
- VPN switching support for API access issues
- Comprehensive retry logic with exponential backoff
- Progress tracking for resume capability
- Detailed error logging and failure reporting
- Graceful degradation when some data is unavailable

## 9. Pipeline Integration

**Upstream Step(s):** Step 2 (Extract Coordinates)

**Downstream Step(s):** Steps 5 (Calculate Feels-Like Temperature) and 6 (Cluster Analysis)

**Failure Impact:** Blocks weather-aware clustering and environmental business rules; affects seasonal analysis accuracy

## 10. Future Improvements

- Implement parallel downloading with multiple API keys
- Add support for additional weather APIs as fallbacks
- Enhance progress tracking with real-time status dashboard
- Implement intelligent VPN switching automation
- Add weather data quality scoring and validation
- Support for incremental weather data updates
- Integration with weather forecast APIs for future planning
