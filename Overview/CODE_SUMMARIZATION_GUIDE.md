# Fast Fish Pipeline - Code Summarization Guide

**Purpose:** Easy-to-understand guide for all pipeline code files  
**Audience:** Team members without professional Python background  
**Last Updated:** 2025-01-05

---

## 📖 How to Read This Guide

Each section describes:
1. **What the file does** - Simple explanation of purpose
2. **How it helps the project** - Connection to client requirements
3. **Key functions** - One-sentence explanation of each function

---

## 🏗️ Core Framework (`src/core/`)

These files provide the foundation that all pipeline steps use.

### `src/core/context.py`
**What it does:** Carries data between pipeline steps like a messenger bag.

**How it helps:** Ensures data flows smoothly from one step to the next without getting lost.

**Key functions:**
- `StepContext` - A container that holds all data being processed in the pipeline

---

### `src/core/step.py`
**What it does:** Defines the blueprint that all pipeline steps must follow.

**How it helps:** Ensures consistency - every step works the same way (setup → apply → validate → persist).

**Key functions:**
- `Step` - The base class that all pipeline steps inherit from
- `setup()` - Loads data needed for processing
- `apply()` - Does the actual data transformation
- `validate()` - Checks if results are correct
- `persist()` - Saves results to files

---

### `src/core/pipeline.py`
**What it does:** Orchestrates running multiple steps in sequence.

**How it helps:** Allows running the entire 36-step pipeline with one command.

**Key functions:**
- `Pipeline` - Manages execution of multiple steps in order
- `run()` - Executes all steps from start to finish

---

### `src/core/logger.py`
**What it does:** Records what happens during pipeline execution.

**How it helps:** Makes debugging easier by tracking what each step did.

**Key functions:**
- `PipelineLogger` - Writes log messages with timestamps and step names

---

### `src/core/exceptions.py`
**What it does:** Defines error types specific to the pipeline.

**How it helps:** Makes error messages clearer and easier to understand.

**Key functions:**
- `DataValidationError` - Raised when data doesn't meet quality standards

---

## 💾 Data Access Layer (`src/repositories/`)

These files handle reading and writing data. Steps never touch files directly - they use repositories.

### `src/repositories/base.py`
**What it does:** Defines the interface for all data access.

**How it helps:** Ensures all data access follows the same pattern, making testing easier.

**Key functions:**
- `ReadOnlyRepository` - Interface for reading data
- `WriteableRepository` - Interface for reading and writing data

---

### `src/repositories/csv_repository.py`
**What it does:** Reads and writes CSV files.

**How it helps:** Centralizes all CSV file operations in one place.

**Key functions:**
- `get_all()` - Reads entire CSV file into memory
- `save()` - Writes data to CSV file

---

### `src/repositories/api_repository.py`
**What it does:** Communicates with the Fast Fish API.

**How it helps:** Downloads store and sales data from Fast Fish systems.

**Key functions:**
- `fetch_store_data()` - Gets store information from API
- `fetch_sales_data()` - Gets sales data from API

---

## 📥 Phase 1: Data Collection (Steps 1-3)

### `src/step1_download_api_data.py`
**What it does:** Downloads store and sales data from Fast Fish API.

**How it helps:** Gets the raw data needed for all analysis - this is where everything starts.

**Key functions:**
- `download_store_master()` - Downloads list of all stores
- `download_sales_data()` - Downloads sales transactions
- `merge_data()` - Combines store and sales data
- `fetch_store_sales()` - Gets sales for a specific store
- `process_batch()` - Handles downloading data in chunks to avoid timeouts

---

### `src/step2_extract_coordinates.py`
**What it does:** Extracts geographic coordinates (latitude/longitude) for each store.

**How it helps:** Enables geographic clustering and map visualizations.

**Key functions:**
- `extract_coordinates()` - Pulls lat/long from store data
- `validate_coordinates()` - Checks if coordinates are valid
- `save_coordinates()` - Saves coordinate data to file

