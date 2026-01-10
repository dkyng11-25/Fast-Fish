#!/usr/bin/env python3
"""
Step 6: Cluster Analysis for Subcategory and SPU-Level Data

This step performs clustering analysis on both subcategory-level and SPU-level matrices
created in Step 3. It supports multiple clustering approaches:

1. Subcategory-level clustering (traditional approach)
2. SPU-level clustering (granular approach with top SPUs)
3. Category-aggregated clustering (balanced approach)

Key Features:
- Multiple matrix type support
- Memory-efficient processing for large SPU matrices
- Temperature-aware clustering (optional)
- Comprehensive cluster analysis and visualization
- Flexible cluster balancing

Author: Data Pipeline
Date: 2025-06-14
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score, silhouette_samples
import os
import time
from typing import Tuple, List, Dict, Optional
from datetime import datetime
import warnings
from tqdm import tqdm

# Suppress warnings
warnings.filterwarnings('ignore')

# Configuration - Matrix Selection
MATRIX_TYPE = "spu"  # SPU-level clustering for SPU rules analysis
# MATRIX_TYPE = "category_agg"  # Uncomment for category-aggregated clustering
# MATRIX_TYPE = "subcategory"  # Options: "subcategory", "spu", "category_agg"

# Matrix file paths based on type
MATRIX_CONFIGS = {
    "subcategory": {
        "normalized": "data/normalized_subcategory_matrix.csv",
        "original": "data/store_subcategory_matrix.csv",
        "feature_name": "subcategory",
        "description": "Subcategory-Level Clustering"
    },
    "spu": {
        "normalized": "data/normalized_spu_limited_matrix.csv",
        "original": "data/store_spu_limited_matrix.csv", 
        "feature_name": "SPU",
        "description": "SPU-Level Clustering (Top 1000 SPUs)"
    },
    "category_agg": {
        "normalized": "data/normalized_category_agg_matrix.csv",
        "original": "data/store_category_agg_matrix.csv",
        "feature_name": "category",
        "description": "Category-Aggregated Clustering"
    }
}

# Get current matrix configuration
CURRENT_CONFIG = MATRIX_CONFIGS[MATRIX_TYPE]
INPUT_MATRIX = CURRENT_CONFIG["normalized"]
ORIGINAL_MATRIX = CURRENT_CONFIG["original"]

# Other configuration
TEMPERATURE_DATA = "output/stores_with_feels_like_temperature.csv"
OUTPUT_DIR = "output"
RANDOM_STATE = 42
N_INIT = 10
MAX_ITER = 300

# PCA configuration - adaptive based on matrix type
PCA_COMPONENTS_CONFIG = {
    "subcategory": 50,
    "spu": 50,  # Lower components for synthetic sample
    "category_agg": 20
}
PCA_COMPONENTS = PCA_COMPONENTS_CONFIG[MATRIX_TYPE]

# Clustering constraints (within 5-degree temperature bands)
MIN_CLUSTER_SIZE = 50
MAX_CLUSTER_SIZE = 50  # Changed to enforce exactly 50 stores per cluster
MAX_BALANCE_ITERATIONS = 100
ENABLE_TEMPERATURE_CONSTRAINTS = False

# Create output directories
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_progress(message: str) -> None:
    """
    Log progress to console with timestamp.
    
    Args:
        message (str): Progress message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Load the normalized matrix, original matrix, and optionally temperature data.
    
    Returns:
        Tuple containing normalized matrix, original matrix, and temperature data
    """
    try:
        log_progress(f"Loading {CURRENT_CONFIG['description']} matrices...")
        
        # Check if files exist
        if not os.path.exists(INPUT_MATRIX):
            raise FileNotFoundError(f"Normalized matrix not found: {INPUT_MATRIX}")
        if not os.path.exists(ORIGINAL_MATRIX):
            raise FileNotFoundError(f"Original matrix not found: {ORIGINAL_MATRIX}")
        
        # Load matrices
        log_progress(f"Loading normalized matrix from {INPUT_MATRIX}")
        normalized_df = pd.read_csv(INPUT_MATRIX, index_col=0)
        log_progress(f"Loaded normalized matrix with {normalized_df.shape[0]} stores and {normalized_df.shape[1]} {CURRENT_CONFIG['feature_name']}s")
        
        log_progress(f"Loading original matrix from {ORIGINAL_MATRIX}")
        original_df = pd.read_csv(ORIGINAL_MATRIX, index_col=0)
        log_progress(f"Loaded original matrix with {original_df.shape[0]} stores and {original_df.shape[1]} {CURRENT_CONFIG['feature_name']}s")
        
        # Validate matrix consistency
        if normalized_df.shape != original_df.shape:
            log_progress(f"Warning: Matrix shapes don't match - normalized: {normalized_df.shape}, original: {original_df.shape}")
        
        # Load temperature data if temperature constraints are enabled
        temp_df = None
        if ENABLE_TEMPERATURE_CONSTRAINTS and os.path.exists(TEMPERATURE_DATA):
            try:
                temp_df = pd.read_csv(TEMPERATURE_DATA)
                temp_df.set_index('store_code', inplace=True)
                temp_df.index = temp_df.index.astype(str)
                log_progress(f"Loaded temperature data for {len(temp_df)} stores")
            except Exception as e:
                log_progress(f"Warning: Could not load temperature data: {str(e)}")
                log_progress("Proceeding with regular clustering without temperature constraints")
        elif ENABLE_TEMPERATURE_CONSTRAINTS:
            log_progress(f"Warning: Temperature constraints enabled but {TEMPERATURE_DATA} not found")
            log_progress("Run step4_download_weather_data.py and step5_calculate_feels_like_temperature.py first")
            log_progress("Proceeding with regular clustering without temperature constraints")
        
        return normalized_df, original_df, temp_df
    except Exception as e:
        log_progress(f"Error loading data: {str(e)}")
        raise

def apply_pca(normalized_df: pd.DataFrame) -> Tuple[pd.DataFrame, PCA]:
    """
    Apply PCA to reduce dimensionality.
    
    Args:
        normalized_df (pd.DataFrame): Normalized matrix data
        
    Returns:
        Tuple containing PCA-transformed data and PCA object
    """
    n_components = min(PCA_COMPONENTS, normalized_df.shape[0], normalized_df.shape[1])
    
    log_progress(f"Applying PCA with {n_components} components for {MATRIX_TYPE} clustering...")
    
    pca = PCA(n_components=n_components, random_state=RANDOM_STATE)
    
    # For large matrices, show progress
    if normalized_df.shape[1] > 500:
        log_progress("Processing large matrix - this may take a few minutes...")
    
    pca_result = pca.fit_transform(normalized_df)
    
    pca_df = pd.DataFrame(
        pca_result,
        index=normalized_df.index,
        columns=[f'PC{i+1}' for i in range(n_components)]
    )
    
    variance_explained = pca.explained_variance_ratio_.sum()
    log_progress(f"Applied PCA with {n_components} components, explaining {variance_explained:.2%} of the variance")
    
    # Log top components for SPU analysis
    if MATRIX_TYPE == "spu" and len(pca.explained_variance_ratio_) >= 10:
        log_progress("Top 10 PCA components explain:")
        for i in range(10):
            log_progress(f"  PC{i+1}: {pca.explained_variance_ratio_[i]:.3%}")
    
    return pca_df, pca

def determine_optimal_initial_clusters(pca_df: pd.DataFrame) -> int:
    """
    Determine the optimal initial number of clusters using silhouette score.
    
    Args:
        pca_df (pd.DataFrame): PCA-transformed data
        
    Returns:
        int: Optimal number of clusters
    """
    n_samples = pca_df.shape[0]
    
    # Calculate number of clusters needed for exactly 50 stores per cluster
    n_clusters = n_samples // 50
    if n_samples % 50 != 0:
        n_clusters += 1
    
    log_progress(f"Calculated number of clusters needed for 50 stores per cluster: {n_clusters}")
    log_progress(f"This will create clusters for {CURRENT_CONFIG['description']}")
    
    return n_clusters

def perform_initial_clustering(pca_df: pd.DataFrame, n_clusters: int) -> Tuple[np.ndarray, KMeans]:
    """
    Perform initial KMeans clustering.
    
    Args:
        pca_df (pd.DataFrame): PCA-transformed data
        n_clusters (int): Number of clusters
        
    Returns:
        Tuple containing cluster labels and KMeans object
    """
    log_progress(f"Performing initial {MATRIX_TYPE} clustering with {n_clusters} clusters...")
    
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=RANDOM_STATE,
        n_init=N_INIT,
        max_iter=MAX_ITER
    )
    
    start_time = time.time()
    
    # For large datasets, show progress
    if pca_df.shape[0] > 1000:
        log_progress("Processing large dataset - clustering in progress...")
    
    cluster_labels = kmeans.fit_predict(pca_df)
    end_time = time.time()
    
    log_progress(f"Initial {MATRIX_TYPE} clustering completed in {end_time - start_time:.2f} seconds")
    
    # Log initial cluster sizes
    unique_labels, counts = np.unique(cluster_labels, return_counts=True)
    log_progress(f"Initial cluster sizes: min={counts.min()}, max={counts.max()}, mean={counts.mean():.1f}")
    
    return cluster_labels, kmeans

def balance_clusters_with_flexibility(pca_df: pd.DataFrame, initial_labels: np.ndarray) -> np.ndarray:
    """
    Balance clusters to have exactly 50 stores per cluster.
    This version enforces strict equal-sized clusters.
    
    Args:
        pca_df (pd.DataFrame): PCA-transformed data
        initial_labels (np.ndarray): Initial cluster labels
        
    Returns:
        np.ndarray: Balanced cluster labels
    """
    log_progress(f"Balancing {MATRIX_TYPE} clusters to have exactly 50 stores per cluster...")
    
    features = pca_df.values
    labels = initial_labels.copy()
    n_clusters = np.max(labels) + 1
    n_samples = features.shape[0]
    
    # Calculate initial cluster centers
    centers = np.zeros((n_clusters, features.shape[1]))
    for i in range(n_clusters):
        mask = labels == i
        if np.sum(mask) > 0:
            centers[i] = np.mean(features[mask], axis=0)
    
    # Calculate distances to all cluster centers for each sample
    log_progress("Calculating distances for cluster balancing...")
    distances = np.zeros((n_samples, n_clusters))
    for i in range(n_clusters):
        distances[:, i] = np.sum((features - centers[i]) ** 2, axis=1)
    
    # Get initial cluster sizes
    counts = np.array([np.sum(labels == i) for i in range(n_clusters)])
    log_progress(f"Initial cluster sizes: {counts}")
    
    # First, handle oversized clusters
    iteration = 0
    while iteration < MAX_BALANCE_ITERATIONS:
        iteration += 1
        if iteration % 10 == 0:
            log_progress(f"Balance iteration {iteration}...")
        
        # Update cluster counts
        counts = np.array([np.sum(labels == i) for i in range(n_clusters)])
        
        # Check if constraints are already satisfied
        oversized = np.where(counts > MAX_CLUSTER_SIZE)[0]
        undersized = np.where(counts < MIN_CLUSTER_SIZE)[0]
        
        if len(oversized) == 0 and len(undersized) == 0:
            log_progress(f"All constraints satisfied after {iteration} iterations")
            break
        
        # Handle oversized clusters
        for cluster_id in oversized:
            # Find samples in this cluster
            cluster_samples = np.where(labels == cluster_id)[0]
            
            # Calculate distances to this cluster center
            dist_to_center = distances[cluster_samples, cluster_id]
            
            # Sort samples by distance (farthest first)
            sorted_indices = np.argsort(-dist_to_center)
            
            # Number of samples to move
            excess = counts[cluster_id] - MAX_CLUSTER_SIZE
            n_to_move = excess
            
            # Move the farthest points to other clusters
            for idx in sorted_indices[:n_to_move]:
                sample_idx = cluster_samples[idx]
                
                # Find the next best cluster 
                dist_to_centers = distances[sample_idx]
                
                # Create a mask for clusters that are full
                full_clusters = counts >= MAX_CLUSTER_SIZE
                full_clusters[cluster_id] = True  # Exclude current cluster
                
                # Set distances to full clusters to infinity
                dist_to_centers = dist_to_centers.copy()
                dist_to_centers[full_clusters] = float('inf')
                
                # Get the closest non-full cluster
                new_cluster = np.argmin(dist_to_centers)
                
                # Move the sample
                labels[sample_idx] = new_cluster
                counts[cluster_id] -= 1
                counts[new_cluster] += 1
                
                # Break if we've moved enough samples
                if counts[cluster_id] <= MAX_CLUSTER_SIZE:
                    break
    
    # Final cluster sizes
    final_counts = np.array([np.sum(labels == i) for i in range(n_clusters)])
    log_progress(f"Final {MATRIX_TYPE} cluster sizes: {final_counts}")
    log_progress(f"Cluster size range: {final_counts.min()}-{final_counts.max()}")
    
    return labels

def analyze_clusters(original_df: pd.DataFrame, cluster_labels: np.ndarray, pca_df: pd.DataFrame, pca: PCA) -> pd.DataFrame:
    """
    Analyze clusters and create cluster profiles.
    
    Args:
        original_df (pd.DataFrame): Original matrix data
        cluster_labels (np.ndarray): Cluster labels
        pca_df (pd.DataFrame): PCA-transformed data
        pca (PCA): PCA object
        
    Returns:
        pd.DataFrame: Cluster analysis results
    """
    log_progress(f"Analyzing {MATRIX_TYPE} clusters...")
    
    n_clusters = np.max(cluster_labels) + 1
    cluster_profiles = []
    
    for cluster_id in tqdm(range(n_clusters), desc="Analyzing clusters"):
        # Get stores in this cluster
        cluster_mask = cluster_labels == cluster_id
        cluster_stores = original_df.index[cluster_mask]
        cluster_data = original_df.iloc[cluster_mask]
        
        # Calculate cluster statistics
        cluster_size = len(cluster_stores)
        
        # Calculate mean values for each feature (subcategory/SPU/category)
        mean_values = cluster_data.mean()
        
        # Get top features for this cluster
        top_features = mean_values.nlargest(10)
        
        # Create cluster profile
        profile = {
            'Cluster': cluster_id,
            'Size': cluster_size,
            'Stores': ','.join(map(str, cluster_stores[:10])),  # First 10 stores
        }
        
        # Add top features based on matrix type
        if MATRIX_TYPE == "subcategory":
            profile['Top_Subcategories'] = ','.join([f"{cat}({val:.1f})" for cat, val in top_features.items()])
        elif MATRIX_TYPE == "spu":
            profile['Top_SPUs'] = ','.join([f"{spu}({val:.1f})" for spu, val in top_features.items()])
        else:  # category_agg
            profile['Top_Categories'] = ','.join([f"{cat}({val:.1f})" for cat, val in top_features.items()])
        
        # Add statistical measures
        profile['Total_Sales'] = cluster_data.sum().sum()
        profile['Avg_Sales_Per_Store'] = profile['Total_Sales'] / cluster_size
        profile['Sales_Std'] = cluster_data.sum(axis=1).std()
        
        cluster_profiles.append(profile)
    
    cluster_df = pd.DataFrame(cluster_profiles)
    
    # Save detailed cluster profiles
    profile_file = f"{OUTPUT_DIR}/cluster_profiles_{MATRIX_TYPE}.csv"
    cluster_df.to_csv(profile_file, index=False)
    log_progress(f"Saved {MATRIX_TYPE} cluster profiles to {profile_file}")
    
    # Create store-cluster mapping
    store_cluster_df = pd.DataFrame({
        'str_code': original_df.index,
        'Cluster': cluster_labels
    })
    
    return store_cluster_df

def visualize_clusters(pca_df: pd.DataFrame, cluster_labels: np.ndarray, cluster_df: pd.DataFrame, n_clusters: int) -> None:
    """
    Create cluster visualizations.
    
    Args:
        pca_df (pd.DataFrame): PCA-transformed data
        cluster_labels (np.ndarray): Cluster labels
        cluster_df (pd.DataFrame): Cluster analysis results
        n_clusters (int): Number of clusters
    """
    log_progress(f"Creating {MATRIX_TYPE} cluster visualizations...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(f'{CURRENT_CONFIG["description"]} - Cluster Analysis', fontsize=16)
    
    # 1. PCA scatter plot (PC1 vs PC2)
    ax1 = axes[0, 0]
    scatter = ax1.scatter(pca_df.iloc[:, 0], pca_df.iloc[:, 1], c=cluster_labels, cmap='tab20', alpha=0.7)
    ax1.set_xlabel('First Principal Component')
    ax1.set_ylabel('Second Principal Component')
    ax1.set_title('Clusters in PCA Space (PC1 vs PC2)')
    plt.colorbar(scatter, ax=ax1)
    
    # 2. PCA scatter plot (PC1 vs PC3) if available
    ax2 = axes[0, 1]
    if pca_df.shape[1] >= 3:
        scatter2 = ax2.scatter(pca_df.iloc[:, 0], pca_df.iloc[:, 2], c=cluster_labels, cmap='tab20', alpha=0.7)
        ax2.set_xlabel('First Principal Component')
        ax2.set_ylabel('Third Principal Component')
        ax2.set_title('Clusters in PCA Space (PC1 vs PC3)')
        plt.colorbar(scatter2, ax=ax2)
    else:
        ax2.text(0.5, 0.5, 'PC3 not available', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('PC3 Not Available')
    
    # 3. Cluster size distribution
    ax3 = axes[1, 0]
    cluster_sizes = [np.sum(cluster_labels == i) for i in range(n_clusters)]
    ax3.bar(range(n_clusters), cluster_sizes)
    ax3.set_xlabel('Cluster ID')
    ax3.set_ylabel('Number of Stores')
    ax3.set_title('Cluster Size Distribution')
    ax3.axhline(y=50, color='r', linestyle='--', label='Target Size (50)')
    ax3.legend()
    
    # 4. Cluster statistics
    ax4 = axes[1, 1]
    if 'Total_Sales' in cluster_df.columns:
        ax4.bar(cluster_df['Cluster'], cluster_df['Total_Sales'])
        ax4.set_xlabel('Cluster ID')
        ax4.set_ylabel('Total Sales')
        ax4.set_title('Total Sales by Cluster')
    else:
        ax4.text(0.5, 0.5, 'Sales data not available', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Sales Data Not Available')
    
    plt.tight_layout()
    
    # Save the plot
    plot_file = f"{OUTPUT_DIR}/cluster_visualization_{MATRIX_TYPE}.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    log_progress(f"Saved {MATRIX_TYPE} cluster visualization to {plot_file}")
    plt.close()

def calculate_clustering_metrics(pca_df: pd.DataFrame, cluster_labels: np.ndarray) -> Dict[str, float]:
    """
    Calculate clustering quality metrics.
    
    Args:
        pca_df (pd.DataFrame): PCA-transformed data
        cluster_labels (np.ndarray): Cluster labels
        
    Returns:
        Dict[str, float]: Clustering metrics
    """
    log_progress(f"Calculating {MATRIX_TYPE} clustering metrics...")
    
    try:
        # Silhouette Score
        silhouette_avg = silhouette_score(pca_df, cluster_labels)
        
        # Calinski-Harabasz Score
        calinski_score = calinski_harabasz_score(pca_df, cluster_labels)
        
        # Davies-Bouldin Score
        davies_bouldin = davies_bouldin_score(pca_df, cluster_labels)
        
        metrics = {
            'silhouette_score': silhouette_avg,
            'calinski_harabasz_score': calinski_score,
            'davies_bouldin_score': davies_bouldin,
            'n_clusters': len(np.unique(cluster_labels)),
            'n_samples': len(cluster_labels)
        }
        
        log_progress(f"{MATRIX_TYPE.upper()} Clustering Metrics:")
        log_progress(f"  • Silhouette Score: {silhouette_avg:.3f}")
        log_progress(f"  • Calinski-Harabasz Score: {calinski_score:.1f}")
        log_progress(f"  • Davies-Bouldin Score: {davies_bouldin:.3f}")
        
        return metrics
        
    except Exception as e:
        log_progress(f"Error calculating metrics: {str(e)}")
        return {'error': str(e)}

def calculate_per_cluster_metrics(pca_df: pd.DataFrame, cluster_labels: np.ndarray) -> pd.DataFrame:
    """
    Calculate clustering metrics for each individual cluster.
    
    Args:
        pca_df (pd.DataFrame): The PCA-transformed data
        cluster_labels (np.ndarray): The cluster labels for each data point
        
    Returns:
        pd.DataFrame: DataFrame containing metrics for each cluster
    """
    log_progress(f"Calculating per-cluster metrics for {MATRIX_TYPE} clustering...")
    
    # Calculate silhouette scores for each sample
    silhouette_scores = silhouette_samples(pca_df, cluster_labels)
    
    # Calculate cluster centers
    n_clusters = np.max(cluster_labels) + 1
    centers = np.zeros((n_clusters, pca_df.shape[1]))
    for i in range(n_clusters):
        mask = cluster_labels == i
        if np.sum(mask) > 0:
            centers[i] = np.mean(pca_df[mask], axis=0)
    
    # Calculate metrics for each cluster
    cluster_metrics = []
    for i in range(n_clusters):
        # Get points in this cluster
        mask = cluster_labels == i
        cluster_points = pca_df[mask]
        cluster_silhouettes = silhouette_scores[mask]
        
        # Calculate average distance to cluster center
        distances_to_center = np.sqrt(np.sum((cluster_points - centers[i])**2, axis=1))
        avg_distance = np.mean(distances_to_center)
        std_distance = np.std(distances_to_center)
        
        # Calculate average silhouette score for this cluster
        avg_silhouette = np.mean(cluster_silhouettes)
        
        # Calculate minimum distance to other cluster centers
        other_centers = np.delete(centers, i, axis=0)
        min_dist_to_others = np.min(np.sqrt(np.sum((centers[i] - other_centers)**2, axis=1)))
        
        # Calculate cluster density (points per unit volume)
        # Using the average distance as a proxy for volume
        density = len(cluster_points) / (avg_distance ** pca_df.shape[1])
        
        cluster_metrics.append({
            'Cluster': i,
            'Size': len(cluster_points),
            'Avg_Silhouette': avg_silhouette,
            'Avg_Distance_to_Center': avg_distance,
            'Std_Distance_to_Center': std_distance,
            'Min_Distance_to_Other_Centers': min_dist_to_others,
            'Density': density,
            'Cohesion_Score': avg_silhouette / (avg_distance + 1e-10),  # Higher is better
            'Separation_Score': min_dist_to_others / (avg_distance + 1e-10)  # Higher is better
        })
    
    # Convert to DataFrame
    metrics_df = pd.DataFrame(cluster_metrics)
    
    # Sort by overall quality score (combination of cohesion and separation)
    metrics_df['Overall_Quality'] = (metrics_df['Cohesion_Score'] + metrics_df['Separation_Score']) / 2
    metrics_df = metrics_df.sort_values('Overall_Quality', ascending=False)
    
    # Save the metrics
    metrics_file = f"{OUTPUT_DIR}/per_cluster_metrics_{MATRIX_TYPE}.csv"
    metrics_df.to_csv(metrics_file, index=False)
    log_progress(f"Saved per-cluster metrics to {metrics_file}")
    
    return metrics_df

def create_documentation(cluster_df: pd.DataFrame, n_clusters: int, 
                        cluster_counts: np.ndarray, metrics: Dict[str, float]) -> None:
    """
    Create comprehensive documentation for the clustering results.
    
    Args:
        cluster_df (pd.DataFrame): Cluster analysis results
        n_clusters (int): Number of clusters
        cluster_counts (np.ndarray): Cluster sizes
        metrics (Dict[str, float]): Clustering metrics
    """
    log_progress(f"Creating {MATRIX_TYPE} clustering documentation...")
    
    doc_content = f"""# {CURRENT_CONFIG['description']} Results

