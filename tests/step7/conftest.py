"""
Shared fixtures for Step 7 Missing Category Rule tests.

This module contains all shared test fixtures including:
- Mock repositories (cluster, sales, quantity, margin, output)
- Mock validators (sell-through)
- Step configuration
- Step instance creation
- Test context management
"""

import pytest
import pandas as pd
from unittest.mock import Mock

from src.steps.missing_category_rule_step import MissingCategoryRuleStep
from src.components.missing_category.config import MissingCategoryConfig


@pytest.fixture
def test_context():
    """Test context for storing state between BDD steps."""
    return {}


@pytest.fixture
def mock_logger(mocker):
    """Mock pipeline logger."""
    logger = mocker.Mock()
    logger.info = mocker.Mock()
    logger.warning = mocker.Mock()
    logger.error = mocker.Mock()
    return logger


@pytest.fixture
def step_config():
    """Configuration for missing category rule step."""
    return MissingCategoryConfig(
        analysis_level='subcategory',
        min_cluster_stores_selling=0.70,  # 70% adoption threshold
        min_cluster_sales_threshold=100.0,  # $100 minimum sales
        min_opportunity_value=10.0,  # Lower threshold to allow opportunities
        data_period_days=15,
        target_period_days=15,
        use_roi=False,  # Disable ROI for simpler tests
        min_stores_selling=3,  # Lower threshold
        min_adoption=0.10,  # Lower to 10% to be more permissive
        min_predicted_st=0.0,  # Disable sell-through filtering for tests
        use_blended_seasonal=False,
        period_label='202510A'
    )


@pytest.fixture
def mock_cluster_repo(mocker):
    """Mock clustering repository with synthetic cluster data."""
    repo = mocker.Mock()
    
    # Synthetic cluster data: 3 clusters with varying sizes
    # Total 50 stores: Cluster 1 (20 stores), Cluster 2 (20 stores), Cluster 3 (10 stores)
    cluster_data = pd.DataFrame({
        'str_code': [f'{i:04d}' for i in range(1, 51)],  # 50 stores total
        'cluster_id': [1]*20 + [2]*20 + [3]*10,  # Cluster sizes
        'store_name': [f'Store {i}' for i in range(1, 51)],
        'region': ['North']*20 + ['South']*20 + ['East']*10
    })
    
    # Mock must accept any arguments (period_label parameter)
    repo.load_clustering_results = mocker.Mock(return_value=cluster_data)
    return repo


@pytest.fixture
def mock_sales_repo(mocker):
    """Mock sales repository with synthetic sales data."""
    repo = mocker.Mock()
    
    # Realistic sales data: High adoption to meet 70% threshold
    # KEY: Some stores DON'T sell categories - these create missing opportunities
    # Cluster 1 (stores 0001-0020): 15 stores sell each category (75% adoption)
    #   - Stores 0001-0015 SELL categories
    #   - Stores 0016-0020 DON'T SELL (5 missing opportunities per category)
    # Cluster 2 (stores 0021-0040): 16 stores sell each category (80% adoption)
    #   - Stores 0021-0036 SELL categories
    #   - Stores 0037-0040 DON'T SELL (4 missing opportunities per category)
    # Cluster 3 (stores 0041-0050): 8 stores sell each category (80% adoption)
    #   - Stores 0041-0048 SELL categories
    #   - Stores 0049-0050 DON'T SELL (2 missing opportunities per category)
    
    data = []
    # Cluster 1: 15 out of 20 stores sell each category (stores 1-15)
    for i in range(1, 16):
        data.extend([
            {'str_code': f'{i:04d}', 'sub_cate_name': '直筒裤', 'sal_amt': 1000.0 + i*10, 'spu_code': 'SPU001'},
            {'str_code': f'{i:04d}', 'sub_cate_name': '锥形裤', 'sal_amt': 800.0 + i*10, 'spu_code': 'SPU002'},
            {'str_code': f'{i:04d}', 'sub_cate_name': '喇叭裤', 'sal_amt': 600.0 + i*10, 'spu_code': 'SPU003'},
        ])
    # Stores 16-20 DON'T sell these categories (missing opportunities)
    
    # Cluster 2: 16 out of 20 stores sell each category (stores 21-36)
    for i in range(21, 37):
        data.extend([
            {'str_code': f'{i:04d}', 'sub_cate_name': '直筒裤', 'sal_amt': 1000.0 + i*10, 'spu_code': 'SPU001'},
            {'str_code': f'{i:04d}', 'sub_cate_name': '锥形裤', 'sal_amt': 800.0 + i*10, 'spu_code': 'SPU002'},
            {'str_code': f'{i:04d}', 'sub_cate_name': '喇叭裤', 'sal_amt': 600.0 + i*10, 'spu_code': 'SPU003'},
        ])
    # Stores 37-40 DON'T sell these categories (missing opportunities)
    
    # Cluster 3: 8 out of 10 stores sell each category (stores 41-48)
    for i in range(41, 49):
        data.extend([
            {'str_code': f'{i:04d}', 'sub_cate_name': '直筒裤', 'sal_amt': 1000.0 + i*10, 'spu_code': 'SPU001'},
            {'str_code': f'{i:04d}', 'sub_cate_name': '锥形裤', 'sal_amt': 800.0 + i*10, 'spu_code': 'SPU002'},
            {'str_code': f'{i:04d}', 'sub_cate_name': '喇叭裤', 'sal_amt': 600.0 + i*10, 'spu_code': 'SPU003'},
        ])
    # Stores 49-50 DON'T sell these categories (missing opportunities)
    
    sales_data = pd.DataFrame(data)
    
    # Create seasonal sales data (80% of current for numeric columns only)
    seasonal_sales = sales_data.copy()
    seasonal_sales['sal_amt'] = sales_data['sal_amt'] * 0.8
    
    # Mock must accept any arguments (period_label, seasonal_years_back parameters)
    repo.load_sales_data = mocker.Mock(return_value=sales_data)
    repo.load_current_sales = mocker.Mock(return_value=sales_data)
    repo.load_seasonal_sales = mocker.Mock(return_value=seasonal_sales)
    return repo


