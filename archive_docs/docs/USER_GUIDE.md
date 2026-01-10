# User Guide

## Getting Started

This guide walks you through using the Product Mix Clustering pipeline from installation to interpreting results.

### 1. Installation

#### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Modern web browser for viewing dashboards

#### Installation Steps
```bash
# Clone the repository
git clone <your-repository-url>
cd product-mix-clustering

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Running Your First Analysis

#### Option A: Test with Sample Data (Recommended)
```bash
python run_pipeline.py --skip-api
```
This creates synthetic data and runs the complete pipeline, perfect for testing.

#### Option B: Run with Real Data
```bash
python run_pipeline.py
```
This downloads real data from API endpoints (requires configuration).

### 3. Understanding the Output

After running the pipeline, you'll find several files in the `output/` directory:

#### Core Results
- **`consolidated_rule_results.csv`**: Main results with all rule violations
- **`clustering_results.csv`**: Store cluster assignments
- **`consolidated_rule_summary.md`**: Executive summary report

#### Interactive Dashboards
- **`global_overview_dashboard.html`**: Open in browser for executive overview
- **`interactive_map_dashboard.html`**: Geographic analysis with clickable stores

#### Rule-Specific Results
- **`rule5_missing_category_results.csv`**: Missing category opportunities
- **`rule6_imbalanced_results.csv`**: Over/under-allocated categories
- **`rule7_below_minimum_results.csv`**: Below-threshold allocations
- **`rule8_smart_overcapacity_results.csv`**: Reallocation opportunities

### 4. Interpreting Results

#### Understanding the Business Rules

**Rule 5: Missing Categories**
- **What it finds**: Product categories that sell well in similar stores but are missing from yours
- **How to use**: Add these categories to underperforming stores
- **Key metric**: Number of missing opportunities per store

**Rule 6: Imbalanced Allocations**
- **What it finds**: Categories with unusually high or low allocations vs similar stores
- **How to use**: Rebalance allocations to match successful peers
- **Key metric**: Z-score magnitude (>2.0 is significant)

**Rule 7: Below Minimum Thresholds**
- **What it finds**: Categories with insufficient minimum allocations
- **How to use**: Increase allocations to meet minimum viable levels
- **Key metric**: Number of styles needed to reach minimum

**Rule 8: Smart Overcapacity**
- **What it finds**: Opportunities to reallocate from underperforming to high-potential categories
- **How to use**: Move inventory from low-performers to high-opportunity areas
- **Key metric**: Performance gap between local and cluster averages

#### Reading the Dashboards

**Global Overview Dashboard**
- **Top KPIs**: Total stores analyzed, violations found, categories affected
- **Rule Breakdown**: Visual breakdown of each rule's impact
- **Cluster Performance**: How different store clusters are performing
- **Strategic Insights**: Automated recommendations based on analysis

**Interactive Map Dashboard**
- **Color Coding**: Green (0 violations) to Purple (4+ violations)
- **Filtering**: Use controls to filter by rule type, cluster, or violation count
- **Store Details**: Click markers for detailed store-specific information
- **Geographic Patterns**: Identify regional trends and opportunities

### 5. Common Use Cases

#### Scenario 1: New Store Planning
Use cluster analysis and missing category rules to determine optimal product mix for new locations.

#### Scenario 2: Underperforming Store Analysis
Focus on stores with high violation counts to identify specific improvement opportunities.

#### Scenario 3: Category Management
Use imbalanced and overcapacity rules to optimize category allocations across your store network.

#### Scenario 4: Regional Strategy
Use the interactive map to identify geographic patterns and develop regional strategies.

### 6. Customizing the Analysis

#### Adjusting Rule Parameters

Edit the configuration values in each step file:

**Missing Category Rule (step5)**
```python
CLUSTER_ADOPTION_THRESHOLD = 0.70  # Percent of cluster that must sell category
MIN_SALES_THRESHOLD = 100          # Minimum average sales to consider
```

**Imbalanced Rule (step6)**
```python
Z_SCORE_THRESHOLD = 2.0            # Statistical significance level
```

**Below Minimum Rule (step7)**
```python
MINIMUM_STYLE_COUNT = 1.0          # Minimum viable allocation
```

**Smart Overcapacity Rule (step8)**
```python
LOCAL_PERFORMANCE_THRESHOLD = 0.5   # Local performance ceiling
TARGET_PERFORMANCE_THRESHOLD = 2.0  # Target cluster performance floor
MINIMUM_GAP_THRESHOLD = 0.3         # Minimum improvement gap
```

#### Running Individual Steps

You can run individual pipeline steps for targeted analysis:
```bash
python src/step5_missing_category_rule.py
python src/step6_imbalanced_rule.py
# etc.
```

### 7. Troubleshooting

#### Common Issues

**Memory Errors**
- Reduce dataset size or increase available RAM
- Process stores in batches for very large datasets

**Slow Performance**
- Check available RAM and CPU usage
- Consider running on a more powerful machine for large datasets

**Missing Output Files**
- Check for error messages in console output
- Verify input data files exist and are properly formatted

**Dashboard Not Loading**
- Ensure you're opening HTML files in a modern web browser
- Check that all required JavaScript libraries are loading

#### Getting Help

1. Check console output for specific error messages
2. Verify all dependencies are installed correctly
3. Try running with sample data first to isolate issues
4. Review the log files for detailed debugging information

### 8. Best Practices

#### Data Quality
- Ensure input data is clean and properly formatted
- Validate store coordinates for accurate mapping
- Remove or handle outliers appropriately

#### Performance Optimization
- Use appropriate hardware for your dataset size
- Consider running analysis during off-peak hours
- Monitor memory usage and adjust batch sizes as needed

#### Result Interpretation
- Always validate results against business knowledge
- Consider seasonal and market factors
- Use results as guidance, not absolute directives

#### Ongoing Usage
- Run analysis regularly to track improvements
- Adjust rule parameters based on business changes
- Archive results for trend analysis over time

---

*For technical support or questions, please refer to the project documentation or contact the development team.*
