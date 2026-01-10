#!/usr/bin/env python3
"""
Fashion/Basic Product Analysis Module

This module provides advanced analysis of fashion vs basic product mix patterns
across stores and clusters, building on the enhanced clustering and store classification.

Author: Analytics Team
Date: 2025-06-15
"""

import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PRODUCT_CATEGORIES = ['BASIC', 'FASHION']
TREND_STATES = ['RISING', 'STABLE', 'DECLINING']
MIN_SALES_THRESHOLD = 10  # Minimum sales for reliable trend analysis


class FashionBasicAnalyzer:
    """
    Analyzes fashion/basic product mix patterns leveraging enhanced clustering.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the FashionBasicAnalyzer.
        
        Args:
            output_dir: Directory for output files and visualizations
        """
        self.output_dir = output_dir or os.path.join('output', 'fashion_basic_analysis')
        self.viz_dir = os.path.join(self.output_dir, 'visualizations')
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.viz_dir, exist_ok=True)
        
        logger.info(f"Initialized FashionBasicAnalyzer with output directory: {self.output_dir}")
    
    def load_data(self, 
                products_path: str, 
                store_classification_path: str, 
                clusters_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load product, store classification, and cluster data.
        
        Args:
            products_path: Path to products data (JSON)
            store_classification_path: Path to store classification data (CSV)
            clusters_path: Path to cluster assignments (CSV)
            
        Returns:
            Tuple of (products_df, classification_df, clusters_df)
        """
        logger.info("Loading product, classification, and cluster data")
        
        # Load products data
        try:
            with open(products_path, 'r') as f:
                products_data = json.load(f)
            
            # Convert to DataFrame - handle both dict and list formats
            products_records = []
            
            # Check if products_data is a list (flat structure) or dict (nested by store)
            if isinstance(products_data, list):
                # Direct list of product records
                products_records = products_data
                logger.info(f"Loaded products data in flat list format")
            elif isinstance(products_data, dict):
                # Dictionary with store_id keys
                for store_id, products in products_data.items():
                    for product in products:
                        product['store_id'] = store_id
                        products_records.append(product)
                logger.info(f"Loaded products data in store-keyed dict format")
            else:
                raise ValueError(f"Unexpected products data format: {type(products_data)}")
            
            products_df = pd.DataFrame(products_records)
            logger.info(f"Loaded {len(products_df)} products for {products_df['store_id'].nunique()} stores")
        except Exception as e:
            logger.error(f"Error loading products data: {str(e)}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Load store classification data
        try:
            classification_df = pd.read_csv(store_classification_path)
            logger.info(f"Loaded classification data for {len(classification_df)} stores")
        except Exception as e:
            logger.error(f"Error loading store classification data: {str(e)}")
            return products_df, pd.DataFrame(), pd.DataFrame()
        
        # Load cluster data
        try:
            clusters_df = pd.read_csv(clusters_path)
            logger.info(f"Loaded cluster data for {len(clusters_df)} stores")
        except Exception as e:
            logger.error(f"Error loading cluster data: {str(e)}")
            return products_df, classification_df, pd.DataFrame()
        
        return products_df, classification_df, clusters_df
    
    def calculate_product_mix_metrics(self, 
                                    products_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate key metrics about product mix by store.
        
        Args:
            products_df: DataFrame with product data
            
        Returns:
            DataFrame with product mix metrics by store
        """
        if products_df.empty or 'product_type' not in products_df.columns:
            logger.error("Cannot calculate metrics: missing data or product_type column")
            return pd.DataFrame()
        
        logger.info("Calculating product mix metrics by store")
        
        # Group by store and product_type
        store_products = products_df.groupby(['store_id', 'product_type']).agg(
            product_count=('product_id', 'count'),
            avg_sales=('sales', 'mean'),
            total_sales=('sales', 'sum'),
            avg_price=('price', 'mean')
        ).reset_index()
        
        # Calculate store totals
        store_totals = products_df.groupby('store_id').agg(
            total_products=('product_id', 'count'),
            total_sales_all=('sales', 'sum')
        ).reset_index()
        
        # Merge with store products
        merged_df = pd.merge(store_products, store_totals, on='store_id', how='left')
        
        # Calculate percentages
        merged_df['product_percentage'] = (merged_df['product_count'] / merged_df['total_products']) * 100
        merged_df['sales_percentage'] = (merged_df['total_sales'] / merged_df['total_sales_all']) * 100
        
        # Pivot to create wide format (one row per store)
        pivot_df = merged_df.pivot(index='store_id', 
                                  columns='product_type', 
                                  values=['product_count', 'product_percentage', 
                                          'total_sales', 'sales_percentage', 'avg_price'])
        
        # Flatten column hierarchy
        pivot_df.columns = ['_'.join(col).strip() for col in pivot_df.columns.values]
        
        # Reset index
        pivot_df = pivot_df.reset_index()
        
        # Add derived metrics
        for category in PRODUCT_CATEGORIES:
            product_count_col = f'product_count_{category}'
            total_sales_col = f'total_sales_{category}'
            
            # Fill NaN values with 0 for stores without certain product types
            pivot_df[product_count_col] = pivot_df[product_count_col].fillna(0)
            pivot_df[total_sales_col] = pivot_df[total_sales_col].fillna(0)
            pivot_df[f'product_percentage_{category}'] = pivot_df[f'product_percentage_{category}'].fillna(0)
            pivot_df[f'sales_percentage_{category}'] = pivot_df[f'sales_percentage_{category}'].fillna(0)
        
        # Add ratio metrics
        if all(f'product_count_{cat}' in pivot_df.columns for cat in ['BASIC', 'FASHION']):
            # Add small epsilon to avoid division by zero
            epsilon = 1e-10
            
            # Calculate ratios
            pivot_df['fashion_basic_count_ratio'] = (
                pivot_df['product_count_FASHION'] / (pivot_df['product_count_BASIC'] + epsilon)
            )
            pivot_df['fashion_basic_sales_ratio'] = (
                pivot_df['total_sales_FASHION'] / (pivot_df['total_sales_BASIC'] + epsilon)
            )
        
        logger.info(f"Calculated product mix metrics for {len(pivot_df)} stores")
        return pivot_df
    
    def analyze_product_trends(self, 
                             products_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze fashion/basic product trends based on historical sales.
        
        Args:
            products_df: DataFrame with product data including historical sales
            
        Returns:
            DataFrame with trend analysis by product and store
        """
        if products_df.empty or 'historical_sales' not in products_df.columns:
            logger.error("Cannot analyze trends: missing historical sales data")
            return pd.DataFrame()
        
        logger.info("Analyzing product trends based on historical sales data")
        
        # Parse historical sales into a workable format
        trend_data = []
        
        for _, row in products_df.iterrows():
            try:
                # Check if historical sales is a string and parse if needed
                hist_sales = row['historical_sales']
                if isinstance(hist_sales, str):
                    hist_sales = json.loads(hist_sales)
                
                # Skip if no historical data or insufficient data points
                if not hist_sales or len(hist_sales) < 2:
                    continue
                
                # Prepare sales values in chronological order
                sales_values = []
                periods = []
                
                # Handle historical sales in different formats
                if isinstance(hist_sales, dict):
                    # Dictionary format: {period: sales_value, ...}
                    for period, sales in hist_sales.items():
                        sales_values.append(float(sales))
                        periods.append(period)
                    
                    # Ensure chronological order if periods are sortable
                    if all(period.isdigit() for period in periods):
                        sales_values = [x for _, x in sorted(zip([int(p) for p in periods], sales_values))]
                elif isinstance(hist_sales, list):
                    # List format: [sales_value1, sales_value2, ...] (already chronological)
                    sales_values = [float(sale) for sale in hist_sales]
                    periods = list(range(len(sales_values)))
                else:
                    # Unexpected format
                    raise ValueError(f"Unexpected historical_sales format: {type(hist_sales)}")
                    
                
                # Skip if sales are too low for reliable trend analysis
                if all(sale < MIN_SALES_THRESHOLD for sale in sales_values):
                    continue
                
                # Calculate trend metrics
                recent_sales = sales_values[-3:]  # Last 3 periods
                older_sales = sales_values[:-3] if len(sales_values) > 3 else [sales_values[0]]  # Earlier periods
                
                # Calculate average sales for recent and older periods
                recent_avg = sum(recent_sales) / len(recent_sales) if recent_sales else 0
                older_avg = sum(older_sales) / len(older_sales) if older_sales else 0
                
                # Calculate trend metrics
                if older_avg > 0:
                    trend_percentage = ((recent_avg - older_avg) / older_avg) * 100
                else:
                    trend_percentage = 0 if recent_avg == 0 else 100
                
                # Determine trend state
                if trend_percentage > 10:
                    trend_state = 'RISING'
                elif trend_percentage < -10:
                    trend_state = 'DECLINING'
                else:
                    trend_state = 'STABLE'
                
                # Add metrics to trend data
                trend_data.append({
                    'store_id': row['store_id'],
                    'product_id': row['product_id'],
                    'product_type': row.get('product_type', 'UNKNOWN'),
                    'category': row.get('category', 'UNKNOWN'),
                    'subcategory': row.get('subcategory', 'UNKNOWN'),
                    'current_sales': sales_values[-1] if sales_values else 0,
                    'avg_recent_sales': recent_avg,
                    'trend_percentage': trend_percentage,
                    'trend_state': trend_state,
                    'price': row.get('price', 0)
                })
                
            except Exception as e:
                logger.warning(f"Error processing historical sales for product {row.get('product_id', 'unknown')}: {str(e)}")
                continue
        
        # Convert to DataFrame
        if trend_data:
            trends_df = pd.DataFrame(trend_data)
            logger.info(f"Analyzed trends for {len(trends_df)} products across {trends_df['store_id'].nunique()} stores")
            return trends_df
        else:
            logger.warning("No trend data could be extracted from the historical sales")
            return pd.DataFrame()
    
    def calculate_store_trend_metrics(self, 
                                   trends_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trend metrics aggregated by store.
        
        Args:
            trends_df: DataFrame with product trend analysis
            
        Returns:
            DataFrame with trend metrics by store
        """
        if trends_df.empty:
            logger.error("Cannot calculate store trend metrics: missing trend data")
            return pd.DataFrame()
        
        logger.info("Calculating store-level trend metrics")
        
        # Group by store and product_type
        store_trends = trends_df.groupby(['store_id', 'product_type', 'trend_state']).size().reset_index(name='count')
        
        # Pivot to create columns for each trend state by product type
        pivot_df = store_trends.pivot_table(
            index=['store_id', 'product_type'],
            columns='trend_state',
            values='count',
            fill_value=0
        ).reset_index()
        
        # Flatten column hierarchy
        pivot_df.columns = [col if not isinstance(col, tuple) else f"{col[1]}" for col in pivot_df.columns]
        
        # Calculate total products by type
        pivot_df['total'] = pivot_df[TREND_STATES].sum(axis=1)
        
        # Calculate percentages
        for state in TREND_STATES:
            pivot_df[f'{state}_pct'] = (pivot_df[state] / pivot_df['total']) * 100
        
        # Pivot again to separate by product_type
        final_pivot = pivot_df.pivot(
            index='store_id',
            columns='product_type',
            values=TREND_STATES + [f'{state}_pct' for state in TREND_STATES] + ['total']
        )
        
        # Flatten column hierarchy
        final_pivot.columns = ['_'.join(col).strip() for col in final_pivot.columns.values]
        
        # Reset index
        store_trend_metrics = final_pivot.reset_index()
        
        # Calculate trend health scores (higher means more positive trends)
        for product_type in PRODUCT_CATEGORIES:
            rising_col = f'RISING_{product_type}'
            stable_col = f'STABLE_{product_type}'
            declining_col = f'DECLINING_{product_type}'
            total_col = f'total_{product_type}'
            
            # Fill NaN values with 0
            for col in [rising_col, stable_col, declining_col, total_col]:
                if col in store_trend_metrics.columns:
                    store_trend_metrics[col] = store_trend_metrics[col].fillna(0)
            
            # Calculate health score only if all required columns exist
            if all(col in store_trend_metrics.columns for col in [rising_col, stable_col, declining_col, total_col]):
                store_trend_metrics[f'trend_health_{product_type}'] = (
                    (store_trend_metrics[rising_col] * 1 + 
                     store_trend_metrics[stable_col] * 0.5 - 
                     store_trend_metrics[declining_col] * 0.5) / 
                    store_trend_metrics[total_col].clip(lower=1)
                ) * 100
        
        logger.info(f"Calculated trend metrics for {len(store_trend_metrics)} stores")
        return store_trend_metrics
    
    def analyze_cluster_product_mix(self,
                                product_mix_df: pd.DataFrame,
                                clusters_df: pd.DataFrame) -> Dict[int, Dict]:
        """
        Analyze fashion/basic product mix patterns by cluster.
        
        Args:
            product_mix_df: DataFrame with product mix metrics by store
            clusters_df: DataFrame with cluster assignments
            
        Returns:
            Dictionary with cluster analysis results
        """
        if product_mix_df.empty or clusters_df.empty:
            logger.error("Cannot analyze clusters: missing data")
            return {}
        
        # Merge product mix with clusters
        merged_df = pd.merge(product_mix_df, clusters_df, on='store_id', how='inner')
        
        if merged_df.empty or 'cluster' not in merged_df.columns:
            logger.error("Cannot analyze clusters: missing cluster column after merge")
            return {}
        
        logger.info(f"Analyzing product mix patterns for {merged_df['cluster'].nunique()} clusters")
        
        # Group by cluster
        cluster_analysis = {}
        
        for cluster_id, group in merged_df.groupby('cluster'):
            # Skip if empty group
            if group.empty:
                continue
                
            # Calculate metrics
            analysis = {
                'cluster_id': int(cluster_id),
                'store_count': len(group),
                'metrics': {}
            }
            
            # Add product mix metrics
            for category in PRODUCT_CATEGORIES:
                # Product counts
                count_col = f'product_count_{category}'
                if count_col in group.columns:
                    analysis['metrics'][f'avg_{count_col}'] = group[count_col].mean()
                    analysis['metrics'][f'median_{count_col}'] = group[count_col].median()
                    analysis['metrics'][f'std_{count_col}'] = group[count_col].std()
                
                # Sales metrics
                sales_col = f'total_sales_{category}'
                if sales_col in group.columns:
                    analysis['metrics'][f'avg_{sales_col}'] = group[sales_col].mean()
                    analysis['metrics'][f'median_{sales_col}'] = group[sales_col].median()
                    analysis['metrics'][f'std_{sales_col}'] = group[sales_col].std()
                
                # Percentage metrics
                pct_col = f'product_percentage_{category}'
                if pct_col in group.columns:
                    analysis['metrics'][f'avg_{pct_col}'] = group[pct_col].mean()
                    analysis['metrics'][f'median_{pct_col}'] = group[pct_col].median()
                    
                sales_pct_col = f'sales_percentage_{category}'
                if sales_pct_col in group.columns:
                    analysis['metrics'][f'avg_{sales_pct_col}'] = group[sales_pct_col].mean()
                    analysis['metrics'][f'median_{sales_pct_col}'] = group[sales_pct_col].median()
            
            # Add ratio metrics
            ratio_col = 'fashion_basic_count_ratio'
            if ratio_col in group.columns:
                analysis['metrics'][f'avg_{ratio_col}'] = group[ratio_col].mean()
                analysis['metrics'][f'median_{ratio_col}'] = group[ratio_col].median()
                analysis['metrics'][f'min_{ratio_col}'] = group[ratio_col].min()
                analysis['metrics'][f'max_{ratio_col}'] = group[ratio_col].max()
            
            sales_ratio_col = 'fashion_basic_sales_ratio'
            if sales_ratio_col in group.columns:
                analysis['metrics'][f'avg_{sales_ratio_col}'] = group[sales_ratio_col].mean()
                analysis['metrics'][f'median_{sales_ratio_col}'] = group[sales_ratio_col].median()
                analysis['metrics'][f'min_{sales_ratio_col}'] = group[sales_ratio_col].min()
                analysis['metrics'][f'max_{sales_ratio_col}'] = group[sales_ratio_col].max()
            
            # Calculate dominant product type based on average percentages
            if all(f'product_percentage_{cat}' in group.columns for cat in PRODUCT_CATEGORIES):
                fashion_pct = group['product_percentage_FASHION'].mean()
                basic_pct = group['product_percentage_BASIC'].mean()
                
                if fashion_pct > 60:
                    dominant_type = 'FASHION'
                elif basic_pct > 60:
                    dominant_type = 'BASIC'
                else:
                    dominant_type = 'MIXED'
                    
                analysis['dominant_product_type'] = dominant_type
                analysis['fashion_percentage'] = fashion_pct
                analysis['basic_percentage'] = basic_pct
            
            # Store in cluster analysis
            cluster_analysis[int(cluster_id)] = analysis
        
        logger.info(f"Completed cluster product mix analysis for {len(cluster_analysis)} clusters")
        return cluster_analysis
    
    def analyze_cluster_trends(self,
                            store_trends_df: pd.DataFrame,
                            clusters_df: pd.DataFrame) -> Dict[int, Dict]:
        """
        Analyze fashion/basic product trends by cluster.
        
        Args:
            store_trends_df: DataFrame with trend metrics by store
            clusters_df: DataFrame with cluster assignments
            
        Returns:
            Dictionary with cluster trend analysis results
        """
        if store_trends_df.empty or clusters_df.empty:
            logger.error("Cannot analyze cluster trends: missing data")
            return {}
            
        # Merge trend data with clusters
        merged_df = pd.merge(store_trends_df, clusters_df, on='store_id', how='inner')
        
        if merged_df.empty or 'cluster' not in merged_df.columns:
            logger.error("Cannot analyze cluster trends: missing cluster column after merge")
            return {}
            
        logger.info(f"Analyzing trend patterns for {merged_df['cluster'].nunique()} clusters")
        
        # Group by cluster
        cluster_trends = {}
        
        for cluster_id, group in merged_df.groupby('cluster'):
            # Skip if empty group
            if group.empty:
                continue
                
            # Calculate metrics
            analysis = {
                'cluster_id': int(cluster_id),
                'store_count': len(group),
                'trend_metrics': {}
            }
            
            # Analyze trends by product type
            for product_type in PRODUCT_CATEGORIES:
                # Get trend counts if available
                trend_data = {}
                
                for trend_state in TREND_STATES:
                    col_name = f'{trend_state}_{product_type}'
                    if col_name in group.columns:
                        trend_data[trend_state] = {
                            'total': int(group[col_name].sum()),
                            'avg': group[col_name].mean(),
                            'median': group[col_name].median()
                        }
                        
                        # Get percentage if available
                        pct_col = f'{trend_state}_pct_{product_type}'
                        if pct_col in group.columns:
                            trend_data[trend_state]['avg_percentage'] = group[pct_col].mean()
                
                # Add trend health score if available
                health_col = f'trend_health_{product_type}'
                if health_col in group.columns:
                    trend_data['health_score'] = {
                        'avg': group[health_col].mean(),
                        'median': group[health_col].median(),
                        'min': group[health_col].min(),
                        'max': group[health_col].max()
                    }
                    
                    # Determine trend state based on health score
                    avg_health = group[health_col].mean()
                    if avg_health > 50:
                        trend_data['cluster_trend'] = 'STRONG_POSITIVE'
                    elif avg_health > 20:
                        trend_data['cluster_trend'] = 'POSITIVE'
                    elif avg_health < -50:
                        trend_data['cluster_trend'] = 'STRONG_NEGATIVE'
                    elif avg_health < -20:
                        trend_data['cluster_trend'] = 'NEGATIVE'
                    else:
                        trend_data['cluster_trend'] = 'NEUTRAL'
                
                # Store trend data for this product type
                if trend_data:
                    analysis['trend_metrics'][product_type] = trend_data
            
            # Store in cluster trends
            cluster_trends[int(cluster_id)] = analysis
        
        logger.info(f"Completed cluster trend analysis for {len(cluster_trends)} clusters")
        return cluster_trends
        
    def visualize_cluster_product_mix(self,
                                   cluster_analysis: Dict[int, Dict],
                                   output_file: Optional[str] = None) -> str:
        """
        Create visualization of fashion/basic product mix by cluster.
        
        Args:
            cluster_analysis: Dictionary with cluster analysis results
            output_file: Path to save visualization (optional)
            
        Returns:
            Path to saved visualization
        """
        if not cluster_analysis:
            logger.error("Cannot visualize: missing cluster analysis data")
            return ""
            
        # Create figure
        plt.figure(figsize=(14, 10))
        
        # Extract data for visualization
        cluster_ids = []
        fashion_pcts = []
        basic_pcts = []
        store_counts = []
        dominant_types = []
        
        for cluster_id, data in sorted(cluster_analysis.items()):
            if 'fashion_percentage' in data and 'basic_percentage' in data:
                cluster_ids.append(cluster_id)
                fashion_pcts.append(data['fashion_percentage'])
                basic_pcts.append(data['basic_percentage'])
                store_counts.append(data.get('store_count', 0))
                dominant_types.append(data.get('dominant_product_type', 'UNKNOWN'))
        
        if not cluster_ids:
            logger.error("Cannot visualize: no valid data in cluster analysis")
            return ""
            
        # Create DataFrame for easier plotting
        df = pd.DataFrame({
            'cluster': cluster_ids,
            'fashion_pct': fashion_pcts,
            'basic_pct': basic_pcts,
            'store_count': store_counts,
            'dominant_type': dominant_types
        })
        
        # Create barplot with percentage stacks
        ax = plt.subplot(111)
        bar_width = 0.7
        
        # Plot fashion percentage bars
        fashion_bars = ax.bar(
            df['cluster'], 
            df['fashion_pct'], 
            width=bar_width, 
            color='lightcoral', 
            label='FASHION'
        )
        
        # Plot basic percentage bars stacked on top
        basic_bars = ax.bar(
            df['cluster'], 
            df['basic_pct'], 
            width=bar_width, 
            bottom=df['fashion_pct'],
            color='lightblue', 
            label='BASIC'
        )
        
        # Add labels and title
        plt.xlabel('Cluster', fontsize=12)
        plt.ylabel('Product Mix Percentage', fontsize=12)
        plt.title('Fashion/Basic Product Mix by Cluster', fontsize=16)
        plt.xticks(cluster_ids, [str(cid) for cid in cluster_ids], fontsize=10)
        plt.yticks(fontsize=10)
        
        # Add grid
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add store count labels
        for i, count in enumerate(store_counts):
            plt.text(
                cluster_ids[i], 
                105, 
                f"{count} stores", 
                ha='center', 
                fontsize=9
            )
        
        # Add legend
        plt.legend(fontsize=10)
        
        # Add dominant type markers
        for i, dom_type in enumerate(dominant_types):
            if dom_type == 'FASHION':
                color = 'darkred'
                y_pos = 10
            elif dom_type == 'BASIC':
                color = 'darkblue'
                y_pos = 90
            else:  # MIXED
                color = 'purple'
                y_pos = 50
                
            plt.text(
                cluster_ids[i], 
                y_pos, 
                dom_type, 
                ha='center', 
                color=color,
                fontweight='bold',
                fontsize=8
            )
        
        # Set y-axis limit
        plt.ylim(0, 110)
        
        # Save visualization
        if output_file is None:
            os.makedirs(self.viz_dir, exist_ok=True)
            output_file = os.path.join(self.viz_dir, 'cluster_product_mix.png')
            
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        
        logger.info(f"Saved cluster product mix visualization to {output_file}")
        return output_file
    
    def run_analysis(self,
                   products_path: str,
                   store_classification_path: str,
                   clusters_path: str,
                   output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the complete fashion/basic product analysis pipeline.
        
        Args:
            products_path: Path to products data file (JSON)
            store_classification_path: Path to store classification data (CSV)
            clusters_path: Path to cluster assignments (CSV)
            output_dir: Directory for output files (optional)
            
        Returns:
            Dictionary with results and output files
        """
        # Set output directory if provided
        if output_dir:
            self.output_dir = output_dir
            self.viz_dir = os.path.join(output_dir, 'visualizations')
            os.makedirs(self.output_dir, exist_ok=True)
            os.makedirs(self.viz_dir, exist_ok=True)
        
        logger.info(f"Running fashion/basic product analysis pipeline")
        results = {}
        
        # Step 1: Load input data
        products_df, classification_df, clusters_df = self.load_data(
            products_path, store_classification_path, clusters_path
        )
        
        if products_df.empty or clusters_df.empty:
            logger.error(f"Failed to load required data for analysis")
            return {'error': f"Failed to load required data for analysis"}
        
        # Step 2: Calculate product mix metrics by store
        product_mix_df = self.calculate_product_mix_metrics(products_df)
        if not product_mix_df.empty:
            # Save product mix metrics
            mix_path = os.path.join(self.output_dir, 'product_mix_metrics.csv')
            product_mix_df.to_csv(mix_path, index=False)
            results['product_mix_path'] = mix_path
        else:
            logger.error(f"Failed to calculate product mix metrics")
            results['error_product_mix'] = "Failed to calculate product mix metrics"
        
        # Step 3: Analyze product trends
        trends_df = self.analyze_product_trends(products_df)
        store_trends_df = pd.DataFrame()  # Initialize to empty DataFrame to avoid UnboundLocalError
        
        if not trends_df.empty:
            # Save trend analysis
            trends_path = os.path.join(self.output_dir, 'product_trends.csv')
            trends_df.to_csv(trends_path, index=False)
            results['trends_path'] = trends_path
            
            # Calculate store-level trend metrics
            store_trends_df = self.calculate_store_trend_metrics(trends_df)
            if not store_trends_df.empty:
                # Save store trend metrics
                store_trends_path = os.path.join(self.output_dir, 'store_trend_metrics.csv')
                store_trends_df.to_csv(store_trends_path, index=False)
                results['store_trends_path'] = store_trends_path
        else:
            logger.error(f"Failed to analyze product trends")
            results['error_trends'] = "Failed to analyze product trends"
        
        # Step 4: Analyze cluster product mix
        if not product_mix_df.empty:
            cluster_mix = self.analyze_cluster_product_mix(product_mix_df, clusters_df)
            if cluster_mix:
                # Save cluster mix analysis
                mix_analysis_path = os.path.join(self.output_dir, 'cluster_product_mix.json')
                with open(mix_analysis_path, 'w') as f:
                    # Convert np.float64 to float for JSON serialization
                    serializable_mix = {}
                    for cluster_id, data in cluster_mix.items():
                        # Handle metrics dictionary separately
                        metrics = {}
                        if 'metrics' in data:
                            for k, v in data['metrics'].items():
                                metrics[k] = float(v) if isinstance(v, np.float64) else v
                        
                        # Convert main values
                        serializable_mix[str(cluster_id)] = {
                            k: float(v) if isinstance(v, np.float64) else v
                            for k, v in data.items()
                            if k != 'metrics'
                        }
                        
                        # Add metrics back
                        if metrics:
                            serializable_mix[str(cluster_id)]['metrics'] = metrics
                    
                    json.dump(serializable_mix, f, indent=2)
                results['cluster_mix_path'] = mix_analysis_path
                
                # Create visualization
                viz_path = self.visualize_cluster_product_mix(cluster_mix)
                if viz_path:
                    results['visualization_mix'] = viz_path
        
        # Step 5: Analyze cluster trends
        if not store_trends_df.empty:
            cluster_trends = self.analyze_cluster_trends(store_trends_df, clusters_df)
            if cluster_trends:
                # Save cluster trends analysis
                trends_analysis_path = os.path.join(self.output_dir, 'cluster_trends.json')
                with open(trends_analysis_path, 'w') as f:
                    # Handle complex nested structure for JSON serialization
                    serializable_trends = {}
                    for cluster_id, data in cluster_trends.items():
                        # Create a copy to modify
                        cluster_data = {}
                        
                        # Handle simple values
                        for k, v in data.items():
                            if k != 'trend_metrics':
                                cluster_data[k] = float(v) if isinstance(v, np.float64) else v
                        
                        # Handle trend_metrics separately (deeply nested)
                        if 'trend_metrics' in data:
                            trend_metrics = {}
                            for product_type, metrics in data['trend_metrics'].items():
                                product_metrics = {}
                                
                                for metric_name, metric_value in metrics.items():
                                    if isinstance(metric_value, dict):
                                        # Handle nested dictionary
                                        nested_metrics = {}
                                        for sub_k, sub_v in metric_value.items():
                                            nested_metrics[sub_k] = float(sub_v) if isinstance(sub_v, np.float64) else sub_v
                                        product_metrics[metric_name] = nested_metrics
                                    else:
                                        product_metrics[metric_name] = float(metric_value) if isinstance(metric_value, np.float64) else metric_value
                                
                                trend_metrics[product_type] = product_metrics
                            
                            cluster_data['trend_metrics'] = trend_metrics
                        
                        serializable_trends[str(cluster_id)] = cluster_data
                    
                    json.dump(serializable_trends, f, indent=2)
                results['cluster_trends_path'] = trends_analysis_path
        
        # Step 6: Generate summary
        summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'analysis_type': 'Fashion/Basic Product Analysis',
            'input_files': {
                'products': os.path.basename(products_path),
                'store_classification': os.path.basename(store_classification_path),
                'clusters': os.path.basename(clusters_path)
            },
            'output_files': {
                k: os.path.basename(v) for k, v in results.items() if not k.startswith('error')
            }
        }
        
        # Save summary
        summary_path = os.path.join(self.output_dir, 'fashion_basic_analysis_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Completed fashion/basic product analysis pipeline")
        results['summary_path'] = summary_path
        
        return results


if __name__ == "__main__":
    # Example usage
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Run Fashion/Basic Product Analysis')
    parser.add_argument('--products', required=True, help='Path to products data file (JSON)')
    parser.add_argument('--classification', required=True, help='Path to store classification data (CSV)')
    parser.add_argument('--clusters', required=True, help='Path to cluster assignments (CSV)')
    parser.add_argument('--output', default='output/fashion_basic_analysis', help='Output directory')
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = FashionBasicAnalyzer(output_dir=args.output)
    results = analyzer.run_analysis(
        products_path=args.products,
        store_classification_path=args.classification,
        clusters_path=args.clusters
    )
    
    # Print summary
    if 'summary_path' in results:
        print(f"\nAnalysis complete! Summary saved to: {results['summary_path']}")
        
        # Print key output files
        print("\nKey output files:")
        for key, path in results.items():
            if not key.startswith('error') and key != 'summary_path':
                print(f"  - {key}: {path}")
    else:
        print("\nAnalysis failed! See log for details.")
        if 'error' in results:
            print(f"Error: {results['error']}")
        for key, msg in results.items():
            if key.startswith('error_'):
                print(f"{key}: {msg}")
