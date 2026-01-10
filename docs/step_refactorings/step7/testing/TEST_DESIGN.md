# Step 7: Missing Category/SPU Rule - Test Design

**Date:** 2025-11-03  
**Status:** ✅ COMPLETE  
**Framework:** pytest-bdd  
**Test File:** `tests/step_definitions/test_step7_missing_category_rule.py`  
**Feature File:** `tests/features/step-7-missing-category-rule.feature`

---

## 📋 Test Design Overview

### Testing Strategy
- **Framework:** pytest-bdd (Gherkin-based BDD testing)
- **Approach:** Mock all repositories, test business logic
- **Data:** Synthetic test data with realistic structures
- **Coverage:** 35 scenarios across all 4 phases + integration + edge cases

### Test Organization
- Tests organized by scenario (NOT by decorator type)
- Each scenario has clear Given-When-Then structure
- Fixtures provide test data and mocked dependencies
- All tests call `step_instance.execute()` (not individual methods)

---

## 🏗️ Test Architecture

### Fixture Structure

```python
@pytest.fixture
def mock_cluster_repo(mocker):
    """Mock cluster repository with synthetic clustering data."""
    repo = mocker.Mock(spec=ClusterRepository)
    
    # Synthetic clustering data: 3 clusters, 50 stores
    cluster_data = pd.DataFrame({
        'str_code': [f'{i:04d}' for i in range(1, 51)],
        'cluster_id': [1]*20 + [2]*20 + [3]*10,
        'cluster_name': ['Cluster_1']*20 + ['Cluster_2']*20 + ['Cluster_3']*10
    })
    
    repo.load_clustering_results.return_value = cluster_data
    return repo

@pytest.fixture
def mock_sales_repo(mocker):
    """Mock sales repository with synthetic sales data."""
    repo = mocker.Mock(spec=SalesRepository)
    
    # Synthetic sales data: subcategories with varying adoption
    sales_data = pd.DataFrame({
        'str_code': [...],  # Store codes
        'sub_cate_name': [...],  # Subcategory names
        'sal_amt': [...],  # Sales amounts
        'spu_code': [...]  # SPU codes (for SPU mode)
    })
    
    repo.load_sales_data.return_value = sales_data
    return repo

@pytest.fixture
def mock_quantity_repo(mocker):
    """Mock quantity repository with synthetic quantity data."""
    repo = mocker.Mock(spec=QuantityRepository)
    
    # Synthetic quantity data with real unit prices
    quantity_data = pd.DataFrame({
        'str_code': [...],
        'total_qty': [...],
        'total_amt': [...],
        'avg_unit_price': [...]  # Pre-calculated prices
    })
    
    repo.load_quantity_data.return_value = quantity_data
    return repo

@pytest.fixture
def mock_margin_repo(mocker):
    """Mock margin repository with synthetic margin rates."""
    repo = mocker.Mock(spec=MarginRepository)
    
    # Synthetic margin rates
    margin_data = pd.DataFrame({
        'str_code': [...],
        'spu_code': [...],
        'margin_rate': [...]  # 0.35 to 0.50 range
    })
    
    repo.load_margin_rates.return_value = margin_data
    return repo

@pytest.fixture
def mock_output_repo(mocker):
    """Mock output repository for file saving."""
    repo = mocker.Mock(spec=CsvFileRepository)
    repo.save.return_value = "output/test_file.csv"
    return repo

@pytest.fixture
def mock_sellthrough_validator(mocker):
    """Mock sell-through validator."""
    validator = mocker.Mock(spec=SellThroughValidator)
    
    # Default: approve all with 50% predicted sell-through
    validator.validate_recommendation.return_value = {
        'fast_fish_compliant': True,
        'predicted_sell_through_rate': 50.0,
        'current_sell_through_rate': 0.0,
        'business_rationale': 'Test approval',
        'approval_reason': 'Mock validator'
    }
    
    return validator

@pytest.fixture
def step_config():
    """Configuration for missing category rule step."""
    return MissingCategoryConfig(
        analysis_level='subcategory',
        min_cluster_stores_selling=0.70,
        min_cluster_sales_threshold=100.0,
        min_opportunity_value=50.0,
        data_period_days=15,
        target_period_days=15,
        use_roi=False,  # Disable ROI for simpler tests
        min_stores_selling=5,
        min_adoption=0.25,
        min_predicted_st=30.0
    )

@pytest.fixture
def step_instance(
    mock_cluster_repo,
    mock_sales_repo,
    mock_quantity_repo,
    mock_margin_repo,
    mock_output_repo,
    mock_sellthrough_validator,
    step_config,
    mock_logger
):
    """Create step instance with all mocked dependencies."""
    return MissingCategoryRuleStep(
        cluster_repo=mock_cluster_repo,
        sales_repo=mock_sales_repo,
        quantity_repo=mock_quantity_repo,
        margin_repo=mock_margin_repo,
        output_repo=mock_output_repo,
        sellthrough_validator=mock_sellthrough_validator,
        config=step_config,
        logger=mock_logger,
        step_name="Missing Category Rule",
        step_number=7
    )

@pytest.fixture
def test_context():
    """Test context for storing state between steps."""
    return {}
```

