"""Results aggregator component for store-level aggregation."""

import fireducks.pandas as pd
from typing import List
from .config import MissingCategoryConfig


class ResultsAggregator:
    """
    Aggregates opportunity-level results to store level.
    
    Creates store-level summary with:
    - Count of missing features
    - Total quantity needed
    - Total investment required
    - Average metrics
    - Binary rule flags
    """
    
    def __init__(self, config: MissingCategoryConfig, logger):
        """
        Initialize results aggregator.
        
        Args:
            config: Configuration for the analysis
            logger: Pipeline logger instance
        """
        self.config = config
        self.logger = logger
    
    def aggregate_to_store_level(
        self,
        opportunities_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Aggregate opportunities to store level.
        
        Args:
            opportunities_df: DataFrame with opportunity-level data
            
        Returns:
            DataFrame with store-level aggregations:
            - str_code
            - cluster_id
            - missing_categories_count (or missing_spus_count)
            - total_quantity_needed
            - total_investment_required
            - total_retail_value
            - avg_sellthrough_improvement
            - avg_predicted_sellthrough
            - fastfish_approved_count
            - rule7_missing_category (binary flag)
        """
        if len(opportunities_df) == 0:
            self.logger.warning("No opportunities to aggregate")
            return pd.DataFrame()
        
        self.logger.info(f"Aggregating {len(opportunities_df)} opportunities to store level...")
        
        feature_col = self.config.feature_column
        
        # Define aggregation functions
        agg_funcs = {
            feature_col: 'count',  # Count of missing features
            'recommended_quantity': 'sum',
            'cluster_id': 'first'  # Assuming all opportunities for a store are in same cluster
        }
        
        # Add optional columns if present
        if 'investment_required' in opportunities_df.columns:
            agg_funcs['investment_required'] = 'sum'
        
        if 'unit_price' in opportunities_df.columns:
            # Calculate retail value
            opportunities_df['retail_value'] = (
                opportunities_df['unit_price'] * opportunities_df['recommended_quantity']
            )
            agg_funcs['retail_value'] = 'sum'
        
        if 'predicted_sellthrough' in opportunities_df.columns:
            agg_funcs['predicted_sellthrough'] = 'mean'
        
        if 'final_approved' in opportunities_df.columns:
            agg_funcs['final_approved'] = 'sum'
        
        # Aggregate by store
        aggregated = opportunities_df.groupby('str_code').agg(agg_funcs).reset_index()
        
        # Rename columns
        column_renames = {
            feature_col: f'missing_{self.config.analysis_level}s_count',
            'recommended_quantity': 'total_quantity_needed',
            'investment_required': 'total_investment_required',
            'retail_value': 'total_retail_value',
            'predicted_sellthrough': 'avg_predicted_sellthrough',
            'final_approved': 'fastfish_approved_count'
        }
        
        for old_name, new_name in column_renames.items():
            if old_name in aggregated.columns:
                aggregated = aggregated.rename(columns={old_name: new_name})
        
        # Add rule flag
        rule_flag_col = f'rule7_missing_{self.config.analysis_level}'
        aggregated[rule_flag_col] = 1  # Binary flag indicating rule applied
        
        # Add downstream compatibility columns
        aggregated['spu_code'] = ''  # Empty for subcategory mode
        aggregated['sub_cate_name'] = ''  # Empty for SPU mode
        aggregated['recommended_quantity_change'] = aggregated['total_quantity_needed']
        
        self.logger.info(
            f"Aggregated to {len(aggregated)} stores with "
            f"{aggregated['total_quantity_needed'].sum():.0f} total units"
        )
        
        # Log statistics
        if len(aggregated) > 0:
            avg_qty = aggregated['total_quantity_needed'].mean()
            avg_features = aggregated[f'missing_{self.config.analysis_level}s_count'].mean()
            
            self.logger.info(
                f"Store averages: {avg_qty:.1f} units, "
                f"{avg_features:.1f} missing {self.config.analysis_level}s"
            )
            
            if 'total_investment_required' in aggregated.columns:
                total_investment = aggregated['total_investment_required'].sum()
                self.logger.info(f"Total investment required: ${total_investment:,.0f}")
        
        return aggregated
    
    def add_store_metadata(
        self,
        aggregated_df: pd.DataFrame,
        cluster_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Add store metadata to aggregated results.
        
        Args:
            aggregated_df: Aggregated store-level results
            cluster_df: Clustering data with store metadata
            
        Returns:
            DataFrame with metadata added
        """
        if len(aggregated_df) == 0:
            return aggregated_df
        
        # Merge with cluster data to get cluster_id if not present
        if 'cluster_id' not in aggregated_df.columns:
            enriched = pd.merge(
                aggregated_df,
                cluster_df[['str_code', 'cluster_id']],
                on='str_code',
                how='left'
            )
        else:
            enriched = aggregated_df.copy()
        
        return enriched
    
    def get_aggregation_summary(
        self,
        aggregated_df: pd.DataFrame
    ) -> dict:
        """
        Generate aggregation summary statistics.
        
        Args:
            aggregated_df: Aggregated store-level results
            
        Returns:
            Dictionary with summary statistics
        """
        if len(aggregated_df) == 0:
            return {
                'total_stores': 0,
                'total_opportunities': 0,
                'total_quantity': 0,
                'total_investment': 0.0,
                'avg_qty_per_store': 0.0,
                'avg_opportunities_per_store': 0.0
            }
        
        feature_count_col = f'missing_{self.config.analysis_level}s_count'
        
        summary = {
            'total_stores': len(aggregated_df),
            'total_opportunities': aggregated_df[feature_count_col].sum() if feature_count_col in aggregated_df.columns else 0,
            'total_quantity': aggregated_df['total_quantity_needed'].sum() if 'total_quantity_needed' in aggregated_df.columns else 0,
            'total_investment': aggregated_df['total_investment_required'].sum() if 'total_investment_required' in aggregated_df.columns else 0.0,
            'avg_qty_per_store': aggregated_df['total_quantity_needed'].mean() if 'total_quantity_needed' in aggregated_df.columns else 0.0,
            'avg_opportunities_per_store': aggregated_df[feature_count_col].mean() if feature_count_col in aggregated_df.columns else 0.0
        }
        
        return summary
    
    def create_empty_results(self, cluster_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create empty results dataframe for all stores (when no opportunities found).
        
        This matches legacy behavior of always creating an output file with all stores,
        even when no opportunities are identified.
        
        Args:
            cluster_df: Cluster assignments with str_code and cluster_id
            
        Returns:
            DataFrame with all stores and zero values for all metrics
        """
        feature_count_col = f'missing_{self.config.analysis_level}s_count'
        rule_col = f'rule7_missing_{self.config.analysis_level}'
        
        # Create base dataframe with all stores
        results = cluster_df[['str_code', 'cluster_id']].copy()
        
        # Add all metric columns with zero values
        results[feature_count_col] = 0
        results['total_opportunity_value'] = 0.0
        results['total_quantity_needed'] = 0
        results['total_investment_required'] = 0.0
        results['total_retail_value'] = 0.0
        results['avg_sellthrough_improvement'] = 0.0
        results['avg_predicted_sellthrough'] = 0.0
        results['fastfish_approved_count'] = 0
        results[rule_col] = 0
        
        # Add rule description and metadata
        threshold_desc = f"≥{int(self.config.min_cluster_stores_selling * 100)}% cluster adoption, ≥{int(self.config.min_cluster_sales_threshold)} sales"
        results['rule7_description'] = f"Store missing {self.config.analysis_level}s well-selling in cluster peers - FAST FISH VALIDATED"
        results['rule7_threshold'] = threshold_desc
        results['rule7_analysis_level'] = self.config.analysis_level
        results['rule7_sellthrough_validation'] = "Applied - only sell-through improving recommendations included"
        results['rule7_fastfish_compliant'] = True
        
        self.logger.info(f"Created empty results for {len(results)} stores (no opportunities found)")
        
        return results
