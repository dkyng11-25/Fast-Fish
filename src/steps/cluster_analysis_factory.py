#!/usr/bin/env python3
"""
Factory function for Step 6: Cluster Analysis

This is the composition root for Step 6 - all dependency injection happens here.
This function creates and wires all dependencies for the ClusterAnalysisStep.
"""

from typing import Optional
from repositories import MatrixRepository, TemperatureRepository, CsvFileRepository
from steps.cluster_analysis_step import ClusterAnalysisStep, ClusterConfig
from core.logger import PipelineLogger


def create_cluster_analysis_step(
    matrix_type: str,
    target_yyyymm: str,
    target_period: str,
    output_dir: str = "output",
    pca_components: int = 20,
    target_cluster_size: int = 50,
    min_cluster_size: int = 50,  # CHANGED: Match legacy strict balancing
    max_cluster_size: int = 50,  # CHANGED: Match legacy strict balancing
    enable_temperature_constraints: bool = False,
    enable_cluster_balancing: bool = True,  # NEW: Enable cluster balancing
    max_balance_iterations: int = 100,
    random_state: int = 42,
    logger: Optional[PipelineLogger] = None
) -> ClusterAnalysisStep:
    """
    Factory function to create Step 6 with all dependencies.
    
    This is the composition root - all dependency injection happens here.
    
    Args:
        matrix_type: Type of matrix to cluster ("spu", "subcategory", "category_agg")
        target_yyyymm: Target year-month (e.g., "202506")
        target_period: Target period ("A" or "B")
        output_dir: Directory for output files (default: "output")
        pca_components: Number of PCA components for dimensionality reduction
        target_cluster_size: Target number of stores per cluster (default: 50)
        min_cluster_size: Minimum allowed cluster size (default: 50, matches legacy)
        max_cluster_size: Maximum allowed cluster size (default: 50, matches legacy)
        enable_temperature_constraints: Enable temperature-aware clustering
        enable_cluster_balancing: Enable cluster balancing (default: True)
        max_balance_iterations: Maximum iterations for cluster balancing (default: 100)
        random_state: Random seed for reproducibility
        logger: Optional logger instance (creates new one if not provided)
    
    Note:
        By default, min_cluster_size = max_cluster_size = 50 to match legacy behavior.
        This produces very tight clustering (std dev ~3-4) with most clusters at exactly 50 stores.
        For flexible clustering, explicitly set different min/max values.
    
    Returns:
        ClusterAnalysisStep: Fully configured step instance
    
    Example:
        >>> # Create step for SPU matrix clustering
        >>> step = create_cluster_analysis_step(
        ...     matrix_type="spu",
        ...     target_yyyymm="202506",
        ...     target_period="A",
        ...     pca_components=20,
        ...     enable_temperature_constraints=True
        ... )
        >>> 
        >>> # Execute the step
        >>> from core.context import StepContext
        >>> context = StepContext()
        >>> final_context = step.execute(context)
    """
    # Create logger if not provided
    if logger is None:
        logger = PipelineLogger("Step6_ClusterAnalysis")
    
    # Build period label for output filenames
    period_label = f"{target_yyyymm}{target_period}" if target_yyyymm and target_period else ""
    
    # Create repositories
    # MatrixRepository with period support (tries period-specific files first, falls back to generic)
    matrix_repo = MatrixRepository(
        base_path=".",
        period_label=period_label  # NEW: Support period-specific matrix files
    )
    
    temperature_repo = TemperatureRepository(
        base_path=".",
        temperature_file=None,  # Will use default
        preferred_band_column="temperature_band_q3q4_seasonal"
    )
    
    # Create separate repository for EACH output file (following Steps 1, 2, 5 pattern)
    # Each repository knows its full file path including period
    clustering_results_repo = CsvFileRepository(
        file_path=f"{output_dir}/clustering_results_{matrix_type}_{period_label}.csv",
        logger=logger
    )
    
    cluster_profiles_repo = CsvFileRepository(
        file_path=f"{output_dir}/cluster_profiles_{matrix_type}_{period_label}.csv",
        logger=logger
    )
    
    per_cluster_metrics_repo = CsvFileRepository(
        file_path=f"{output_dir}/per_cluster_metrics_{matrix_type}_{period_label}.csv",
        logger=logger
    )
    
    # Create step configuration
    config = ClusterConfig(
        matrix_type=matrix_type,
        pca_components=100,  # Use 100 for temperature-aware (legacy), 20 for standard
        target_cluster_size=target_cluster_size,
        min_cluster_size=min_cluster_size,
        max_cluster_size=max_cluster_size,
        enable_temperature_constraints=enable_temperature_constraints,
        enable_cluster_balancing=enable_cluster_balancing,  # NEW
        output_dir=output_dir,
        max_balance_iterations=max_balance_iterations,
        random_state=random_state
    )
    
    # Create and return step with all dependencies injected
    # Business logic (clustering algorithm) is in the step's apply() method
    # One repository per output file (following Steps 1, 2, 5 pattern)
    return ClusterAnalysisStep(
        matrix_repo=matrix_repo,
        temperature_repo=temperature_repo,
        clustering_results_repo=clustering_results_repo,
        cluster_profiles_repo=cluster_profiles_repo,
        per_cluster_metrics_repo=per_cluster_metrics_repo,
        config=config,
        logger=logger,
        step_name="Cluster Analysis",
        step_number=6
    )


# Example usage (for documentation and testing)
if __name__ == "__main__":
    import os
    from core.context import StepContext
    from core.exceptions import DataValidationError
    
    # Get configuration from environment variables
    target_yyyymm = os.environ.get('PIPELINE_TARGET_YYYYMM', '202510')
    target_period = os.environ.get('PIPELINE_TARGET_PERIOD', 'A')
    matrix_type = os.environ.get('PIPELINE_MATRIX_TYPE', 'spu')
    
    print(f"Creating Step 6 for {matrix_type} matrix, period {target_yyyymm}{target_period}")
    
    # Create step with dependencies
    step = create_cluster_analysis_step(
        matrix_type=matrix_type,
        target_yyyymm=target_yyyymm,
        target_period=target_period,
        pca_components=20,
        target_cluster_size=50,
        enable_temperature_constraints=True
    )
    
    # Create initial context
    context = StepContext()
    
    # Execute step
    try:
        print("Executing Step 6...")
        final_context = step.execute(context)
        print("✅ Step 6 completed successfully")
        
        # Show summary
        results = final_context.data.get('results')
        if results is not None:
            n_stores = len(results)
            n_clusters = results['Cluster'].nunique()
            print(f"Clustered {n_stores} stores into {n_clusters} clusters")
        
    except DataValidationError as e:
        print(f"❌ Step 6 validation failed: {e}")
        raise
    except Exception as e:
        print(f"❌ Step 6 execution failed: {e}")
        raise
