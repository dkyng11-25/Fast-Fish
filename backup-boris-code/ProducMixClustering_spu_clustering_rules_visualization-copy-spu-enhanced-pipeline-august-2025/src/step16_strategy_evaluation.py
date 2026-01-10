#!/usr/bin/env python3
"""
Rule 16: Strategy Performance Evaluation

This script evaluates the performance of rule-based recommendations against the default strategy
for June 2025, focusing on stockout rates and sell-through rates at the SPU-store level.
"""

import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime
import traceback
from typing import Dict, List, Optional, Tuple, Any, Union
import json  # Corrected the import statement

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rule16_evaluation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
CURRENT_PERIOD = '202506B'  # June 2025
PREVIOUS_PERIOD = '202505'   # May 2025

class StrategyEvaluator:
    """Evaluates performance of rule-based recommendations vs default strategy."""
    
    def __init__(self):
        """Initialize the evaluator with required data paths and logging setup."""
        self.data_dir = 'data/api_data'
        self.output_dir = 'output'
        self.logs_dir = 'logs'
        self.period = CURRENT_PERIOD
        self.previous_period = PREVIOUS_PERIOD
        
        # Ensure output and logs directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Set up file handler for detailed logging
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(self.logs_dir, f'rule16_evaluation_{timestamp}.log')
        
        # Clear any existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Create file handler
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setFormatter(formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            handlers=[console_handler, file_handler],
            force=True  # This ensures we override any existing config
        )
        
        # Log initialization message
        logging.info("=" * 80)
        logging.info(f"INITIALIZING RULE 16 EVALUATION - {timestamp}")
        logging.info("=" * 80)
        logging.info(f"Log file: {os.path.abspath(log_file)}")
        logging.info(f"Output directory: {os.path.abspath(self.output_dir)}")
        logging.info("-" * 80)
    
    def load_data(self) -> pd.DataFrame:
        """
        Load and merge all required data files at store-SPU level.
        
        Returns:
            DataFrame containing merged data from all sources at store-SPU level
        """
        logger.info("Loading data files at store-SPU level...")
        
        try:
            # 1. Load SPU sales data for the current period
            spu_sales_path = os.path.join(self.data_dir, f'complete_spu_sales_{self.period}.csv')
            if not os.path.exists(spu_sales_path):
                raise FileNotFoundError(f"SPU sales file not found at {spu_sales_path}")
                
            spu_sales = pd.read_csv(spu_sales_path, dtype={'str_code': str, 'spu_code': str})
            logger.info(f"Loaded {len(spu_sales)} SPU sales records")
            
            # 2. Load rule recommendations from step12
            rule_recommendations_path = os.path.join('output', 'rule12_sales_performance_spu_details.csv')
            if not os.path.exists(rule_recommendations_path):
                raise FileNotFoundError(f"Rule recommendations file not found at {rule_recommendations_path}")
                
            rule_recommendations = pd.read_csv(rule_recommendations_path, 
                                            dtype={'str_code': str, 'spu_code': str})
            logger.info(f"Loaded {len(rule_recommendations)} rule-based recommendations")
            
            # 3. Process rule recommendations at store-SPU level
            rule_recommendations['rule_qty'] = (
                rule_recommendations['current_quantity'] + 
                rule_recommendations['recommended_quantity_change']
            ).round().clip(lower=0).astype(int)
            
            # 4. Merge SPU sales with rule recommendations
            merged_data = pd.merge(
                spu_sales,
                rule_recommendations[['str_code', 'spu_code', 'rule_qty']],
                on=['str_code', 'spu_code'],
                how='left'
            )
            
            # 5. Add default strategy (using target_sty_cnt_avg from store config if available)
            store_config_path = os.path.join(self.data_dir, f'store_config_{self.period}.csv')
            if os.path.exists(store_config_path):
                store_config = pd.read_csv(store_config_path, dtype={'str_code': str})
                store_config['default_qty'] = store_config['target_sty_cnt_avg'].fillna(0).round().astype(int)
                merged_data = pd.merge(
                    merged_data,
                    store_config[['str_code', 'default_qty']],
                    on='str_code',
                    how='left'
                )
            else:
                logger.warning(f"Store config not found at {store_config_path}. Using 0 as default quantity.")
                merged_data['default_qty'] = 0
            
            # 6. Fill missing values
            merged_data['actual_sales'] = merged_data['quantity'].fillna(0).astype(int)
            merged_data['rule_qty'] = merged_data['rule_qty'].fillna(merged_data['default_qty']).astype(int)
            
            # 7. Calculate inventory (1.5x actual sales, with min of 1)
            merged_data['inventory'] = (merged_data['actual_sales'] * 1.5).round().clip(lower=1).astype(int)
            
            # 8. Filter out records with no sales and no recommendations
            merged_data = merged_data[
                (merged_data['actual_sales'] > 0) | 
                (merged_data['rule_qty'] > 0) | 
                (merged_data['default_qty'] > 0)
            ]
            
            logger.info(f"Merged data contains {len(merged_data)} store-SPU records")
            return merged_data
            
        except Exception as e:
            logger.error(f"Error loading or merging data files: {e}", exc_info=True)
            return pd.DataFrame()
    
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess and clean the merged data for store-SPU level analysis.
        
        Args:
            df: Input DataFrame with raw merged data
            
        Returns:
            Preprocessed DataFrame ready for analysis
        """
        logger.info("Preprocessing store-SPU level data...")
        
        try:
            if df.empty:
                logger.error("No data to preprocess")
                return pd.DataFrame()
                
            # Log column names for debugging
            logger.info(f"Input columns: {df.columns.tolist()}")
            
            # Ensure we have required columns
            required_cols = ['str_code', 'spu_code', 'rule_qty', 'actual_sales', 'default_qty', 'inventory']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return pd.DataFrame()
            
            # Convert to appropriate data types
            df['str_code'] = df['str_code'].astype(str).str.strip()
            df['spu_code'] = df['spu_code'].astype(str).str.strip()
            
            # Ensure numeric columns are numeric and non-negative
            for col in ['rule_qty', 'actual_sales', 'default_qty', 'inventory']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna(0).clip(lower=0).round().astype(int)
            
            # Filter out invalid records
            df = df[df['str_code'] != '0']  # Remove invalid store codes
            df = df[df['spu_code'] != '0']  # Remove invalid SPU codes
            
            # Calculate derived metrics
            df['sales_amount'] = df.get('sales_amount', 0)  # Will be 0 if column doesn't exist
            
            logger.info(f"Preprocessed data contains {len(df)} store-SPU records")
            logger.info(f"Sample records:\n{df.head(3).to_string()}")
            
            return df
            
            
        except Exception as e:
            logger.error(f"Error during data preprocessing: {e}")
            raise
    
    def calculate_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate performance metrics for both strategies at store-SPU level.
        
        Args:
            df: Preprocessed DataFrame with required columns
            
        Returns:
            DataFrame with calculated metrics
        """
        logger.info("Calculating store-SPU level performance metrics...")
        
        try:
            # Make a copy to avoid SettingWithCopyWarning
            metrics_df = df.copy()
            
            # 1. Stockout indicators (1 if stockout occurred, 0 otherwise)
            metrics_df['rule_stockout'] = (metrics_df['rule_qty'] < metrics_df['actual_sales']).astype(int)
            metrics_df['default_stockout'] = (metrics_df['default_qty'] < metrics_df['actual_sales']).astype(int)
            
            # 2. Sell-through rates (percentage of inventory sold)
            with np.errstate(divide='ignore', invalid='ignore'):
                metrics_df['rule_sell_through'] = np.where(
                    metrics_df['rule_qty'] > 0,
                    (np.minimum(metrics_df['rule_qty'], metrics_df['actual_sales']) / metrics_df['rule_qty']) * 100,
                    0
                )
                metrics_df['default_sell_through'] = np.where(
                    metrics_df['default_qty'] > 0,
                    (np.minimum(metrics_df['default_qty'], metrics_df['actual_sales']) / metrics_df['default_qty']) * 100,
                    0
                )
            
            # 3. Service level (percentage of demand met)
            metrics_df['rule_service_level'] = np.where(
                metrics_df['actual_sales'] > 0,
                (np.minimum(metrics_df['rule_qty'], metrics_df['actual_sales']) / metrics_df['actual_sales']) * 100,
                100  # If no actual sales, consider service level as 100%
            )
            metrics_df['default_service_level'] = np.where(
                metrics_df['actual_sales'] > 0,
                (np.minimum(metrics_df['default_qty'], metrics_df['actual_sales']) / metrics_df['actual_sales']) * 100,
                100  # If no actual sales, consider service level as 100%
            )
            
            # 4. Absolute and percentage differences from actual sales
            metrics_df['rule_abs_diff'] = (metrics_df['rule_qty'] - metrics_df['actual_sales']).abs()
            metrics_df['default_abs_diff'] = (metrics_df['default_qty'] - metrics_df['actual_sales']).abs()
            
            metrics_df['rule_pct_diff'] = np.where(
                metrics_df['actual_sales'] > 0,
                ((metrics_df['rule_qty'] - metrics_df['actual_sales']) / metrics_df['actual_sales']) * 100,
                0
            )
            metrics_df['default_pct_diff'] = np.where(
                metrics_df['actual_sales'] > 0,
                ((metrics_df['default_qty'] - metrics_df['actual_sales']) / metrics_df['actual_sales']) * 100,
                0
            )
            
            # 5. Inventory turnover (sales / average inventory)
            metrics_df['rule_turnover'] = np.where(
                metrics_df['inventory'] > 0,
                metrics_df['actual_sales'] / metrics_df['inventory'],
                0
            )
            
            # 6. MAPE (Mean Absolute Percentage Error)
            metrics_df['rule_mape'] = np.where(
                metrics_df['actual_sales'] > 0,
                (metrics_df['rule_abs_diff'] / metrics_df['actual_sales']) * 100,
                0
            )
            metrics_df['default_mape'] = np.where(
                metrics_df['actual_sales'] > 0,
                (metrics_df['default_abs_diff'] / metrics_df['actual_sales']) * 100,
                0
            )
            
            # 7. Improvement metrics
            metrics_df['mape_improvement_pct'] = np.where(
                metrics_df['default_mape'] > 0,
                ((metrics_df['default_mape'] - metrics_df['rule_mape']) / metrics_df['default_mape']) * 100,
                0
            )
            metrics_df['abs_diff_improvement_pct'] = np.where(
                metrics_df['default_abs_diff'] > 0,
                ((metrics_df['default_abs_diff'] - metrics_df['rule_abs_diff']) / metrics_df['default_abs_diff']) * 100,
                0
            )
            metrics_df['service_level_improvement_pct'] = np.where(
                metrics_df['default_service_level'] > 0,
                ((metrics_df['rule_service_level'] - metrics_df['default_service_level']) / metrics_df['default_service_level']) * 100,
                0
            )
            
            # 8. Revenue metrics (using quantity as proxy if sales_amount not available)
            if 'sales_amount' in metrics_df.columns:
                metrics_df['rule_revenue'] = np.where(
                    metrics_df['actual_sales'] > 0,
                    np.minimum(metrics_df['rule_qty'], metrics_df['actual_sales']) * (metrics_df['sales_amount'] / metrics_df['actual_sales']),
                    0
                )
                metrics_df['default_revenue'] = np.where(
                    metrics_df['actual_sales'] > 0,
                    np.minimum(metrics_df['default_qty'], metrics_df['actual_sales']) * (metrics_df['sales_amount'] / metrics_df['actual_sales']),
                    0
                )
            else:
                logger.warning("'sales_amount' column not found. Using quantity as a proxy for revenue metrics.")
                metrics_df['rule_revenue'] = np.minimum(metrics_df['rule_qty'], metrics_df['actual_sales'])
                metrics_df['default_revenue'] = np.minimum(metrics_df['default_qty'], metrics_df['actual_sales'])
            
            # 9. Inventory efficiency
            metrics_df['rule_inv_efficiency'] = np.where(
                metrics_df['inventory'] > 0,
                metrics_df['rule_revenue'] / metrics_df['inventory'],
                0
            )
            metrics_df['default_inv_efficiency'] = np.where(
                metrics_df['inventory'] > 0,
                metrics_df['default_revenue'] / metrics_df['inventory'],
                0
            )
            
            # 10. Clip extreme values for stability
            for col in ['rule_sell_through', 'default_sell_through', 'rule_service_level', 'default_service_level']:
                metrics_df[col] = metrics_df[col].clip(0, 100)  # Percentages between 0-100%
                
            for col in ['rule_mape', 'default_mape', 'rule_pct_diff', 'default_pct_diff']:
                metrics_df[col] = metrics_df[col].clip(0, 1000)  # Cap at 1000% for stability
            
            logger.info(f"Calculated metrics for {len(metrics_df)} store-SPU records")
            return metrics_df
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            raise
    
    def get_seven_number_summary(self, series):
        """Calculate seven-number summary for a series following the standard definition.
        
        Returns:
            Dict with: minimum, lower_hinge, lower_whisker, median, 
                     upper_whisker, upper_hinge, maximum
        """
        # Calculate percentiles for the seven-number summary
        percentiles = series.quantile([0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0])
        
        # Calculate whiskers using 1.5 * IQR rule
        q1 = percentiles[0.25]
        q3 = percentiles[0.75]
        iqr = q3 - q1
        lower_whisker = max(series.min(), q1 - 1.5 * iqr)
        upper_whisker = min(series.max(), q3 + 1.5 * iqr)
        
        return {
            'minimum': percentiles[0.00],
            'lower_hinge': percentiles[0.05],  # 5th percentile
            'lower_whisker': lower_whisker,
            'median': percentiles[0.5],
            'upper_whisker': upper_whisker,
            'upper_hinge': percentiles[0.95],   # 95th percentile
            'maximum': percentiles[1.00]
        }
    
    def _calculate_win_rates(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate win rates between rule-based and default strategies."""
        win_rates = {}
        
        # Stockout comparison (lower is better)
        df['stockout_rule'] = (df['actual_sales'] > df['rule_qty']).astype(int)
        df['stockout_default'] = (df['actual_sales'] > df['default_qty']).astype(int)
        
        stockout_comparison = {
            'rule_wins': ((df['stockout_rule'] < df['stockout_default']).sum() / len(df) * 100) if len(df) > 0 else 0,
            'default_wins': ((df['stockout_rule'] > df['stockout_default']).sum() / len(df) * 100) if len(df) > 0 else 0,
            'ties': ((df['stockout_rule'] == df['stockout_default']).sum() / len(df) * 100) if len(df) > 0 else 0
        }
        win_rates['stockout'] = stockout_comparison
        
        # Sell-through comparison (higher is better, only compare when both have inventory)
        has_inventory = (df['rule_qty'] > 0) & (df['default_qty'] > 0)
        if has_inventory.any():
            df_compare = df[has_inventory].copy()
            df_compare['sell_through_rule'] = np.minimum(1, df_compare['actual_sales'] / df_compare['rule_qty'])
            df_compare['sell_through_default'] = np.minimum(1, df_compare['actual_sales'] / df_compare['default_qty'])
            
            sell_through_comparison = {
                'rule_wins': ((df_compare['sell_through_rule'] > df_compare['sell_through_default']).sum() / len(df_compare) * 100) if len(df_compare) > 0 else 0,
                'default_wins': ((df_compare['sell_through_rule'] < df_compare['sell_through_default']).sum() / len(df_compare) * 100) if len(df_compare) > 0 else 0,
                'ties': ((df_compare['sell_through_rule'] == df_compare['sell_through_default']).sum() / len(df_compare) * 100) if len(df_compare) > 0 else 0
            }
        else:
            sell_through_comparison = {'rule_wins': 0, 'default_wins': 0, 'ties': 0}
        
        win_rates['sell_through'] = sell_through_comparison
        
        return win_rates

    def generate_report(self, df: pd.DataFrame) -> Dict:
        """
        Generate performance report with distribution statistics at store-SPU level.
        
        Args:
            df: DataFrame containing the metrics at store-SPU level
            
        Returns:
            Dictionary with summary statistics
        """
        logger.info("Generating store-SPU level performance report...")
        
        def get_metric_stats(series, is_percent=False):
            """Helper to calculate distribution statistics with robust handling of edge cases."""
            valid_series = series.replace([np.inf, -np.inf], np.nan).dropna()
            
            if len(valid_series) == 0:
                stats = {
                    'mean': 0, 'median': 0, 'p25': 0, 'p75': 0,
                    'p10': 0, 'p90': 0, 'iqr': 0, 'seven_number': {}
                }
            else:
                stats = {
                    'mean': valid_series.mean(),
                    'median': valid_series.median(),
                    'p25': valid_series.quantile(0.25),
                    'p75': valid_series.quantile(0.75),
                    'p10': valid_series.quantile(0.10),
                    'p90': valid_series.quantile(0.90),
                    'iqr': valid_series.quantile(0.75) - valid_series.quantile(0.25),
                    'seven_number': self.get_seven_number_summary(valid_series)
                }
                
            if is_percent:
                stats = {k: v * 100 if k != 'seven_number' 
                        else {sk: sv * 100 for sk, sv in v.items()} 
                        for k, v in stats.items()}
                        
            return stats
        
        # Calculate distribution metrics with robust error handling
        try:
            # Stockout rate stats
            stockout_stats = {
                'rule': get_metric_stats(df['rule_stockout'], is_percent=True),
                'default': get_metric_stats(df['default_stockout'], is_percent=True)
            }
            
            # Sell-through rate stats
            str_stats = {
                'rule': get_metric_stats(df['rule_sell_through'], is_percent=True),
                'default': get_metric_stats(df['default_sell_through'], is_percent=True)
            }
            
            # Service level stats
            service_level_stats = {
                'rule': get_metric_stats(df['rule_service_level'], is_percent=True),
                'default': get_metric_stats(df['default_service_level'], is_percent=True)
            }
            
            # Inventory metrics
            inventory_metrics = {
                'avg_turnover': df['rule_turnover'].mean(),
                'total_rule_inventory': df['rule_qty'].sum(),
                'total_default_inventory': df['default_qty'].sum(),
                'inventory_efficiency_ratio': (df['rule_inv_efficiency'].mean() / 
                                             df['default_inv_efficiency'].replace(0, np.nan).mean() 
                                             if df['default_inv_efficiency'].mean() > 0 else 1)
            }
            
            # Calculate accuracy metrics with robust handling
            accuracy_metrics = {
                'rule_mape': df['rule_mape'].replace([np.inf, -np.inf], np.nan).mean(),
                'default_mape': df['default_mape'].replace([np.inf, -np.inf], np.nan).mean(),
                'rule_avg_abs_diff': df['rule_abs_diff'].mean(),
                'default_avg_abs_diff': df['default_abs_diff'].mean(),
                'rule_avg_pct_diff': df['rule_pct_diff'].replace([np.inf, -np.inf], np.nan).mean(),
                'default_avg_pct_diff': df['default_pct_diff'].replace([np.inf, -np.inf], np.nan).mean()
            }
            
            # Calculate improvement metrics
            improvement_metrics = {
                'mape_improvement_pct': (
                    (accuracy_metrics['default_mape'] - accuracy_metrics['rule_mape']) / 
                    accuracy_metrics['default_mape'] * 100 if accuracy_metrics['default_mape'] > 0 else 0
                ),
                'service_level_improvement_pct': (
                    (service_level_stats['rule']['mean'] - service_level_stats['default']['mean']) / 
                    service_level_stats['default']['mean'] * 100 if service_level_stats['default']['mean'] > 0 else 0
                ),
                'sell_through_improvement_pct': (
                    (str_stats['rule']['mean'] - str_stats['default']['mean']) / 
                    str_stats['default']['mean'] * 100 if str_stats['default']['mean'] > 0 else 0
                )
            }
            
            # Calculate SPU-level statistics
            spu_stats = df.groupby('spu_code').agg({
                'actual_sales': 'sum',
                'rule_qty': 'sum',
                'default_qty': 'sum',
                'rule_stockout': 'mean',
                'default_stockout': 'mean'
            }).reset_index()
            
            # Store-level statistics
            store_stats = df.groupby('str_code').agg({
                'actual_sales': 'sum',
                'rule_qty': 'sum',
                'default_qty': 'sum',
                'rule_stockout': 'mean',
                'default_stockout': 'mean'
            }).reset_index()
            
            # Prepare the final report
            report = {
                'total_spu_store_pairs': len(df),
                'unique_stores': df['str_code'].nunique(),
                'unique_products': df['spu_code'].nunique(),
                'period': self.period,
                'evaluation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stockout_stats': stockout_stats,
                'sell_through_stats': str_stats,
                'service_level_stats': service_level_stats,
                'accuracy_metrics': accuracy_metrics,
                'improvement_metrics': improvement_metrics,
                'inventory_metrics': inventory_metrics,
                'spu_stats_summary': {
                    'total_products': len(spu_stats),
                    'avg_products_per_store': len(df) / df['str_code'].nunique() if df['str_code'].nunique() > 0 else 0,
                    'top_products_by_sales': spu_stats.nlargest(5, 'actual_sales')[['spu_code', 'actual_sales']].to_dict('records')
                },
                'store_stats_summary': {
                    'total_stores': len(store_stats),
                    'avg_sales_per_store': store_stats['actual_sales'].mean(),
                    'top_stores_by_sales': store_stats.nlargest(5, 'actual_sales')[['str_code', 'actual_sales']].to_dict('records')
                }
            }
            
            logger.info(f"Generated report for {len(df)} store-SPU pairs across {df['str_code'].nunique()} stores and {df['spu_code'].nunique()} products")
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return {
                'error': f"Error generating report: {str(e)}",
                'traceback': traceback.format_exc()
            }
            
    def _print_summary(self, df: pd.DataFrame, report: Dict) -> None:
        """Print summary of the evaluation."""
        inventory_metrics = report['inventory_metrics']
        total_stores = report.get('store_stats_summary', {}).get('total_stores', 1)
        
        # Calculate average actual sales per store
        avg_actual_sales = inventory_metrics.get('total_actual_sales', 0) / total_stores if total_stores > 0 else 0
        
        # Calculate win rates
        win_rates = self._calculate_win_rates(df)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"{'SUMMARY':^80}")
        logger.info(f"{'='*80}")
        logger.info(f"\n{'Average Values per Store:':<30} {avg_actual_sales:.1f} units")
        
        # Print key metrics
        for metric, value in inventory_metrics.items():
            if metric not in ['total_actual_sales', 'total_rule_inventory', 'total_default_inventory']:
                logger.info(f"{metric.replace('_', ' ').title() + ':':<30} {value:.1f}")
        
        # Print win rates
        logger.info("\n" + "-"*80)
        logger.info("WIN RATE COMPARISONS")
        logger.info("-"*80)
        
        # Stockout win rates (lower is better)
        stockout = win_rates['stockout']
        logger.info(f"\n{'Stockout Rate (Lower is Better)':<40}")
        logger.info(f"{'  • Rule Wins (Less Stockouts):':<30} {stockout['rule_wins']:.1f}%")
        logger.info(f"{'  • Default Wins:':<30} {stockout['default_wins']:.1f}%")
        logger.info(f"{'  • Ties:':<30} {stockout['ties']:.1f}%")
        
        # Sell-through win rates (higher is better)
        sell_through = win_rates['sell_through']
        logger.info(f"\n{'Sell-Through Rate (Higher is Better)':<40}")
        logger.info(f"{'  • Rule Wins (Higher Sell-Through):':<30} {sell_through['rule_wins']:.1f}%")
        logger.info(f"{'  • Default Wins:':<30} {sell_through['default_wins']:.1f}%")
        logger.info(f"{'  • Ties:':<30} {sell_through['ties']:.1f}%")
        
        logger.info("\n" + "="*80)
        logger.info(f"{'Inventory Efficiency Ratio:':<30} {inventory_metrics.get('inventory_efficiency_ratio', 0):.2f}")
        logger.info("="*80 + "\n")
    
    def save_results(self, df: pd.DataFrame, report: Dict) -> None:
        """
        Save analysis results and generate reports.
        
        Args:
            df: DataFrame with detailed metrics
            report: Dictionary with summary metrics
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            # Save detailed results
            detail_file = os.path.join(self.output_dir, f'rule16_detailed_comparison_{timestamp}.csv')
            df.to_csv(detail_file, index=False)
            logging.info(f"Saved detailed comparison to {detail_file}")
            
            # Save summary report
            report_file = os.path.join(self.output_dir, f'rule16_summary_report_{timestamp}.csv')
            pd.DataFrame([report]).to_csv(report_file, index=False)
            logging.info(f"Saved summary report to {report_file}")
            
            # Print and log summary
            self._print_summary(df, report)
            
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            raise
    
    def analyze_example_triplets(self, df: pd.DataFrame, n_examples: int = 5) -> pd.DataFrame:
        """
        Analyze example triplets of rule-default-actual values with detailed KPIs.
        Optimized for large datasets by using efficient sampling and processing.
        
        Args:
            df: DataFrame with the analysis data
            n_examples: Number of examples to show for each case (reduced to 5 for efficiency)
            
        Returns:
            DataFrame with example triplets and their metrics
        """
        logger.info("\n" + "="*80)
        logger.info("RUNNING EXAMPLE TRIPLET ANALYSIS")
        logger.info("="*80)
        
        try:
            # Ensure we have enough data to sample from
            if len(df) == 0:
                logger.warning("No data available for example analysis")
                return pd.DataFrame()
                
            # Sample a smaller subset for analysis to save memory
            sample_size = min(1000, len(df))
            df_sample = df.sample(n=sample_size).copy()
            
            # Calculate KPIs directly without using apply for better performance
            logger.info("Calculating KPIs for sample data...")
            
            # Calculate sell-through rates
            df_sample['rule_sell_through'] = np.where(
                df_sample['rule_qty'] > 0,
                np.minimum(df_sample['actual_sales'], df_sample['rule_qty']) / df_sample['rule_qty'],
                0
            )
            df_sample['default_sell_through'] = np.where(
                df_sample['default_qty'] > 0,
                np.minimum(df_sample['actual_sales'], df_sample['default_qty']) / df_sample['default_qty'],
                0
            )
            
            # Calculate service levels
            df_sample['rule_service_level'] = np.where(
                df_sample['actual_sales'] > 0,
                np.minimum(1, df_sample['rule_qty'] / df_sample['actual_sales']),
                1
            )
            df_sample['default_service_level'] = np.where(
                df_sample['actual_sales'] > 0,
                np.minimum(1, df_sample['default_qty'] / df_sample['actual_sales']),
                1
            )
            
            # Calculate stockout indicators
            df_sample['rule_stockout'] = df_sample['rule_qty'] < df_sample['actual_sales']
            df_sample['default_stockout'] = df_sample['default_qty'] < df_sample['actual_sales']
            
            # Calculate MAPE
            df_sample['rule_mape'] = np.where(
                df_sample['actual_sales'] > 0,
                np.abs(df_sample['rule_qty'] - df_sample['actual_sales']) / df_sample['actual_sales'],
                0
            )
            df_sample['default_mape'] = np.where(
                df_sample['actual_sales'] > 0,
                np.abs(df_sample['default_qty'] - df_sample['actual_sales']) / df_sample['actual_sales'],
                0
            )
            
            # Find interesting examples
            examples = []
            
            try:
                # Calculate samples per group (half for each case)
                samples_per_group = max(1, n_examples // 2)
                
                # 1. Cases where actual sales > default strategy
                gt_default = df_sample[df_sample['actual_sales'] > df_sample['default_qty']]
                if len(gt_default) > 0:
                    gt_sample = gt_default.sample(min(samples_per_group, len(gt_default)))
                    for _, row in gt_sample.iterrows():
                        examples.append({
                            'type': 'actual_gt_default',
                            'str_code': row['str_code'],
                            'spu_code': row['spu_code'],
                            'actual_sales': row['actual_sales'],
                            'rule_qty': row['rule_qty'],
                            'default_qty': row['default_qty'],
                            'rule_service_level': row['rule_service_level'],
                            'default_service_level': row['default_service_level'],
                            'rule_sell_through': row['rule_sell_through'],
                            'default_sell_through': row['default_sell_through']
                        })
                
                # 2. Cases where actual sales < default strategy
                lt_default = df_sample[df_sample['actual_sales'] < df_sample['default_qty']]
                if len(lt_default) > 0:
                    lt_sample = lt_default.sample(min(samples_per_group, len(lt_default)))
                    for _, row in lt_sample.iterrows():
                        examples.append({
                            'type': 'actual_lt_default',
                            'str_code': row['str_code'],
                            'spu_code': row['spu_code'],
                            'actual_sales': row['actual_sales'],
                            'rule_qty': row['rule_qty'],
                            'default_qty': row['default_qty'],
                            'rule_service_level': row['rule_service_level'],
                            'default_service_level': row['default_service_level'],
                            'rule_sell_through': row['rule_sell_through'],
                            'default_sell_through': row['default_sell_through']
                        })
                
                # 3. If we don't have enough examples, fill with random samples
                remaining = max(0, n_examples - len(examples))
                if remaining > 0:
                    remaining_sample = df_sample[~df_sample.index.isin([e.get('index') for e in examples if 'index' in e])]
                    if len(remaining_sample) > 0:
                        remaining_sample = remaining_sample.sample(min(remaining, len(remaining_sample)))
                        for _, row in remaining_sample.iterrows():
                            examples.append({
                                'type': 'random_sample',
                                'str_code': row['str_code'],
                                'spu_code': row['spu_code'],
                                'actual_sales': row['actual_sales'],
                                'rule_qty': row['rule_qty'],
                                'default_qty': row['default_qty'],
                                'rule_service_level': row['rule_service_level'],
                                'default_service_level': row['default_service_level'],
                                'rule_sell_through': row['rule_sell_through'],
                                'default_sell_through': row['default_sell_through']
                            })
            except Exception as e:
                logger.warning(f"Error sampling balanced examples: {str(e)}")
                logger.debug(traceback.format_exc())
            
            # Convert examples to DataFrame
            if not examples:
                logger.warning("No examples could be generated")
                return pd.DataFrame()
                
            results_df = pd.DataFrame(examples)
            
            # Log examples
            logger.info("\n" + "="*80)
            logger.info(f"GENERATED {len(examples)} EXAMPLE TRIPLETS")
            logger.info("="*80)
            
            for _, row in results_df.iterrows():
                logger.info(f"\nExample Type: {row['type']}")
                logger.info(f"Store: {row['str_code']}, SPU: {row['spu_code']}")
                logger.info(f"Actual: {row['actual_sales']:.1f} | "
                          f"Rule: {row['rule_qty']:.1f} | "
                          f"Default: {row['default_qty']:.1f}")
                
                if 'rule_service_level' in row and 'default_service_level' in row:
                    logger.info(f"Service Level: Rule={row['rule_service_level']:.1%} vs Default={row['default_service_level']:.1%}")
                if 'rule_sell_through' in row and 'default_sell_through' in row:
                    logger.info(f"Sell-Through: Rule={row['rule_sell_through']:.1%} vs Default={row['default_sell_through']:.1%}")
                if 'rule_qty' in row and 'default_qty' in row:
                    qty_diff = row['rule_qty'] - row['default_qty']
                    logger.info(f"Qty Diff (Rule - Default): {qty_diff:+.1f}")
            
            # Save to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f'example_triplets_analysis_{timestamp}.csv')
            results_df.to_csv(output_file, index=False)
            logger.info(f"\nSaved example triplets to {output_file}")
            
            return results_df
            
        except Exception as e:
            logger.error(f"Error in example triplet analysis: {str(e)}")
            logger.error(traceback.format_exc())
            return pd.DataFrame()
            
            # Log the formatted output
            logging.info("\n".join(output))
            logging.info("="*150 + "\n")
            logging.info(f"Saved detailed example analysis to {output_file}")
            
            return results_df[display_columns]  # Return only display columns
            
        except Exception as e:
            logging.error(f"Error in analyze_example_triplets: {e}", exc_info=True)
            return pd.DataFrame()
            
    def run_analysis(self) -> None:
        """Run the complete analysis pipeline."""
        try:
            logging.info("Starting Rule 16 analysis...")
            
            # 1. Load data
            df = self.load_data()
            if df is None or df.empty:
                logging.error("No data available for analysis")
                return
                
            # 2. Preprocess data
            df = self.preprocess_data(df)
            
            # 3. Calculate metrics
            df = self.calculate_metrics(df)
            
            # 4. Generate report with seven-number summaries
            report = self.generate_report(df)
            
            # 5. Save results and summary report
            self.save_results(df, report)
            
            # 6. Run example triplet analysis
            logging.info("\n" + "="*80)
            logging.info("RUNNING EXAMPLE TRIPLET ANALYSIS")
            logging.info("="*80)
            self.analyze_example_triplets(df, n_examples=10)
            
            logging.info("Rule 16 analysis completed successfully")
            
        except Exception as e:
            logging.error(f"Error in run_analysis: {e}", exc_info=True)
            raise


def main():
    """Main entry point for Rule 16 execution."""
    try:
        evaluator = StrategyEvaluator()
        evaluator.run_analysis()
    except Exception as e:
        logger.critical(f"Fatal error in Rule 16: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
