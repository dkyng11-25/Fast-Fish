"""
Enhanced Trendiness Analyzer
Vendored from backup trending module as a library. No side effects on import.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class EnhancedTrendinessAnalyzer:
    """
    Enhanced analyzer for product trendiness with weather correlation,
    seasonal patterns, and advanced classification logic.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.fashion_threshold = self.config.get('fashion_threshold', 0.6)
        self.basic_threshold = self.config.get('basic_threshold', 0.4)
        self.weather_correlation_threshold = self.config.get('weather_correlation_threshold', 0.3)
        self.seasonal_window = self.config.get('seasonal_window', 30)
        self.min_seasonal_periods = self.config.get('min_seasonal_periods', 2)
        self.store_type_thresholds = {
            'FASHION': self.config.get('fashion_store_threshold', 0.7),
            'BASIC': self.config.get('basic_store_threshold', 0.3),
            'HYBRID': self.config.get('hybrid_store_range', (0.3, 0.7))
        }
        logger.info("Enhanced Trendiness Analyzer initialized")
    
    def classify_product_trendiness(self, product_data: pd.DataFrame, 
                                   sales_history: pd.DataFrame = None) -> pd.DataFrame:
        df = product_data.copy()
        df['trendiness_score'] = self._calculate_basic_trendiness(df)
        if sales_history is not None:
            df = self._enhance_with_sales_patterns(df, sales_history)
        df['trendiness_category'] = self._classify_trendiness_category(df['trendiness_score'])
        df['classification_confidence'] = self._calculate_classification_confidence(df)
        logger.info(f"Classified {len(df)} products by trendiness")
        return df
    
    def _calculate_basic_trendiness(self, df: pd.DataFrame) -> pd.Series:
        score = pd.Series(0.5, index=df.index)
        if 'category' in df.columns:
            fashion_categories = ['clothing', 'fashion', 'accessories', 'shoes', 'jewelry']
            basic_categories = ['food', 'household', 'tools', 'books', 'electronics']
            for cat in fashion_categories:
                score += df['category'].str.contains(cat, case=False, na=False) * 0.2
            for cat in basic_categories:
                score -= df['category'].str.contains(cat, case=False, na=False) * 0.2
        if 'price_std' in df.columns:
            price_volatility = df['price_std'] / df.get('price_mean', df.get('price', 1))
            score += np.clip(price_volatility * 2, 0, 0.3)
        if 'seasonal_flag' in df.columns:
            score += df['seasonal_flag'].fillna(0) * 0.3
        if 'brand_tier' in df.columns:
            tier_mapping = {'premium': 0.3, 'mid': 0.1, 'basic': -0.2}
            for tier, adjustment in tier_mapping.items():
                score += df['brand_tier'].str.contains(tier, case=False, na=False) * adjustment
        return np.clip(score, 0, 1)
    
    def _enhance_with_sales_patterns(self, df: pd.DataFrame, sales_history: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        sales_stats = self._calculate_sales_volatility(sales_history)
        df = df.merge(sales_stats, left_index=True, right_index=True, how='left')
        if 'sales_volatility' in df.columns:
            volatility_factor = np.clip(df['sales_volatility'] / df['sales_volatility'].quantile(0.9), 0, 1)
            df['trendiness_score'] = np.clip(df['trendiness_score'] + volatility_factor * 0.2, 0, 1)
        seasonal_patterns = self._detect_seasonal_patterns(sales_history)
        df = df.merge(seasonal_patterns, left_index=True, right_index=True, how='left')
        if 'seasonal_strength' in df.columns:
            df['trendiness_score'] = np.clip(
                df['trendiness_score'] + df['seasonal_strength'] * 0.15, 0, 1
            )
        return df
    
    def _calculate_sales_volatility(self, sales_history: pd.DataFrame) -> pd.DataFrame:
        if 'product_id' not in sales_history.columns or 'sales_amount' not in sales_history.columns:
            return pd.DataFrame()
        volatility_stats = sales_history.groupby('product_id').agg({
            'sales_amount': ['mean', 'std', 'count'],
            'date': ['min', 'max']
        }).reset_index()
        volatility_stats.columns = ['product_id', 'sales_mean', 'sales_std', 'sales_count', 
                                   'first_sale', 'last_sale']
        volatility_stats['sales_volatility'] = (
            volatility_stats['sales_std'] / volatility_stats['sales_mean']
        ).fillna(0)
        volatility_stats['sales_trend'] = self._calculate_sales_trend(sales_history)
        return volatility_stats.set_index('product_id')
    
    def _calculate_sales_trend(self, sales_history: pd.DataFrame) -> pd.Series:
        if 'date' not in sales_history.columns:
            return pd.Series(0, index=sales_history['product_id'].unique())
        trends = []
        for product_id in sales_history['product_id'].unique():
            product_sales = sales_history[sales_history['product_id'] == product_id].copy()
            product_sales = product_sales.sort_values('date')
            if len(product_sales) < 3:
                trends.append(0)
                continue
            x = np.arange(len(product_sales))
            y = product_sales['sales_amount'].values
            trend_slope = np.polyfit(x, y, 1)[0]
            trends.append(np.clip(trend_slope / np.mean(y), -1, 1))
        return pd.Series(trends, index=sales_history['product_id'].unique())
    
    def _detect_seasonal_patterns(self, sales_history: pd.DataFrame) -> pd.DataFrame:
        if 'date' not in sales_history.columns:
            return pd.DataFrame()
        seasonal_stats = []
        for product_id in sales_history['product_id'].unique():
            product_sales = sales_history[sales_history['product_id'] == product_id].copy()
            if len(product_sales) < 90:
                seasonal_stats.append({'product_id': product_id, 'seasonal_strength': 0, 'peak_season': None, 'seasonal_variance': 0})
                continue
            product_sales['month'] = pd.to_datetime(product_sales['date']).dt.month
            monthly_sales = product_sales.groupby('month')['sales_amount'].mean()
            seasonal_strength = monthly_sales.std() / monthly_sales.mean()
            peak_season = monthly_sales.idxmax()
            seasonal_variance = monthly_sales.var()
            seasonal_stats.append({'product_id': product_id, 'seasonal_strength': min(seasonal_strength, 1), 'peak_season': peak_season, 'seasonal_variance': seasonal_variance})
        return pd.DataFrame(seasonal_stats).set_index('product_id')
    
    def _classify_trendiness_category(self, trendiness_scores: pd.Series) -> pd.Series:
        categories = pd.Series('HYBRID', index=trendiness_scores.index)
        categories[trendiness_scores >= self.fashion_threshold] = 'FASHION'
        categories[trendiness_scores <= self.basic_threshold] = 'BASIC'
        return categories
    
    def _calculate_classification_confidence(self, df: pd.DataFrame) -> pd.Series:
        confidence = pd.Series(0.5, index=df.index)
        fashion_dist = np.abs(df['trendiness_score'] - self.fashion_threshold)
        basic_dist = np.abs(df['trendiness_score'] - self.basic_threshold)
        confidence = np.maximum(fashion_dist, basic_dist) + 0.5
        return np.clip(confidence, 0, 1)