---

### `src/step2b_consolidate_seasonal_data.py`
**What it does:** Combines data from multiple time periods for seasonal analysis.

**How it helps:** Enables seasonal pattern detection for better clustering.

**Key functions:**
- `consolidate_periods()` - Merges data from multiple half-month periods
- `calculate_seasonal_features()` - Computes seasonal metrics
- `generate_clustering_features()` - Creates features for clustering algorithm

---

### `src/step3_prepare_matrix.py`
**What it does:** Prepares data matrices for the clustering algorithm.

**How it helps:** Transforms raw data into the format needed for store clustering.

**Key functions:**
- `create_store_matrix()` - Builds matrix of store characteristics
- `normalize_features()` - Scales features to comparable ranges
- `prepare_clustering_input()` - Formats data for clustering algorithm

---

## 🌡️ Phase 2: Weather Integration (Steps 4-5)

### `src/step4_download_weather_data.py`
**What it does:** Downloads weather data for each store location.

**How it helps:** Enables weather-aware clustering for seasonal product alignment.

**Key functions:**
- `download_weather()` - Gets weather data from weather API
- `parse_weather_response()` - Extracts relevant weather metrics
- `validate_and_repair_weather_file()` - Fixes missing data in weather files

---

### `src/step5_calculate_feels_like_temperature.py`
**What it does:** Calculates "feels like" temperature for each store.

**How it helps:** More accurate than raw temperature for predicting product demand.

**Key functions:**
- `calculate_feels_like()` - Computes perceived temperature
- `assign_temperature_band()` - Groups stores by temperature range
- `merge_with_store_data()` - Adds temperature to store records

---

## 🎯 Phase 3: Clustering (Step 6)

### `src/step6_cluster_analysis.py`
**What it does:** Groups similar stores into clusters.

**How it helps:** Enables coordinated merchandise strategy for similar stores.

**Key functions:**
- `perform_clustering()` - Runs clustering algorithm on store data
- `assign_clusters()` - Labels each store with its cluster ID
- `calculate_cluster_statistics()` - Computes metrics for each cluster
- `validate_clusters()` - Checks cluster quality and balance

---

## 📊 Phase 4: Business Rules (Steps 7-12)

### `src/step7_missing_category_rule.py`
**What it does:** Identifies stores missing high-performing product categories.

**How it helps:** Finds opportunities to add profitable categories to stores.

**Key functions:**
- `identify_missing_categories()` - Finds categories store should have but doesn't
- `calculate_opportunity_value()` - Estimates revenue from adding category
- `generate_recommendations()` - Creates actionable recommendations

---

### `src/step8_imbalanced_rule.py`
**What it does:** Detects products that are over or under-allocated.

**How it helps:** Balances inventory to match actual demand.

**Key functions:**
- `detect_imbalances()` - Finds allocation mismatches
- `calculate_rebalancing()` - Determines how to fix imbalances
- `prioritize_actions()` - Ranks fixes by impact

---

### `src/step9_below_minimum_rule.py`
**What it does:** Finds categories below minimum threshold levels.

**How it helps:** Ensures stores have adequate stock in all categories.

**Key functions:**
- `check_minimum_thresholds()` - Compares inventory to minimums
- `identify_shortfalls()` - Lists categories needing replenishment
- `calculate_replenishment()` - Determines quantities to add

---

### `src/step10_spu_assortment_optimization.py`
**What it does:** Optimizes the number of product types (SPUs) per category.

**How it helps:** Determines optimal assortment breadth for each store cluster.

**Key functions:**
- `analyze_spu_performance()` - Evaluates how each product type performs
- `calculate_optimal_spu_count()` - Determines ideal number of product types
- `generate_spu_recommendations()` - Creates add/remove recommendations

---

