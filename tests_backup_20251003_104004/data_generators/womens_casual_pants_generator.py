#!/usr/bin/env python3
"""
Women's Casual Pants Test Data Generator

Generates subsample test data based on the Women's Casual Pants Filter Guide.
Creates realistic test data for steps 5-37 using the 254 women's casual pants records.

Author: Data Pipeline
Date: 2025-09-16
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class WomensCasualPantsGenerator:
    """Generator for women's casual pants test data based on filter guide specifications."""
    
    def __init__(self, base_data_dir: str = "data"):
        """
        Initialize the generator.
        
        Args:
            base_data_dir: Base directory containing reference data files
        """
        self.base_data_dir = Path(base_data_dir)
        self.output_dir = Path("tests/data")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load reference data
        self.store_list = self._load_store_list()
        self.category_list = self._load_category_list()
        self.subcategory_list = self._load_subcategory_list()
        
        # Women's casual pants specifications from filter guide
        self.womens_casual_pants_specs = {
            "total_records": 254,
            "store_groups": 46,
            "date_range": "2025-08",
            "period": "First Half",
            "subcategories": {
                "直筒裤": 46,  # Straight pants
                "工装裤": 46,  # Cargo pants  
                "锥形裤": 46,  # Tapered pants
                "短裤": 46,    # Shorts
                "弯刀裤": 46,  # Curved pants
                "喇叭裤": 24   # Bell-bottom pants
            },
            "suggested_actions": {
                "Increase": 185,  # 72.8%
                "Maintain": 63,   # 24.8%
                "Decrease": 6     # 2.4%
            },
            "quantity_ranges": {
                "current_spu": (1, 69),
                "target_spu": (1, 72),
                "avg_current": 29.0,
                "avg_target": 31.1
            }
        }
    
    def _load_store_list(self) -> List[str]:
        """Load store list from reference data."""
        try:
            store_file = self.base_data_dir / "store_list.txt"
            if store_file.exists():
                with open(store_file, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
            else:
                # Generate sample store codes if file doesn't exist
                return [f"ST{i:04d}" for i in range(1, 1001)]
        except Exception as e:
            logger.warning(f"Could not load store list: {e}")
            return [f"ST{i:04d}" for i in range(1, 1001)]
    
    def _load_category_list(self) -> List[str]:
        """Load category list from reference data."""
        try:
            category_file = self.base_data_dir / "category_list.txt"
            if category_file.exists():
                with open(category_file, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
            else:
                return ["Women's Clothing", "Men's Clothing", "Accessories", "Shoes"]
        except Exception as e:
            logger.warning(f"Could not load category list: {e}")
            return ["Women's Clothing", "Men's Clothing", "Accessories", "Shoes"]
    
    def _load_subcategory_list(self) -> List[str]:
        """Load subcategory list from reference data."""
        try:
            subcategory_file = self.base_data_dir / "subcategory_list.txt"
            if subcategory_file.exists():
                with open(subcategory_file, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
            else:
                return list(self.womens_casual_pants_specs["subcategories"].keys())
        except Exception as e:
            logger.warning(f"Could not load subcategory list: {e}")
            return list(self.womens_casual_pants_specs["subcategories"].keys())
    
    def generate_womens_casual_pants_data(self) -> pd.DataFrame:
        """
        Generate women's casual pants test data based on filter guide specifications.
        
        Returns:
            DataFrame with women's casual pants test data
        """
        logger.info("Generating women's casual pants test data")
        
        data = []
        record_id = 0
        
        # Generate data for each subcategory
        for subcategory, count in self.womens_casual_pants_specs["subcategories"].items():
            for i in range(count):
                record_id += 1
                
                # Select random store group (1-46)
                store_group = f"Store Group {random.randint(1, 46)}"
                
                # Generate style tags
                style_tags = self._generate_style_tags(subcategory)
                
                # Generate quantities based on specifications
                current_spu = random.randint(*self.womens_casual_pants_specs["quantity_ranges"]["current_spu"])
                target_spu = random.randint(*self.womens_casual_pants_specs["quantity_ranges"]["target_spu"])
                
                # Determine suggested action based on distribution
                action_rand = random.random()
                if action_rand < 0.728:  # 72.8%
                    suggested_action = "Increase"
                elif action_rand < 0.976:  # 24.8%
                    suggested_action = "Maintain"
                else:  # 2.4%
                    suggested_action = "Decrease"
                
                record = {
                    "Year": 2025,
                    "Month": 8,
                    "Period": "First Half",
                    "Store_Group": store_group,
                    "Style_Tags": style_tags,
                    "Target_SPU_Quantity": target_spu,
                    "Current_SPU_Quantity": current_spu,
                    "Suggested_Action": suggested_action
                }
                
                data.append(record)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} women's casual pants records")
        
        return df
    
    def _generate_style_tags(self, subcategory: str) -> str:
        """Generate style tags for a subcategory."""
        base_tags = ["Summer", "Women", "Casual Pants", subcategory]
        
        # Add location tag
        location_tags = ["Back-store", "Front-store"]
        if subcategory == "短裤":  # Shorts are more likely front-store
            location = random.choices(location_tags, weights=[0.3, 0.7])[0]
        else:
            location = random.choices(location_tags, weights=[0.8, 0.2])[0]
        
        base_tags.append(location)
        
        # Add additional style attributes occasionally
        additional_tags = ["Trendy", "Classic", "Comfortable", "Stylish"]
        if random.random() < 0.3:  # 30% chance
            base_tags.append(random.choice(additional_tags))
        
        return f"[{', '.join(base_tags)}]"
    
    def generate_store_subsample(self, n_stores: int = 50) -> List[str]:
        """
        Generate a subsample of stores for faster testing.
        
        Args:
            n_stores: Number of stores to include in subsample
            
        Returns:
            List of store codes
        """
        if n_stores >= len(self.store_list):
            return self.store_list
        
        # Use stratified sampling to ensure good distribution
        random.seed(42)  # For reproducible results
        return random.sample(self.store_list, n_stores)
    
    def generate_step5_weather_data(self, store_codes: List[str], days: int = 30) -> pd.DataFrame:
        """
        Generate weather data for Step 5 testing.
        
        Args:
            store_codes: List of store codes
            days: Number of days to generate data for
            
        Returns:
            DataFrame with weather data
        """
        logger.info(f"Generating weather data for {len(store_codes)} stores over {days} days")
        
        data = []
        start_date = datetime(2025, 8, 1)
        
        for store_code in store_codes:
            for day in range(days):
                date = start_date + timedelta(days=day)
                
                # Generate realistic weather data for August
                temperature = random.uniform(20, 35)  # August temperatures
                humidity = random.uniform(40, 80)
                wind_speed = random.uniform(0, 10)
                pressure = random.uniform(1000, 1020)
                radiation = random.uniform(200, 800) if random.random() < 0.8 else None
                
                record = {
                    "str_code": store_code,
                    "date": date.strftime("%Y-%m-%d"),
                    "temperature": round(temperature, 1),
                    "humidity": round(humidity, 1),
                    "wind_speed": round(wind_speed, 1),
                    "pressure": round(pressure, 1),
                    "radiation": round(radiation, 1) if radiation else None
                }
                
                data.append(record)
        
        return pd.DataFrame(data)
    
    def generate_step5_store_altitudes(self, store_codes: List[str]) -> pd.DataFrame:
        """
        Generate store altitude data for Step 5 testing.
        
        Args:
            store_codes: List of store codes
            
        Returns:
            DataFrame with store altitude data
        """
        logger.info(f"Generating altitude data for {len(store_codes)} stores")
        
        data = []
        
        for i, store_code in enumerate(store_codes):
            # Generate realistic coordinates and altitudes for China
            latitude = random.uniform(18, 54)  # China latitude range
            longitude = random.uniform(73, 135)  # China longitude range
            altitude = random.uniform(0, 4000)  # China altitude range
            
            record = {
                "str_code": store_code,
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6),
                "altitude": round(altitude, 1),
                "store_name": f"Store {store_code}"
            }
            
            data.append(record)
        
        return pd.DataFrame(data)
    
    def generate_step6_clustering_data(self, store_codes: List[str], analysis_level: str = "spu") -> pd.DataFrame:
        """
        Generate clustering input data for Step 6 testing.
        
        Args:
            store_codes: List of store codes
            analysis_level: Analysis level (spu, subcategory, category_aggregated)
            
        Returns:
            DataFrame with clustering input data
        """
        logger.info(f"Generating clustering data for {len(store_codes)} stores, level: {analysis_level}")
        
        data = []
        
        if analysis_level == "spu":
            # Generate SPU-level data
            spu_codes = [f"SPU{i:06d}" for i in range(1, 201)]  # 200 SPUs
            
            for store_code in store_codes:
                # Each store gets a subset of SPUs
                n_spus = random.randint(50, 150)
                store_spus = random.sample(spu_codes, n_spus)
                
                for spu_code in store_spus:
                    sales_amt = random.uniform(100, 10000)
                    quantity = random.randint(1, 100)
                    
                    record = {
                        "str_code": store_code,
                        "spu_code": spu_code,
                        "spu_sales_amt": round(sales_amt, 2),
                        "quantity": quantity,
                        "cate_name": "Women's Clothing",
                        "sub_cate_name": random.choice(list(self.womens_casual_pants_specs["subcategories"].keys()))
                    }
                    
                    data.append(record)
        
        elif analysis_level == "subcategory":
            # Generate subcategory-level data
            for store_code in store_codes:
                for subcategory in self.womens_casual_pants_specs["subcategories"].keys():
                    sal_amt = random.uniform(1000, 50000)
                    target_count = random.randint(10, 50)
                    
                    record = {
                        "str_code": store_code,
                        "sub_cate_name": subcategory,
                        "sal_amt": round(sal_amt, 2),
                        "target_sty_cnt_avg": target_count,
                        "cate_name": "Women's Clothing"
                    }
                    
                    data.append(record)
        
        elif analysis_level == "category_aggregated":
            # Generate category-aggregated data
            for store_code in store_codes:
                total_sales = random.uniform(50000, 200000)
                target_count = random.randint(100, 500)
                
                record = {
                    "str_code": store_code,
                    "cate_name": "Women's Clothing",
                    "total_sales": round(total_sales, 2),
                    "target_sty_cnt_avg": target_count
                }
                
                data.append(record)
        
        return pd.DataFrame(data)
    
    def generate_step7_rule_data(self, store_codes: List[str], period_label: str = "202508A") -> Dict[str, pd.DataFrame]:
        """
        Generate data for Step 7 (Missing Category Rule) testing.
        
        Args:
            store_codes: List of store codes
            period_label: Period label for file naming
            
        Returns:
            Dictionary with DataFrames for different input files
        """
        logger.info(f"Generating Step 7 rule data for {len(store_codes)} stores")
        
        # Generate clustering results
        clustering_data = []
        n_clusters = random.randint(5, 15)
        
        for i, store_code in enumerate(store_codes):
            cluster_id = i % n_clusters
            cluster_label = f"Cluster_{cluster_id}"
            
            record = {
                "str_code": store_code,
                "cluster_id": cluster_id,
                "Cluster": cluster_label,
                "analysis_level": "spu",
                "period_label": period_label
            }
            
            clustering_data.append(record)
        
        clustering_df = pd.DataFrame(clustering_data)
        
        # Generate SPU sales data
        spu_sales_data = []
        spu_codes = [f"SPU{i:06d}" for i in range(1, 101)]  # 100 SPUs
        
        for store_code in store_codes:
            n_spus = random.randint(20, 80)
            store_spus = random.sample(spu_codes, n_spus)
            
            for spu_code in store_spus:
                sales_amt = random.uniform(500, 5000)
                quantity = random.randint(1, 50)
                
                record = {
                    "str_code": store_code,
                    "spu_code": spu_code,
                    "spu_sales_amt": round(sales_amt, 2),
                    "quantity": quantity,
                    "cate_name": "Women's Clothing",
                    "sub_cate_name": random.choice(list(self.womens_casual_pants_specs["subcategories"].keys()))
                }
                
                spu_sales_data.append(record)
        
        spu_sales_df = pd.DataFrame(spu_sales_data)
        
        # Generate store config data
        store_config_data = []
        for store_code in store_codes:
            sty_sal_amt = {
                "Women's Clothing": {
                    "subcategories": {
                        subcat: random.uniform(1000, 10000) 
                        for subcat in self.womens_casual_pants_specs["subcategories"].keys()
                    }
                }
            }
            
            record = {
                "str_code": store_code,
                "sty_sal_amt": str(sty_sal_amt),
                "target_sty_cnt_avg": random.randint(50, 200),
                "store_name": f"Store {store_code}",
                "region": random.choice(["North", "South", "East", "West", "Central"])
            }
            
            store_config_data.append(record)
        
        store_config_df = pd.DataFrame(store_config_data)
        
        return {
            "clustering_results": clustering_df,
            "spu_sales": spu_sales_df,
            "store_config": store_config_df
        }
    
    def save_test_data(self, data: pd.DataFrame, filename: str) -> str:
        """
        Save test data to file.
        
        Args:
            data: DataFrame to save
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        file_path = self.output_dir / filename
        data.to_csv(file_path, index=False)
        logger.info(f"Saved test data to {file_path}")
        return str(file_path)
    
    def generate_all_test_data(self, n_stores: int = 50) -> Dict[str, str]:
        """
        Generate all test data files for comprehensive testing.
        
        Args:
            n_stores: Number of stores to include in subsample
            
        Returns:
            Dictionary mapping data type to file path
        """
        logger.info(f"Generating comprehensive test data for {n_stores} stores")
        
        # Generate store subsample
        store_codes = self.generate_store_subsample(n_stores)
        
        # Generate women's casual pants data
        womens_pants_df = self.generate_womens_casual_pants_data()
        womens_pants_path = self.save_test_data(womens_pants_df, "subsample_womens_casual_pants.csv")
        
        # Generate Step 5 data
        weather_df = self.generate_step5_weather_data(store_codes)
        weather_path = self.save_test_data(weather_df, "subsample_weather_data.csv")
        
        altitude_df = self.generate_step5_store_altitudes(store_codes)
        altitude_path = self.save_test_data(altitude_df, "subsample_store_altitudes.csv")
        
        # Generate Step 6 data for different analysis levels
        spu_clustering_df = self.generate_step6_clustering_data(store_codes, "spu")
        spu_clustering_path = self.save_test_data(spu_clustering_df, "subsample_spu_clustering_data.csv")
        
        subcategory_clustering_df = self.generate_step6_clustering_data(store_codes, "subcategory")
        subcategory_clustering_path = self.save_test_data(subcategory_clustering_df, "subsample_subcategory_clustering_data.csv")
        
        # Generate Step 7 data
        step7_data = self.generate_step7_rule_data(store_codes)
        step7_paths = {}
        for data_type, df in step7_data.items():
            filename = f"subsample_step7_{data_type}.csv"
            path = self.save_test_data(df, filename)
            step7_paths[data_type] = path
        
        return {
            "womens_casual_pants": womens_pants_path,
            "weather_data": weather_path,
            "store_altitudes": altitude_path,
            "spu_clustering_data": spu_clustering_path,
            "subcategory_clustering_data": subcategory_clustering_path,
            "step7_data": step7_paths,
            "store_codes": store_codes
        }


def main():
    """Main function to generate test data."""
    generator = WomensCasualPantsGenerator()
    
    # Generate comprehensive test data
    test_data_paths = generator.generate_all_test_data(n_stores=50)
    
    print("Generated test data files:")
    for data_type, path in test_data_paths.items():
        if isinstance(path, dict):
            print(f"\n{data_type}:")
            for sub_type, sub_path in path.items():
                print(f"  {sub_type}: {sub_path}")
        else:
            print(f"{data_type}: {path}")


if __name__ == "__main__":
    main()


