"""Debug test to understand why E2E test produces no opportunities."""

import pytest
import fireducks.pandas as pd
from src.components.missing_category.cluster_analyzer import ClusterAnalyzer
from src.components.missing_category.opportunity_identifier import OpportunityIdentifier
from src.components.missing_category.config import MissingCategoryConfig
from src.core.logger import PipelineLogger

def test_debug_well_selling_identification():
    """Debug: Check if well-selling features are identified correctly."""
    
    # Setup
    config = MissingCategoryConfig(
        analysis_level='subcategory',
        min_cluster_stores_selling=0.70,
        min_cluster_sales_threshold=100.0,
        period_label='202510A'
    )
    logger = PipelineLogger("Debug")
    analyzer = ClusterAnalyzer(config, logger)
    
    # Create mock cluster data
    cluster_df = pd.DataFrame({
        'str_code': [f'{i:04d}' for i in range(1, 51)],
        'cluster_id': [1]*20 + [2]*20 + [3]*10
    })
    
    # Create mock sales data
    data = []
    # Cluster 1: 15 out of 20 stores sell each category
    for i in range(1, 16):
        data.extend([
            {'str_code': f'{i:04d}', 'sub_cate_name': '直筒裤', 'sal_amt': 1000.0 + i*10},
            {'str_code': f'{i:04d}', 'sub_cate_name': '锥形裤', 'sal_amt': 800.0 + i*10},
            {'str_code': f'{i:04d}', 'sub_cate_name': '喇叭裤', 'sal_amt': 600.0 + i*10},
        ])
    
    # Cluster 2: 16 out of 20 stores sell each category
    for i in range(21, 37):
        data.extend([
            {'str_code': f'{i:04d}', 'sub_cate_name': '直筒裤', 'sal_amt': 1000.0 + i*10},
            {'str_code': f'{i:04d}', 'sub_cate_name': '锥形裤', 'sal_amt': 800.0 + i*10},
            {'str_code': f'{i:04d}', 'sub_cate_name': '喇叭裤', 'sal_amt': 600.0 + i*10},
        ])
    
    # Cluster 3: 8 out of 10 stores sell each category
    for i in range(41, 49):
        data.extend([
            {'str_code': f'{i:04d}', 'sub_cate_name': '直筒裤', 'sal_amt': 1000.0 + i*10},
            {'str_code': f'{i:04d}', 'sub_cate_name': '锥形裤', 'sal_amt': 800.0 + i*10},
            {'str_code': f'{i:04d}', 'sub_cate_name': '喇叭裤', 'sal_amt': 600.0 + i*10},
        ])
    
    sales_df = pd.DataFrame(data)
    
    print(f"\n=== DEBUG: Sales Data ===")
    print(f"Total sales records: {len(sales_df)}")
    print(f"Unique stores: {sales_df['str_code'].nunique()}")
    print(f"Unique categories: {sales_df['sub_cate_name'].nunique()}")
    print(f"Categories: {sales_df['sub_cate_name'].unique()}")
    print(f"\nSales amount stats:")
    print(sales_df.groupby('sub_cate_name')['sal_amt'].agg(['count', 'sum', 'mean']))
    
    # Identify well-selling features
    well_selling = analyzer.identify_well_selling_features(sales_df, cluster_df)
    
    print(f"\n=== DEBUG: Well-Selling Features ===")
    print(f"Well-selling features found: {len(well_selling)}")
    
    if len(well_selling) > 0:
        print(f"\nWell-selling features:")
        print(well_selling[['cluster_id', 'sub_cate_name', 'stores_selling', 'cluster_size', 
                            'pct_stores_selling', 'total_cluster_sales']])
    else:
        print("❌ NO WELL-SELLING FEATURES IDENTIFIED!")
        print("\nThis is the root cause - no opportunities can be generated without well-selling features.")
    
    # Expected: 9 feature-cluster combinations (3 categories × 3 clusters)
    assert len(well_selling) > 0, "Should identify at least some well-selling features"
    assert len(well_selling) == 9, f"Expected 9 combinations, got {len(well_selling)}"


