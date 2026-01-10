# Phase 3: Code Refactoring - Implementation Plan

**Date:** 2025-11-03  
**Status:** 📋 PLANNING  
**Estimated Duration:** 14-17 hours  
**Approach:** Methodical, one component at a time

---

## 📋 Overview

Phase 3 involves implementing the actual Step 7 code following CUPID principles and the 4-phase step pattern. This will transform the 1,625-line monolithic script into 13 modular files totaling ~2,000 lines.

---

## 🎯 Implementation Strategy

### Methodical Development Approach

**From AGENTS.md:**
> "Sequential Focus: Complete one component fully before starting the next"
> "Iterative Enhancement: Build → Test → Debug → Improve in focused cycles"

**We will:**
1. Implement ONE component at a time
2. Test each component immediately after creation
3. Debug and fix before moving to next component
4. Track progress in real-time

**We will NOT:**
- ❌ Attempt multiple components simultaneously
- ❌ Rush through without testing
- ❌ Accumulate technical debt
- ❌ Make assumptions without verification

---

## 📁 File Structure to Create

```
src/
├── components/
│   └── missing_category/
│       ├── __init__.py
│       ├── config.py                    # 150 LOC - Configuration dataclass
│       ├── data_loader.py               # 250 LOC - Data loading with seasonal blending
│       ├── cluster_analyzer.py          # 180 LOC - Well-selling feature identification
│       ├── opportunity_identifier.py    # 200 LOC - Missing opportunity detection
│       ├── sellthrough_validator.py     # 150 LOC - Fast Fish validation
│       ├── roi_calculator.py            # 180 LOC - ROI and margin calculations
│       ├── results_aggregator.py        # 150 LOC - Store-level aggregation
│       └── report_generator.py          # 200 LOC - Summary report generation
├── steps/
│   └── missing_category_rule_step.py    # 450 LOC - Main step class
└── repositories/
    ├── cluster_repository.py            # 100 LOC - Clustering data access
    ├── sales_repository.py              # 150 LOC - Sales data access
    ├── quantity_repository.py           # 120 LOC - Quantity data access
    └── margin_repository.py             # 100 LOC - Margin data access

Total: 13 files, ~2,280 LOC
```

---

## 🔄 Implementation Sequence

### Phase 3.1: Configuration (30 minutes)

**File:** `src/components/missing_category/config.py`

**Purpose:** Replace 130 lines of global configuration with type-safe dataclass

**Implementation:**
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MissingCategoryConfig:
    """Configuration for Missing Category/SPU Rule step."""
    
    # Analysis settings
    analysis_level: str = 'subcategory'  # or 'spu'
    period_label: str = '202510A'
    
    # Thresholds (vary by analysis level)
    min_cluster_stores_selling: float = 0.70  # 70% for subcategory, 80% for SPU
    min_cluster_sales_threshold: float = 100.0  # $100 for subcategory, $1500 for SPU
    min_opportunity_value: float = 50.0
    
    # Seasonal blending
    use_blended_seasonal: bool = False
    seasonal_weight: float = 0.6
    recent_weight: float = 0.4
    seasonal_years_back: int = 1
    
    # Sell-through validation
    min_stores_selling: int = 5
    min_adoption: float = 0.25
    min_predicted_st: float = 0.30
    
    # ROI settings
    use_roi: bool = False
    roi_min_threshold: float = 0.30
    min_margin_uplift: float = 100.0
    min_comparables: int = 10
    
    # Scaling
    data_period_days: int = 15
    target_period_days: int = 15
    
    @classmethod
    def from_env_and_args(cls, **kwargs):
        """Create config from environment variables and arguments."""
        # Load from environment, override with kwargs
        # Implementation follows Step 5 pattern
        pass
