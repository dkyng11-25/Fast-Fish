# Phase 3: Code Refactoring - Execution Plan

**Date:** 2025-11-03  
**Status:** 📋 READY TO EXECUTE  
**Total Estimated Time:** 14-17 hours  
**Recommended Approach:** 6 focused sessions

---

## 🎯 Executive Summary

Phase 3 is too large to complete in one session. This plan breaks it into **6 focused sessions** of 2-3 hours each, with clear deliverables and checkpoints.

**Key Principle:** Complete one session fully before starting the next. Each session builds on the previous one.

---

## 📅 Session Breakdown

### **Session 1: Foundation (2.5 hours)**
**Goal:** Create configuration and data loading infrastructure

**Deliverables:**
1. `src/components/missing_category/__init__.py`
2. `src/components/missing_category/config.py` (150 LOC)
3. `src/components/missing_category/data_loader.py` (250 LOC)
4. `src/repositories/cluster_repository.py` (100 LOC)
5. `src/repositories/sales_repository.py` (150 LOC)

**Tests Expected to Pass:** 4-5 SETUP scenarios

**Checkpoint:** Can load and normalize clustering data, load sales data

---

### **Session 2: Core Analysis (3 hours)**
**Goal:** Implement cluster analysis and opportunity identification

**Deliverables:**
1. `src/components/missing_category/cluster_analyzer.py` (180 LOC)
2. `src/components/missing_category/opportunity_identifier.py` (200 LOC)
3. `src/repositories/quantity_repository.py` (120 LOC)

**Tests Expected to Pass:** 10-12 APPLY scenarios

**Checkpoint:** Can identify well-selling features and missing opportunities

---

### **Session 3: Validation & ROI (2.5 hours)**
**Goal:** Implement sell-through validation and ROI calculation

**Deliverables:**
1. `src/components/missing_category/sellthrough_validator.py` (150 LOC)
2. `src/components/missing_category/roi_calculator.py` (180 LOC)
3. `src/repositories/margin_repository.py` (100 LOC)

**Tests Expected to Pass:** 18-20 APPLY scenarios

**Checkpoint:** Can validate opportunities and calculate ROI

---

### **Session 4: Aggregation & Reporting (2 hours)**
**Goal:** Implement results aggregation and report generation

**Deliverables:**
1. `src/components/missing_category/results_aggregator.py` (150 LOC)
2. `src/components/missing_category/report_generator.py` (200 LOC)

**Tests Expected to Pass:** 25-27 scenarios (APPLY + PERSIST)

**Checkpoint:** Can aggregate results and generate reports

---

### **Session 5: Step Integration (3 hours)**
**Goal:** Implement main step class and factory

**Deliverables:**
1. `src/steps/missing_category_rule_step.py` (450 LOC)
2. `src/factories/missing_category_rule_factory.py` (50 LOC)

**Tests Expected to Pass:** 30-33 scenarios (ALL)

**Checkpoint:** Complete step works end-to-end

---

### **Session 6: Testing & Refinement (2 hours)**
**Goal:** Debug, refine, and ensure 100% test pass rate

**Deliverables:**
1. All tests passing (33/33)
2. Code quality verification
3. Documentation updates
4. `PHASE3_COMPLETE.md`

**Checkpoint:** Production-ready implementation

---

## 📋 Detailed Session Plans

---

## 🔷 SESSION 1: Foundation (2.5 hours)

### **Objective:** Create configuration and data loading infrastructure

### **Step 1.1: Create Directory Structure (5 minutes)**

```bash
mkdir -p src/components/missing_category
mkdir -p src/repositories
mkdir -p src/factories
touch src/components/missing_category/__init__.py
```

**Verify:**
```bash
ls -la src/components/missing_category/
ls -la src/repositories/
```

---

### **Step 1.2: Implement Configuration (30 minutes)**

**File:** `src/components/missing_category/config.py`

