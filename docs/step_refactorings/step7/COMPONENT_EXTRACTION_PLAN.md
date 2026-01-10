# Component Extraction Plan - Step 7 Missing Category Rule

**Date:** 2025-11-03  
**Current Size:** 1,625 LOC  
**Target Size:** ≤500 LOC per file  
**Violation:** 3.2x over limit  
**Strategy:** CUPID-based modularization

---

## 📊 Current Code Analysis

### File Breakdown by Responsibility:

| Lines | Responsibility | CUPID Violation |
|-------|---------------|-----------------|
| 1-55 | Helper functions (period calculation, averaging) | ❌ Module-level functions |
| 56-132 | Imports and configuration | ❌ Scattered, global vars |
| 133-262 | Configuration constants | ❌ Global variables |
| 263-393 | Data loading (quantity, prices) | ✅ Could be component |
| 394-585 | Main data loading orchestration | ✅ Could be component |
| 586-630 | Sell-through prediction logic | ✅ Could be component |
| 631-688 | Well-selling feature identification | ✅ Business logic |
| 689-1132 | Missing opportunities identification | ❌ 443 lines! |
| 1133-1251 | Rule application | ✅ Business logic |
| 1252-1305 | Preflight validation | ✅ Validation logic |
| 1306-1445 | Results persistence | ✅ Persistence logic |
| 1446-1511 | Report generation | ✅ Reporting logic |
| 1512-1625 | Main execution + CLI | ✅ Orchestration |

### Critical Issues:

1. **Missing opportunities function: 443 lines** (lines 689-1132)
   - Violates Unix Philosophy (does too many things)
   - Violates 200 LOC function limit
   - Needs extraction into multiple components

2. **Global configuration** (lines 133-262)
   - Should be dataclass
   - Violates Predictable principle

3. **Module-level helper functions** (lines 1-55)
   - Should be in utility module or class methods
   - Violates Composable principle

---

## 🎯 CUPID-Based Component Design

### Component 1: Configuration (Predictable + Domain-based)

**File:** `src/components/missing_category/config.py` (~150 LOC)

**Purpose:** Centralize all configuration with clear contracts

```python
@dataclass
class MissingCategoryConfig:
    """Configuration for missing category/SPU rule analysis."""
    
    # Analysis settings
    analysis_level: str  # "subcategory" or "spu"
    data_period_days: int = 15
    target_period_days: int = 15
    scaling_factor: float = 1.0
    
    # Thresholds
    min_cluster_stores_selling: float = 0.80  # 80% for SPU
    min_cluster_sales_threshold: float = 1500
    min_opportunity_value: float = 500
    max_missing_spus_per_store: int = 5
    
    # Seasonal blending
    use_blended_seasonal: bool = False
    seasonal_yyyymm: Optional[str] = None
    seasonal_period: Optional[str] = None
    seasonal_weight: float = 0.6
    recent_weight: float = 0.4
    seasonal_years_back: int = 0
    
    # ROI settings
    use_roi: bool = True
    roi_min_threshold: float = 0.3
    min_margin_uplift: float = 100.0
    min_comparables: int = 10
    default_margin_rate: float = 0.45
    
    # Sell-through validation
    min_stores_selling: int = 5
    min_adoption: float = 0.25
    min_predicted_st: float = 30.0
    
    @classmethod
    def from_env_and_args(cls, args: argparse.Namespace) -> 'MissingCategoryConfig':
        """Create config from environment variables and CLI arguments."""
        # Implementation here
```

**CUPID Compliance:**
- ✅ **Predictable:** Clear configuration contract
- ✅ **Domain-based:** Business terminology (adoption, threshold, etc.)
- ✅ **Idiomatic:** Uses dataclass pattern

---

### Component 2: Data Loader (Composable + Unix Philosophy)

**File:** `src/components/missing_category/data_loader.py` (~200 LOC)

**Purpose:** Load and prepare all required data (single responsibility)

