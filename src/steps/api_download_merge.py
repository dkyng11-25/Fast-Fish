#!/usr/bin/env python3
"""
Step 1: Download and merge API data following the 4-phase Step pattern.

This step downloads store configuration and sales data from the FastFish API,
processes and merges the data, and outputs both category-level and SPU-level sales data.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from dataclasses import dataclass
from typing import NamedTuple
import json
import pandas as pd
import numpy as np
from tqdm import tqdm

# Type aliases for better readability
StoreCode = str
SpuCode = str
CategoryName = str
StoreQuantityMap = Dict[StoreCode, 'StoreQuantityData']
SpuSalesData = Dict[SpuCode, float]

from core.step import Step
from core.context import StepContext
from core.logger import PipelineLogger


class ApiDownloadError(Exception):
    """Raised when API data download fails."""
    pass


class DataTransformationError(Exception):
    """Raised when data transformation fails."""
    pass


class SpuProcessingError(Exception):
    """Raised when SPU data processing fails."""
    pass
from repositories import (
    CsvFileRepository,
    FastFishApiRepository, 
    StoreTrackingRepository
)


@dataclass
class StoreQuantityData:
    """Store-level quantity and pricing information."""
    total_quantity: float
    total_sales: float
    unit_price: float


@dataclass 
class ProcessingResult:
    """Result of data processing operation."""
    category_df: pd.DataFrame
    spu_df: pd.DataFrame
    processed_stores: List[str]


class ApiDataBatch(NamedTuple):
    """Batch of API data from setup phase."""
    config_data_list: List[pd.DataFrame]
    sales_data_list: List[pd.DataFrame]


@dataclass
class ValidationData:
    """Data structure for validation phase."""
    config_data_list: List[pd.DataFrame]
    sales_data_list: List[pd.DataFrame]
    category_data_list: List[pd.DataFrame]
    spu_data_list: List[pd.DataFrame]
    stores_to_process: List[str]


@dataclass
class DataCollections:
    """Data collections for persistence phase."""
    config_data_list: List[pd.DataFrame]
    sales_data_list: List[pd.DataFrame]
    category_data_list: List[pd.DataFrame]
    spu_data_list: List[pd.DataFrame]


class ApiDownloadStep(Step):
    """Step 1: Download, transform, and prepare API data."""
    
    # Business Constants
    DEFAULT_UNIT_PRICE = 50.0
    QUANTITY_PRECISION = 1
    PRICE_PRECISION = 2
    
    # Column Name Constants
    STORE_CODE_COL = 'str_code'
    STORE_NAME_COL = 'str_name'
    BIG_CLASS_COL = 'big_class_name'
    SUB_CATEGORY_COL = 'sub_cate_name'
    SALES_AMOUNT_COL = 'sal_amt'
    SPU_SALES_COL = 'sty_sal_amt'
    BASE_QTY_COL = 'base_sal_qty'
    FASHION_QTY_COL = 'fashion_sal_qty'
    BASE_AMT_COL = 'base_sal_amt'
    FASHION_AMT_COL = 'fashion_sal_amt'
    SPU_CODE_COL = 'spu_code'
    SPU_SALES_AMT_COL = 'spu_sales_amt'
    
    # Category Price Multipliers
    CATEGORY_PRICE_MULTIPLIERS = {
        't恤': 0.7,
        'polo': 0.7,
        '裤': 1.2,
        '衬': 1.1,
        '鞋': 1.6,
        '外套': 1.8,
        'jacket': 1.8,
        '袜': 0.2,
        '内衣': 0.6
    }
    
    # Required columns for validation
    REQUIRED_CATEGORY_COLUMNS = ['str_code', 'sub_cate_name', 'sal_amt']
    REQUIRED_SPU_COLUMNS = ['str_code', 'spu_code', 'spu_sales_amt']
    
    def __init__(self,
                 store_codes_repo: CsvFileRepository,
                 api_repo: FastFishApiRepository,
                 tracking_repo: StoreTrackingRepository,
                 config_output_repo: CsvFileRepository,
                 sales_output_repo: CsvFileRepository,
                 category_output_repo: CsvFileRepository,
                 spu_output_repo: CsvFileRepository,
                 yyyymm: str,
                 period: Optional[str],
                 batch_size: int,
                 force_full_download: bool,
                 logger: PipelineLogger,
                 step_name: str,
                 step_number: int):
        super().__init__(logger, step_name, step_number)
        
        # Injected repositories
        self.store_codes_repo = store_codes_repo
        self.api_repo = api_repo
        self.tracking_repo = tracking_repo
        self.config_output_repo = config_output_repo
        self.sales_output_repo = sales_output_repo
        self.category_output_repo = category_output_repo
        self.spu_output_repo = spu_output_repo
        
        # Injected configuration
        self.yyyymm = yyyymm
        self.period = period
        self.batch_size = batch_size
        self.force_full_download = force_full_download
    
    def setup(self, context: StepContext) -> StepContext:
        """Load store codes, determine processing needs, and fetch API data."""
        stores_to_process = self._discover_stores_to_process()
        if not stores_to_process:
            return self._handle_no_stores_to_process(context)
        
        api_data = self._download_api_data_in_batches(list(stores_to_process))
        return self._populate_context_with_api_data(context, stores_to_process, api_data)
    
    def apply(self, context: StepContext) -> StepContext:
        """Process and transform the downloaded API data."""
        stores_to_process = context.get_state('stores_to_process', [])
        config_data_list = context.get_state('config_data_list', [])
        sales_data_list = context.get_state('sales_data_list', [])
        
        if not stores_to_process:
            self.logger.info("No data to process", self.class_name)
            return context
        
        category_data_list = []
        spu_data_list = []
        all_processed_stores = []
        all_failed_stores = []
        
        self.logger.info(f"Processing and merging data from {len(config_data_list)} config batches and {len(sales_data_list)} sales batches", self.class_name)
        
        # Process each batch of data
        for i, (config_df, sales_df) in enumerate(zip(config_data_list, sales_data_list)):
            self.logger.info(f"Processing data batch {i + 1}/{len(config_data_list)}", self.class_name)
            
            # Process and merge data if both config and sales are available
            if not config_df.empty and not sales_df.empty:
                result = self._process_and_merge_data(sales_df, config_df)
                
                if not result.category_df.empty:
                    category_data_list.append(result.category_df)
                if not result.spu_df.empty:
                    spu_data_list.append(result.spu_df)
                
                all_processed_stores.extend(result.processed_stores)
        
        # Update tracking for all processed stores
        if all_processed_stores:
            self.tracking_repo.save_processed_stores(all_processed_stores)
            self.logger.info(f"Successfully processed {len(all_processed_stores)} stores", self.class_name)
        
        # Track failed stores (stores that were attempted but didn't produce data)
        attempted_stores = set(stores_to_process)
        successful_stores = set(all_processed_stores)
        failed_stores = list(attempted_stores - successful_stores)
        
        if failed_stores:
            self.tracking_repo.save_failed_stores(failed_stores)
            self.logger.info(f"Recorded {len(failed_stores)} failed stores for retry", self.class_name)
        
        # Store results in context
        context.set_state('category_data_list', category_data_list)
        context.set_state('spu_data_list', spu_data_list)
        
        # Set primary data as consolidated category sales (main output)
        if category_data_list:
            consolidated_category = pd.concat(category_data_list, ignore_index=True)
            context.set_data(consolidated_category)
            self.logger.info(f"Generated {len(consolidated_category)} category sales records", self.class_name)
        
        return context
    
    def validate(self, context: StepContext) -> None:
        """Validate the downloaded and processed data."""
        validation_data = self._extract_validation_data(context)
        
        self._validate_data_availability(validation_data)
        self._validate_category_data_structure(validation_data.category_data_list)
        self._validate_spu_data_structure(validation_data.spu_data_list)
    
    def persist(self, context: StepContext) -> StepContext:
        """Save the processed data to output repositories."""
        data_collections = self._extract_data_collections(context)
        
        self._save_consolidated_data('config', data_collections.config_data_list, self.config_output_repo)
        self._save_consolidated_data('sales', data_collections.sales_data_list, self.sales_output_repo)
        self._save_consolidated_data('category', data_collections.category_data_list, self.category_output_repo)
        self._save_consolidated_spu_data(data_collections.spu_data_list, self.spu_output_repo)
        
        return context
    
    def _extract_data_collections(self, context: StepContext) -> DataCollections:
        """Extract data collections from context for persistence."""
        return DataCollections(
            config_data_list=context.get_state('config_data_list', []),
            sales_data_list=context.get_state('sales_data_list', []),
            category_data_list=context.get_state('category_data_list', []),
            spu_data_list=context.get_state('spu_data_list', [])
        )
    
    def _save_consolidated_data(self, data_type: str, data_list: List[pd.DataFrame], 
                               repo: CsvFileRepository) -> None:
        """Generic method to consolidate and save data."""
        if not data_list:
            self.logger.info(f"No {data_type} data to save", self.class_name)
            return
            
        try:
            consolidated_data = pd.concat(data_list, ignore_index=True)
            consolidated_data = consolidated_data.drop_duplicates()
            repo.save(consolidated_data)
            self.logger.info(f"Saved {data_type} data: {len(consolidated_data)} records", self.class_name)
        except Exception as e:
            self.logger.error(f"Failed to save {data_type} data: {e}", self.class_name)
            raise DataTransformationError(f"Failed to consolidate and save {data_type} data: {e}")
    
    def _save_consolidated_spu_data(self, spu_data_list: List[pd.DataFrame], 
                                   repo: CsvFileRepository) -> None:
        """Save consolidated SPU data with store-SPU deduplication."""
        if not spu_data_list:
            self.logger.info("No SPU data to save", self.class_name)
            return
            
        try:
            consolidated_spu = pd.concat(spu_data_list, ignore_index=True)
            # Remove duplicates by store-SPU combination (more specific than generic deduplication)
            consolidated_spu = consolidated_spu.drop_duplicates(
                subset=[self.STORE_CODE_COL, self.SPU_CODE_COL], 
                keep='first'
            )
            repo.save(consolidated_spu)
            self.logger.info(f"Saved SPU data: {len(consolidated_spu)} records", self.class_name)
        except Exception as e:
            self.logger.error(f"Failed to save SPU data: {e}", self.class_name)
            raise DataTransformationError(f"Failed to consolidate and save SPU data: {e}")
    
    def _extract_validation_data(self, context: StepContext) -> ValidationData:
        """Extract validation data from context."""
        return ValidationData(
            config_data_list=context.get_state('config_data_list', []),
            sales_data_list=context.get_state('sales_data_list', []),
            category_data_list=context.get_state('category_data_list', []),
            spu_data_list=context.get_state('spu_data_list', []),
            stores_to_process=context.get_state('stores_to_process', [])
        )
    
    def _validate_data_availability(self, validation_data: ValidationData) -> None:
        """Validate that we have some data if stores were supposed to be processed."""
        if validation_data.stores_to_process and not validation_data.category_data_list:
            raise DataValidationError("No category data was generated despite having stores to process")
        
        if validation_data.stores_to_process and not validation_data.spu_data_list:
            raise DataValidationError("No SPU data was generated despite having stores to process")
    
    def _validate_category_data_structure(self, category_data_list: List[pd.DataFrame]) -> None:
        """Validate category data structure and content."""
        if not category_data_list:
            return
            
        consolidated_category = pd.concat(category_data_list, ignore_index=True)
        
        # Check required columns
        missing_columns = [col for col in self.REQUIRED_CATEGORY_COLUMNS if col not in consolidated_category.columns]
        if missing_columns:
            raise DataValidationError(f"Category data missing required columns: {missing_columns}")
        
        # Check for empty store codes
        empty_stores = consolidated_category[self.STORE_CODE_COL].isnull().sum() + (consolidated_category[self.STORE_CODE_COL] == '').sum()
        if empty_stores > 0:
            raise DataValidationError(f"Found {empty_stores} records with empty store codes in category data")
    
    def _validate_spu_data_structure(self, spu_data_list: List[pd.DataFrame]) -> None:
        """Validate SPU data structure and content."""
        if not spu_data_list:
            return
            
        consolidated_spu = pd.concat(spu_data_list, ignore_index=True)
        
        # Check required columns
        missing_columns = [col for col in self.REQUIRED_SPU_COLUMNS if col not in consolidated_spu.columns]
        if missing_columns:
            raise DataValidationError(f"SPU data missing required columns: {missing_columns}")
        
        # Check for empty SPU codes
        empty_spus = consolidated_spu[self.SPU_CODE_COL].isnull().sum() + (consolidated_spu[self.SPU_CODE_COL] == '').sum()
        if empty_spus > 0:
            raise DataValidationError(f"Found {empty_spus} records with empty SPU codes")
    
    def _discover_stores_to_process(self) -> Set[StoreCode]:
        """Discover and filter stores that need processing."""
        # Load all available store codes
        store_data = self.store_codes_repo.get_all()
        all_store_codes = {str(record[self.STORE_CODE_COL]) for record in store_data}
        
        # Determine which stores need processing
        stores_to_process = self.tracking_repo.get_stores_to_process(
            all_store_codes, 
            self.force_full_download
        )
        
        self.logger.info(
            f"Store processing analysis: {len(stores_to_process)}/{len(all_store_codes)} stores need processing",
            self.class_name
        )
        
        return stores_to_process
    
    def _handle_no_stores_to_process(self, context: StepContext) -> StepContext:
        """Handle the case where no stores need processing."""
        self.logger.info("No stores to process - all data is up to date", self.class_name)
        context.set_data(pd.DataFrame())
        context.set_state('stores_to_process', [])
        return context
    
    def _download_api_data_in_batches(self, stores_list: List[StoreCode]) -> ApiDataBatch:
        """Download configuration and sales data in batches."""
        config_data_list = []
        sales_data_list = []
        
        self.logger.info(f"Downloading API data for {len(stores_list)} stores in batches of {self.batch_size}", self.class_name)
        
        total_batches = (len(stores_list) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(stores_list), self.batch_size):
            batch = stores_list[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            self.logger.info(f"Downloading batch {batch_num}/{total_batches} ({len(batch)} stores)", self.class_name)
            
            # Fetch and process configuration data
            try:
                config_df = self._fetch_config_batch(batch)
                if not config_df.empty:
                    config_data_list.append(config_df)
            except ApiDownloadError as e:
                self.logger.warning(f"Batch {batch_num} configuration download failed, continuing with next batch: {e}", self.class_name)
                continue
            
            # Fetch and process sales data
            try:
                sales_df = self._fetch_sales_batch(batch)
                if not sales_df.empty:
                    sales_data_list.append(sales_df)
            except ApiDownloadError as e:
                self.logger.warning(f"Batch {batch_num} sales download failed, continuing with next batch: {e}", self.class_name)
                continue
        
        return ApiDataBatch(config_data_list, sales_data_list)
    
    def _fetch_config_batch(self, batch: List[StoreCode]) -> pd.DataFrame:
        """Fetch configuration data for a batch of stores."""
        try:
            config_records, config_stores = self.api_repo.fetch_store_config(batch, self.yyyymm, self.period)
            return pd.DataFrame(config_records) if config_records else pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to fetch configuration data for batch {batch}: {e}", self.class_name)
            raise ApiDownloadError(f"Configuration data download failed for stores {batch}: {e}")
    
    def _fetch_sales_batch(self, batch: List[StoreCode]) -> pd.DataFrame:
        """Fetch sales data for a batch of stores."""
        try:
            sales_records, sales_stores = self.api_repo.fetch_store_sales(batch, self.yyyymm, self.period)
            return pd.DataFrame(sales_records) if sales_records else pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Failed to fetch sales data for batch {batch}: {e}", self.class_name)
            raise ApiDownloadError(f"Sales data download failed for stores {batch}: {e}")
    
    def _populate_context_with_api_data(self, context: StepContext, stores_to_process: Set[StoreCode], 
                                       api_data: ApiDataBatch) -> StepContext:
        """Populate context with downloaded API data."""
        config_data_list, sales_data_list = api_data
        stores_list = list(stores_to_process)
        
        # Store raw API data in context
        context.set_data(pd.DataFrame())  # Will be populated in apply phase
        context.set_state('all_store_codes', stores_to_process)
        context.set_state('stores_to_process', stores_list)
        context.set_state('config_data_list', config_data_list)
        context.set_state('sales_data_list', sales_data_list)
        context.set_state('category_data_list', [])
        context.set_state('spu_data_list', [])
        
        return context
    
    def _process_and_merge_data(self, sales_df: pd.DataFrame, config_df: pd.DataFrame) -> ProcessingResult:
        """
        Process and merge store sales and configuration data.
        
        Returns:
            ProcessingResult containing category_df, spu_df, and processed_stores
        """
        try:
            if sales_df.empty or config_df.empty:
                return ProcessingResult(pd.DataFrame(), pd.DataFrame(), [])
            
            # Create store-level quantity and unit price mapping
            store_quantity_map = self._build_store_quantity_mapping(sales_df)
            
            # Create category-level data
            category_sales = self._create_category_data(config_df, store_quantity_map)
            
            # Create SPU-level data
            spu_sales = self._create_spu_data(config_df, store_quantity_map)
            
            # Get successfully processed stores
            processed_stores = []
            if not category_sales.empty:
                processed_stores = category_sales[self.STORE_CODE_COL].unique().tolist()
            
            return ProcessingResult(category_sales, spu_sales, processed_stores)
            
        except Exception as e:
            self.logger.error(f"Failed to process and merge data: {e}", self.class_name)
            return ProcessingResult(pd.DataFrame(), pd.DataFrame(), [])
    
    def _process_spu_row(self, row: pd.Series, store_quantity_map: StoreQuantityMap) -> List[Dict[str, Any]]:
        """Process a single SPU row with specific error handling."""
        try:
            str_code = str(row[self.STORE_CODE_COL])
        except KeyError as e:
            raise SpuProcessingError(f"Missing required column {e} in configuration data")
        
        store_data = store_quantity_map.get(str_code, StoreQuantityData(0, 0, self.DEFAULT_UNIT_PRICE))
        store_unit_price = store_data.unit_price
        
        sty_sal_amt = row.get(self.SPU_SALES_COL)
        if not sty_sal_amt or str(sty_sal_amt).strip() == '':
            return []  # Empty SPU data is valid, just return empty list
        
        try:
            spu_dict = self._parse_spu_sales_data(sty_sal_amt)
        except json.JSONDecodeError as e:
            raise SpuProcessingError(f"Invalid JSON in SPU sales data: {e}")
        except Exception as e:
            raise SpuProcessingError(f"Failed to parse SPU sales data: {e}")
        
        spu_row_data = []
        for spu_code, spu_sales_amt in spu_dict.items():
            try:
                spu_sales_amt = float(spu_sales_amt or 0)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Invalid sales amount for SPU {spu_code}: {spu_sales_amt}. Skipping.", self.class_name)
                continue
            
            try:
                # Estimate category-specific unit price
                category = row.get(self.SUB_CATEGORY_COL, "")
                category_unit_price = self._estimate_category_unit_price(category, store_unit_price)
                
                # Calculate quantity
                spu_quantity = spu_sales_amt / category_unit_price if category_unit_price > 0 else 0
                
                spu_row_data.append({
                    self.STORE_CODE_COL: str_code,
                    self.STORE_NAME_COL: row[self.STORE_NAME_COL],
                    "cate_name": row.get(self.BIG_CLASS_COL),
                    self.SUB_CATEGORY_COL: row[self.SUB_CATEGORY_COL],
                    self.SPU_CODE_COL: spu_code,
                    self.SPU_SALES_AMT_COL: spu_sales_amt,
                    "quantity": round(spu_quantity, self.QUANTITY_PRECISION),
                    "unit_price": round(category_unit_price, self.PRICE_PRECISION)
                })
            except KeyError as e:
                raise SpuProcessingError(f"Missing required column {e} in configuration data for SPU {spu_code}")
            except Exception as e:
                self.logger.warning(f"Failed to process SPU {spu_code}: {e}. Skipping.", self.class_name)
                continue
        
        return spu_row_data
    
    def _build_store_quantity_mapping(self, sales_df: pd.DataFrame) -> StoreQuantityMap:
        """Build mapping of store codes to quantity and pricing data."""
        store_quantity_map: Dict[str, StoreQuantityData] = {}
        has_quantity_data = self.BASE_QTY_COL in sales_df.columns and self.FASHION_QTY_COL in sales_df.columns
        
        if not has_quantity_data:
            return store_quantity_map
            
        for _, row in sales_df.iterrows():
            str_code = str(row[self.STORE_CODE_COL])
            
            base_qty = float(row.get(self.BASE_QTY_COL, 0) or 0)
            fashion_qty = float(row.get(self.FASHION_QTY_COL, 0) or 0)
            base_amt = float(row.get(self.BASE_AMT_COL, 0) or 0)
            fashion_amt = float(row.get(self.FASHION_AMT_COL, 0) or 0)
            
            total_qty = base_qty + fashion_qty
            total_amt = base_amt + fashion_amt
            
            unit_price = total_amt / total_qty if total_qty > 0 else self.DEFAULT_UNIT_PRICE
            
            store_quantity_map[str_code] = StoreQuantityData(
                total_quantity=total_qty,
                total_sales=total_amt,
                unit_price=unit_price
            )
        
        return store_quantity_map
    
    def _create_category_data(self, config_df: pd.DataFrame, 
                             store_quantity_map: StoreQuantityMap) -> pd.DataFrame:
        """Create category-level sales data from configuration data."""
        if self.BIG_CLASS_COL not in config_df.columns or self.SUB_CATEGORY_COL not in config_df.columns:
            return pd.DataFrame()
            
        category_sales = config_df[[
            self.STORE_CODE_COL, self.STORE_NAME_COL, self.BIG_CLASS_COL, self.SUB_CATEGORY_COL, self.SALES_AMOUNT_COL
        ]].copy()
        category_sales.rename(columns={self.BIG_CLASS_COL: "cate_name"}, inplace=True)
        
        # Add quantity estimates if quantity data is available
        if store_quantity_map:
            category_sales['store_unit_price'] = category_sales[self.STORE_CODE_COL].astype(str).map(
                lambda x: store_quantity_map.get(x, StoreQuantityData(0, 0, self.DEFAULT_UNIT_PRICE)).unit_price
            )
            category_sales['estimated_quantity'] = category_sales[self.SALES_AMOUNT_COL] / category_sales['store_unit_price']
        
        return category_sales
    
    def _create_spu_data(self, config_df: pd.DataFrame, 
                        store_quantity_map: StoreQuantityMap) -> pd.DataFrame:
        """Create SPU-level sales data from configuration data."""
        config_df_clean = config_df.drop_duplicates(subset=[self.STORE_CODE_COL, self.SUB_CATEGORY_COL], keep='first')
        
        spu_rows = []
        for _, row in tqdm(config_df_clean.iterrows(), total=len(config_df_clean), desc="Expanding SPU data"):
            try:
                spu_row_data = self._process_spu_row(row, store_quantity_map)
                spu_rows.extend(spu_row_data)
            except SpuProcessingError as e:
                self.logger.warning(f"SPU processing failed for store {row.get(self.STORE_CODE_COL, 'unknown')}: {e}", self.class_name)
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error processing SPU data for store {row.get(self.STORE_CODE_COL, 'unknown')}: {e}", self.class_name)
                continue
        
        return pd.DataFrame(spu_rows)
    
    def _parse_spu_sales_data(self, sty_sal_amt: Union[str, dict]) -> SpuSalesData:
        """Parse SPU sales amount JSON string with specific error handling."""
        if isinstance(sty_sal_amt, str):
            return json.loads(sty_sal_amt)
        elif isinstance(sty_sal_amt, dict):
            return sty_sal_amt
        else:
            raise SpuProcessingError(f"Invalid SPU sales data type: {type(sty_sal_amt)}")
    
    def _estimate_category_unit_price(self, category: CategoryName, store_avg_price: float) -> float:
        """Estimate unit price for a specific category based on store average."""
        category_lower = str(category).lower()
        
        # Category-specific price adjustments using constants
        for category_key, multiplier in self.CATEGORY_PRICE_MULTIPLIERS.items():
            if category_key in category_lower:
                return store_avg_price * multiplier
        
        # Default to store average price if no specific category match
        return store_avg_price
