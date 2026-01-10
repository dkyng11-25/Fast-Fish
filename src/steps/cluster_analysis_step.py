"""
Step 6: Cluster Analysis

This step performs clustering analysis on store-level matrices to group similar
stores together for targeted merchandising strategies.

Supports:
- Multiple matrix types (SPU, subcategory, category-aggregated)
- PCA dimensionality reduction
- KMeans clustering with flexible balancing
- Temperature-aware clustering (optional)
- Comprehensive metrics and visualizations

Author: Data Pipeline Team
Date: 2025-10-22
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

from core.step import Step
from core.context import StepContext
from core.logger import PipelineLogger
from core.exceptions import DataValidationError

# Optional imports - may not be available in all environments
try:
    from config import get_current_period, get_period_label
except ImportError:
    get_current_period = None
    get_period_label = None

try:
    from output_utils import create_output_with_symlinks
except ImportError:
    create_output_with_symlinks = None


@dataclass
class ClusterConfig:
    """Configuration for cluster analysis."""
    matrix_type: str  # "spu", "subcategory", or "category_agg"
    pca_components: int
    target_cluster_size: int
    min_cluster_size: int
    max_cluster_size: int
    enable_temperature_constraints: bool
    enable_cluster_balancing: bool = True  # Enable cluster balancing
    strict_balancing: bool = False  # NEW: Enforce exactly target_cluster_size (legacy mode)
    output_dir: str = "output"  # Output directory for results
    max_balance_iterations: int = 100
    random_state: int = 42
    n_init: int = 10
    max_iter: int = 300


class ClusterAnalysisStep(Step):
    """
    Step 6: Cluster Analysis
    
    Groups stores based on sales patterns using PCA and KMeans clustering.
    Supports temperature-aware clustering and flexible cluster balancing.
    """
    
    def __init__(
        self,
        matrix_repo,  # MatrixRepository
        temperature_repo,  # TemperatureRepository
        clustering_results_repo,  # CsvFileRepository - one per output file
        cluster_profiles_repo,    # CsvFileRepository - one per output file
        per_cluster_metrics_repo, # CsvFileRepository - one per output file
        config: ClusterConfig,
        logger: PipelineLogger,
        step_name: str = "Cluster Analysis",
        step_number: int = 6
    ):
        """
        Initialize the ClusterAnalysisStep.
        
        Args:
            matrix_repo: Repository for matrix data access
            temperature_repo: Repository for temperature data
            clustering_results_repo: Repository for saving clustering results
            cluster_profiles_repo: Repository for saving cluster profiles
            per_cluster_metrics_repo: Repository for saving per-cluster metrics
            config: Configuration for clustering
            logger: Pipeline logger
            step_name: Name of the step
            step_number: Step number in pipeline
        """
        super().__init__(logger, step_name, step_number)
        self.matrix_repo = matrix_repo
        self.temperature_repo = temperature_repo
        self.clustering_results_repo = clustering_results_repo
        self.cluster_profiles_repo = cluster_profiles_repo
        self.per_cluster_metrics_repo = per_cluster_metrics_repo
        self.config = config
        
        # Will be populated during execution
        self.pca_model: Optional[PCA] = None
        self.kmeans_model: Optional[KMeans] = None
    
    def setup(self, context: StepContext) -> StepContext:
        """
        Load matrices and temperature data.
        
        Args:
            context: Step context
            
        Returns:
            Updated context with loaded data
        """
        self.logger.info(f"Loading {self.config.matrix_type} matrices...")
        
        # Load normalized matrix
        normalized_df = self.matrix_repo.get_normalized_matrix(self.config.matrix_type)
        if normalized_df is None or normalized_df.empty:
            raise DataValidationError(f"Normalized matrix not found for {self.config.matrix_type}")
        
        self.logger.info(f"Loaded normalized matrix: {normalized_df.shape[0]} stores, {normalized_df.shape[1]} features")
        
        # Load original matrix
        original_df = self.matrix_repo.get_original_matrix(self.config.matrix_type)
        if original_df is None or original_df.empty:
            raise DataValidationError(f"Original matrix not found for {self.config.matrix_type}")
        
        self.logger.info(f"Loaded original matrix: {original_df.shape[0]} stores, {original_df.shape[1]} features")
        
        # Ensure indices are strings for alignment
        normalized_df.index = normalized_df.index.astype(str)
        original_df.index = original_df.index.astype(str)
        
        # Validate matrix consistency
        if normalized_df.shape != original_df.shape:
            self.logger.warning(f"Matrix shapes don't match - normalized: {normalized_df.shape}, original: {original_df.shape}")
        
        # Load temperature data if enabled
        temp_df = None
        if self.config.enable_temperature_constraints:
            temp_df = self.temperature_repo.get_temperature_data()
            if temp_df is not None:
                temp_df.index = temp_df.index.astype(str)
                self.logger.info(f"Loaded temperature data for {len(temp_df)} stores")
                
                # Filter matrices to only stores with temperature data
                temp_stores = set(temp_df.index)
                stores_before = len(normalized_df)
                
                normalized_df = normalized_df[normalized_df.index.isin(temp_stores)]
                original_df = original_df[original_df.index.isin(temp_stores)]
                
                stores_after = len(normalized_df)
                self.logger.info(f"Filtered matrices to stores with temperature data: {stores_before} → {stores_after} stores")
                
                if stores_after == 0:
                    raise DataValidationError("No stores remaining after temperature filtering")
            else:
                self.logger.warning("Temperature constraints enabled but no temperature data available")
        
        # Store in context
        context.data = {
            'normalized_matrix': normalized_df,
            'original_matrix': original_df,
            'temperature_data': temp_df
        }
        
        return context
    
    def apply(self, context: StepContext) -> StepContext:
        """
        Perform clustering analysis (APPLY phase - business logic).
        
        This method contains the core clustering algorithm (legacy proven implementation).
        Business logic belongs in the apply() method per the 4-phase pattern.
        
        Args:
            context: Step context with loaded data
            
        Returns:
            Updated context with clustering results
        """
        normalized_df = context.data['normalized_matrix']
        original_df = context.data['original_matrix']
        temp_df = context.data.get('temperature_data')
        
        self.logger.info("Starting clustering analysis...")
        
        # Use temperature-aware clustering if enabled and data available
        if self.config.enable_temperature_constraints and temp_df is not None:
            self.logger.info("Using temperature-aware clustering algorithm (legacy proven)...")
            final_labels, pca_df, cluster_profiles = self._perform_temperature_aware_clustering(
                normalized_df, original_df, temp_df
            )
            self.logger.info(f"Temperature-aware clustering created {len(np.unique(final_labels))} clusters")
        else:
            # Fallback to simple clustering if no temperature data
            self.logger.info("Using standard clustering (no temperature data)...")
            pca_df, variance_explained = self._apply_pca(normalized_df)
            self.logger.info(f"PCA complete: {pca_df.shape[1]} components, {variance_explained:.2%} variance explained")
            
            n_clusters = self._determine_optimal_clusters(len(normalized_df))
            self.logger.info(f"Target clusters: {n_clusters}")
            
            initial_labels = self._perform_clustering(pca_df, n_clusters)
            final_labels = self._balance_clusters(pca_df, initial_labels)
            self.logger.info(f"Cluster balancing complete")
            
            cluster_profiles = self._calculate_profiles(original_df, final_labels)
        
        # Create results DataFrame
        results_df = pd.DataFrame({
            'str_code': original_df.index,
            'Cluster': final_labels,
            'cluster_id': final_labels  # Compatibility column
        })
        
        # Store in context
        context.data['pca_data'] = pca_df
        context.data['cluster_labels'] = final_labels
        context.data['cluster_profiles'] = cluster_profiles
        context.data['results'] = results_df
        
        # Calculate quality metrics (for validation to check)
        self.logger.info("Calculating clustering quality metrics...")
        
        silhouette = silhouette_score(pca_df, final_labels)
        calinski = calinski_harabasz_score(pca_df, final_labels)
        davies_bouldin = davies_bouldin_score(pca_df, final_labels)
        
        overall_metrics = {
            'silhouette_score': silhouette,
            'calinski_harabasz_score': calinski,
            'davies_bouldin_score': davies_bouldin,
            'n_clusters': len(np.unique(final_labels)),
            'n_stores': len(final_labels)
        }
        
        self.logger.info(f"Silhouette Score: {silhouette:.3f}")
        self.logger.info(f"Calinski-Harabasz: {calinski:.1f}")
        self.logger.info(f"Davies-Bouldin: {davies_bouldin:.3f}")
        
        # Per-cluster metrics
        per_cluster_metrics = self._calculate_per_cluster_metrics(pca_df, final_labels)
        
        context.data['overall_metrics'] = overall_metrics
        context.data['per_cluster_metrics'] = per_cluster_metrics
        
        return context
    
    def validate(self, context: StepContext) -> None:
        """
        Validate clustering results.
        
        Args:
            context: Step context with clustering results
            
        Raises:
            DataValidationError: If validation fails
        """
        # Check 1: Results exist
        if 'results' not in context.data or context.data['results'] is None:
            raise DataValidationError("No clustering results generated")
        
        results = context.data['results']
        
        # Check if results is empty
        if len(results) == 0:
            raise DataValidationError("No clustering results generated")
        
        # Check 2: Required columns (MUST come before accessing columns!)
        required_cols = ['str_code', 'Cluster', 'cluster_id']
        missing_cols = [col for col in required_cols if col not in results.columns]
        
        if missing_cols:
            raise DataValidationError(f"Missing required columns: {missing_cols}")
        
        # Check 3: Cluster count
        n_clusters = results['Cluster'].nunique()
        if n_clusters < 1:
            raise DataValidationError("No clusters generated")
        
        # Check 4: Cluster size constraints
        cluster_sizes = results.groupby('Cluster').size()
        
        undersized = cluster_sizes[cluster_sizes < self.config.min_cluster_size]
        # Allow ONE undersized cluster (remainder when total stores not divisible by target)
        if len(undersized) > 1:
            raise DataValidationError(
                f"Multiple clusters smaller than minimum size {self.config.min_cluster_size}: "
                f"{undersized.to_dict()}"
            )
        
        oversized = cluster_sizes[cluster_sizes > self.config.max_cluster_size]
        if len(oversized) > 0:
            raise DataValidationError(
                f"Clusters larger than maximum size {self.config.max_cluster_size}: "
                f"{oversized.to_dict()}"
            )
        
        # Check 5: Store assignment
        if results['Cluster'].isnull().any():
            raise DataValidationError("Stores without cluster assignment found")
        
        # Check 6: Clustering quality
        overall_metrics = context.data.get('overall_metrics', {})
        silhouette = overall_metrics.get('silhouette_score', -1)
        
        if silhouette < -0.5:
            raise DataValidationError(
                f"Poor clustering quality: silhouette score {silhouette:.3f} < -0.5"
            )
        
        self.logger.info(f"Validation passed: {n_clusters} clusters, {len(results)} stores")
    
    def persist(self, context: StepContext) -> StepContext:
        """
        Save clustering results.
        
        Following Steps 1, 2, 5 pattern: Simple repo.save() calls.
        Each repository knows its full file path including period.
        
        Also creates generic symlinks for backward compatibility:
        - clustering_results_{matrix_type}.csv -> period-specific file
        - cluster_profiles_{matrix_type}.csv -> period-specific file
        - per_cluster_metrics_{matrix_type}.csv -> period-specific file
        
        Args:
            context: Step context with results
            
        Returns:
            Updated context
        """
        from pathlib import Path
        
        results_df = context.data['results']
        cluster_profiles = context.data['cluster_profiles']
        per_cluster_metrics = context.data['per_cluster_metrics']
        
        self.logger.info("Saving clustering results...")
        
        # Simple save - repository knows its file path
        self.clustering_results_repo.save(results_df)
        self.logger.info(f"Saved: {self.clustering_results_repo.file_path}")
        
        self.cluster_profiles_repo.save(cluster_profiles)
        self.logger.info(f"Saved: {self.cluster_profiles_repo.file_path}")
        
        self.per_cluster_metrics_repo.save(per_cluster_metrics)
        self.logger.info(f"Saved: {self.per_cluster_metrics_repo.file_path}")
        
        # Create generic symlinks for backward compatibility
        matrix_type = self.config.matrix_type
        self._create_generic_symlink(
            self.clustering_results_repo.file_path,
            f"output/clustering_results_{matrix_type}.csv"
        )
        self._create_generic_symlink(
            self.cluster_profiles_repo.file_path,
            f"output/cluster_profiles_{matrix_type}.csv"
        )
        self._create_generic_symlink(
            self.per_cluster_metrics_repo.file_path,
            f"output/per_cluster_metrics_{matrix_type}.csv"
        )
        
        self.logger.info("Clustering analysis complete!")
        
        return context
    
    def _create_generic_symlink(self, source_file: str, generic_file: str) -> None:
        """
        Create symlink from generic filename to period-specific file.
        
        For backward compatibility with steps expecting generic filenames.
        
        Args:
            source_file: Period-specific file path (e.g., file_202506A.csv)
            generic_file: Generic file path (e.g., file.csv)
        """
        from pathlib import Path
        
        source_path = Path(source_file)
        generic_path = Path(generic_file)
        
        if not source_path.exists():
            self.logger.warning(f"Source file doesn't exist: {source_file}")
            return
        
        # Remove existing symlink or file
        if generic_path.exists() or generic_path.is_symlink():
            generic_path.unlink()
        
        # Create symlink (relative path for portability)
        generic_path.symlink_to(source_path.name)
        self.logger.info(f"Created symlink: {generic_file} -> {source_path.name}")
    
    # ========================================================================
    # Private Helper Methods - APPLY Phase
    # ========================================================================
    
    def _apply_pca(self, normalized_df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
        """Apply PCA transformation to reduce dimensionality."""
        n_stores, n_features = normalized_df.shape
        
        # Determine optimal components
        n_components = min(self.config.pca_components, n_stores, n_features)
        
        self.logger.info(f"Applying PCA: {n_features} features → {n_components} components")
        
        # Apply PCA
        self.pca_model = PCA(n_components=n_components, random_state=self.config.random_state)
        pca_data = self.pca_model.fit_transform(normalized_df)
        
        # Create DataFrame
        pca_df = pd.DataFrame(
            pca_data,
            index=normalized_df.index,
            columns=[f"PC{i+1}" for i in range(n_components)]
        )
        
        # Calculate variance explained
        variance_explained = self.pca_model.explained_variance_ratio_.sum()
        
        return pca_df, variance_explained
    
    def _determine_optimal_clusters(self, n_stores: int) -> int:
        """Determine optimal number of clusters based on target size."""
        n_clusters = int(np.ceil(n_stores / self.config.target_cluster_size))
        return max(1, n_clusters)
    
    def _perform_clustering(self, pca_df: pd.DataFrame, n_clusters: int) -> np.ndarray:
        """Perform initial KMeans clustering."""
        self.logger.info(f"Performing KMeans clustering with {n_clusters} clusters...")
        
        self.kmeans_model = KMeans(
            n_clusters=n_clusters,
            random_state=self.config.random_state,
            n_init=self.config.n_init,
            max_iter=self.config.max_iter
        )
        
        cluster_labels = self.kmeans_model.fit_predict(pca_df)
        
        # Log cluster sizes
        unique, counts = np.unique(cluster_labels, return_counts=True)
        self.logger.info(f"Initial cluster sizes: min={counts.min()}, max={counts.max()}, mean={counts.mean():.1f}")
        
        return cluster_labels
    
    def _balance_clusters(self, pca_df: pd.DataFrame, initial_labels: np.ndarray) -> np.ndarray:
        """
        Balance clusters to respect size constraints.
        
        Uses the legacy-proven balancing algorithm to ensure clusters are
        approximately target_cluster_size stores each (default 50).
        
        Args:
            pca_df: PCA-transformed features
            initial_labels: Initial cluster labels from KMeans
            
        Returns:
            Balanced cluster labels
        """
        # Check if balancing is enabled
        if not self.config.enable_cluster_balancing:
            self.logger.info("Cluster balancing disabled, using initial labels")
            return initial_labels
        
        self.logger.info("Balancing clusters...")
        
        # Log initial cluster sizes
        initial_sizes = np.bincount(initial_labels, minlength=len(np.unique(initial_labels)))
        self.logger.info(f"Initial cluster sizes: min={initial_sizes.min()}, max={initial_sizes.max()}, mean={initial_sizes.mean():.1f}")
        
        # Use legacy algorithm (proven to produce well-balanced clusters)
        balanced_labels = self._balance_clusters_legacy(pca_df, initial_labels)
        
        # Log final sizes
        final_sizes = np.bincount(balanced_labels, minlength=len(np.unique(balanced_labels)))
        self.logger.info(f"Final cluster sizes: min={final_sizes.min()}, max={final_sizes.max()}, mean={final_sizes.mean():.1f}")
        self.logger.info(f"Cluster size range: {final_sizes.min()}-{final_sizes.max()}")
        
        return balanced_labels
    
    def _perform_temperature_aware_clustering(
        self,
        normalized_df: pd.DataFrame,
        original_df: pd.DataFrame,
        temp_df: pd.DataFrame
    ) -> Tuple[np.ndarray, pd.DataFrame, pd.DataFrame]:
        """
        Perform temperature-aware clustering (legacy proven algorithm).
        
        This is the core business logic for temperature-aware clustering.
        It groups stores by temperature bands and clusters within each group,
        producing well-balanced clusters (e.g., 40/60 stores).
        
        Args:
            normalized_df: Normalized feature matrix
            original_df: Original feature matrix
            temp_df: Temperature data with band information
            
        Returns:
            Tuple of (cluster_labels, pca_df, cluster_profiles)
        """
        # Determine temperature band column
        band_col = self._get_temperature_band_column(temp_df)
        
        # Group temperature bands
        band_groups = self._group_temperature_bands(temp_df, band_col)
        self.logger.info(f"Created {len(band_groups)} temperature band groups")
        
        # Apply PCA globally for consistency
        pca_df_global, pca_model = self._apply_pca(normalized_df)
        self.pca_model = pca_model
        
        # Cluster each band group
        all_labels = []
        all_store_indices = []
        combined_pca_data = []
        global_cluster_id = 0
        
        for gi, group_bands in enumerate(band_groups):
            self.logger.info(f"Processing band group {gi+1}/{len(band_groups)}: {group_bands[0]} .. {group_bands[-1]}")
            
            # Get stores in this band group
            group_stores = temp_df[temp_df[band_col].isin(group_bands)].index.astype(str)
            valid_store_index = pca_df_global.index.astype(str)
            valid_group_stores = [s for s in group_stores if s in valid_store_index]
            group_size = len(valid_group_stores)
            
            self.logger.info(f"  • {group_size} stores in this group")
            
            if group_size == 0:
                continue
            
            group_pca_df = pca_df_global.loc[valid_group_stores]
            
            # Determine number of clusters for this group
            n_clusters = max(1, int(round(group_size / self.config.target_cluster_size)))
            if group_size < int(1.2 * self.config.target_cluster_size):
                n_clusters = 1
            
            self.logger.info(f"  • Creating {n_clusters} clusters for this group")
            
            # Perform clustering
            if n_clusters == 1:
                cluster_labels = np.zeros(group_size, dtype=int)
            else:
                kmeans = KMeans(
                    n_clusters=n_clusters,
                    random_state=self.config.random_state,
                    n_init=self.config.n_init,
                    max_iter=self.config.max_iter
                )
                cluster_labels = kmeans.fit_predict(group_pca_df)
            
            # Balance clusters within this group
            balanced_labels = self._balance_clusters_legacy(group_pca_df, cluster_labels)
            
            # Adjust labels for global cluster IDs
            adjusted_labels = balanced_labels + global_cluster_id
            global_cluster_id += len(np.unique(balanced_labels))
            
            all_labels.extend(adjusted_labels)
            all_store_indices.extend(valid_group_stores)
            combined_pca_data.append(group_pca_df)
        
        # Combine results
        final_labels = np.array(all_labels)
        final_store_indices = all_store_indices
        
        if combined_pca_data:
            combined_pca_df = pd.concat(combined_pca_data)
        else:
            combined_pca_df = pca_df_global
        
        # Align with original matrix
        original_index_str = original_df.index.astype(str)
        aligned_store_indices = [s for s in final_store_indices if s in original_index_str]
        
        if len(aligned_store_indices) != len(final_store_indices):
            keep_mask = [s in original_index_str for s in final_store_indices]
            final_labels = np.array(final_labels)[np.array(keep_mask, dtype=bool)]
            combined_pca_df = combined_pca_df.loc[aligned_store_indices]
        
        # Create cluster profiles
        cluster_profiles = self._calculate_profiles(
            original_df.loc[aligned_store_indices],
            final_labels
        )
        
        return final_labels, combined_pca_df, cluster_profiles
    
    def _get_temperature_band_column(self, temp_df: pd.DataFrame) -> str:
        """Determine which temperature band column to use."""
        if '__band_col__' in temp_df.columns:
            return temp_df['__band_col__'].iloc[0]
        elif 'temperature_band_q3q4_seasonal' in temp_df.columns:
            return 'temperature_band_q3q4_seasonal'
        else:
            return 'temperature_band'
    
    def _group_temperature_bands(
        self,
        temp_df: pd.DataFrame,
        band_col: str
    ) -> List[List[str]]:
        """
        Group temperature bands to ensure minimum group size.
        
        Merges adjacent bands until each group has at least 100 stores (band_group_min_size).
        """
        def band_lower(b: str) -> float:
            """Extract lower bound temperature from band label."""
            try:
                return float(str(b).split('°C')[0])
            except Exception:
                return float('inf')
        
        # Get sorted bands
        bands = sorted([b for b in temp_df[band_col].dropna().unique()], key=band_lower)
        
        # Group bands
        band_groups: List[List[str]] = []
        current_group: List[str] = []
        current_count = 0
        band_group_min_size = 100  # Minimum stores per band group
        
        for b in bands:
            b_count = int((temp_df[band_col] == b).sum())
            current_group.append(b)
            current_count += b_count
            
            if current_count >= band_group_min_size:
                band_groups.append(current_group)
                current_group = []
                current_count = 0
        
        # Handle leftover small group
        if current_group:
            if len(band_groups) > 0:
                band_groups[-1].extend(current_group)
            else:
                band_groups.append(current_group)
        
        return band_groups
    
    def _balance_clusters_legacy(
        self,
        pca_df: pd.DataFrame,
        initial_labels: np.ndarray
    ) -> np.ndarray:
        """
        Balance clusters using legacy algorithm (proven to produce well-balanced clusters).
        
        This is the original balancing logic from legacy Step 6 that ensures
        clusters are approximately target_cluster_size stores each.
        
        Algorithm:
        1. Calculate cluster centers and distances
        2. Iteratively move stores from oversized to undersized clusters
        3. Move farthest stores first (minimal impact on cluster quality)
        4. Assign stores to nearest available cluster
        5. Converge when all clusters within [min_size, max_size]
        
        Args:
            pca_df: PCA-transformed features
            initial_labels: Initial cluster labels
            
        Returns:
            Balanced cluster labels
        """
        features = pca_df.values
        labels = initial_labels.copy()
        n_clusters = np.max(labels) + 1
        n_samples = features.shape[0]
        
        # Calculate initial cluster centers
        self.logger.info("Calculating cluster centers for balancing...")
        centers = np.zeros((n_clusters, features.shape[1]))
        for i in range(n_clusters):
            mask = labels == i
            if np.sum(mask) > 0:
                centers[i] = np.mean(features[mask], axis=0)
        
        # Calculate distances to all cluster centers (pre-compute for efficiency)
        self.logger.info("Calculating distances for cluster balancing...")
        distances = np.zeros((n_samples, n_clusters))
        for i in range(n_clusters):
            distances[:, i] = np.sum((features - centers[i]) ** 2, axis=1)
        
        # Get initial cluster sizes
        initial_counts = np.array([np.sum(labels == i) for i in range(n_clusters)])
        self.logger.info(f"Initial cluster sizes: {initial_counts}")
        
        # Iterative balancing
        iteration = 0
        while iteration < self.config.max_balance_iterations:
            iteration += 1
            
            # Log progress every 10 iterations
            if iteration % 10 == 0:
                self.logger.info(f"Balance iteration {iteration}...")
            
            # Update cluster counts
            counts = np.array([np.sum(labels == i) for i in range(n_clusters)])
            
            # Check if constraints satisfied
            oversized = np.where(counts > self.config.max_cluster_size)[0]
            undersized = np.where(counts < self.config.min_cluster_size)[0]
            
            if len(oversized) == 0 and len(undersized) == 0:
                self.logger.info(f"All constraints satisfied after {iteration} iterations")
                break
            
            # Handle oversized clusters
            for cluster_id in oversized:
                cluster_samples = np.where(labels == cluster_id)[0]
                dist_to_center = distances[cluster_samples, cluster_id]
                
                # Sort by distance (farthest first)
                sorted_indices = np.argsort(-dist_to_center)
                
                # Number of samples to move
                excess = counts[cluster_id] - self.config.max_cluster_size
                
                # Move the farthest points to other clusters
                for idx in sorted_indices[:excess]:
                    sample_idx = cluster_samples[idx]
                    
                    # Find the next best cluster
                    dist_to_centers = distances[sample_idx].copy()
                    
                    # Create a mask for clusters that are full
                    full_clusters = counts >= self.config.max_cluster_size
                    full_clusters[cluster_id] = True  # Exclude current cluster
                    
                    # Set distances to full clusters to infinity
                    dist_to_centers[full_clusters] = float('inf')
                    
                    # Get the closest non-full cluster
                    new_cluster = np.argmin(dist_to_centers)
                    
                    # Move the sample
                    labels[sample_idx] = new_cluster
                    counts[cluster_id] -= 1
                    counts[new_cluster] += 1
                    
                    # Break if we've moved enough samples
                    if counts[cluster_id] <= self.config.max_cluster_size:
                        break
            
            # Handle undersized clusters (if no oversized clusters remain)
            if len(oversized) == 0 and len(undersized) > 0:
                # Find donor clusters (largest first)
                donors = np.argsort(-counts)
                
                for u in undersized:
                    for d in donors:
                        if d == u or counts[d] <= self.config.min_cluster_size:
                            continue
                        
                        # Find stores in donor cluster closest to undersized cluster
                        donor_indices = np.where(labels == d)[0]
                        nearest_idx = donor_indices[np.argmin(distances[donor_indices, u])]
                        
                        # Move the store
                        labels[nearest_idx] = u
                        counts[d] -= 1
                        counts[u] += 1
                        break
        
        # Final cluster sizes
        final_counts = np.array([np.sum(labels == i) for i in range(n_clusters)])
        self.logger.info(f"Final cluster sizes: {final_counts}")
        
        return labels
    
    def _apply_temperature_clustering(
        self, 
        pca_df: pd.DataFrame, 
        labels: np.ndarray, 
        temp_df: pd.DataFrame
    ) -> np.ndarray:
        """Apply temperature-aware clustering by regrouping within temperature bands."""
        self.logger.info("Applying temperature-aware clustering...")
        
        # Align temperature data with PCA data
        common_stores = pca_df.index.intersection(temp_df.index)
        
        if len(common_stores) == 0:
            self.logger.warning("No common stores between clustering and temperature data")
            return labels
        
        # Get temperature bands
        temp_bands = temp_df.loc[common_stores, 'temperature_band']
        
        # Recluster within each temperature band
        new_labels = labels.copy()
        next_cluster_id = labels.max() + 1
        
        for band in temp_bands.unique():
            band_stores = temp_bands[temp_bands == band].index
            band_pca = pca_df.loc[band_stores]
            
            # Determine clusters for this band
            n_band_clusters = max(1, len(band_stores) // self.config.target_cluster_size)
            
            if n_band_clusters > 1:
                kmeans = KMeans(n_clusters=n_band_clusters, random_state=self.config.random_state)
                band_labels = kmeans.fit_predict(band_pca)
                
                # Assign new cluster IDs
                for i, store in enumerate(band_stores):
                    new_labels[pca_df.index == store] = next_cluster_id + band_labels[i]
                
                next_cluster_id += n_band_clusters
        
        self.logger.info(f"Temperature-aware clustering created {len(np.unique(new_labels))} clusters")
        
        return new_labels
    
    def _calculate_profiles(self, original_df: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
        """Calculate cluster profiles (mean values per feature)."""
        self.logger.info("Calculating cluster profiles...")
        
        profiles = []
        for cluster_id in np.unique(labels):
            cluster_data = original_df[labels == cluster_id]
            profile = cluster_data.mean()
            profile['cluster_id'] = cluster_id
            profile['n_stores'] = len(cluster_data)
            profiles.append(profile)
        
        profiles_df = pd.DataFrame(profiles)
        
        return profiles_df
    
    # ========================================================================
    # Private Helper Methods - VALIDATE Phase
    # ========================================================================
    
    def _calculate_per_cluster_metrics(
        self, 
        pca_data: pd.DataFrame, 
        labels: np.ndarray
    ) -> pd.DataFrame:
        """Calculate metrics for each cluster."""
        metrics = []
        
        for cluster_id in np.unique(labels):
            cluster_points = pca_data[labels == cluster_id]
            center = cluster_points.mean(axis=0)
            
            # Intra-cluster distance
            distances = np.linalg.norm(cluster_points - center, axis=1)
            
            metrics.append({
                'cluster_id': cluster_id,
                'size': len(cluster_points),
                'mean_distance': distances.mean(),
                'max_distance': distances.max(),
                'cohesion': 1 / (1 + distances.mean())  # Higher is better
            })
        
        return pd.DataFrame(metrics)
    
    # ========================================================================
    # Private Helper Methods - PERSIST Phase
    # ========================================================================
    # 
    # Legacy helper methods removed - persist() now uses simple repo.save() calls
    # Following Steps 1, 2, 5 pattern