## Overview
This document contains the results of {MATRIX_TYPE} clustering analysis performed on {cluster_df.shape[0]} stores.

## Configuration
- **Matrix Type**: {MATRIX_TYPE}
- **Input Matrix**: {INPUT_MATRIX}
- **Original Matrix**: {ORIGINAL_MATRIX}
- **Feature Type**: {CURRENT_CONFIG['feature_name']}
- **PCA Components**: {PCA_COMPONENTS}
- **Target Cluster Size**: {MAX_CLUSTER_SIZE} stores per cluster

## Clustering Results
- **Number of Clusters**: {n_clusters}
- **Total Stores**: {cluster_df.shape[0]}
- **Cluster Size Range**: {cluster_counts.min()} - {cluster_counts.max()} stores
- **Average Cluster Size**: {cluster_counts.mean():.1f} stores

## Quality Metrics
"""
    
    if 'error' not in metrics:
        doc_content += f"""- **Silhouette Score**: {metrics.get('silhouette_score', 'N/A'):.3f}
- **Calinski-Harabasz Score**: {metrics.get('calinski_harabasz_score', 'N/A'):.1f}
- **Davies-Bouldin Score**: {metrics.get('davies_bouldin_score', 'N/A'):.3f}
"""
    else:
        doc_content += f"- **Error**: {metrics['error']}\n"
    
    doc_content += f"""