```python
class MissingCategoryDataLoader:
    """Loads and prepares data for missing category analysis."""
    
    def __init__(
        self,
        cluster_repo: ClusterRepository,
        sales_repo: SalesRepository,
        quantity_repo: QuantityRepository,
        config: MissingCategoryConfig,
        logger: PipelineLogger
    ):
        """Inject all data access dependencies."""
        self.cluster_repo = cluster_repo
        self.sales_repo = sales_repo
        self.quantity_repo = quantity_repo
        self.config = config
        self.logger = logger
    
    def load_all_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load cluster, sales, and quantity data.
        
        Returns:
            Tuple of (cluster_df, sales_df, quantity_df)
        """
        cluster_df = self._load_cluster_data()
        sales_df = self._load_sales_data()
        quantity_df = self._load_quantity_data()
        
        return cluster_df, sales_df, quantity_df
    
    def _load_cluster_data(self) -> pd.DataFrame:
        """Load clustering results via repository."""
        # Use repository pattern - no hard-coded paths
    
    def _load_sales_data(self) -> pd.DataFrame:
        """Load sales data with optional seasonal blending."""
        # Seasonal blending logic here
    
    def _load_quantity_data(self) -> pd.DataFrame:
        """Load quantity data with unit price backfill."""
        # Quantity loading with backfill logic
```

**CUPID Compliance:**
- ✅ **Composable:** Reusable across different analysis levels
- ✅ **Unix Philosophy:** Does one thing (data loading)
- ✅ **Predictable:** Clear return types
- ✅ **Idiomatic:** Uses repository pattern
- ✅ **Domain-based:** Business method names

---

### Component 3: Cluster Analyzer (Unix Philosophy + Domain-based)

**File:** `src/components/missing_category/cluster_analyzer.py` (~150 LOC)

**Purpose:** Identify well-selling features within clusters

```python
class ClusterAnalyzer:
    """Analyzes cluster patterns to identify well-selling features."""
    
    def __init__(
        self,
        config: MissingCategoryConfig,
        logger: PipelineLogger
    ):
        self.config = config
        self.logger = logger
    
    def identify_well_selling_features(
        self,
        sales_df: pd.DataFrame,
        cluster_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Identify features well-selling within each cluster.
        
        Args:
            sales_df: Sales data
            cluster_df: Cluster assignments
            
        Returns:
            DataFrame with well-selling features per cluster
        """
        # Lines 631-688 from original
        # Calculate cluster-level statistics
        # Filter by thresholds
        # Return well-selling features
```

**CUPID Compliance:**
- ✅ **Unix Philosophy:** Single responsibility (cluster analysis)
- ✅ **Domain-based:** Business terminology
- ✅ **Predictable:** Clear input/output contract

---

### Component 4: Opportunity Identifier (Composable + Unix Philosophy)

**File:** `src/components/missing_category/opportunity_identifier.py` (~250 LOC)

**Purpose:** Identify missing opportunities (WITHOUT sell-through validation)

```python
class OpportunityIdentifier:
    """Identifies missing category/SPU opportunities."""
    
    def __init__(
        self,
        config: MissingCategoryConfig,
        logger: PipelineLogger
    ):
        self.config = config
        self.logger = logger
    
    def identify_missing_opportunities(
        self,
        sales_df: pd.DataFrame,
        cluster_df: pd.DataFrame,
        well_selling_features: pd.DataFrame,
        quantity_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Identify stores missing well-selling features.
        
        Returns:
            DataFrame with opportunity records (before validation)
        """
        opportunities = []
        
        for _, feature_row in well_selling_features.iterrows():
            # Find missing stores
            # Calculate expected sales
            # Calculate quantities
            # Create opportunity records
            
        return pd.DataFrame(opportunities)
    
    def _calculate_unit_price(
        self,
        store_code: str,
        sales_df: pd.DataFrame,
        quantity_df: pd.DataFrame,
        cluster_df: pd.DataFrame
    ) -> Tuple[float, str]:
        """Calculate unit price with fallback logic."""
        # Lines 842-886 from original
        # 1) Store avg from quantity_df
        # 2) Store avg from sales_df
        # 3) Cluster median
        # Return (price, source)
    
    def _calculate_expected_quantity(
        self,
        avg_sales: float,
        unit_price: float
    ) -> int:
        """Calculate expected quantity recommendation."""
        # Lines 889-890 from original
```

**CUPID Compliance:**
- ✅ **Composable:** Can be used independently
- ✅ **Unix Philosophy:** Focuses on opportunity identification
- ✅ **Predictable:** Clear calculation logic
- ✅ **Idiomatic:** Uses pandas idioms

---

### Component 5: Sell-Through Validator (Composable + Domain-based)

**File:** `src/components/missing_category/sellthrough_validator.py` (~200 LOC)

**Purpose:** Validate opportunities using sell-through analysis

