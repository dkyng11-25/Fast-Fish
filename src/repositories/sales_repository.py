"""Repository for sales data access."""

import fireducks.pandas as pd
from typing import Optional, List
from datetime import datetime


class SalesRepository:
    """Repository for accessing sales data."""
    
    def __init__(self, csv_repo, logger):
        """
        Initialize sales repository.
        
        Args:
            csv_repo: CSV file repository for file operations
            logger: Pipeline logger instance
        """
        self.csv_repo = csv_repo
        self.logger = logger
    
    def load_current_sales(self, period_label: str, analysis_level: str = 'subcategory') -> pd.DataFrame:
        """
        Load current period sales data with fallback patterns.
        
        Tries multiple file naming patterns and locations:
        1. complete_category_sales_{period} or complete_spu_sales_{period} (data/api_data/)
        2. sales_{period}.csv (output/)
        3. Legacy combined files
        
        Args:
            period_label: Period identifier (e.g., '202510A')
            analysis_level: Analysis level ('subcategory' or 'spu')
            
        Returns:
            DataFrame with sales data
            
        Raises:
            FileNotFoundError: If sales file not found
        """
        # Build fallback chain based on analysis level
        if analysis_level == 'spu':
            filenames = [
                f"data/api_data/complete_spu_sales_{period_label}.csv",
                f"complete_spu_sales_{period_label}.csv",
                f"sales_{period_label}.csv",
            ]
        else:  # subcategory
            filenames = [
                f"data/api_data/complete_category_sales_{period_label}.csv",
                f"complete_category_sales_{period_label}.csv",
                f"sales_{period_label}.csv",
            ]
        
        for filename in filenames:
            try:
                from pathlib import Path
                # Handle paths that include directory structure
                if '/' in filename:
                    file_path = Path(filename)
                    df = pd.read_csv(file_path)
                else:
                    df = self.csv_repo.load(filename)
                
                self.logger.info(f"Loaded current sales from: {filename}")
                df = self._standardize_columns(df)
                
                self.logger.info(
                    f"Current sales loaded: {len(df)} records, "
                    f"{df['str_code'].nunique()} stores"
                )
                
                return df
            except FileNotFoundError:
                continue
        
        # If we get here, none of the files were found
        raise FileNotFoundError(
            f"Sales data not found. Tried:\n" +
            "\n".join(f"  - {fn}" for fn in filenames) +
            f"\nEnsure sales data exists for period {period_label}"
        )
    
    def load_seasonal_sales(
        self, 
        period_label: str, 
        years_back: int = 1
    ) -> Optional[pd.DataFrame]:
        """
        Load seasonal period sales data.
        
        Calculates seasonal period (same month, previous year) and loads data.
        
        Args:
            period_label: Current period identifier (e.g., '202510A')
            years_back: Number of years to look back (default: 1)
            
        Returns:
            DataFrame with seasonal sales data, or None if not found
        """
        seasonal_period = self._calculate_seasonal_period(period_label, years_back)
        filename = f"sales_{seasonal_period}.csv"
        
        try:
            df = self.csv_repo.load(filename)
            self.logger.info(
                f"Loaded seasonal sales from: {filename} "
                f"({years_back} year(s) back)"
            )
            df = self._standardize_columns(df)
            
            self.logger.info(
                f"Seasonal sales loaded: {len(df)} records, "
                f"{df['str_code'].nunique()} stores"
            )
            
            return df
        except FileNotFoundError:
            self.logger.warning(
                f"Seasonal sales not found: {filename}. "
                f"Continuing without seasonal data."
            )
            return None
    
    def _calculate_seasonal_period(self, period_label: str, years_back: int) -> str:
        """
        Calculate seasonal period label.
        
        Args:
            period_label: Current period (e.g., '202510A')
            years_back: Number of years to look back
            
        Returns:
            Seasonal period label (e.g., '202410A' for 1 year back)
        """
        # Extract year and month
        year = int(period_label[:4])
        month = period_label[4:6]
        period_half = period_label[6] if len(period_label) > 6 else 'A'
        
        # Calculate seasonal year
        seasonal_year = year - years_back
        
        # Construct seasonal period label
        seasonal_period = f"{seasonal_year}{month}{period_half}"
        
        self.logger.debug(
            f"Calculated seasonal period: {period_label} -> {seasonal_period}"
        )
        
        return seasonal_period
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names in sales data.
        
        Ensures consistent column naming across different data sources.
        
        Args:
            df: DataFrame with sales data
            
        Returns:
            DataFrame with standardized column names
        """
        # Standardize column names
        column_mapping = {
            'store_cd': 'str_code',
            'sales_amt': 'sal_amt',
            'amount': 'sal_amt',
            'spu_sales_amt': 'sal_amt',  # SPU mode uses this column name
        }
        
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.rename(columns={old_name: new_name})
                self.logger.debug(f"Renamed column: {old_name} -> {new_name}")
        
        # Validate required columns
        required_columns = ['str_code', 'sal_amt']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(
                f"Sales data missing required columns: {missing_columns}. "
                f"Available columns: {list(df.columns)}"
            )
        
        return df