---

## 🎯 Test Scenarios by Phase

### SETUP Phase Tests (8 scenarios)

**Test Group 1: Clustering Data Loading**
```python
# ============================================================
# Scenario 1: Load clustering results with column normalization
# ============================================================

@given('a clustering results file exists with "Cluster" column')
def clustering_with_cluster_column(mock_cluster_repo):
    # Mock returns data with "Cluster" instead of "cluster_id"
    data = pd.DataFrame({
        'str_code': ['0001', '0002'],
        'Cluster': [1, 1]  # Note: "Cluster" not "cluster_id"
    })
    mock_cluster_repo.load_clustering_results.return_value = data

@when('loading clustering data')
def load_clustering(step_instance, test_context):
    context = StepContext()
    result = step_instance.setup(context)
    test_context['setup_result'] = result

@then('the "Cluster" column is normalized to "cluster_id"')
def verify_cluster_normalization(test_context):
    result = test_context['setup_result']
    cluster_df = result.data['cluster_df']
    assert 'cluster_id' in cluster_df.columns
    assert 'Cluster' not in cluster_df.columns or cluster_df['Cluster'].equals(cluster_df['cluster_id'])
```

**Test Group 2: Sales Data with Seasonal Blending**
```python
# ============================================================
# Scenario 2: Load sales data with seasonal blending
# ============================================================

@given('current period sales data exists (202510A)')
def current_sales_data(mock_sales_repo):
    current_data = pd.DataFrame({
        'str_code': ['0001', '0002'],
        'sub_cate_name': ['直筒裤', '锥形裤'],
        'sal_amt': [1000.0, 1500.0]
    })
    mock_sales_repo.load_current_sales.return_value = current_data

@given('seasonal period data exists (202409A from last year)')
def seasonal_sales_data(mock_sales_repo):
    seasonal_data = pd.DataFrame({
        'str_code': ['0001', '0002'],
        'sub_cate_name': ['直筒裤', '锥形裤'],
        'sal_amt': [800.0, 1200.0]
    })
    mock_sales_repo.load_seasonal_sales.return_value = seasonal_data

@given('seasonal blending is enabled with 60% seasonal weight')
def enable_seasonal_blending(step_config):
    step_config.use_blended_seasonal = True
    step_config.seasonal_weight = 0.6
    step_config.recent_weight = 0.4

@when('loading sales data')
def load_sales(step_instance, test_context):
    # Execute setup phase
    context = StepContext()
    result = step_instance.setup(context)
    test_context['setup_result'] = result

@then('current period sales are weighted by 40%')
def verify_current_weight(test_context):
    # Verify weighting was applied
    result = test_context['setup_result']
    sales_df = result.data['sales_df']
    # Check that blended values reflect 40% current + 60% seasonal
    # For store 0001, 直筒裤: 1000*0.4 + 800*0.6 = 880
    assert sales_df[sales_df['str_code'] == '0001']['sal_amt'].iloc[0] == pytest.approx(880.0)
```