```python
class SellThroughOpportunityValidator:
    """Validates opportunities using Fast Fish sell-through criteria."""
    
    def __init__(
        self,
        validator: SellThroughValidator,  # External validator
        config: MissingCategoryConfig,
        logger: PipelineLogger
    ):
        self.validator = validator
        self.config = config
        self.logger = logger
    
    def validate_opportunities(
        self,
        opportunities_df: pd.DataFrame,
        sales_df: pd.DataFrame,
        cluster_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Filter opportunities by sell-through validation.
        
        Args:
            opportunities_df: Raw opportunities
            sales_df: Sales data for context
            cluster_df: Cluster data
            
        Returns:
            DataFrame with only validated opportunities
        """
        validated = []
        
        for _, opp in opportunities_df.iterrows():
            # Get validation from external validator
            validation = self._validate_single_opportunity(opp, sales_df)
            
            # Apply approval logic
            if self._should_approve(opp, validation):
                # Add validation metrics
                opp_with_validation = self._enrich_with_validation(opp, validation)
                validated.append(opp_with_validation)
        
        return pd.DataFrame(validated)
    
    def _validate_single_opportunity(
        self,
        opportunity: pd.Series,
        sales_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Validate single opportunity."""
        # Lines 905-956 from original
    
    def _should_approve(
        self,
        opportunity: pd.Series,
        validation: Dict[str, Any]
    ) -> bool:
        """Determine if opportunity should be approved."""
        # Lines 938-943 from original
    
    def predict_sellthrough_from_adoption(
        self,
        pct_stores_selling: float
    ) -> float:
        """Predict sell-through from adoption rate."""
        # Lines 586-599 from original
    
    def blended_predicted_sellthrough(
        self,
        pct_stores_selling: float,
        cluster_st_p50: Optional[float],
        cluster_st_p80: Optional[float],
        store_cat_baseline_st: Optional[float],
        seasonal_adj: Optional[float],
        n_comparables: int
    ) -> float:
        """Blend multiple sell-through predictions."""
        # Lines 601-629 from original
```

**CUPID Compliance:**
- ✅ **Composable:** Can validate any opportunities
- ✅ **Domain-based:** Business terminology (sell-through, approval)
- ✅ **Predictable:** Clear validation contract

---

### Component 6: ROI Calculator (Unix Philosophy + Predictable)

**File:** `src/components/missing_category/roi_calculator.py` (~150 LOC)

**Purpose:** Calculate ROI and margin metrics

```python
class ROICalculator:
    """Calculates ROI and margin metrics for opportunities."""
    
    def __init__(
        self,
        margin_rates_df: pd.DataFrame,
        config: MissingCategoryConfig,
        logger: PipelineLogger
    ):
        self.margin_map_pair = self._build_margin_map(margin_rates_df)
        self.margin_map_store = self._build_store_margin_map(margin_rates_df)
        self.config = config
        self.logger = logger
    
    def calculate_roi_metrics(
        self,
        opportunities_df: pd.DataFrame,
        sales_df: pd.DataFrame,
        cluster_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Add ROI metrics to opportunities.
        
        Returns:
            DataFrame with ROI columns added
        """
        # Lines 976-1011 from original
    
    def resolve_margin_rate(
        self,
        store_code: str,
        feature_name: str,
        parent_category: Optional[str] = None
    ) -> float:
        """Resolve margin rate with fallback logic."""
        # Lines 774-785 from original
    
    def _build_margin_map(self, margin_df: pd.DataFrame) -> Dict[Tuple[str, str], float]:
        """Build (store, feature) -> margin rate map."""
        # Lines 747-772 from original
```

**CUPID Compliance:**
- ✅ **Unix Philosophy:** Single responsibility (ROI calculation)
- ✅ **Predictable:** Consistent margin resolution
- ✅ **Idiomatic:** Uses dict lookups for performance

---

### Component 7: Results Aggregator (Unix Philosophy + Domain-based)

**File:** `src/components/missing_category/results_aggregator.py` (~150 LOC)

**Purpose:** Aggregate opportunities into store-level results

```python
class ResultsAggregator:
    """Aggregates opportunities into store-level rule results."""
    
    def __init__(
        self,
        config: MissingCategoryConfig,
        logger: PipelineLogger
    ):
        self.config = config
        self.logger = logger
    
    def aggregate_to_store_results(
        self,
        cluster_df: pd.DataFrame,
        opportunities_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Aggregate opportunities to store-level results.
        
        Args:
            cluster_df: Store cluster assignments
            opportunities_df: Validated opportunities
            
        Returns:
            Store-level results with aggregated metrics
        """
        # Lines 1134-1251 from original
        # Group by store
        # Aggregate metrics
        # Create rule flags
        # Add metadata
```

