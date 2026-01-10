# Product Mix Clustering & Rule Analysis Pipeline

## 🚀 Quick Start

This comprehensive pipeline analyzes retail product mix optimization through clustering and business rule validation. Execute the complete pipeline with a single command:

```bash
python pipeline.py --month 202506 --period A --validate-data
```

## 📋 Overview

The pipeline provides end-to-end analysis for retail product mix optimization:

- **15 automated steps** from data collection to visualization
- **6 business rules** for optimization opportunities
- **Weather-aware clustering** for similar store grouping
- **Interactive dashboards** for executive and geographic insights
- **Complete automation** with robust error handling

## 🏗️ Pipeline Architecture

### 5 Main Phases

1. **Data Collection (Steps 1-3)**: API download → Coordinates → Matrix preparation
2. **Weather Integration (Steps 4-5)**: Weather data → Temperature analysis
3. **Clustering (Step 6)**: Temperature-aware store clustering
4. **Business Rules (Steps 7-12)**: 6 optimization rules analysis
5. **Visualization (Steps 13-15)**: Consolidation → Dashboards

### Recent Performance (June 2025 First Half)
- **Total Time**: 65.2 minutes
- **Success Rate**: 100% (2,263 stores processed)
- **Total Violations**: 6,104 across 6 business rules
- **Key Output**: Interactive dashboards + consolidated CSV results

## 🎯 Key Results

### Business Rules Summary
| Rule | Purpose | Results | Analysis Level |
|------|---------|---------|----------------|
| 7 | Missing Categories | 1,611 stores, 3,878 opportunities | Subcategory |
| 8 | Imbalanced Allocation | 2,254 stores, 43,170 cases | SPU |
| 9 | Below Minimum | 2,263 stores, 54,698 cases | Subcategory |
| 10 | Smart Overcapacity | 601 stores, 1,219 cases | Subcategory |
| 11 | Missed Sales | 0 stores (no issues) | SPU |
| 12 | Sales Performance | 1,326 stores with opportunities | SPU |

### Key Outputs
- `consolidated_rule_results.csv` - Main analysis results
- `global_overview_spu_dashboard.html` - Executive dashboard
- `interactive_map_spu_dashboard.html` - Geographic visualization
- Individual rule result files for detailed analysis

## ⚙️ Command Options

### Complete Pipeline
```bash
# Full pipeline with validation
python pipeline.py --month 202506 --period A --validate-data

# Full pipeline without validation (faster)
python pipeline.py --month 202506 --period A
```

### Step Control
```bash
# Run specific steps
python pipeline.py --month 202506 --period A --start-step 7 --end-step 12

# List available steps
python pipeline.py --list-steps

# List available periods
python pipeline.py --list-periods
```

### Seasonal Consolidation (Step 2B)
Run Step 2B before clustering (Step 6) with a dynamic half‑month look‑back window:

```bash
# Trigger Step 2B via pipeline just before Step 6
python pipeline.py --month 202509 --period A \
  --run-2b --seasonal-look-back 2 --start-step 6 --end-step 6

# Run Step 2B directly (for quick smoke tests)
python src/step2b_consolidate_seasonal_data.py \
  --seasonal-look-back 2 --target-yyyymm 202509 --target-period A
```

Notes:
- `--seasonal-look-back` sets how many half‑month periods to include, counting backward from the target period (inclusive). Example above processes `202509A` and `202508B`.
- If `--target-yyyymm/--target-period` are omitted in direct runs, Step 2B falls back to environment variables `PIPELINE_TARGET_YYYYMM` and `PIPELINE_TARGET_PERIOD`.
- Outputs include:
  - `output/consolidated_seasonal_features.csv` (consumed by Step 6)
  - `output/seasonal_store_profiles_<timestamp>.csv`
  - `output/seasonal_category_patterns_<timestamp>.csv`
  - `output/seasonal_clustering_features_<timestamp>.csv`
  - `output/seasonal_clustering_metadata_<timestamp>.json`

### Error Handling
```bash
# Strict mode (stop on any error)
python pipeline.py --month 202506 --period A --strict

# Clear previous data
python pipeline.py --month 202506 --period A --clear-period
```

## 📊 Step Breakdown

| Step | Component | Typical Time | Purpose |
|------|-----------|--------------|---------|
| 1 | API Download | 15 min | Download store/sales data |
| 2 | Coordinates | 1 min | Extract store locations |
| 3 | Matrix Prep | <1 min | Create clustering matrices |
| 4 | Weather Data | <1 min | Load weather information |
| 5 | Temperature | 14 min | Calculate feels-like temperatures |
| 6 | Clustering | <1 min | Create store clusters |
| 7-12 | Business Rules | 35 min | Analyze 6 optimization rules |
| 13-15 | Dashboards | <1 min | Generate visualizations |

## 🔧 System Requirements

- **Memory**: 32GB+ RAM recommended
- **Python**: 3.12+ with dependencies
- **Storage**: ~2GB per analysis period
- **Network**: Stable internet for API calls