@pytest.fixture
def mock_quantity_repo(mocker):
    """Mock quantity repository with synthetic quantity data."""
    repo = mocker.Mock()
    
    # Synthetic quantity data with real unit prices
    # Must include feature column (sub_cate_name) for each store-category combination
    data = []
    for store_id in range(1, 51):
        for category in ['直筒裤', '锥形裤', '喇叭裤']:
            data.append({
                'str_code': f'{store_id:04d}',
                'sub_cate_name': category,
                'total_qty': 100,
                'total_amt': 4500.0,
                'avg_unit_price': 45.0
            })
    
    quantity_data = pd.DataFrame(data)
    
    # Mock must accept any arguments
    repo.load_quantity_data = mocker.Mock(side_effect=lambda *args, **kwargs: quantity_data)
    repo.load_historical_prices = mocker.Mock(side_effect=lambda *args, **kwargs: quantity_data[['str_code', 'sub_cate_name', 'avg_unit_price']])
    return repo


@pytest.fixture
def mock_margin_repo(mocker):
    """Mock margin repository with synthetic margin rates."""
    repo = mocker.Mock()
    
    # Synthetic margin rates
    margin_data = pd.DataFrame({
        'str_code': [f'{i:04d}' for i in range(1, 51)],
        'spu_code': ['SPU001'] * 50,
        'margin_rate': [0.40] * 50  # 40% margin
    })
    
    # Mock must accept any arguments
    repo.load_margin_rates = mocker.Mock(return_value=margin_data)
    return repo


@pytest.fixture
def mock_output_repo(mocker):
    """Mock output repository for file saving."""
    repo = mocker.Mock()
    repo.save.return_value = "output/test_file.csv"
    repo.create_symlink.return_value = None
    return repo


@pytest.fixture
def mock_sellthrough_validator(mocker):
    """Mock sell-through validator - returns high sell-through to allow opportunities."""
    validator = mocker.Mock()
    # Return high sell-through (85%) to ensure opportunities pass validation
    validator.predict_sellthrough.return_value = 0.85  # 85% predicted sell-through
    validator.validate_recommendation.return_value = {
        'fast_fish_compliant': True,
        'predicted_sell_through_rate': 85.0,
        'current_sell_through_rate': 0.0,
        'business_rationale': 'Test approval',
        'approval_reason': 'Mock validator'
    }
    return validator


@pytest.fixture
def step_instance(
    mock_cluster_repo,
    mock_sales_repo,
    mock_quantity_repo,
    mock_margin_repo,
    mock_output_repo,
    mock_sellthrough_validator,
    mock_logger,
    step_config
):
    """Create a fully configured step instance with all mocked dependencies."""
    return MissingCategoryRuleStep(
        cluster_repo=mock_cluster_repo,
        sales_repo=mock_sales_repo,
        quantity_repo=mock_quantity_repo,
        margin_repo=mock_margin_repo,
        output_repo=mock_output_repo,
        sellthrough_validator=mock_sellthrough_validator,
        logger=mock_logger,
        config=step_config
    )