**CUPID Compliance:**
- ✅ **Unix Philosophy:** Single responsibility (aggregation)
- ✅ **Domain-based:** Business aggregation logic
- ✅ **Predictable:** Clear aggregation rules

---

### Component 8: Report Generator (Unix Philosophy + Domain-based)

**File:** `src/components/missing_category/report_generator.py` (~150 LOC)

**Purpose:** Generate sell-through summary reports

```python
class SellThroughReportGenerator:
    """Generates sell-through analysis reports."""
    
    def __init__(
        self,
        config: MissingCategoryConfig,
        logger: PipelineLogger
    ):
        self.config = config
        self.logger = logger
    
    def generate_summary_report(
        self,
        opportunities_df: pd.DataFrame,
        results_df: pd.DataFrame,
        output_path: str
    ) -> None:
        """Generate markdown summary report."""
        # Lines 1446-1511 from original
```

**CUPID Compliance:**
- ✅ **Unix Philosophy:** Single responsibility (reporting)
- ✅ **Domain-based:** Business report structure
- ✅ **Idiomatic:** Uses context managers for file I/O

---

### Main Step Class: Missing Category Rule Step (≤500 LOC)

**File:** `src/steps/missing_category_rule_step.py` (~450 LOC)

**Purpose:** Orchestrate all components following 4-phase pattern