def test_debug_opportunity_identification():
    """Debug: Check if opportunities are identified correctly given well-selling features."""
    
    # Setup
    config = MissingCategoryConfig(
        analysis_level='subcategory',
        min_cluster_stores_selling=0.70,
        min_cluster_sales_threshold=100.0,
        min_opportunity_value=10.0,
        period_label='202510A'
    )
    logger = PipelineLogger("Debug")
    identifier = OpportunityIdentifier(config, logger)
    
    # Create mock data
    cluster_df = pd.DataFrame({
        'str_code': [f'{i:04d}' for i in range(1, 51)],
        'cluster_id': [1]*20 + [2]*20 + [3]*10
    })
    
    # Well-selling features (manually created to bypass the analyzer)
    well_selling_df = pd.DataFrame([
        {'cluster_id': 1, 'sub_cate_name': '直筒裤', 'stores_selling': 15, 'cluster_size': 20, 
         'pct_stores_selling': 0.75, 'total_cluster_sales': 16125.0},
        {'cluster_id': 1, 'sub_cate_name': '锥形裤', 'stores_selling': 15, 'cluster_size': 20,
         'pct_stores_selling': 0.75, 'total_cluster_sales': 13125.0},
        {'cluster_id': 1, 'sub_cate_name': '喇叭裤', 'stores_selling': 15, 'cluster_size': 20,
         'pct_stores_selling': 0.75, 'total_cluster_sales': 10125.0},
    ])
    
    # Sales data
    data = []
    for i in range(1, 16):  # Stores 1-15 sell
        data.extend([
            {'str_code': f'{i:04d}', 'sub_cate_name': '直筒裤', 'sal_amt': 1000.0 + i*10},
            {'str_code': f'{i:04d}', 'sub_cate_name': '锥形裤', 'sal_amt': 800.0 + i*10},
            {'str_code': f'{i:04d}', 'sub_cate_name': '喇叭裤', 'sal_amt': 600.0 + i*10},
        ])
    sales_df = pd.DataFrame(data)
    
    # Quantity data with prices
    quantity_df = pd.DataFrame([
        {'str_code': f'{i:04d}', 'sub_cate_name': '直筒裤', 'avg_unit_price': 100.0}
        for i in range(1, 51)
    ] + [
        {'str_code': f'{i:04d}', 'sub_cate_name': '锥形裤', 'avg_unit_price': 90.0}
        for i in range(1, 51)
    ] + [
        {'str_code': f'{i:04d}', 'sub_cate_name': '喇叭裤', 'avg_unit_price': 80.0}
        for i in range(1, 51)
    ])
    
    print(f"\n=== DEBUG: Opportunity Identification ===")
    print(f"Well-selling features: {len(well_selling_df)}")
    print(f"Cluster 1 stores: 20 (stores 0001-0020)")
    print(f"Stores selling: 15 (stores 0001-0015)")
    print(f"Missing stores: 5 (stores 0016-0020)")
    print(f"Expected opportunities: 5 stores × 3 categories = 15")
    
    # Identify opportunities
    opportunities = identifier.identify_missing_opportunities(
        well_selling_df, cluster_df, sales_df, quantity_df
    )
    
    print(f"\nOpportunities identified: {len(opportunities)}")
    
    if len(opportunities) > 0:
        print(f"\nFirst few opportunities:")
        print(opportunities.head(10))
    else:
        print("❌ NO OPPORTUNITIES IDENTIFIED!")
        print("Even with well-selling features provided, no opportunities were generated.")
    
    # Expected: 15 opportunities for Cluster 1
    assert len(opportunities) > 0, "Should identify opportunities for missing stores"
    assert len(opportunities) == 15, f"Expected 15 opportunities, got {len(opportunities)}"


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
