#!/usr/bin/env python3
"""
Generate synthetic fixtures for Step 7 isolated tests

Creates realistic test data that matches Step 7's expectations:
- Clustering results with store clusters
- SPU sales data with categories and subcategories
- Store sales data
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Set random seed for reproducibility
np.random.seed(42)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)

def generate_clustering_results():
    """Generate clustering_results_spu_202501A.csv"""
    
    # 50 stores across 3 clusters
    stores = [f"1100{i}" for i in range(1, 51)]
    
    data = {
        'str_code': stores,
        'cluster_id': np.random.choice([0, 1, 2], size=len(stores)),
        'cluster_name': [''] * len(stores),
        'store_type': np.random.choice(['Fashion', 'Balanced', 'Basic'], size=len(stores)),
        'capacity': np.random.randint(800, 1500, size=len(stores)),
        'fashion_ratio': np.random.uniform(0.2, 0.8, size=len(stores)),
    }
    
    df = pd.DataFrame(data)
    
    # Add cluster names
    cluster_names = {0: 'Fashion Forward', 1: 'Balanced Mix', 2: 'Basic Essentials'}
    df['cluster_name'] = df['cluster_id'].map(cluster_names)
    
    output_file = FIXTURES_DIR / "clustering_results_spu_202501A.csv"
    df.to_csv(output_file, index=False)
    print(f"✓ Created {output_file.name} ({len(df)} stores)")
    return df

def generate_spu_sales(period_label="202501A", seasonal=False):
    """Generate complete_spu_sales_YYYYMMA.csv"""
    
    # Categories and subcategories (Chinese names to match real data)
    categories = {
        'T恤': ['圆领T恤', '合体圆领T恤', 'V领T恤'],
        '休闲裤': ['女休闲裤', '男休闲裤', '直筒休闲裤'],
        '卫衣': ['套头卫衣', '拉链卫衣', '连帽卫衣'],
        '牛仔裤': ['直筒牛仔裤', '修身牛仔裤', '宽松牛仔裤'],
    }
    
    # Generate SPU codes
    rows = []
    spu_id = 1000
    
    for category, subcategories in categories.items():
        for subcategory in subcategories:
            # 5-10 SPUs per subcategory
            n_spus = np.random.randint(5, 11)
            
            for _ in range(n_spus):
                spu_code = f"SPU{spu_id:06d}"
                spu_id += 1
                
                # 10-30 stores sell this SPU
                n_stores = np.random.randint(10, 31)
                stores = np.random.choice(range(1, 51), size=n_stores, replace=False)
                
                for store_num in stores:
                    str_code = f"1100{store_num}"
                    
                    # Sales data
                    base_sales = np.random.randint(50, 500)
                    if seasonal:
                        # Seasonal data has different patterns
                        base_sales = int(base_sales * np.random.uniform(0.7, 1.3))
                    
                    rows.append({
                        'str_code': str_code,
                        'spu_code': spu_code,
                        'category': category,
                        'sub_cate_name': subcategory,
                        'spu_sales_amt': base_sales * np.random.uniform(80, 150),  # Step 7 expects this column name
                        'spu_sales_qty': base_sales,
                        'stock_qty': int(base_sales * np.random.uniform(0.5, 2.0)),
                        'unit_price': np.random.uniform(80, 300),
                    })
    
    df = pd.DataFrame(rows)
    
    filename = f"complete_spu_sales_{period_label}.csv"
    output_file = FIXTURES_DIR / filename
    df.to_csv(output_file, index=False)
    print(f"✓ Created {filename} ({len(df)} rows, {df['spu_code'].nunique()} SPUs)")
    return df

def generate_store_sales(period_label="202501A"):
    """Generate store_sales_YYYYMMA.csv"""
    
    stores = [f"1100{i}" for i in range(1, 51)]
    
    rows = []
    for str_code in stores:
        rows.append({
            'str_code': str_code,
            'total_sales_amount': np.random.uniform(50000, 200000),
            'total_sales_qty': np.random.randint(500, 2000),
            'avg_unit_price': np.random.uniform(100, 200),
            'store_type': np.random.choice(['Fashion', 'Balanced', 'Basic']),
        })
    
    df = pd.DataFrame(rows)
    
    filename = f"store_sales_{period_label}.csv"
    output_file = FIXTURES_DIR / filename
    df.to_csv(output_file, index=False)
    print(f"✓ Created {filename} ({len(df)} stores)")
    return df

def main():
    """Generate all fixtures"""
    print("Generating Step 7 test fixtures...")
    print("=" * 60)
    
    # 1. Clustering results
    generate_clustering_results()
    
    # 2. Current period SPU sales
    generate_spu_sales("202501A", seasonal=False)
    
    # 3. Seasonal reference SPU sales (December 2024)
    generate_spu_sales("202412B", seasonal=True)
    
    # 4. Store sales
    generate_store_sales("202501A")
    
    print("=" * 60)
    print(f"✅ All fixtures created in {FIXTURES_DIR}")
    print("\nGenerated files:")
    for f in sorted(FIXTURES_DIR.glob("*.csv")):
        size = f.stat().st_size
        print(f"  - {f.name} ({size:,} bytes)")

if __name__ == "__main__":
    main()