### `src/step11_missed_sales_opportunity.py`
**What it does:** Identifies sales opportunities that were missed.

**How it helps:** Prevents future lost sales by identifying root causes.

**Key functions:**
- `detect_stockouts()` - Finds products that ran out of stock
- `calculate_lost_sales()` - Estimates revenue lost to stockouts
- `identify_root_causes()` - Determines why stockouts occurred

---

### `src/step12_sales_performance_rule.py`
**What it does:** Analyzes sales performance gaps between stores.

**How it helps:** Identifies underperforming stores and improvement opportunities.

**Key functions:**
- `calculate_performance_metrics()` - Computes sales KPIs per store
- `compare_to_benchmarks()` - Measures against cluster averages
- `identify_improvement_opportunities()` - Lists actionable improvements

---

## 📈 Phase 5: Visualization (Steps 13-15)

### `src/step13_consolidate_spu_rules.py`
**What it does:** Combines results from all business rules into one report.

**How it helps:** Creates unified view of all optimization opportunities.

**Key functions:**
- `merge_rule_results()` - Combines outputs from steps 7-12
- `deduplicate_recommendations()` - Removes conflicting recommendations
- `prioritize_actions()` - Ranks all recommendations by impact

---

### `src/step14_global_overview_dashboard.py`
**What it does:** Creates executive summary dashboard.

**How it helps:** Provides high-level view for management decision-making.

**Key functions:**
- `generate_summary_metrics()` - Calculates key performance indicators
- `create_charts()` - Builds visual charts and graphs
- `render_dashboard()` - Generates HTML dashboard file

---

### `src/step15_interactive_map_dashboard.py`
**What it does:** Creates geographic visualization of stores.

**How it helps:** Shows store performance and clusters on a map.

**Key functions:**
- `create_map_layer()` - Builds map with store markers
- `add_cluster_colors()` - Colors stores by cluster
- `add_performance_indicators()` - Shows performance metrics on map

---

## 🔧 Extended Steps (16-36)

### `src/step15_download_historical_baseline.py`
**What it does:** Downloads historical data for baseline comparisons.

**How it helps:** Enables before/after analysis of optimization impact.

---

### `src/step16_create_comparison_tables.py`
**What it does:** Creates comparison tables between periods.

**How it helps:** Shows improvement trends over time.

---

### `src/step17_augment_recommendations.py`
**What it does:** Enhances recommendations with additional context.

**How it helps:** Makes recommendations more actionable.

---

### `src/step18_validate_results.py`
**What it does:** Validates all pipeline outputs for quality.

**How it helps:** Ensures data quality before delivery to client.

---

### `src/step19_detailed_spu_breakdown.py`
**What it does:** Creates detailed breakdown by product type.

**How it helps:** Provides granular analysis for category managers.

---

### `src/step20_data_validation.py`
**What it does:** Comprehensive data quality checks.

**How it helps:** Catches data issues before they affect analysis.

---

### `src/step21_label_tag_recommendations.py`
**What it does:** Generates product label and tag recommendations.

**How it helps:** Improves product categorization accuracy.

---

### `src/step22_store_attribute_enrichment.py`
**What it does:** Adds additional attributes to store data.

**How it helps:** Enables more sophisticated clustering and analysis.

---

### `src/step23_update_clustering_features.py`
**What it does:** Updates clustering features with new data.

**How it helps:** Keeps clustering current with latest information.

---

### `src/step24_comprehensive_cluster_labeling.py`
**What it does:** Creates descriptive labels for each cluster.

**How it helps:** Makes clusters understandable to business users.

---

### `src/step25_product_role_classifier.py`
**What it does:** Classifies products by their role (hero, filler, etc.).

**How it helps:** Enables role-based assortment planning.

---

### `src/step26_price_elasticity_analyzer.py`
**What it does:** Analyzes how price changes affect demand.

**How it helps:** Supports pricing optimization decisions.

---