```

**Test:** Create config instance, verify defaults

---

### Phase 3.2: Data Loader Component (1 hour)

**File:** `src/components/missing_category/data_loader.py`

**Purpose:** Load and blend data from multiple sources

**Key Methods:**
- `load_clustering_data()` - Load and normalize cluster assignments
- `load_sales_data()` - Load current period sales
- `load_seasonal_sales()` - Load seasonal period sales (if enabled)
- `blend_sales_data()` - Weighted blending of current + seasonal
- `load_quantity_data()` - Load quantity data with prices
- `backfill_prices()` - Fill missing prices from historical data
- `load_margin_rates()` - Load margin rates for ROI

**Dependencies:**
- ClusterRepository
- SalesRepository
- QuantityRepository
- MarginRepository
- PipelineLogger

**Test:** Mock repos, verify data loading and blending logic

---

### Phase 3.3: Cluster Analyzer Component (45 minutes)

**File:** `src/components/missing_category/cluster_analyzer.py`

**Purpose:** Identify well-selling features per cluster

**Key Methods:**
- `identify_well_selling_features()` - Main analysis method
- `calculate_cluster_metrics()` - Stores selling, total sales per feature
- `apply_thresholds()` - Filter by adoption % and sales threshold

**Logic:**
```python
def identify_well_selling_features(
    self,
    sales_df: pd.DataFrame,
    cluster_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Identify features that are well-selling in each cluster.
    
    Returns DataFrame with:
    - cluster_id
    - feature (sub_cate_name or spu_code)
    - stores_selling (count)
    - total_cluster_sales (sum)
    - pct_stores_selling (percentage)
    """
```

**Test:** Synthetic data with known thresholds, verify filtering

---

### Phase 3.4: Opportunity Identifier Component (1.5 hours)

**File:** `src/components/missing_category/opportunity_identifier.py`

**Purpose:** Find missing opportunities and calculate quantities

**Key Methods:**
- `identify_missing_opportunities()` - Main method
- `find_missing_stores()` - Stores not selling well-selling features
- `calculate_expected_sales()` - Robust median with outlier trimming
- `resolve_unit_price()` - 4-level fallback chain
- `calculate_quantity()` - Units needed based on sales and price

**Price Resolution Priority:**
1. Store average from quantity_df
2. Store average from sales_df
3. Cluster median from quantity_df
4. FAIL (strict mode - no synthetic)

**Test:** Verify price fallback chain, quantity calculations

---

### Phase 3.5: Sell-Through Validator Component (1 hour)

**File:** `src/components/missing_category/sellthrough_validator.py`

**Purpose:** Validate opportunities using Fast Fish sell-through prediction

**Key Methods:**
- `validate_opportunity()` - Main validation method
- `predict_sellthrough()` - Adoption-based or blended prediction
- `check_approval_gates()` - Multi-criteria approval logic

**Approval Gates:**
- Validator approves (predicted ST >= threshold)
- Stores selling >= min_stores_selling
- Adoption rate >= min_adoption
- Predicted sell-through >= min_predicted_st

**Test:** Mock validator, verify approval/rejection logic

---

### Phase 3.6: ROI Calculator Component (1 hour)

**File:** `src/components/missing_category/roi_calculator.py`

**Purpose:** Calculate ROI metrics and filter by thresholds

**Key Methods:**
- `calculate_roi()` - Main calculation method
- `resolve_margin_rate()` - 2-level lookup (store+feature, store)
- `apply_roi_filter()` - Filter by ROI, margin uplift, comparables

**Calculation:**
```python
unit_cost = unit_price * (1 - margin_rate)
margin_per_unit = unit_price - unit_cost
margin_uplift = margin_per_unit * quantity
investment_required = quantity * unit_cost
roi = margin_uplift / investment_required
```

**Test:** Verify calculations, threshold filtering

---

### Phase 3.7: Results Aggregator Component (45 minutes)

**File:** `src/components/missing_category/results_aggregator.py`

**Purpose:** Aggregate opportunities to store level

**Key Methods:**
- `aggregate_to_store_level()` - Main aggregation method
- `calculate_store_metrics()` - Sum quantities, investment, etc.
- `create_rule_flags()` - Binary flags for rule application

**Aggregations:**
- Count of missing features
- Sum of quantities needed
- Sum of investment required
- Sum of retail values
- Average sell-through improvement
- Count of Fast Fish approved

**Test:** Multiple opportunities per store, verify aggregations

---

### Phase 3.8: Report Generator Component (1 hour)

**File:** `src/components/missing_category/report_generator.py`

**Purpose:** Generate markdown summary reports

**Key Methods:**
- `generate_summary_report()` - Main report generation
- `format_executive_summary()` - High-level metrics
- `format_sellthrough_distribution()` - Distribution analysis
- `format_top_opportunities()` - Top 10 table

**Report Sections:**
1. Header with metadata
2. Seasonal blending info
3. Executive summary
4. Sell-through distribution
5. Quantity & price diagnostics
6. Fast Fish compliance
7. Top opportunities table

**Test:** Generate report, verify formatting and content

---

### Phase 3.9: Main Step Class (2 hours)

**File:** `src/steps/missing_category_rule_step.py`

**Purpose:** Orchestrate all components following 4-phase pattern

**Class Structure:**
```python
class MissingCategoryRuleStep(BaseStep):
    """Step 7: Missing Category/SPU Rule with Sell-Through Validation."""
    
    def __init__(
        self,
        cluster_repo: ClusterRepository,
        sales_repo: SalesRepository,
        quantity_repo: QuantityRepository,
        margin_repo: MarginRepository,
        output_repo: CsvFileRepository,
        sellthrough_validator: SellThroughValidator,
        config: MissingCategoryConfig,
        logger: PipelineLogger,
        step_name: str = "Missing Category Rule",
        step_number: int = 7
    ):
        super().__init__(logger, step_name, step_number)
        # Store dependencies
        
    def setup(self, context: StepContext) -> StepContext:
        """Load all data using DataLoader component."""
        # Use DataLoader to load clustering, sales, quantity, margin data
        # Store in context.data
        return context
        
    def apply(self, context: StepContext) -> StepContext:
        """Identify opportunities and calculate quantities."""
        # 1. Use ClusterAnalyzer to find well-selling features
        # 2. Use OpportunityIdentifier to find missing opportunities
        # 3. Use SellThroughValidator to validate opportunities
        # 4. Use ROICalculator to calculate ROI (if enabled)
        # 5. Use ResultsAggregator to aggregate to store level
        # Store results in context.data
        return context
        
    def validate(self, context: StepContext) -> None:
        """Validate results meet quality standards."""
        # Check required columns present
        # Check no negative quantities
        # Check data types correct
        # Raise DataValidationError if validation fails
        # Return None (not StepContext!)
        
    def persist(self, context: StepContext) -> StepContext:
        """Save results and generate reports."""
        # 1. Save store results CSV
        # 2. Save opportunities CSV
        # 3. Use ReportGenerator to create summary report
        # 4. Register all outputs in manifest
        # 5. Create symlinks
        return context
```

**Test:** Execute full step, verify all phases work together

---

### Phase 3.10: Repositories (2 hours)

**Files:**
- `src/repositories/cluster_repository.py`
- `src/repositories/sales_repository.py`
- `src/repositories/quantity_repository.py`
- `src/repositories/margin_repository.py`

**Purpose:** Abstract all data access operations

**Pattern (from Step 5):**
```python
class ClusterRepository:
    """Repository for clustering data access."""
    
    def __init__(self, csv_repo: CsvFileRepository, logger: PipelineLogger):
        self.csv_repo = csv_repo
        self.logger = logger
        
    def load_clustering_results(self, period_label: str) -> pd.DataFrame:
        """Load clustering results with fallback chain."""
        # Try period-specific file
        # Try generic file
        # Try enhanced file
        # Raise FileNotFoundError if none found
```

**Test:** Mock CsvFileRepository, verify fallback logic

---

### Phase 3.11: Factory (30 minutes)

**File:** `src/factories/missing_category_rule_factory.py`

**Purpose:** Create step instance with all dependencies

**Implementation:**
```python
class MissingCategoryRuleFactory:
    """Factory for creating MissingCategoryRuleStep instances."""
    
    @staticmethod
    def create(config: MissingCategoryConfig, logger: PipelineLogger) -> MissingCategoryRuleStep:
        """Create step with all dependencies injected."""
        # Create CSV repository
        # Create all domain repositories
        # Create sell-through validator
        # Create all components
        # Create and return step instance
```

**Test:** Create step via factory, verify all dependencies injected

---

## 🧪 Testing Strategy

### Continuous Testing (After Each Component)

```bash
# Test individual component
pytest tests/step_definitions/test_step7_missing_category_rule.py::test_specific_scenario -v

# Test all scenarios
pytest tests/step_definitions/test_step7_missing_category_rule.py -v

# Check code quality
find src/components/missing_category/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "VIOLATION: " $2}'
```

### Expected Test Progression

- **After Config:** 0 tests pass (no step implementation)
- **After DataLoader:** 4-5 tests pass (SETUP scenarios)
- **After ClusterAnalyzer:** 6-7 tests pass (well-selling identification)
- **After OpportunityIdentifier:** 10-12 tests pass (opportunity detection)
- **After SellThroughValidator:** 15-18 tests pass (validation scenarios)
- **After ROICalculator:** 18-20 tests pass (ROI scenarios)
- **After ResultsAggregator:** 22-25 tests pass (aggregation scenarios)
- **After ReportGenerator:** 25-27 tests pass (persist scenarios)
- **After Step Class:** 28-30 tests pass (integration scenarios)
- **After Repositories:** 30-33 tests pass (all scenarios)

---

## 📊 Progress Tracking

### Component Checklist

- [ ] Config dataclass (150 LOC)
- [ ] DataLoader component (250 LOC)
- [ ] ClusterAnalyzer component (180 LOC)
- [ ] OpportunityIdentifier component (200 LOC)
- [ ] SellThroughValidator component (150 LOC)
- [ ] ROICalculator component (180 LOC)
- [ ] ResultsAggregator component (150 LOC)
- [ ] ReportGenerator component (200 LOC)
- [ ] MissingCategoryRuleStep class (450 LOC)
- [ ] ClusterRepository (100 LOC)
- [ ] SalesRepository (150 LOC)
- [ ] QuantityRepository (120 LOC)
- [ ] MarginRepository (100 LOC)
- [ ] Factory (50 LOC)

**Total:** 14 components, ~2,280 LOC

### Quality Gates

After each component:
- [ ] File compiles (no syntax errors)
- [ ] File ≤ 500 LOC
- [ ] Functions ≤ 200 LOC
- [ ] Type hints on public methods
- [ ] Docstrings on classes and methods
- [ ] Tests pass for that component
- [ ] No regressions in other tests

---

## ⚠️ Critical Reminders

### From Phase 0 Design Review:

1. **VALIDATE returns None** (not StepContext)
2. **VALIDATE validates only** (no calculations)
3. **All imports at top of file** (no inline imports)
4. **Use fireducks.pandas** (not standard pandas)
5. **No hard-coded paths** (all via repositories)
6. **No global variables** (all via config)

### From AGENTS.md:

1. **One component at a time** - Complete, test, move on
2. **Continuous validation** - Test after each component
3. **Monitor file size** - Stop if approaching 500 LOC
4. **Document as you go** - Docstrings, comments, type hints

---

## 🚀 Ready to Begin

**Estimated Total Time:** 14-17 hours

**Approach:**
1. Start with Config (simplest)
2. Build components in dependency order
3. Test continuously
4. Debug immediately
5. Track progress in real-time

**Next Step:** Implement `src/components/missing_category/config.py`

---

**Implementation Plan Complete:** ✅  
**Ready to Start:** YES  
**Date:** 2025-11-03  
**Time:** 10:25 AM UTC+08:00
