from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import pandas as pd

from src.core.logger import PipelineLogger
from .base import Repository


class FastFishApiRepository(Repository):
    """Repository for accessing FastFish API endpoints."""
    
    def __init__(self, 
                 base_url: str, 
                 config_endpoint: str,
                 sales_endpoint: str,
                 headers: Dict[str, str],
                 timeout: int,
                 retry_config: Dict[str, Any],
                 logger: PipelineLogger):
        Repository.__init__(self, logger)
        self.base_url = base_url
        self.config_endpoint = config_endpoint
        self.sales_endpoint = sales_endpoint
        self.headers = headers
        self.timeout = timeout
        self.retry_config = retry_config
        self._session = None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Not applicable for API repository - use specific fetch methods instead."""
        raise NotImplementedError("Use fetch_store_config or fetch_store_sales methods")
    
    def save(self, data: pd.DataFrame) -> None:
        """Not applicable for API repository - this is read-only."""
        raise NotImplementedError("API repository is read-only")
    
    def _get_session(self) -> requests.Session:
        """Create or return cached session with retry configuration."""
        if self._session is None:
            retry_strategy = Retry(
                total=self.retry_config.get('total', 3),
                backoff_factor=self.retry_config.get('backoff_factor', 2),
                status_forcelist=self.retry_config.get('status_forcelist', [429, 500, 502, 503, 504]),
                allowed_methods=self.retry_config.get('allowed_methods', ["GET", "POST"])
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session = requests.Session()
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        return self._session
    
    def fetch_store_config(self, 
                          store_codes: List[str], 
                          yyyymm: str, 
                          period: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Fetch store configuration data from API.
        
        Args:
            store_codes: List of store codes to fetch configurations for
            yyyymm: Year and month in YYYYMM format
            period: Period indicator ("A" for first half, "B" for second half)
            
        Returns:
            Tuple containing:
                - List of store configuration records
                - List of successfully processed store codes
        """
        payload = {"strCodes": store_codes, "yyyymm": yyyymm}
        if period:
            payload["period"] = period
        
        session = self._get_session()
        
        try:
            response = session.post(
                self.config_endpoint, 
                json=payload, 
                headers=self.headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json().get("data", [])
            if not data:
                return [], []
            
            # Extract successfully processed store codes
            processed_codes = []
            for record in data:
                if "str_code" in record:
                    processed_codes.append(str(record["str_code"]))
            
            return data, list(set(processed_codes))
            
        except Exception as e:
            self.logger.error(f"Failed to fetch store configuration: {e}", self.repo_name)
            return [], []
    
    def fetch_store_sales(self, 
                         store_codes: List[str], 
                         yyyymm: str, 
                         period: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Fetch store sales data from API.
        
        Args:
            store_codes: List of store codes to fetch sales data for
            yyyymm: Year and month in YYYYMM format
            period: Period indicator ("A" for first half, "B" for second half)
            
        Returns:
            Tuple containing:
                - List of store sales records
                - List of successfully processed store codes
        """
        payload = {"strCodes": store_codes, "yyyymm": yyyymm}
        if period:
            payload["period"] = period
        
        session = self._get_session()
        
        try:
            response = session.post(
                self.sales_endpoint, 
                json=payload, 
                headers=self.headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json().get("data", [])
            if not data:
                return [], []
            
            # Extract successfully processed store codes
            processed_codes = []
            for record in data:
                if "str_code" in record:
                    processed_codes.append(str(record["str_code"]))
            
            return data, list(set(processed_codes))
            
        except Exception as e:
            self.logger.error(f"Failed to fetch store sales: {e}", self.repo_name)
            return [], []