**Template:**
```python
"""Configuration for Missing Category/SPU Rule step."""

from dataclasses import dataclass, field
from typing import Optional
import os

@dataclass
class MissingCategoryConfig:
    """Configuration for Missing Category/SPU Rule analysis."""
    
    # Analysis settings
    analysis_level: str = 'subcategory'  # 'subcategory' or 'spu'
    period_label: str = '202510A'
    
    # Thresholds (vary by analysis level)
    min_cluster_stores_selling: float = 0.70
    min_cluster_sales_threshold: float = 100.0
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
    
    def __post_init__(self):
        """Adjust thresholds based on analysis level."""
        if self.analysis_level == 'spu':
            self.min_cluster_stores_selling = 0.80
            self.min_cluster_sales_threshold = 1500.0
    
    @classmethod
    def from_env_and_args(cls, **kwargs):
        """Create config from environment variables and arguments."""
        config_dict = {}
        
        # Load from environment
        if os.getenv('ANALYSIS_LEVEL'):
            config_dict['analysis_level'] = os.getenv('ANALYSIS_LEVEL')
        if os.getenv('PERIOD_LABEL'):
            config_dict['period_label'] = os.getenv('PERIOD_LABEL')
        
        # Override with kwargs
        config_dict.update(kwargs)
        
        return cls(**config_dict)
```

**Test:**
```python
# Quick verification
config = MissingCategoryConfig()
assert config.analysis_level == 'subcategory'
assert config.min_cluster_stores_selling == 0.70

config_spu = MissingCategoryConfig(analysis_level='spu')
assert config_spu.min_cluster_stores_selling == 0.80
```

---

### **Step 1.3: Implement Cluster Repository (30 minutes)**

**File:** `src/repositories/cluster_repository.py`

**Key Methods:**
- `load_clustering_results()` - Load with fallback chain
- `_normalize_cluster_column()` - Rename Cluster → cluster_id

**Reference:** Look at existing repository pattern in `src/repositories/`

---

### **Step 1.4: Implement Sales Repository (30 minutes)**

**File:** `src/repositories/sales_repository.py`

**Key Methods:**
- `load_current_sales()` - Load current period
- `load_seasonal_sales()` - Load seasonal period(s)
- `_standardize_columns()` - Normalize column names

---

### **Step 1.5: Implement Data Loader Component (45 minutes)**

**File:** `src/components/missing_category/data_loader.py`

**Key Methods:**
- `load_clustering_data()` - Use ClusterRepository
- `load_sales_data()` - Use SalesRepository
- `blend_sales_data()` - Weighted blending if enabled
- `load_quantity_data()` - Use QuantityRepository (stub for now)
- `load_margin_rates()` - Use MarginRepository (stub for now)

**Critical:** Use `import fireducks.pandas as pd` (not standard pandas)

---

### **Step 1.6: Test Session 1 (10 minutes)**

```bash
# Run SETUP scenarios
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -k "setup" -v

# Expected: 4-5 tests should now pass
```

**Checkpoint Questions:**
- ✅ Can load clustering data?
- ✅ Can normalize Cluster → cluster_id?
- ✅ Can load sales data?
- ✅ Can blend seasonal data (if enabled)?

---

## 🔷 SESSION 2: Core Analysis (3 hours)

### **Objective:** Implement cluster analysis and opportunity identification

### **Step 2.1: Implement Quantity Repository (30 minutes)**

**File:** `src/repositories/quantity_repository.py`

**Key Methods:**
- `load_quantity_data()` - Load current period
- `load_historical_prices()` - Load historical for backfill
- `backfill_missing_prices()` - Fill from historical

---

### **Step 2.2: Update Data Loader (15 minutes)**

**Update:** `src/components/missing_category/data_loader.py`

**Add:**
- Complete `load_quantity_data()` implementation
- Complete `load_margin_rates()` stub

---

### **Step 2.3: Implement Cluster Analyzer (1 hour)**

**File:** `src/components/missing_category/cluster_analyzer.py`