**Test Group 3: Quantity Data with Price Backfill**
```python
# ============================================================
# Scenario 3: Backfill missing unit prices from historical data
# ============================================================

@given('current period has no unit prices (all NA)')
def no_current_prices(mock_quantity_repo):
    current_data = pd.DataFrame({
        'str_code': ['0001', '0002'],
        'total_qty': [0, 0],
        'total_amt': [0, 0],
        'avg_unit_price': [np.nan, np.nan]
    })
    mock_quantity_repo.load_quantity_data.return_value = current_data

@given('historical data exists for previous 6 half-months')
def historical_price_data(mock_quantity_repo):
    historical_data = pd.DataFrame({
        'str_code': ['0001', '0002'],
        'avg_unit_price': [45.0, 52.0]
    })
    mock_quantity_repo.load_historical_prices.return_value = historical_data

@when('loading quantity data')
def load_quantity(step_instance, test_context):
    context = StepContext()
    result = step_instance.setup(context)
    test_context['setup_result'] = result

@then('missing prices are filled with historical medians')
def verify_price_backfill(test_context):
    result = test_context['setup_result']
    quantity_df = result.data['quantity_df']
    assert quantity_df[quantity_df['str_code'] == '0001']['avg_unit_price'].iloc[0] == 45.0
    assert quantity_df[quantity_df['str_code'] == '0002']['avg_unit_price'].iloc[0] == 52.0
```

---

### APPLY Phase Tests (15 scenarios)

**Test Group 4: Well-Selling Feature Identification**
```python
# ============================================================
# Scenario 4: Identify well-selling subcategories in clusters
# ============================================================

@given('sales data with 100 stores in cluster 1')
def cluster_sales_data(test_context):
    # Create synthetic sales data
    test_context['cluster_size'] = 100

@given('90 stores sell "直筒裤" with total sales of $150,000')
def high_adoption_category(test_context):
    test_context['category_1'] = {
        'name': '直筒裤',
        'stores_selling': 90,
        'total_sales': 150000
    }

@when('identifying well-selling features')
def identify_well_selling(step_instance, test_context):
    context = StepContext()
    context = step_instance.setup(context)
    context = step_instance.apply(context)
    test_context['apply_result'] = context

@then('"直筒裤" is identified as well-selling (90% adoption, $150k sales)')
def verify_well_selling(test_context):
    result = test_context['apply_result']
    well_selling = result.data['well_selling_features']
    
    category_row = well_selling[well_selling['sub_cate_name'] == '直筒裤']
    assert len(category_row) > 0
    assert category_row['pct_stores_selling'].iloc[0] >= 0.70
    assert category_row['total_cluster_sales'].iloc[0] >= 100
```

**Test Group 5: Sell-Through Validation**
```python
# ============================================================
# Scenario 5: Approve opportunity meeting all criteria
# ============================================================

@given('a missing opportunity for store "1001"')
def missing_opportunity(test_context):
    test_context['store_code'] = '1001'

@given('45 stores in cluster sell this feature (90% adoption)')
def high_adoption(test_context):
    test_context['stores_selling'] = 45
    test_context['pct_adoption'] = 0.90

@given('sell-through validator predicts 55% sell-through')
def high_predicted_st(mock_sellthrough_validator):
    mock_sellthrough_validator.validate_recommendation.return_value = {
        'fast_fish_compliant': True,
        'predicted_sell_through_rate': 55.0,
        'current_sell_through_rate': 0.0
    }

@when('validating with sell-through')
def validate_sellthrough(step_instance, test_context):
    context = StepContext()
    context = step_instance.setup(context)
    context = step_instance.apply(context)
    test_context['apply_result'] = context

@then('opportunity is approved')
def verify_approved(test_context):
    result = test_context['apply_result']
    opportunities = result.data['opportunities']
    
    opp = opportunities[opportunities['str_code'] == '1001']
    assert len(opp) > 0
    assert opp['fast_fish_compliant'].iloc[0] == True
```

---

### VALIDATE Phase Tests (4 scenarios)

```python
# ============================================================
# Scenario 6: Validate results have required columns
# ============================================================

@given('store results DataFrame is generated')
def results_generated(step_instance, test_context):
    context = StepContext()
    context = step_instance.setup(context)
    context = step_instance.apply(context)
    test_context['apply_result'] = context

@when('validating results')
def validate_results(step_instance, test_context):
    context = test_context['apply_result']
    try:
        step_instance.validate(context)
        test_context['validation_passed'] = True
    except DataValidationError as e:
        test_context['validation_error'] = e

@then('required columns are present')
def verify_required_columns(test_context):
    assert test_context.get('validation_passed') == True
    
    result = test_context['apply_result']
    results_df = result.data['results']
    
    required_cols = ['str_code', 'cluster_id', 'total_quantity_needed',
                     'total_investment_required', 'total_retail_value']
    for col in required_cols:
        assert col in results_df.columns

@then('no DataValidationError is raised')
def verify_no_error(test_context):
    assert 'validation_error' not in test_context
```

