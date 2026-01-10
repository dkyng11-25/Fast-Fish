"""
Test Data Utilities - Extract Sensible Subsets from Real Data

This module provides utilities to extract coherent subsets of real pipeline data
for testing purposes. Instead of creating synthetic data, we take real data subsets
that maintain referential integrity and business logic.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def extract_store_subset(
    source_periods: List[str],
    num_stores: int = 3,
    output_dir: Path = None
) -> Dict[str, pd.DataFrame]:
    """
    Extract a coherent subset of stores across multiple periods.
    
    This ensures:
    - Same stores appear in all periods
    - All related data (SPU sales, categories) is included
    - Referential integrity is maintained
    
    Args:
        source_periods: List of periods like ['202509A', '202509B', '202510A']
        num_stores: Number of stores to extract
        output_dir: Where to save extracted files
        
    Returns:
        Dict mapping period to DataFrames
    """
    api_data_dir = PROJECT_ROOT / "data" / "api_data"
    
    # Step 1: Get stores that exist in ALL periods
    common_stores = None
    
    for period in source_periods:
        store_config_file = api_data_dir / f"store_config_{period}.csv"
        if not store_config_file.exists():
            print(f"⚠️  Missing: {store_config_file}")
            continue
            
        df = pd.read_csv(store_config_file, dtype={'str_code': str}, nrows=10000)
        stores_in_period = set(df['str_code'].unique())
        
        if common_stores is None:
            common_stores = stores_in_period
        else:
            common_stores = common_stores.intersection(stores_in_period)
    
    # Step 2: Select subset of stores
    selected_stores = sorted(list(common_stores))[:num_stores]
    print(f"✅ Selected {len(selected_stores)} stores: {selected_stores}")
    
    # Step 3: Extract data for these stores across all periods
    extracted_data = {}
    
    for period in source_periods:
        period_data = {}
        
        # Extract store_config
        store_config_file = api_data_dir / f"store_config_{period}.csv"
        if store_config_file.exists():
            df = pd.read_csv(store_config_file, dtype={'str_code': str})
            period_data['store_config'] = df[df['str_code'].isin(selected_stores)]
            print(f"   {period} store_config: {len(period_data['store_config'])} rows")
        
        # Extract SPU sales
        spu_sales_file = api_data_dir / f"complete_spu_sales_{period}.csv"
        if spu_sales_file.exists():
            df = pd.read_csv(spu_sales_file, dtype={'str_code': str})
            period_data['spu_sales'] = df[df['str_code'].isin(selected_stores)]
            print(f"   {period} spu_sales: {len(period_data['spu_sales'])} rows")
        
        # Extract category sales
        cat_sales_file = api_data_dir / f"complete_category_sales_{period}.csv"
        if cat_sales_file.exists():
            df = pd.read_csv(cat_sales_file, dtype={'str_code': str})
            period_data['category_sales'] = df[df['str_code'].isin(selected_stores)]
            print(f"   {period} category_sales: {len(period_data['category_sales'])} rows")
        
        extracted_data[period] = period_data
        
        # Save to output directory if specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            for data_type, data_df in period_data.items():
                if data_type == 'store_config':
                    filename = f"store_config_{period}.csv"
                elif data_type == 'spu_sales':
                    filename = f"complete_spu_sales_{period}.csv"
                elif data_type == 'category_sales':
                    filename = f"complete_category_sales_{period}.csv"
                
                output_file = output_dir / filename
                data_df.to_csv(output_file, index=False)
                print(f"   💾 Saved: {output_file}")
    
    return extracted_data


def extract_clustering_data(
    selected_stores: List[str],
    output_dir: Path = None
) -> pd.DataFrame:
    """Extract clustering results for selected stores."""
    
    # Try multiple possible locations
    possible_files = [
        PROJECT_ROOT / "output" / "clustering_results_spu.csv",
        PROJECT_ROOT / "output" / "clustering_results_spu_202510A.csv",
        PROJECT_ROOT / "data" / "clustering_results.csv"
    ]
    
    for clustering_file in possible_files:
        if clustering_file.exists():
            df = pd.read_csv(clustering_file, dtype={'str_code': str})
            
            # Filter to selected stores
            subset = df[df['str_code'].isin(selected_stores)]
            
            if output_dir and len(subset) > 0:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / "clustering_results_spu.csv"
                subset.to_csv(output_file, index=False)
                print(f"✅ Saved clustering: {output_file} ({len(subset)} stores)")
            
            return subset
    
    print("⚠️  No clustering file found")
    return pd.DataFrame()


if __name__ == "__main__":
    # Example usage
    print("=== Extracting Test Data Subset ===\n")
    
    # Extract 3 stores across 3 periods
    periods = ['202509B', '202510A', '202510B']
    test_output = PROJECT_ROOT / "tests" / "test_data_subset"
    
    data = extract_store_subset(
        source_periods=periods,
        num_stores=3,
        output_dir=test_output
    )
    
    # Extract clustering
    if data and periods[0] in data:
        stores = data[periods[0]]['store_config']['str_code'].unique().tolist()
        extract_clustering_data(stores, test_output)
    
    print("\n✅ Test data extraction complete!")