**Class Structure:**
```python
class ClusterAnalyzer:
    """Identifies well-selling features per cluster."""
    
    def __init__(self, config: MissingCategoryConfig, logger: PipelineLogger):
        self.config = config
        self.logger = logger
    
    def identify_well_selling_features(
        self,
        sales_df: pd.DataFrame,
        cluster_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Identify features well-selling in each cluster.
        
        Returns:
            DataFrame with columns:
            - cluster_id
            - feature (sub_cate_name or spu_code)
            - stores_selling
            - total_cluster_sales
            - pct_stores_selling
        """
        # 1. Merge sales with clusters
        # 2. Group by (cluster_id, feature)
        # 3. Calculate stores_selling, total_sales
        # 4. Calculate pct_stores_selling
        # 5. Filter by thresholds
        # 6. Return well-selling features
```

**Test:**
```bash
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -k "well_selling" -v
```

---

### **Step 2.4: Implement Opportunity Identifier (1 hour)**

**File:** `src/components/missing_category/opportunity_identifier.py`

**Key Methods:**
- `identify_missing_opportunities()` - Main method
- `_find_missing_stores()` - Stores not selling feature
- `_calculate_expected_sales()` - Robust median
- `_resolve_unit_price()` - 4-level fallback
- `_calculate_quantity()` - Units from sales/price

**Critical Logic:**
```python
def _resolve_unit_price(self, store_code, feature, quantity_df, sales_df, cluster_id):
    """
    Resolve unit price with 4-level fallback:
    1. Store average from quantity_df
    2. Store average from sales_df
    3. Cluster median from quantity_df
    4. FAIL (strict mode)
    """
```

---

### **Step 2.5: Test Session 2 (15 minutes)**

```bash
# Run APPLY scenarios
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -k "apply" -v

# Expected: 10-12 tests should now pass
```

**Checkpoint Questions:**
- ✅ Can identify well-selling features?
- ✅ Can find missing stores?
- ✅ Can calculate expected sales?
- ✅ Can resolve unit prices with fallback?
- ✅ Can calculate quantities?

---

## 🔷 SESSION 3: Validation & ROI (2.5 hours)

### **Objective:** Implement sell-through validation and ROI calculation

### **Step 3.1: Implement Margin Repository (20 minutes)**

**File:** `src/repositories/margin_repository.py`

**Key Methods:**
- `load_margin_rates()` - Load period-aware margins
- `build_margin_lookup()` - Create (store, feature) → rate map

---

### **Step 3.2: Implement Sell-Through Validator (1 hour)**

**File:** `src/components/missing_category/sellthrough_validator.py`

**Key Methods:**
- `validate_opportunity()` - Main validation
- `_predict_sellthrough()` - Adoption-based prediction
- `_check_approval_gates()` - Multi-criteria check

**Approval Logic:**
```python
def _check_approval_gates(self, opportunity_data):
    """
    Check all approval gates:
    1. Validator approves (predicted ST >= threshold)
    2. Stores selling >= min_stores_selling
    3. Adoption rate >= min_adoption
    4. Predicted ST >= min_predicted_st
    
    Returns: (approved: bool, reason: str)
    """
```

---

### **Step 3.3: Implement ROI Calculator (1 hour)**

**File:** `src/components/missing_category/roi_calculator.py`

**Key Methods:**
- `calculate_roi()` - Main calculation
- `_resolve_margin_rate()` - 2-level lookup
- `_apply_roi_filter()` - Filter by thresholds

**Calculation:**
```python
def calculate_roi(self, opportunity_data, margin_rates_df):
    """
    Calculate ROI metrics:
    - unit_cost = unit_price * (1 - margin_rate)
    - margin_per_unit = unit_price - unit_cost
    - margin_uplift = margin_per_unit * quantity
    - investment_required = quantity * unit_cost
    - roi = margin_uplift / investment_required
    """
```

---

### **Step 3.4: Test Session 3 (10 minutes)**

```bash
# Run validation and ROI scenarios
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -k "validation or roi" -v

# Expected: 18-20 tests should now pass
```

---

## 🔷 SESSION 4: Aggregation & Reporting (2 hours)

### **Objective:** Implement results aggregation and report generation

### **Step 4.1: Implement Results Aggregator (1 hour)**

**File:** `src/components/missing_category/results_aggregator.py`