## 📁 File Structure

```
├── pipeline.py              # Main pipeline execution
├── config.py               # Configuration management
├── src/                    # Individual step scripts
│   ├── step1_api_download.py
│   ├── step2_coordinate_extraction.py
│   └── ... (steps 3-15)
├── data/                   # Data files and matrices
├── output/                 # Results and dashboards
└── docs/                   # Documentation
```

## 🛠️ Installation

1. **Clone Repository**
```bash
git clone <repository-url>
cd ProducMixClustering_pipeline
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Environment**
- Set up API credentials if needed
- Ensure write permissions for `data/` and `output/` directories

## 📈 Output Files

### Main Results
- `consolidated_rule_results.csv` - Complete analysis results (2.3MB)
- `clustering_results.csv` - Store cluster assignments
- `global_overview_spu_dashboard.html` - Executive dashboard
- `interactive_map_spu_dashboard.html` - Geographic dashboard

### Individual Rules
- `rule7_missing_category_results.csv` - Missing categories
- `rule8_imbalanced_results.csv` - Imbalanced allocations
- `rule9_below_minimum_results.csv` - Below minimum thresholds
- `rule10_smart_overcapacity_results.csv` - Overcapacity opportunities
- `rule11_missed_sales_opportunity_results.csv` - Missed sales
- `rule12_sales_performance_results.csv` - Performance gaps

## 🔍 Error Handling & Debugging

### Common Issues
1. **Memory Issues**: Ensure 32GB+ RAM, monitor with task manager
2. **API Timeouts**: Automatic retry logic handles temporary failures
3. **Missing Files**: Use `--clear-period` to reset and restart
4. **Permissions**: Ensure write access to data/ and output/ directories

### Debug Mode
```bash
# Enable strict mode for detailed error reporting
python pipeline.py --month 202506 --period A --strict --validate-data
```

## 📚 Documentation

- **Complete Documentation**: `docs/COMPLETE_PIPELINE_DOCUMENTATION.md`
- **Individual Steps**: Detailed documentation in each step script
- **Configuration**: `config.py` inline documentation
- **Business Rules**: Individual rule analysis documentation

## 🚦 Pipeline Status

### Current Version: v2.0
- ✅ 15-step complete pipeline
- ✅ Comprehensive error handling
- ✅ Step control system
- ✅ Data validation
- ✅ Interactive dashboards
- ✅ Complete documentation

### Recent Improvements
- Enhanced memory optimization
- Robust error handling with retry logic
- Step-by-step execution control
- Comprehensive data validation
- Professional dashboards with SPU-level analysis

## 🤝 Support

For technical support, feature requests, or issues:
1. Check the complete documentation in `docs/`
2. Review error logs for debugging information
3. Use `--strict` mode for detailed error reporting
4. Contact the development team for advanced support

## 📊 Success Metrics

Latest execution (June 2025 First Half):
- **✅ 100% Success Rate** - All 15 steps completed
- **⚡ 65.2 minutes** - Complete pipeline execution
- **📈 2,263 stores** - Successfully analyzed
- **🎯 6,104 violations** - Identified across 6 rules
- **📊 2 dashboards** - Interactive visualizations generated

---

*Ready to optimize your product mix? Run the pipeline and explore the interactive dashboards!*


## Temperature Band Pipeline (2025-09 updates)

- Step 5 (`src/step5_calculate_feels_like_temperature.py`) produces per-store `feels_like_temperature` and `temperature_band` into `output/stores_with_feels_like_temperature.csv` with a `store_code` column.
- Step 22 (`src/step22_store_attribute_enrichment.py`) merges temperature into enriched attributes. It emits `str_code`; Step 36 now normalizes this to `Store_Code` automatically.
- Step 36 (`src/step36_unified_delivery_builder.py`) now:
  - Normalizes `str_code` → `Store_Code` for Step 22 attributes.
  - Merges `Store_Temperature_Band`/`temperature_band`, `feels_like_temperature`, and `Temperature_Zone` into the base.
  - Derives `Temperature_Value_C`, `Temperature_Band_Simple`, `Temperature_Band_Detailed`, and `Temperature_Suitability_Graded`.

### Weather data schema expectations

- Weather CSVs under `output/weather_data/` must include `store_code`.
- Step 4 (`src/step4_download_weather_data.py`) includes a repair helper `validate_and_repair_weather_file(path)` which adds `store_code` parsed from the filename when missing.
- If using `src/step20a_weather_proxy.py` (minimal schema generator), do not mix its outputs into the same folder as Step 4 outputs unless you run schema repair. Prefer keeping Step 20A outputs in a separate directory or run Step 4 repair first.

### Join key alignment

- Store key naming diverges across steps (`str_code` vs `Store_Code`). Step 36 now normalizes on load of Step 22 attributes, so downstream joins succeed without manual preprocessing.

