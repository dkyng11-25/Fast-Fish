from __future__ import annotations
from typing import List, Dict, Any, Set
import os
from pathlib import Path

import pandas as pd

from src.core.logger import PipelineLogger
from .base import Repository


class StoreTrackingRepository(Repository):
    """Repository for managing store processing tracking files."""
    
    def __init__(self, 
                 output_dir: str, 
                 period_label: str,
                 logger: PipelineLogger):
        Repository.__init__(self, logger)
        self.output_dir = Path(output_dir)
        self.period_label = period_label
        self.processed_stores_file = self.output_dir / f"processed_stores_{period_label}.txt"
        self.failed_stores_file = self.output_dir / f"failed_stores_{period_label}.txt"
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all tracking data as list of dictionaries."""
        processed_stores = self.get_processed_stores()
        failed_stores = self.get_failed_stores()
        
        tracking_data = []
        for store in processed_stores:
            tracking_data.append({
                'store_code': store,
                'status': 'processed',
                'period': self.period_label
            })
        
        for store in failed_stores:
            tracking_data.append({
                'store_code': store,
                'status': 'failed',
                'period': self.period_label
            })
        
        return tracking_data
    
    def save(self, data: pd.DataFrame) -> None:
        """Save tracking data from DataFrame."""
        if 'store_code' not in data.columns or 'status' not in data.columns:
            raise ValueError("DataFrame must have 'store_code' and 'status' columns")
        
        processed_stores = data[data['status'] == 'processed']['store_code'].tolist()
        failed_stores = data[data['status'] == 'failed']['store_code'].tolist()
        
        if processed_stores:
            self.save_processed_stores(processed_stores)
        
        if failed_stores:
            self.save_failed_stores(failed_stores)
    
    def get_processed_stores(self) -> Set[str]:
        """Get set of successfully processed store codes."""
        processed_stores = set()
        
        if self.processed_stores_file.exists():
            try:
                with open(self.processed_stores_file, 'r') as f:
                    processed_stores = {line.strip() for line in f if line.strip()}
            except Exception as e:
                self.logger.error(f"Could not read processed stores file: {e}", self.repo_name)
        
        return processed_stores
    
    def get_failed_stores(self) -> Set[str]:
        """Get set of failed store codes that should be retried."""
        failed_stores = set()
        
        if self.failed_stores_file.exists():
            try:
                with open(self.failed_stores_file, 'r') as f:
                    failed_stores = {line.strip() for line in f if line.strip()}
            except Exception as e:
                self.logger.error(f"Could not read failed stores file: {e}", self.repo_name)
        
        return failed_stores
    
    def save_processed_stores(self, store_codes: List[str]) -> None:
        """Append successfully processed stores to tracking file."""
        try:
            with open(self.processed_stores_file, 'a') as f:
                for store_code in store_codes:
                    f.write(f"{store_code}\n")
        except Exception as e:
            self.logger.error(f"Could not save processed stores: {e}", self.repo_name)
    
    def save_failed_stores(self, store_codes: List[str]) -> None:
        """Append failed stores to tracking file."""
        try:
            with open(self.failed_stores_file, 'a') as f:
                for store_code in store_codes:
                    f.write(f"{store_code}\n")
        except Exception as e:
            self.logger.error(f"Could not save failed stores: {e}", self.repo_name)
    
    def clear_tracking_files(self) -> None:
        """Clear all tracking files for this period."""
        try:
            if self.processed_stores_file.exists():
                self.processed_stores_file.unlink()
            if self.failed_stores_file.exists():
                self.failed_stores_file.unlink()
        except Exception as e:
            self.logger.error(f"Could not clear tracking files: {e}", self.repo_name)
    
    def get_stores_to_process(self, all_stores: Set[str], force_full: bool = False) -> Set[str]:
        """
        Determine which stores need to be processed based on tracking files.
        
        Args:
            all_stores: Set of all available store codes
            force_full: If True, return all stores regardless of tracking
            
        Returns:
            Set of store codes that need to be processed
        """
        if force_full:
            return all_stores
        
        processed_stores = self.get_processed_stores()
        failed_stores = self.get_failed_stores()
        
        # Skip successfully processed stores, but retry failed ones
        stores_to_skip = processed_stores - failed_stores
        stores_to_process = all_stores - stores_to_skip
        
        return stores_to_process