**Key Methods:**
- `aggregate_to_store_level()` - Main aggregation
- `_calculate_store_metrics()` - Sum/average metrics
- `_create_rule_flags()` - Binary flags

**Aggregations:**
```python
def aggregate_to_store_level(self, opportunities_df):
    """
    Aggregate opportunities by store:
    - missing_categories_count (or missing_spus_count)
    - total_quantity_needed
    - total_investment_required
    - total_retail_value
    - avg_sellthrough_improvement
    - avg_predicted_sellthrough
    - fastfish_approved_count
    - rule7_missing_category (flag: 0 or 1)
    """
```

---

### **Step 4.2: Implement Report Generator (45 minutes)**

**File:** `src/components/missing_category/report_generator.py`

**Key Methods:**
- `generate_summary_report()` - Main report
- `_format_executive_summary()` - High-level metrics
- `_format_sellthrough_distribution()` - Distribution table
- `_format_top_opportunities()` - Top 10 table

---

### **Step 4.3: Test Session 4 (15 minutes)**

```bash
# Run aggregation and persist scenarios
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -k "aggregate or persist" -v

# Expected: 25-27 tests should now pass
```

---

## 🔷 SESSION 5: Step Integration (3 hours)

### **Objective:** Implement main step class and factory

### **Step 5.1: Implement Main Step Class (2 hours)**

**File:** `src/steps/missing_category_rule_step.py`

**Class Structure:**
```python
from src.core.step_base import BaseStep
from src.core.context import StepContext
from src.core.exceptions import DataValidationError
import fireducks.pandas as pd

class MissingCategoryRuleStep(BaseStep):
    """Step 7: Missing Category/SPU Rule with Sell-Through Validation."""
    
    def __init__(
        self,
        cluster_repo,
        sales_repo,
        quantity_repo,
        margin_repo,
        output_repo,
        sellthrough_validator,
        config,
        logger,
        step_name="Missing Category Rule",
        step_number=7
    ):
        super().__init__(logger, step_name, step_number)
        # Store all dependencies
        
        # Create components
        self.data_loader = DataLoader(...)
        self.cluster_analyzer = ClusterAnalyzer(...)
        self.opportunity_identifier = OpportunityIdentifier(...)
        self.sellthrough_validator = sellthrough_validator
        self.roi_calculator = ROICalculator(...) if config.use_roi else None
        self.results_aggregator = ResultsAggregator(...)
        self.report_generator = ReportGenerator(...)
    
    def setup(self, context: StepContext) -> StepContext:
        """Load all data."""
        self.logger.info("Loading data...")
        
        # Use DataLoader
        context.data['cluster_df'] = self.data_loader.load_clustering_data()
        context.data['sales_df'] = self.data_loader.load_sales_data()
        context.data['quantity_df'] = self.data_loader.load_quantity_data()
        context.data['margin_df'] = self.data_loader.load_margin_rates()
        
        return context
    
    def apply(self, context: StepContext) -> StepContext:
        """Identify opportunities and calculate quantities."""
        self.logger.info("Analyzing opportunities...")
        
        # 1. Identify well-selling features
        well_selling = self.cluster_analyzer.identify_well_selling_features(
            context.data['sales_df'],
            context.data['cluster_df']
        )
        context.data['well_selling_features'] = well_selling
        
        # 2. Identify missing opportunities
        opportunities = self.opportunity_identifier.identify_missing_opportunities(
            well_selling,
            context.data['cluster_df'],
            context.data['sales_df'],
            context.data['quantity_df']
        )
        
        # 3. Validate with sell-through
        validated = self.sellthrough_validator.validate_opportunities(opportunities)
        
        # 4. Calculate ROI (if enabled)
        if self.roi_calculator:
            validated = self.roi_calculator.calculate_and_filter(
                validated,
                context.data['margin_df']
            )
        
        context.data['opportunities'] = validated
        
        # 5. Aggregate to store level
        results = self.results_aggregator.aggregate_to_store_level(validated)
        context.data['results'] = results
        
        return context
    
    def validate(self, context: StepContext) -> None:
        """Validate results meet quality standards."""
        # CRITICAL: Returns None, not StepContext!
        
        results = context.data.get('results')
        opportunities = context.data.get('opportunities')
        
        # Check required columns
        required_result_cols = ['str_code', 'cluster_id', 'total_quantity_needed']
        missing_cols = [c for c in required_result_cols if c not in results.columns]
        if missing_cols:
            raise DataValidationError(f"Missing columns in results: {missing_cols}")
        
        # Check no negative quantities
        if (results['total_quantity_needed'] < 0).any():
            raise DataValidationError("Negative quantities found in results")
        
        # Validate opportunities
        if len(opportunities) > 0:
            required_opp_cols = ['str_code', 'spu_code', 'recommended_quantity_change']
            missing_cols = [c for c in required_opp_cols if c not in opportunities.columns]
            if missing_cols:
                raise DataValidationError(f"Missing columns in opportunities: {missing_cols}")
        
        self.logger.info("Validation passed")
        # Return None (implicitly)
    
    def persist(self, context: StepContext) -> StepContext:
        """Save results and generate reports."""
        self.logger.info("Saving results...")
        
        # 1. Save store results
        results_file = self.output_repo.save(
            context.data['results'],
            f"rule7_missing_{self.config.analysis_level}_sellthrough_results"
        )
        
        # 2. Save opportunities
        if len(context.data['opportunities']) > 0:
            opp_file = self.output_repo.save(
                context.data['opportunities'],
                f"rule7_missing_{self.config.analysis_level}_sellthrough_opportunities"
            )
        
        # 3. Generate report
        report = self.report_generator.generate_summary_report(
            context.data['opportunities'],
            context.data['results']
        )
        
        # 4. Register in manifest (if available)
        # 5. Create symlinks
        
        return context
```

