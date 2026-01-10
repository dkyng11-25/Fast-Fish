# Consolidated SPU-Level Rule Analysis Summary

**Date**: 2025-06-17T21:08:42.455231
**Analysis Level**: SPU

## Overview
- Total stores analyzed: 2,263
- Rules applied: 6
- Rules: rule7_missing_category, rule8_imbalanced, rule9_below_minimum, rule10_smart_overcapacity, rule11_missed_sales_opportunity, rule12_sales_performance

## Overall SPU-Level Results
- Stores with rule violations: 2,246 (99.2%)
- Total rule violations: 6,312
- Average violations per store: 2.79
- Maximum violations per store: 5

## Individual SPU-Level Rule Results
### Rule10 Smart Overcapacity
- **Overall stores flagged**: 2,001 (88.4%)
- **Profile breakdown**:
  - Strict: 2,157 stores (95.3%)
  - Standard: 2,001 stores (88.4%)
  - Lenient: 1,983 stores (87.6%)

### Rule11 Missed Sales Opportunity
- Primary opportunities: 1,326 (58.6%)
- Cluster relative underperformance: 2,256 stores
- Cluster misjudgment cases: 2,259 stores

### Rule12 Sales Performance
- **Total stores classified**: 1,326 (58.6%)
- **Performance breakdown**:
  - Top Performer: 29 stores (1.3%)
  - Performing Well: 904 stores (39.9%)
  - Some Opportunity: 1313 stores (58.0%)
  - Good Opportunity: 13 stores (0.6%)
  - Major Opportunity: 0 stores (0.0%)

## SPU-Level Cluster Analysis
Top 10 clusters by violation rate:

- **Cluster 7**: 50/50 stores (100.0% flagged)
- **Cluster 23**: 50/50 stores (100.0% flagged)
- **Cluster 10**: 50/50 stores (100.0% flagged)
- **Cluster 0**: 52/52 stores (100.0% flagged)
- **Cluster 12**: 50/50 stores (100.0% flagged)
- **Cluster 31**: 50/50 stores (100.0% flagged)
- **Cluster 15**: 49/50 stores (98.0% flagged)
- **Cluster 34**: 50/50 stores (100.0% flagged)
- **Cluster 8**: 50/50 stores (100.0% flagged)
- **Cluster 17**: 50/50 stores (100.0% flagged)

## SPU-Level Analysis Benefits
- **Granular Insights**: Individual SPU performance analysis
- **Precise Targeting**: Product-specific optimization opportunities
- **Enhanced Sensitivity**: More detailed detection of performance gaps
- **Strategic Value**: Enables precise inventory and promotion decisions

## Column Guide
### SPU Rule Flags
- `rule7_missing_spu`: 1 if store has missing SPUs at SPU level, 0 otherwise
- `rule8_imbalanced_spu`: 1 if store has imbalanced allocations at SPU level, 0 otherwise
- `rule12_sales_performance`: 1 if store has performance opportunities at SPU level, 0 otherwise
- `total_spu_rule_violations`: Sum of all SPU-level rule violations for the store
- `overall_spu_unreasonable`: 1 if store has any SPU-level rule violations, 0 otherwise

**Note**: Rules 10 (Overcapacity) and 11 (Missed Sales) are disabled at SPU level due to
circular logic in allocation proxy calculations. They require proper allocation targets.

### SPU-Level Detailed Metrics
- `*_count`: Number of SPU-level cases identified
- `*_value`: Expected value/impact from SPU-level opportunities
- `categories_analyzed`: Number of SPU categories analyzed per store
- `avg_opportunity_z_score`: Average performance Z-score across SPUs
