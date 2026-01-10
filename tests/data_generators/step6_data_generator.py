
import pandas as pd
import numpy as np
import os
from pathlib import Path
import sys
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent))

from sales_data import generate_sales_transactions, generate_daily_sales_summary
from spu_data import generate_spus
from store_data import generate_all_store_data

def generate_step6_test_data(
    n_stores: int = 100,
    n_spus: int = 200,
    start_date: str = '2024-06-01',
    end_date: str = '2024-08-31',
    output_base_dir: str = "tests"
) -> Dict[str, pd.DataFrame]:
    """
    Generates all necessary test data for Step 6 (cluster_analysis).

    Args:
        n_stores (int): Number of stores to generate.
        n_spus (int): Number of SPUs to generate.
        start_date (str): Start date for sales data generation (YYYY-MM-DD).
        end_date (str): End date for sales data generation (YYYY-MM-DD).
        output_base_dir (str): Base directory for saving output files (e.g., "tests").

    Returns:
        Dict[str, pd.DataFrame]: A dictionary containing the generated DataFrames.
    """
    print("🚀 Generating Step 6 test data...")
    
    # Define output directories
    data_dir = Path(output_base_dir) / "data"
    output_dir = Path(output_base_dir) / "output"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate core store and SPU data
    stores_dfs = generate_all_store_data(n_stores=n_stores)
    stores = stores_dfs['stores']
    stores_with_feels_like_temperature = stores_dfs['stores_with_feels_like_temperature']
    spus = generate_spus(n_spus)

    # 2. Generate sales data
    transactions = generate_sales_transactions(
        stores=stores,
        spus=spus,
        start_date=start_date,
        end_date=end_date,
        avg_daily_transactions=50
    )
    daily_sales = generate_daily_sales_summary(transactions, stores, spus)

    # 3. Create SPU-level matrix (simplified for testing)
    print("Creating SPU matrices...")
    # Ensure we have enough data for pivot table
    if len(daily_sales) > 0 and not daily_sales[['str_code', 'spu_code', 'sales_amount']].isnull().any().any():
        spu_matrix = daily_sales.pivot_table(
            index='str_code',
            columns='spu_code',
            values='sales_amount',
            fill_value=0
        )

        # Limit SPUs for a more realistic test matrix size, if too many
        if spu_matrix.shape[1] > 1000:
            top_spus = daily_sales.groupby('spu_code')['sales_amount'].sum().nlargest(1000).index
            spu_matrix = spu_matrix[top_spus]

        normalized_spu_matrix = spu_matrix.div(spu_matrix.sum(axis=1), axis=0).fillna(0)

        # Save matrices
        spu_matrix.to_csv(data_dir / "store_spu_limited_matrix.csv")
        normalized_spu_matrix.to_csv(data_dir / "normalized_spu_limited_matrix.csv")
        print(f"Saved SPU matrices to {data_dir}")
    else:
        print("No valid sales data to create SPU matrices.")
        # Create empty dummy files to prevent FileNotFoundError, for testing error handling
        pd.DataFrame().to_csv(data_dir / "store_spu_limited_matrix.csv")
        pd.DataFrame().to_csv(data_dir / "normalized_spu_limited_matrix.csv")

    # Save stores with feels like temperature
    stores_with_feels_like_temperature.to_csv(
        output_dir / "stores_with_feels_like_temperature.csv", index=False
    )
    print(f"Saved stores_with_feels_like_temperature to {output_dir}")

    print("✅ Step 6 test data generation complete!")

    return {
        'stores': stores,
        'spus': spus,
        'transactions': transactions,
        'daily_sales': daily_sales,
        'stores_with_feels_like_temperature': stores_with_feels_like_temperature
    }

if __name__ == "__main__":
    generate_step6_test_data(n_stores=200, n_spus=100)