---

### **Step 5.2: Implement Factory (30 minutes)**

**File:** `src/factories/missing_category_rule_factory.py`

**Implementation:**
```python
class MissingCategoryRuleFactory:
    """Factory for creating MissingCategoryRuleStep instances."""
    
    @staticmethod
    def create(config: MissingCategoryConfig, logger: PipelineLogger):
        """Create step with all dependencies injected."""
        # Create base CSV repository
        csv_repo = CsvFileRepository(...)
        
        # Create domain repositories
        cluster_repo = ClusterRepository(csv_repo, logger)
        sales_repo = SalesRepository(csv_repo, logger)
        quantity_repo = QuantityRepository(csv_repo, logger)
        margin_repo = MarginRepository(csv_repo, logger)
        
        # Create sell-through validator
        validator = SellThroughValidator(...)
        
        # Create and return step
        return MissingCategoryRuleStep(
            cluster_repo=cluster_repo,
            sales_repo=sales_repo,
            quantity_repo=quantity_repo,
            margin_repo=margin_repo,
            output_repo=csv_repo,
            sellthrough_validator=validator,
            config=config,
            logger=logger
        )
```

---

### **Step 5.3: Test Session 5 (30 minutes)**

```bash
# Run ALL tests
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -v

# Expected: 30-33 tests should now pass (ideally ALL)
```

---

## 🔷 SESSION 6: Testing & Refinement (2 hours)

### **Objective:** Debug, refine, and ensure 100% test pass rate

### **Step 6.1: Debug Failing Tests (1 hour)**

**Process:**
1. Run tests, identify failures
2. Debug one failure at a time
3. Fix root cause
4. Re-run tests
5. Repeat until all pass

**Common Issues:**
- Missing imports
- Incorrect data types
- Mock data structure mismatches
- Logic errors in calculations

---

### **Step 6.2: Code Quality Verification (30 minutes)**

```bash
# Check file sizes
find src/components/missing_category/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "VIOLATION: " $2 ": " $1 " lines"}'

# Check function sizes (manual review)
# Each function should be ≤ 200 LOC

# Verify fireducks.pandas usage
grep -r "import pandas" src/components/missing_category/ src/steps/missing_category_rule_step.py
# Should return nothing (should use fireducks.pandas)

grep -r "import fireducks.pandas" src/components/missing_category/ src/steps/missing_category_rule_step.py
# Should find all imports
```