```python
class MissingCategoryRuleStep(Step):
    """
    Step 7: Missing Category/SPU Rule with Sell-Through Validation.
    
    Identifies stores missing categories/SPUs that are well-selling
    in their cluster peers, with Fast Fish sell-through validation.
    """
    
    def __init__(
        self,
        cluster_repo: ClusterRepository,
        sales_repo: SalesRepository,
        quantity_repo: QuantityRepository,
        margin_repo: MarginRepository,
        output_repo: CsvFileRepository,
        config: MissingCategoryConfig,
        logger: PipelineLogger,
        step_name: str = "Missing Category Rule",
        step_number: int = 7
    ):
        """Initialize with injected dependencies."""
        super().__init__(logger, step_name, step_number)
        
        # Inject repositories
        self.cluster_repo = cluster_repo
        self.sales_repo = sales_repo
        self.quantity_repo = quantity_repo
        self.margin_repo = margin_repo
        self.output_repo = output_repo
        self.config = config
        
        # Create components
        self.data_loader = MissingCategoryDataLoader(
            cluster_repo, sales_repo, quantity_repo, config, logger
        )
        self.cluster_analyzer = ClusterAnalyzer(config, logger)
        self.opportunity_identifier = OpportunityIdentifier(config, logger)
        self.roi_calculator = None  # Created in setup after loading margin data
        self.sellthrough_validator = None  # Created in setup
        self.results_aggregator = ResultsAggregator(config, logger)
        self.report_generator = SellThroughReportGenerator(config, logger)
    
    def setup(self, context: StepContext) -> StepContext:
        """
        SETUP Phase: Load all required data.
        
        Returns:
            Context with loaded data
        """
        self.logger.info("Loading data for missing category analysis...")
        
        # Load data via data loader component
        cluster_df, sales_df, quantity_df = self.data_loader.load_all_data()
        
        # Load margin rates for ROI calculation
        margin_df = self.margin_repo.load_margin_rates(
            self.config.analysis_level
        )
        
        # Create ROI calculator with margin data
        self.roi_calculator = ROICalculator(margin_df, self.config, self.logger)
        
        # Initialize sell-through validator
        if SELLTHROUGH_VALIDATION_AVAILABLE:
            historical_data = load_historical_data_for_validation()
            validator = SellThroughValidator(historical_data)
            self.sellthrough_validator = SellThroughOpportunityValidator(
                validator, self.config, self.logger
            )
        else:
            raise RuntimeError("Sell-through validator required")
        
        # Store in context
        context.data = {
            'cluster_df': cluster_df,
            'sales_df': sales_df,
            'quantity_df': quantity_df,
            'margin_df': margin_df
        }
        
        self.logger.info(f"Loaded data: {len(cluster_df)} stores, {len(sales_df)} sales records")
        
        return context
    
    def apply(self, context: StepContext) -> StepContext:
        """
        APPLY Phase: Identify and validate opportunities.
        
        Business logic:
        1. Identify well-selling features in clusters
        2. Find missing opportunities
        3. Validate with sell-through analysis
        4. Calculate ROI metrics
        5. Aggregate to store results
        
        Returns:
            Context with results
        """
        cluster_df = context.data['cluster_df']
        sales_df = context.data['sales_df']
        quantity_df = context.data['quantity_df']
        
        self.logger.info("Analyzing cluster patterns...")
        
        # Step 1: Identify well-selling features
        well_selling = self.cluster_analyzer.identify_well_selling_features(
            sales_df, cluster_df
        )
        
        # Step 2: Identify missing opportunities
        opportunities = self.opportunity_identifier.identify_missing_opportunities(
            sales_df, cluster_df, well_selling, quantity_df
        )
        
        # Step 3: Validate with sell-through
        validated_opportunities = self.sellthrough_validator.validate_opportunities(
            opportunities, sales_df, cluster_df
        )
        
        # Step 4: Calculate ROI metrics (if enabled)
        if self.config.use_roi:
            validated_opportunities = self.roi_calculator.calculate_roi_metrics(
                validated_opportunities, sales_df, cluster_df
            )
        
        # Step 5: Aggregate to store results
        results_df = self.results_aggregator.aggregate_to_store_results(
            cluster_df, validated_opportunities
        )
        
        # Store results in context
        context.data['results'] = results_df
        context.data['opportunities'] = validated_opportunities
        
        self.logger.info(f"Identified {len(validated_opportunities)} validated opportunities")
        
        return context
    
    def validate(self, context: StepContext) -> None:
        """
        VALIDATE Phase: Verify results meet business constraints.
        
        Raises:
            DataValidationError: If validation fails
        """
        results = context.data.get('results')
        opportunities = context.data.get('opportunities')
        
        # Check 1: Results exist
        if results is None or results.empty:
            raise DataValidationError("No results generated")
        
        # Check 2: Required columns present
        required_cols = [
            'str_code', 'cluster_id', 'total_quantity_needed',
            'total_investment_required', 'total_retail_value'
        ]
        missing_cols = [col for col in required_cols if col not in results.columns]
        if missing_cols:
            raise DataValidationError(f"Missing required columns: {missing_cols}")
        
        # Check 3: No negative quantities
        if 'total_quantity_needed' in results.columns:
            if (results['total_quantity_needed'] < 0).any():
                raise DataValidationError("Negative quantities found")
        
        # Check 4: Opportunities have required columns
        if opportunities is not None and not opportunities.empty:
            opp_required = [
                'str_code', 'spu_code', 'recommended_quantity_change',
                'unit_price', 'investment_required'
            ]
            missing_opp = [col for col in opp_required if col not in opportunities.columns]
            if missing_opp:
                raise DataValidationError(f"Opportunities missing columns: {missing_opp}")
        
        self.logger.info(f"Validation passed: {len(results)} stores, {len(opportunities) if opportunities is not None else 0} opportunities")
    
    def persist(self, context: StepContext) -> StepContext:
        """
        PERSIST Phase: Save results and reports.
        
        Returns:
            Updated context
        """
        results_df = context.data['results']
        opportunities_df = context.data['opportunities']
        
        # Save results via repository
        results_path = self.output_repo.save(results_df)
        self.logger.info(f"Saved results: {results_path}")
        
        # Save opportunities if any
        if opportunities_df is not None and not opportunities_df.empty:
            opp_path = self.output_repo.save(opportunities_df, suffix='_opportunities')
            self.logger.info(f"Saved opportunities: {opp_path}")
            
            # Generate report
            report_path = results_path.replace('.csv', '_summary.md')
            self.report_generator.generate_summary_report(
                opportunities_df, results_df, report_path
            )
            self.logger.info(f"Generated report: {report_path}")
        
        return context
```

**CUPID Compliance:**
- ✅ **Composable:** Uses injected components
- ✅ **Unix Philosophy:** Orchestrates, doesn't implement
- ✅ **Predictable:** Clear 4-phase pattern
- ✅ **Idiomatic:** Follows Step pattern
- ✅ **Domain-based:** Business method names

---

## 📁 Final File Structure

