"""Repository for quantity and price data access."""

import fireducks.pandas as pd
from typing import Optional


class QuantityRepository:
    """Repository for accessing quantity and price data."""
    
    def __init__(self, csv_repo, logger):
        """
        Initialize quantity repository.
        
        Args:
            csv_repo: CSV file repository for file operations
            logger: Pipeline logger instance
        """
        self.csv_repo = csv_repo
        self.logger = logger
    
    def load_quantity_data(self, period_label: str) -> pd.DataFrame:
        """
        Load quantity data with price information.
        
        Args:
            period_label: Period identifier (e.g., '202510A')
            
        Returns:
            DataFrame with quantity and price data
            
        Raises:
            FileNotFoundError: If quantity file not found
        """
        filename = f"quantity_{period_label}.csv"
        
        try:
            df = self.csv_repo.load(filename)
            self.logger.info(f"Loaded quantity data from: {filename}")
            df = self._standardize_columns(df)
            
            # Calculate average unit price if not present
            if 'avg_unit_price' not in df.columns:
                df = self._calculate_unit_price(df)
            
            self.logger.info(
                f"Quantity data loaded: {len(df)} records, "
                f"{df['str_code'].nunique()} stores"
            )
            
            return df
        except FileNotFoundError:
            self.logger.warning(
                f"Quantity data not found: {filename}. "
                f"Price resolution will be limited."
            )
            # Return empty DataFrame with expected structure
            return pd.DataFrame(columns=[
                'str_code', 'sub_cate_name', 'spu_code',
                'total_qty', 'total_amt', 'avg_unit_price'
            ])
    
    def load_historical_prices(
        self,
        period_label: str,
        months_back: int = 3
    ) -> pd.DataFrame:
        """
        Load historical price data for backfilling.
        
        Attempts to load quantity data from previous periods to backfill
        missing prices.
        
        Args:
            period_label: Current period identifier
            months_back: Number of months to look back
            
        Returns:
            DataFrame with historical price data
        """
        self.logger.info(
            f"Loading historical prices ({months_back} months back)..."
        )
        
        historical_dfs = []
        
        # Try to load previous periods
        for i in range(1, months_back + 1):
            try:
                prev_period = self._calculate_previous_period(period_label, i)
                df = self.load_quantity_data(prev_period)
                
                if len(df) > 0:
                    df['source_period'] = prev_period
                    historical_dfs.append(df)
                    self.logger.debug(
                        f"Loaded historical data from {prev_period}: {len(df)} records"
                    )
            except Exception as e:
                self.logger.debug(f"Could not load period {i} months back: {e}")
                continue
        
        if not historical_dfs:
            self.logger.warning("No historical price data available")
            return pd.DataFrame()
        
        # Combine all historical data
        combined = pd.concat(historical_dfs, ignore_index=True)
        
        self.logger.info(
            f"Historical prices loaded: {len(combined)} records from "
            f"{len(historical_dfs)} periods"
        )
        
        return combined
    
    def _calculate_previous_period(self, period_label: str, months_back: int) -> str:
        """
        Calculate previous period label.
        
        Args:
            period_label: Current period (e.g., '202510A')
            months_back: Number of months to go back
            
        Returns:
            Previous period label
        """
        year = int(period_label[:4])
        month = int(period_label[4:6])
        period_half = period_label[6] if len(period_label) > 6 else 'A'
        
        # Calculate previous month
        month = month - months_back
        while month <= 0:
            month += 12
            year -= 1
        
        return f"{year}{month:02d}{period_half}"
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names in quantity data.
        
        Args:
            df: DataFrame with quantity data
            
        Returns:
            DataFrame with standardized column names
        """
        # Column name mappings
        column_mappings = {
            'store_code': 'str_code',
            'subcategory_name': 'sub_cate_name',
            'subcategory': 'sub_cate_name',
            'quantity': 'total_qty',
            'amount': 'total_amt',
            'unit_price': 'avg_unit_price',
        }
        
        # Apply mappings
        for old_name, new_name in column_mappings.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        return df
    
    def _calculate_unit_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate average unit price from quantity and amount.
        
        Args:
            df: DataFrame with total_qty and total_amt columns
            
        Returns:
            DataFrame with avg_unit_price column added
        """
        if 'total_qty' in df.columns and 'total_amt' in df.columns:
            # Avoid division by zero
            df['avg_unit_price'] = df.apply(
                lambda row: row['total_amt'] / row['total_qty'] 
                if row['total_qty'] > 0 else 0,
                axis=1
            )
            self.logger.debug("Calculated avg_unit_price from total_qty and total_amt")
        else:
            df['avg_unit_price'] = 0.0
            self.logger.warning(
                "Cannot calculate unit price: missing total_qty or total_amt columns"
            )
        
        return df