---

### PERSIST Phase Tests (3 scenarios)

```python
# ============================================================
# Scenario 7: Save opportunities CSV with timestamped filename
# ============================================================

@given('opportunities DataFrame with 150 records')
def opportunities_data(test_context):
    test_context['num_opportunities'] = 150

@when('persisting opportunities')
def persist_opportunities(step_instance, test_context):
    context = StepContext()
    context = step_instance.setup(context)
    context = step_instance.apply(context)
    step_instance.validate(context)
    result = step_instance.persist(context)
    test_context['persist_result'] = result

@then('timestamped file is created')
def verify_timestamped_file(test_context, mock_output_repo):
    # Verify save was called
    assert mock_output_repo.save.called
    
    # Verify filename pattern
    call_args = mock_output_repo.save.call_args
    assert 'opportunities' in str(call_args)
```

---

## 🧪 Test Data Design

### Synthetic Data Principles
1. **Realistic structures** - Match actual data schemas
2. **Edge cases included** - Empty, single record, large datasets
3. **Business logic coverage** - Test all thresholds and rules
4. **No external dependencies** - All data mocked

### Sample Test Data

**Clustering Data:**
```python
cluster_data = pd.DataFrame({
    'str_code': ['0001', '0002', '0003', '0004', '0005'],
    'cluster_id': [1, 1, 1, 2, 2],
    'cluster_name': ['High_Volume', 'High_Volume', 'High_Volume', 'Medium_Volume', 'Medium_Volume']
})
```

**Sales Data:**
```python
sales_data = pd.DataFrame({
    'str_code': ['0001', '0001', '0002', '0002', '0003'],
    'sub_cate_name': ['直筒裤', '锥形裤', '直筒裤', '喇叭裤', '直筒裤'],
    'sal_amt': [1000.0, 800.0, 1200.0, 600.0, 900.0],
    'spu_code': ['SPU001', 'SPU002', 'SPU001', 'SPU003', 'SPU001']
})
```

**Quantity Data:**
```python
quantity_data = pd.DataFrame({
    'str_code': ['0001', '0002', '0003'],
    'total_qty': [100, 120, 90],
    'total_amt': [4500.0, 5400.0, 4050.0],
    'avg_unit_price': [45.0, 45.0, 45.0]
})
```

---

## ✅ Test Quality Standards

### Assertion Requirements
- ✅ **No placeholder assertions** (`assert True`)
- ✅ **Specific value checks** (not just type checks)
- ✅ **Error message validation** (check exception messages)
- ✅ **Binary outcomes** (PASS or FAIL, no conditionals)

### Test Organization
- ✅ **Grouped by scenario** (not by decorator)
- ✅ **Clear section headers** with scenario names
- ✅ **Matches feature file order**
- ✅ **Easy to read and validate**

### Coverage Requirements
- ✅ **Happy path** - Normal operation
- ✅ **Error cases** - Validation failures
- ✅ **Edge cases** - Boundary conditions
- ✅ **Business rules** - All thresholds tested

---

## 📊 Test Execution Plan

### Phase 2: Test Scaffolding
1. Create feature file with all scenarios
2. Create test file with fixtures
3. Implement @given, @when, @then steps
4. Run tests - expect ALL to FAIL (no implementation yet)

### Phase 4: Test Implementation
1. Implement Step 7 code
2. Run tests - expect some to PASS
3. Debug failures
4. Achieve 100% pass rate

### Continuous Testing
```bash
# Run all Step 7 tests
pytest tests/step_definitions/test_step7_missing_category_rule.py -v

# Run specific scenario
pytest tests/step_definitions/test_step7_missing_category_rule.py::test_scenario_name -v

# Run with coverage
pytest tests/step_definitions/test_step7_missing_category_rule.py --cov=src.steps.missing_category_rule_step
```

---

**Test Design Complete:** ✅  
**Next Step:** Create PHASE1_COMPLETE.md  
**Date:** 2025-11-03