```
src/
├── steps/
│   └── missing_category_rule_step.py          (~450 LOC) ✅
│
├── components/
│   └── missing_category/
│       ├── __init__.py
│       ├── config.py                          (~150 LOC) ✅
│       ├── data_loader.py                     (~200 LOC) ✅
│       ├── cluster_analyzer.py                (~150 LOC) ✅
│       ├── opportunity_identifier.py          (~250 LOC) ✅
│       ├── sellthrough_validator.py           (~200 LOC) ✅
│       ├── roi_calculator.py                  (~150 LOC) ✅
│       ├── results_aggregator.py              (~150 LOC) ✅
│       └── report_generator.py                (~150 LOC) ✅
│
├── repositories/
│   ├── cluster_repository.py                  (existing or new)
│   ├── sales_repository.py                    (existing or new)
│   ├── quantity_repository.py                 (new)
│   └── margin_repository.py                   (new)
│
└── factories/
    └── step7_factory.py                       (~100 LOC) ✅
```

**Total LOC:** ~2,000 LOC (distributed across 13 files)  
**Largest File:** 450 LOC (main step) ✅  
**Average File Size:** ~154 LOC ✅

---

## ✅ CUPID Compliance Verification

| Component | Composable | Unix Philosophy | Predictable | Idiomatic | Domain-based |
|-----------|-----------|-----------------|-------------|-----------|--------------|
| Config | ✅ | ✅ | ✅ | ✅ | ✅ |
| DataLoader | ✅ | ✅ | ✅ | ✅ | ✅ |
| ClusterAnalyzer | ✅ | ✅ | ✅ | ✅ | ✅ |
| OpportunityIdentifier | ✅ | ✅ | ✅ | ✅ | ✅ |
| SellThroughValidator | ✅ | ✅ | ✅ | ✅ | ✅ |
| ROICalculator | ✅ | ✅ | ✅ | ✅ | ✅ |
| ResultsAggregator | ✅ | ✅ | ✅ | ✅ | ✅ |
| ReportGenerator | ✅ | ✅ | ✅ | ✅ | ✅ |
| MissingCategoryRuleStep | ✅ | ✅ | ✅ | ✅ | ✅ |

**All components pass CUPID compliance! ✅**

---

## 🔄 Migration Strategy

### Phase 1: Create Component Structure
1. Create `src/components/missing_category/` directory
2. Create `__init__.py` with component exports
3. Create empty component files

### Phase 2: Extract Configuration
1. Create `config.py` with dataclass
2. Move all global constants
3. Add `from_env_and_args()` factory method

### Phase 3: Extract Components (One at a Time)
1. Start with simplest: `ClusterAnalyzer`
2. Then: `OpportunityIdentifier`
3. Then: `SellThroughValidator`
4. Then: `ROICalculator`
5. Then: `ResultsAggregator`
6. Then: `ReportGenerator`
7. Finally: `DataLoader`

### Phase 4: Create Main Step
1. Create `MissingCategoryRuleStep` class
2. Implement 4-phase pattern
3. Wire up all components

### Phase 5: Create Repositories
1. `ClusterRepository` (if not exists)
2. `SalesRepository` (if not exists)
3. `QuantityRepository`
4. `MarginRepository`

### Phase 6: Create Factory
1. Create `step7_factory.py`
2. Implement dependency injection
3. Create all repositories
4. Create all components
5. Create step instance

---

## 🎯 Benefits of This Design

### Maintainability
- ✅ Each file ≤ 500 LOC (easy to understand)
- ✅ Single responsibility per component
- ✅ Clear separation of concerns

### Testability
- ✅ Each component can be tested independently
- ✅ Easy to mock dependencies
- ✅ Clear input/output contracts

### Reusability
- ✅ Components can be used in other steps
- ✅ `OpportunityIdentifier` could be used in other rules
- ✅ `ROICalculator` is reusable

### Extensibility
- ✅ Easy to add new validation strategies
- ✅ Easy to add new data sources
- ✅ Easy to modify business logic

### Performance
- ✅ Can optimize individual components
- ✅ Can parallelize independent operations
- ✅ Clear bottleneck identification

---

## 🚨 Critical Success Factors

1. **NO `algorithms/` folder** - Business logic stays in components
2. **ALL imports at top** - No inline imports
3. **Repository pattern** - No hard-coded paths
4. **Dependency injection** - All dependencies via constructor
5. **VALIDATE returns None** - Not StepContext
6. **File size ≤ 500 LOC** - Mandatory for all files

---

**This plan ensures Step 7 refactoring follows ALL architectural requirements while achieving CUPID compliance and maintaining all business functionality.**