## Cluster Size Distribution
{cluster_counts.tolist()}

## Files Generated
- `clustering_results_{MATRIX_TYPE}.csv`: Store-to-cluster assignments
- `cluster_profiles_{MATRIX_TYPE}.csv`: Detailed cluster profiles
- `per_cluster_metrics_{MATRIX_TYPE}.csv`: Quality metrics for each cluster
- `cluster_visualization_{MATRIX_TYPE}.png`: Cluster visualization plots

## Interpretation
"""
    
    if MATRIX_TYPE == "subcategory":
        doc_content += """
This analysis clusters stores based on their subcategory sales patterns. Stores in the same cluster
have similar preferences for product subcategories, which can inform:
- Product assortment strategies
- Inventory allocation
- Marketing campaigns
"""
    elif MATRIX_TYPE == "spu":
        doc_content += """
This analysis clusters stores based on their SPU (Stock Keeping Unit) sales patterns. This provides
the most granular view of store similarities and can inform:
- Precise product allocation
- SKU-level inventory management
- Detailed customer preference analysis
"""
    else:  # category_agg
        doc_content += """
This analysis clusters stores based on their category-level sales patterns (aggregated from SPUs).
This provides a balanced view between granularity and interpretability, useful for:
- High-level product strategy
- Category management
- Store format decisions
"""
    
    doc_content += f"""