---

### **Step 6.3: Documentation Updates (20 minutes)**

**Update:**
1. Add docstrings to all classes
2. Add docstrings to all public methods
3. Add type hints to all public methods
4. Update `PHASE3_COMPLETE.md`

---

### **Step 6.4: Final Test Run (10 minutes)**

```bash
# Run all tests one final time
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -v

# Expected: 33/33 PASS ✅
```

---

## 📊 Progress Tracking Template

### **Session Completion Checklist**

**Session 1: Foundation**
- [ ] Config dataclass created
- [ ] ClusterRepository implemented
- [ ] SalesRepository implemented
- [ ] DataLoader component implemented
- [ ] 4-5 SETUP tests passing
- [ ] Code compiles without errors

**Session 2: Core Analysis**
- [ ] QuantityRepository implemented
- [ ] ClusterAnalyzer component implemented
- [ ] OpportunityIdentifier component implemented
- [ ] 10-12 APPLY tests passing
- [ ] All files ≤ 500 LOC

**Session 3: Validation & ROI**
- [ ] MarginRepository implemented
- [ ] SellThroughValidator component implemented
- [ ] ROICalculator component implemented
- [ ] 18-20 tests passing
- [ ] Validation logic working

**Session 4: Aggregation & Reporting**
- [ ] ResultsAggregator component implemented
- [ ] ReportGenerator component implemented
- [ ] 25-27 tests passing
- [ ] Reports generating correctly

**Session 5: Step Integration**
- [ ] MissingCategoryRuleStep class implemented
- [ ] Factory implemented
- [ ] 30-33 tests passing
- [ ] End-to-end flow working

**Session 6: Testing & Refinement**
- [ ] All 33 tests passing
- [ ] Code quality verified
- [ ] Documentation complete
- [ ] PHASE3_COMPLETE.md created

---

## 🚨 Critical Reminders

### **Before Each Session:**
1. Review the session plan
2. Ensure previous session is complete
3. Have tests ready to run
4. Clear your workspace

### **During Each Session:**
1. Work methodically, one component at a time
2. Test after each component
3. Debug immediately when issues arise
4. Track progress in checklist

### **After Each Session:**
1. Run all tests
2. Verify no regressions
3. Update progress checklist
4. Document any issues or learnings

---

## 📝 Quick Reference

### **File Locations:**
```
src/components/missing_category/
├── __init__.py
├── config.py
├── data_loader.py
├── cluster_analyzer.py
├── opportunity_identifier.py
├── sellthrough_validator.py
├── roi_calculator.py
├── results_aggregator.py
└── report_generator.py

src/steps/
└── missing_category_rule_step.py

src/repositories/
├── cluster_repository.py
├── sales_repository.py
├── quantity_repository.py
└── margin_repository.py

src/factories/
└── missing_category_rule_factory.py
```

### **Test Command:**
```bash
# Run all tests
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -v

# Run specific scenario
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -k "scenario_name" -v

# Run with verbose output
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -v -s
```

### **Quality Check Commands:**
```bash
# File size check
find src/components/missing_category/ -name "*.py" -exec wc -l {} +

# Import check
grep -r "import pandas" src/components/missing_category/
grep -r "import fireducks.pandas" src/components/missing_category/
```

---

## ✅ Success Criteria

**Phase 3 is complete when:**
- ✅ All 14 files created
- ✅ All 33 tests passing
- ✅ All files ≤ 500 LOC
- ✅ All functions ≤ 200 LOC
- ✅ Uses fireducks.pandas (not standard pandas)
- ✅ VALIDATE returns None (not StepContext)
- ✅ All imports at top of files
- ✅ Complete type hints and docstrings
- ✅ No hard-coded paths or globals

---

**Execution Plan Complete:** ✅  
**Ready to Execute:** YES  
**Estimated Total Time:** 14-17 hours across 6 sessions  
**Date:** 2025-11-03  
**Time:** 10:30 AM UTC+08:00
