"""
Matrix Preparation Step

Creates normalized matrices for both subcategory-level and SPU-level analysis
using comprehensive year-over-year data aggregation. Handles data filtering, 
normalization, and matrix creation for downstream clustering.
"""

import pandas as pd
import os
from typing import List, Tuple, Optional
from datetime import datetime

from core.step import Step
from core.context import StepContext
from core.logger import PipelineLogger
from repositories.matrix_data_repository import MatrixDataRepository
from steps.matrix_processor import MatrixProcessor


class MatrixPreparationStep(Step):
    """
    Step for preparing comprehensive multi-period clustering matrices.
    """
    
    def __init__(self, logger: PipelineLogger, step_name: str = "Matrix Preparation", step_number: int = 3):
        super().__init__(logger, step_name, step_number)
        self.class_name = "MatrixPreparationStep"

        # Initialize dependencies with configuration system
        self.data_repository = MatrixDataRepository(logger)
        self.matrix_processor = MatrixProcessor(logger)
    
    def setup(self, context: StepContext) -> StepContext:
        """
        Setup phase: Load and validate required data.
        
        Args:
            context: Pipeline context
            
        Returns:
            Updated context with loaded data
        """
        self.logger.info("Setting up matrix preparation step", self.class_name)
        
        try:
            # Get target period from context or environment
            target_period = context.get_state("target_period", None)
            if not target_period:
                # Try to get from environment
                import os
                yyyymm = os.environ.get('PIPELINE_TARGET_YYYYMM', '202509')
                period = os.environ.get('PIPELINE_TARGET_PERIOD', 'A')
                target_period = f"{yyyymm}{period}"
            
            self.logger.info(f"Target period: {target_period}", self.class_name)
            
            # Load coordinates and identify anomaly stores
            coords_df = self.data_repository.load_coordinates()
            anomaly_stores = self.data_repository.identify_anomalous_stores(coords_df)
            
            # Store in context
            context.set_data(coords_df)
            context.set_state("anomaly_stores", anomaly_stores)
            context.set_state("target_period", target_period)
            
            self.logger.info(f"Setup completed. Loaded coordinates for {len(coords_df)} stores", self.class_name)
            self.logger.info(f"Identified {len(anomaly_stores)} anomalous stores", self.class_name)
            
            return context
            
        except Exception as e:
            self.logger.error(f"Setup failed: {str(e)}", self.class_name)
            raise
    
    def apply(self, context: StepContext) -> StepContext:
        """
        Apply phase: Create matrices for clustering analysis.
        
        Args:
            context: Pipeline context
            
        Returns:
            Updated context with matrix results
        """
        self.logger.info("Applying matrix preparation step", self.class_name)
        
        try:
            # Get data from context
            coords_df = context.get_data()
            anomaly_stores = context.get_state("anomaly_stores", [])
            target_period = context.get_state("target_period", "202509A")
            
            # Get year-over-year periods
            periods = self._get_year_over_year_periods(target_period)
            self.logger.info(f"Processing {len(periods)} periods for matrix creation", self.class_name)
            
            # Load multi-period data
            category_dfs, spu_dfs = self.data_repository.load_multi_period_data(periods)
            
            # Process subcategory-level data
            if category_dfs:
                subcategory_df = self.data_repository.aggregate_subcategory_data(category_dfs)
                subcategory_filtered = self.matrix_processor.filter_subcategory_data(subcategory_df, anomaly_stores)
                
                # Create subcategory matrix
                subcategory_matrix, normalized_subcategory_matrix = self.matrix_processor.create_matrix(
                    subcategory_filtered, 'str_code', 'sub_cate_name', 'sal_amt', 'subcategory'
                )
                
                # Save subcategory matrices
                self.matrix_processor.save_matrix_files(subcategory_matrix, normalized_subcategory_matrix, "subcategory")
                
                # Save general store list (from subcategory analysis)
                self._save_general_store_list(subcategory_matrix)
                
                self.logger.info("✓ Subcategory-level matrices created successfully", self.class_name)
            else:
                self.logger.warning("No category data available - skipping subcategory analysis", self.class_name)
            
            # Process SPU-level data if available
            if spu_dfs:
                spu_df = self.data_repository.aggregate_spu_data(spu_dfs)
                spu_filtered = self.matrix_processor.filter_spu_data(spu_df, anomaly_stores)
                
                # Create SPU matrix (may be limited for memory management)
                spu_matrix, normalized_spu_matrix = self.matrix_processor.create_matrix(
                    spu_filtered, 'str_code', 'spu_code', 'spu_sales_amt', 'spu'
                )
                
                # Save SPU matrices
                matrix_type = "spu_limited" if spu_matrix.shape[1] <= self.matrix_processor.max_spu_count else "spu"
                self.matrix_processor.save_matrix_files(spu_matrix, normalized_spu_matrix, matrix_type)
                
                # Create category-aggregated matrix
                category_matrix, normalized_category_matrix = self.matrix_processor.create_category_aggregated_matrix(
                    spu_filtered, anomaly_stores
                )
                self.matrix_processor.save_matrix_files(category_matrix, normalized_category_matrix, "category_agg")
                
                self.logger.info("✓ SPU-level matrices created successfully", self.class_name)
            else:
                self.logger.warning("No SPU data available - skipping SPU analysis", self.class_name)
            
            # Store results in context
            context.set_state("matrices_created", True)
            context.set_state("subcategory_available", len(category_dfs) > 0)
            context.set_state("spu_available", len(spu_dfs) > 0)
            
            self.logger.info("Matrix preparation step completed successfully", self.class_name)
            return context
            
        except Exception as e:
            self.logger.error(f"Apply phase failed: {str(e)}", self.class_name)
            raise
    
    def _get_year_over_year_periods(self, target_period: str) -> List[Tuple[str, str]]:
        """
        Get year-over-year periods for matrix creation.
        
        Args:
            target_period: Target period in YYYYMM format
            
        Returns:
            List of (yyyymm, period) tuples
        """
        # Parse target period
        yyyymm = target_period[:6]
        period = target_period[6:] if len(target_period) > 6 else "A"
        
        # Generate periods for the last 3 months
        periods = []
        year = int(yyyymm[:4])
        month = int(yyyymm[4:6])
        
        # Add current period
        periods.append((yyyymm, period))
        
        # Add previous periods (last 3 months)
        for i in range(1, 6):  # 5 additional periods
            if period == "A":
                period = "B"
            else:
                period = "A"
                month -= 1
                if month < 1:
                    month = 12
                    year -= 1
            
            periods.append((f"{year:04d}{month:02d}", period))
        
        # Reverse to get chronological order
        periods.reverse()
        
        return periods
    
    def _save_general_store_list(self, matrix: pd.DataFrame) -> None:
        """
        Save general store list from matrix.

        Args:
            matrix: Matrix with stores as index
        """
        from ..config_new.output_config import get_output_config

        output_config = get_output_config()
        os.makedirs(output_config.step3_output_dir, exist_ok=True)

        store_list_file = output_config.get_step3_file_path("store_list.txt")
        with open(store_list_file, 'w') as f:
            for store in matrix.index:
                f.write(f"{store}\n")

        self.logger.info(f"Saved general store list with {len(matrix)} stores", self.class_name)
    
    def validate(self, context: StepContext) -> bool:
        """
        Validate that matrix preparation was successful.
        
        Args:
            context: Pipeline context
            
        Returns:
            True if validation passes
        """
        try:
            matrices_created = context.get_state("matrices_created", False)
            
            if not matrices_created:
                self.logger.error("Matrices were not created", self.class_name)
                return False
            
            # Check if required files exist
            required_files = [
                "data/store_subcategory_matrix.csv",
                "data/normalized_subcategory_matrix.csv",
                "data/subcategory_store_list.txt",
                "data/store_list.txt"
            ]
            
            missing_files = []
            for file_path in required_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.logger.error(f"Missing required files: {missing_files}", self.class_name)
                return False
            
            self.logger.info("Matrix preparation validation passed", self.class_name)
            return True
            
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}", self.class_name)
            return False