## Usage
The main output file `clustering_results_{MATRIX_TYPE}.csv` contains store codes and their cluster assignments.
This can be used in downstream analysis steps for business rule validation and strategy development.

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Matrix Type: {MATRIX_TYPE}
"""
    
    # Save the documentation
    doc_file = f"{OUTPUT_DIR}/{MATRIX_TYPE}_clustering_documentation.md"
    with open(doc_file, "w") as f:
        f.write(doc_content)
    
    log_progress(f"Saved {MATRIX_TYPE} clustering documentation to {doc_file}")

def perform_temperature_aware_clustering(normalized_df: pd.DataFrame, original_df: pd.DataFrame, 
                                        temp_df: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame, pd.DataFrame, PCA]:
    """
    Perform clustering within temperature bands.
    
    Args:
        normalized_df (pd.DataFrame): Normalized matrix data
        original_df (pd.DataFrame): Original matrix data
        temp_df (pd.DataFrame): Temperature data
        
    Returns:
        Tuple containing cluster labels, cluster analysis, PCA data, and PCA object
    """
    log_progress(f"Performing temperature-aware {MATRIX_TYPE} clustering...")
    
    # Get unique temperature bands
    temperature_bands = temp_df['temperature_band'].unique()
    log_progress(f"Found {len(temperature_bands)} temperature bands")
    
    all_labels = []
    all_store_indices = []
    global_cluster_id = 0
    combined_pca_data = []
    
    for band in sorted(temperature_bands):
        log_progress(f"\nProcessing temperature band: {band}")
        
        # Get stores in this temperature band
        band_stores = temp_df[temp_df['temperature_band'] == band].index
        band_size = len(band_stores)
        log_progress(f"  • {band_size} stores in this band")
        
        if band_size < MIN_CLUSTER_SIZE:
            log_progress(f"  • Skipping band with < {MIN_CLUSTER_SIZE} stores")
            continue
        
        # Get data for this band
        band_normalized = normalized_df.loc[band_stores]
        
        # Apply PCA to this band
        n_components = min(PCA_COMPONENTS, band_size, band_normalized.shape[1])
        pca = PCA(n_components=n_components, random_state=RANDOM_STATE)
        pca_result = pca.fit_transform(band_normalized)
        
        band_pca_df = pd.DataFrame(
            pca_result,
            index=band_stores,
            columns=[f'PC{i+1}' for i in range(n_components)]
        )
        
        # Calculate optimal clusters for this band
        n_clusters = max(1, band_size // MAX_CLUSTER_SIZE)
        if band_size % MAX_CLUSTER_SIZE > MIN_CLUSTER_SIZE // 2:
            n_clusters += 1
        
        log_progress(f"  • Creating {n_clusters} clusters for this band")
        
        # Perform clustering within this band
        if n_clusters == 1:
            cluster_labels = np.zeros(band_size, dtype=int)
        else:
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=RANDOM_STATE,
                n_init=N_INIT,
                max_iter=MAX_ITER
            )
            cluster_labels = kmeans.fit_predict(band_pca_df)
        
        # Balance clusters within this band
        balanced_labels = balance_clusters_with_flexibility(band_pca_df, cluster_labels)
        
        # Adjust labels to global cluster IDs
        adjusted_labels = balanced_labels + global_cluster_id
        global_cluster_id += len(np.unique(balanced_labels))
        
        # Store results
        all_labels.extend(adjusted_labels)
        all_store_indices.extend(band_stores)
        combined_pca_data.append(band_pca_df)
        
        # Log cluster sizes for this band
        unique_labels, counts = np.unique(balanced_labels, return_counts=True)
        for label, count in zip(unique_labels, counts):
            log_progress(f"  • Band cluster {label}: {count} stores")
    
    # Combine all results
    final_labels = np.array(all_labels)
    final_store_indices = all_store_indices
    
    # Create combined PCA dataframe (this is approximate since different bands have different PCA)
    if combined_pca_data:
        # Use the PCA from the largest band as representative
        largest_band_idx = max(range(len(combined_pca_data)), key=lambda i: len(combined_pca_data[i]))
        representative_pca = combined_pca_data[largest_band_idx]
        
        # Create a combined PCA dataframe with consistent columns
        max_components = max(df.shape[1] for df in combined_pca_data)
        combined_pca_list = []
        
        for df in combined_pca_data:
            # Pad with zeros if needed
            if df.shape[1] < max_components:
                padding = pd.DataFrame(
                    np.zeros((len(df), max_components - df.shape[1])),
                    index=df.index,
                    columns=[f'PC{i+1}' for i in range(df.shape[1], max_components)]
                )
                df = pd.concat([df, padding], axis=1)
            combined_pca_list.append(df)
        
        combined_pca_df = pd.concat(combined_pca_list)
        
        # Create dummy PCA object for consistency
        pca = PCA(n_components=max_components, random_state=RANDOM_STATE)
    else:
        # Fallback to regular clustering if no temperature bands worked
        log_progress("No valid temperature bands found, falling back to regular clustering")
        pca_df, pca = apply_pca(normalized_df)
        return perform_initial_clustering(pca_df, determine_optimal_initial_clusters(pca_df))[0], \
               analyze_clusters(original_df, final_labels, pca_df, pca), pca_df, pca
    
    # Analyze the combined clusters
    cluster_df = analyze_clusters(original_df.loc[final_store_indices], final_labels, combined_pca_df, pca)
    
    log_progress(f"Temperature-aware {MATRIX_TYPE} clustering created {len(np.unique(final_labels))} clusters across {len(temperature_bands)} temperature bands")
    
    return final_labels, cluster_df, combined_pca_df, pca

def main():
    """Main function to perform clustering analysis."""
    start_time = datetime.now()
    log_progress(f"Starting Step 6: {CURRENT_CONFIG['description']}...")
    
    try:
        # Load data (including optional temperature data)
        normalized_df, original_df, temp_df = load_data()
        
        # Check if we should use temperature-based clustering
        if temp_df is not None and ENABLE_TEMPERATURE_CONSTRAINTS:
            log_progress(f"Using temperature-aware {MATRIX_TYPE} clustering within 5°C bands")
            
            # Filter to stores with both product and temperature data
            normalized_df.index = normalized_df.index.astype(str)
            original_df.index = original_df.index.astype(str)
            common_stores = normalized_df.index.intersection(temp_df.index)
            
            log_progress(f"Found {len(common_stores)} stores with both product and temperature data")
            
            normalized_df = normalized_df.loc[common_stores]
            original_df = original_df.loc[common_stores]
            temp_df = temp_df.loc[common_stores]
            
            # Perform temperature-aware clustering
            balanced_labels, cluster_df, pca_df, pca = perform_temperature_aware_clustering(
                normalized_df, original_df, temp_df
            )
        else:
            log_progress(f"Using standard {MATRIX_TYPE} clustering without temperature constraints")
            
            # Apply PCA
            pca_df, pca = apply_pca(normalized_df)
            
            # Determine optimal initial clusters
            optimal_clusters = determine_optimal_initial_clusters(pca_df)
            
            # Perform initial clustering
            initial_labels, kmeans = perform_initial_clustering(pca_df, optimal_clusters)
            
            # Balance clusters with flexibility
            balanced_labels = balance_clusters_with_flexibility(pca_df, initial_labels)
            
            # Analyze clusters
            cluster_df = analyze_clusters(original_df, balanced_labels, pca_df, pca)
        
        # Get final number of clusters and their sizes
        n_clusters = np.max(balanced_labels) + 1
        cluster_counts = np.array([np.sum(balanced_labels == i) for i in range(n_clusters)])
        
        # Calculate overall clustering metrics
        metrics = calculate_clustering_metrics(pca_df, balanced_labels)
        
        # Calculate per-cluster metrics
        per_cluster_metrics = calculate_per_cluster_metrics(pca_df, balanced_labels)
        
        # Visualize clusters
        visualize_clusters(pca_df, balanced_labels, cluster_df, n_clusters)
        
        # Create documentation
        create_documentation(cluster_df, n_clusters, cluster_counts, metrics)
        
        # Save clustering results
        results_file = f"{OUTPUT_DIR}/clustering_results_{MATRIX_TYPE}.csv"
        cluster_df.to_csv(results_file, index=False)
        log_progress(f"Saved {MATRIX_TYPE} clustering results to {results_file}")

        # Also save as the standard filename for backward compatibility (always)
        cluster_df.to_csv(f"{OUTPUT_DIR}/clustering_results.csv", index=False)
        log_progress(f"Saved backward-compatible clustering results to {OUTPUT_DIR}/clustering_results.csv")
        
        # Summary
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress(f"\n=== {MATRIX_TYPE.upper()} CLUSTERING COMPLETED SUCCESSFULLY ===")
        log_progress(f"Execution time: {execution_time:.1f} seconds")
        log_progress(f"Created {n_clusters} clusters from {len(balanced_labels)} stores")
        log_progress(f"Matrix type: {MATRIX_TYPE}")
        log_progress(f"Feature count: {original_df.shape[1]} {CURRENT_CONFIG['feature_name']}s")
        
        log_progress(f"\nNext step: Run python src/step7_missing_category_rule.py for business rule analysis")
        
    except Exception as e:
        log_progress(f"Error in main function: {str(e)}")
        raise

if __name__ == "__main__":
    main() 