### `src/step27_gap_matrix_generator.py`
**What it does:** Creates supply-demand gap matrices.

**How it helps:** Visualizes where supply doesn't match demand.

---

### `src/step28_scenario_analyzer.py`
**What it does:** Runs what-if scenarios for planning.

**How it helps:** Enables scenario planning and forecasting.

---

### `src/step29_supply_demand_gap_analysis.py`
**What it does:** Detailed analysis of supply-demand gaps.

**How it helps:** Identifies root causes of inventory imbalances.

---

### `src/step30_sellthrough_optimization_engine.py`
**What it does:** Mathematical optimization for sell-through rate.

**How it helps:** Maximizes sell-through under constraints (client's primary KPI).

---

### `src/step31_gap_analysis_workbook.py`
**What it does:** Creates Excel workbook with gap analysis.

**How it helps:** Provides interactive analysis tool for planners.

---

### `src/step32_store_allocation.py`
**What it does:** Allocates products to stores.

**How it helps:** Determines what products go to which stores.

---

### `src/step33_store_level_merchandising_rules.py`
**What it does:** Applies merchandising rules at store level.

**How it helps:** Ensures consistent merchandising standards.

---

### `src/step34a_cluster_strategy_optimization.py`
**What it does:** Optimizes strategy for each cluster.

**How it helps:** Tailors approach to each store group.

---

### `src/step34b_unify_outputs.py`
**What it does:** Unifies all outputs into consistent format.

**How it helps:** Ensures deliverables are consistent.

---

### `src/step35_merchandising_strategy_deployment.py`
**What it does:** Prepares merchandising strategies for deployment.

**How it helps:** Makes strategies ready for store execution.

---

### `src/step36_unified_delivery_builder.py`
**What it does:** Builds final delivery package for client.

**How it helps:** Creates complete deliverable for Fast Fish.

---

### `src/step37_customer_delivery_formatter.py`
**What it does:** Formats output in client's preferred format.

**How it helps:** Ensures deliverables match client expectations.

---

## ⚙️ Configuration & Utilities

### `config.py`
**What it does:** Stores all configuration settings.

**How it helps:** Centralizes settings so they're easy to change.

**Key settings:**
- API endpoints and credentials
- File paths for input/output
- Business rule thresholds
- Clustering parameters

---

### `pipeline.py`
**What it does:** Main entry point for running the pipeline.

**How it helps:** Allows running entire pipeline with one command.

**Key commands:**
```bash
# Run full pipeline
python pipeline.py --month 202506 --period A

# Run specific steps
python pipeline.py --month 202506 --period A --start-step 7 --end-step 12

# List available steps
python pipeline.py --list-steps
```

---

## 📁 Output Files

### Main Results
- `consolidated_rule_results.csv` - All optimization opportunities
- `clustering_results.csv` - Store cluster assignments
- `global_overview_spu_dashboard.html` - Executive dashboard
- `interactive_map_spu_dashboard.html` - Geographic dashboard

### Individual Rule Results
- `rule7_missing_category_results.csv`
- `rule8_imbalanced_results.csv`
- `rule9_below_minimum_results.csv`
- `rule10_smart_overcapacity_results.csv`
- `rule11_missed_sales_opportunity_results.csv`
- `rule12_sales_performance_results.csv`

---

## 🔑 Key Concepts Glossary

| Term | Meaning |
|------|---------|
| **SPU** | Stock Keeping Unit - a unique product type |
| **Sell-Through Rate** | Percentage of inventory sold in a period |
| **Store Cluster** | Group of similar stores for coordinated strategy |
| **Store Group** | Fast Fish's organizational unit (46 groups total) |
| **Period** | Half-month time window (A = first half, B = second half) |
| **Temperature Band** | Climate-based store grouping |
| **Repository** | Code that handles reading/writing data |
| **4-Phase Pattern** | setup → apply → validate → persist |

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-05
