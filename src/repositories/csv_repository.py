from __future__ import annotations
from typing import List, Dict, Any

import pandas as pd

from src.core.logger import PipelineLogger
from .base import Repository


class CsvFileRepository(Repository):
    def __init__(self, file_path: str, logger: PipelineLogger):
        Repository.__init__(self, logger)
        self.file_path = file_path

    def get_all(self) -> pd.DataFrame:
        """Load CSV and return as DataFrame (Steps expect DataFrame, not list)."""
        return pd.read_csv(self.file_path)
    
    def load(self, filename: str) -> pd.DataFrame:
        """
        Load CSV file by filename relative to base path.
        
        Args:
            filename: Name of CSV file to load
            
        Returns:
            DataFrame with loaded data
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        from pathlib import Path
        file_path = Path(self.file_path) / filename
        return pd.read_csv(file_path)

    def save(self, data: pd.DataFrame) -> None:
        data.to_csv(self.file_path, index=False)


class MultiPeriodCsvRepository(Repository):
    """
    Repository for loading data from multiple periods using file pattern matching.

    This repository scans for files matching a pattern across different periods
    and combines the data for comprehensive analysis.
    """

    def __init__(self, file_pattern: str, logger: PipelineLogger):
        """
        Initialize multi-period CSV repository.

        Args:
            file_pattern: Pattern for matching files (e.g., "output/store_sales_*.csv")
            logger: Pipeline logger instance
        """
        Repository.__init__(self, logger)
        self.file_pattern = file_pattern

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Load and combine data from all matching files across periods.

        Returns:
            Combined list of records from all periods
        """
        import glob
        import os

        self.logger.info(f"Scanning for files matching pattern: {self.file_pattern}", self.__class__.__name__)

        matching_files = glob.glob(self.file_pattern)
        self.logger.info(f"Found {len(matching_files)} matching files", self.__class__.__name__)

        if not matching_files:
            self.logger.warning("No files found matching pattern", self.__class__.__name__)
            return []

        combined_records = []

        for file_path in matching_files:
            try:
                self.logger.debug(f"Loading data from: {file_path}", self.__class__.__name__)
                df = pd.read_csv(file_path)

                # Add period information if not present
                if 'period_label' not in df.columns:
                    # Extract period from filename
                    filename = os.path.basename(file_path)
                    if 'store_sales_' in filename:
                        period_part = filename.replace('store_sales_', '').replace('.csv', '')
                    elif 'complete_category_sales_' in filename:
                        period_part = filename.replace('complete_category_sales_', '').replace('.csv', '')
                    elif 'complete_spu_sales_' in filename:
                        period_part = filename.replace('complete_spu_sales_', '').replace('.csv', '')
                    else:
                        period_part = 'unknown'

                    df['period_label'] = period_part

                records = df.to_dict('records')
                combined_records.extend(records)
                self.logger.debug(f"Loaded {len(records)} records from {file_path}", self.__class__.__name__)

            except Exception as e:
                self.logger.error(f"Failed to load data from {file_path}: {e}", self.__class__.__name__)

        self.logger.info(f"Combined {len(combined_records)} records from {len(matching_files)} files", self.__class__.__name__)
        return combined_records

    def save(self, data: pd.DataFrame) -> None:
        """Not implemented for multi-period repository."""
        raise NotImplementedError("Multi-period repository does not support save operation")


class StoreCoordinatesRepository(Repository):
    """Repository for store coordinates data."""

    def __init__(self, file_path: str, logger: PipelineLogger):
        Repository.__init__(self, logger)
        self.file_path = file_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Load store coordinates data."""
        try:
            df = pd.read_csv(self.file_path)
            return df.to_dict('records')
        except FileNotFoundError:
            return []

    def save(self, data: pd.DataFrame) -> None:
        """Save store coordinates data."""
        data.to_csv(self.file_path, index=False)


class SPUMappingRepository(Repository):
    """Repository for SPU-to-store mapping data."""

    def __init__(self, file_path: str, logger: PipelineLogger):
        Repository.__init__(self, logger)
        self.file_path = file_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Load SPU mapping data."""
        try:
            df = pd.read_csv(self.file_path)
            return df.to_dict('records')
        except FileNotFoundError:
            return []

    def save(self, data: pd.DataFrame) -> None:
        """Save SPU mapping data."""
        data.to_csv(self.file_path, index=False)


class SPUMetadataRepository(Repository):
    """Repository for SPU metadata data."""

    def __init__(self, file_path: str, logger: PipelineLogger):
        Repository.__init__(self, logger)
        self.file_path = file_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Load SPU metadata data."""
        try:
            df = pd.read_csv(self.file_path)
            return df.to_dict('records')
        except FileNotFoundError:
            return []

    def save(self, data: pd.DataFrame) -> None:
        """Save SPU metadata data."""
        data.to_csv(self.file_path, index=False)


