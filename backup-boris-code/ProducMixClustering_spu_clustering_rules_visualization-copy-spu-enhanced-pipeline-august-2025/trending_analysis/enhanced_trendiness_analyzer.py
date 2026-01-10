"""
Enhanced Trendiness Analyzer
Advanced product trendiness classification with weather correlation and seasonal analysis.
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

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedTrendinessAnalyzer:
    """
    Enhanced analyzer for product trendiness with weather correlation,
    seasonal patterns, and advanced classification logic.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize Enhanced Trendiness Analyzer.
        
        Args:
            config: Configuration dictionary with analysis parameters
        """
        self.config = config or {}
        
        # Trendiness thresholds
        self.fashion_threshold = self.config.get('fashion_threshold', 0.6)
        self.basic_threshold = self.config.get('basic_threshold', 0.4)
        
        # Weather correlation thresholds
        self.weather_correlation_threshold = self.config.get('weather_correlation_threshold', 0.3)
        
        # Seasonal analysis parameters
        self.seasonal_window = self.config.get('seasonal_window', 30)  # days
        self.min_seasonal_periods = self.config.get('min_seasonal_periods', 2)
        
        # Store type classification
        self.store_type_thresholds = {
            'FASHION': self.config.get('fashion_store_threshold', 0.7),
            'BASIC': self.config.get('basic_store_threshold', 0.3),
            'HYBRID': self.config.get('hybrid_store_range', (0.3, 0.7))
        }
        
        logger.info("Enhanced Trendiness Analyzer initialized")
    
    def classify_product_trendiness(self, product_data: pd.DataFrame, 
                                  sales_history: pd.DataFrame = None) -> pd.DataFrame:
        """
        Classify products by trendiness using advanced metrics.
        
        Args:
            product_data: DataFrame with product information
            sales_history: Optional historical sales data
            
        Returns:
            DataFrame with trendiness classifications
        """
        df = product_data.copy()
        
        # Basic trendiness indicators
        df['trendiness_score'] = self._calculate_basic_trendiness(df)
        
        # Advanced metrics if sales history available
        if sales_history is not None:
            df = self._enhance_with_sales_patterns(df, sales_history)
        
        # Classify trendiness categories
        df['trendiness_category'] = self._classify_trendiness_category(df['trendiness_score'])
        
        # Calculate confidence scores
        df['classification_confidence'] = self._calculate_classification_confidence(df)
        
        logger.info(f"Classified {len(df)} products by trendiness")
        return df
    
    def _calculate_basic_trendiness(self, df: pd.DataFrame) -> pd.Series:
        """Calculate basic trendiness score from product attributes."""
        score = pd.Series(0.5, index=df.index)  # Neutral baseline
        
        # Category-based scoring
        if 'category' in df.columns:
            fashion_categories = ['clothing', 'fashion', 'accessories', 'shoes', 'jewelry']
            basic_categories = ['food', 'household', 'tools', 'books', 'electronics']
            
            for cat in fashion_categories:
                score += df['category'].str.contains(cat, case=False, na=False) * 0.2
            
            for cat in basic_categories:
                score -= df['category'].str.contains(cat, case=False, na=False) * 0.2
        
        # Price volatility (higher volatility suggests fashion)
        if 'price_std' in df.columns:
            price_volatility = df['price_std'] / df.get('price_mean', df.get('price', 1))
            score += np.clip(price_volatility * 2, 0, 0.3)
        
        # Seasonal indicators
        if 'seasonal_flag' in df.columns:
            score += df['seasonal_flag'].fillna(0) * 0.3
        
        # Brand prestige (if available)
        if 'brand_tier' in df.columns:
            tier_mapping = {'premium': 0.3, 'mid': 0.1, 'basic': -0.2}
            for tier, adjustment in tier_mapping.items():
                score += df['brand_tier'].str.contains(tier, case=False, na=False) * adjustment
        
        return np.clip(score, 0, 1)
    
    def _enhance_with_sales_patterns(self, df: pd.DataFrame, 
                                   sales_history: pd.DataFrame) -> pd.DataFrame:
        """Enhance trendiness classification with sales pattern analysis."""
        df = df.copy()
        
        # Calculate sales volatility
        sales_stats = self._calculate_sales_volatility(sales_history)
        df = df.merge(sales_stats, left_index=True, right_index=True, how='left')
        
        # Adjust trendiness score based on sales patterns
        if 'sales_volatility' in df.columns:
            volatility_factor = np.clip(df['sales_volatility'] / df['sales_volatility'].quantile(0.9), 0, 1)
            df['trendiness_score'] = np.clip(df['trendiness_score'] + volatility_factor * 0.2, 0, 1)
        
        # Seasonal sales patterns
        seasonal_patterns = self._detect_seasonal_patterns(sales_history)
        df = df.merge(seasonal_patterns, left_index=True, right_index=True, how='left')
        
        if 'seasonal_strength' in df.columns:
            df['trendiness_score'] = np.clip(
                df['trendiness_score'] + df['seasonal_strength'] * 0.15, 0, 1
            )
        
        return df
    
    def _calculate_sales_volatility(self, sales_history: pd.DataFrame) -> pd.DataFrame:
        """Calculate sales volatility metrics for products."""
        if 'product_id' not in sales_history.columns or 'sales_amount' not in sales_history.columns:
            return pd.DataFrame()
        
        volatility_stats = sales_history.groupby('product_id').agg({
            'sales_amount': ['mean', 'std', 'count'],
            'date': ['min', 'max']
        }).reset_index()
        
        volatility_stats.columns = ['product_id', 'sales_mean', 'sales_std', 'sales_count', 
                                   'first_sale', 'last_sale']
        
        # Calculate coefficient of variation
        volatility_stats['sales_volatility'] = (
            volatility_stats['sales_std'] / volatility_stats['sales_mean']
        ).fillna(0)
        
        # Calculate sales trend
        volatility_stats['sales_trend'] = self._calculate_sales_trend(sales_history)
        
        return volatility_stats.set_index('product_id')
    
    def _calculate_sales_trend(self, sales_history: pd.DataFrame) -> pd.Series:
        """Calculate sales trend (increasing/decreasing) for products."""
        if 'date' not in sales_history.columns:
            return pd.Series(0, index=sales_history['product_id'].unique())
        
        trends = []
        for product_id in sales_history['product_id'].unique():
            product_sales = sales_history[sales_history['product_id'] == product_id].copy()
            product_sales = product_sales.sort_values('date')
            
            if len(product_sales) < 3:
                trends.append(0)
                continue
            
            # Simple linear trend
            x = np.arange(len(product_sales))
            y = product_sales['sales_amount'].values
            trend_slope = np.polyfit(x, y, 1)[0]
            trends.append(np.clip(trend_slope / np.mean(y), -1, 1))
        
        return pd.Series(trends, index=sales_history['product_id'].unique())
    
    def _detect_seasonal_patterns(self, sales_history: pd.DataFrame) -> pd.DataFrame:
        """Detect seasonal patterns in sales data."""
        if 'date' not in sales_history.columns:
            return pd.DataFrame()
        
        seasonal_stats = []
        
        for product_id in sales_history['product_id'].unique():
            product_sales = sales_history[sales_history['product_id'] == product_id].copy()
            
            if len(product_sales) < 90:  # Need at least 3 months of data
                seasonal_stats.append({
                    'product_id': product_id,
                    'seasonal_strength': 0,
                    'peak_season': None,
                    'seasonal_variance': 0
                })
                continue
            
            # Add month column
            product_sales['month'] = pd.to_datetime(product_sales['date']).dt.month
            
            # Calculate monthly averages
            monthly_sales = product_sales.groupby('month')['sales_amount'].mean()
            
            # Calculate seasonal strength (coefficient of variation of monthly sales)
            seasonal_strength = monthly_sales.std() / monthly_sales.mean()
            peak_season = monthly_sales.idxmax()
            seasonal_variance = monthly_sales.var()
            
            seasonal_stats.append({
                'product_id': product_id,
                'seasonal_strength': min(seasonal_strength, 1),  # Cap at 1
                'peak_season': peak_season,
                'seasonal_variance': seasonal_variance
            })
        
        return pd.DataFrame(seasonal_stats).set_index('product_id')
    
    def _classify_trendiness_category(self, trendiness_scores: pd.Series) -> pd.Series:
        """Classify products into trendiness categories."""
        categories = pd.Series('HYBRID', index=trendiness_scores.index)
        
        categories[trendiness_scores >= self.fashion_threshold] = 'FASHION'
        categories[trendiness_scores <= self.basic_threshold] = 'BASIC'
        
        return categories
    
    def _calculate_classification_confidence(self, df: pd.DataFrame) -> pd.Series:
        """Calculate confidence scores for trendiness classifications."""
        confidence = pd.Series(0.5, index=df.index)
        
        # Distance from thresholds indicates confidence
        fashion_dist = np.abs(df['trendiness_score'] - self.fashion_threshold)
        basic_dist = np.abs(df['trendiness_score'] - self.basic_threshold)
        
        # Higher confidence for scores further from thresholds
        confidence = np.maximum(fashion_dist, basic_dist) + 0.5
        confidence = np.clip(confidence, 0, 1)
        
        return confidence
    
    def analyze_weather_correlation(self, product_data: pd.DataFrame, 
                                  weather_data: pd.DataFrame, 
                                  sales_data: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze correlation between weather patterns and product performance.
        
        Args:
            product_data: Product information with trendiness classifications
            weather_data: Weather data with feels-like temperatures and bands
            sales_data: Sales data for correlation analysis
            
        Returns:
            DataFrame with weather correlation metrics
        """
        correlations = []
        
        # Merge sales with weather data by date
        if 'date' in sales_data.columns and 'date' in weather_data.columns:
            sales_weather = sales_data.merge(weather_data, on='date', how='inner')
            
            for product_id in product_data.index:
                product_sales = sales_weather[sales_weather.get('product_id') == product_id]
                
                if len(product_sales) < 30:  # Need sufficient data
                    correlations.append({
                        'product_id': product_id,
                        'temp_correlation': 0,
                        'weather_sensitivity': 'LOW',
                        'optimal_temp_range': None
                    })
                    continue
                
                # Calculate temperature correlation
                temp_corr = product_sales['sales_amount'].corr(product_sales['feels_like_temp'])
                temp_corr = 0 if pd.isna(temp_corr) else temp_corr
                
                # Determine weather sensitivity
                weather_sensitivity = self._classify_weather_sensitivity(abs(temp_corr))
                
                # Find optimal temperature range
                optimal_range = self._find_optimal_temp_range(product_sales)
                
                correlations.append({
                    'product_id': product_id,
                    'temp_correlation': temp_corr,
                    'weather_sensitivity': weather_sensitivity,
                    'optimal_temp_range': optimal_range
                })
        
        correlation_df = pd.DataFrame(correlations)
        if not correlation_df.empty:
            correlation_df = correlation_df.set_index('product_id')
        
        return correlation_df
    
    def _classify_weather_sensitivity(self, correlation_strength: float) -> str:
        """Classify weather sensitivity based on correlation strength."""
        if correlation_strength >= 0.5:
            return 'HIGH'
        elif correlation_strength >= 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _find_optimal_temp_range(self, sales_weather_data: pd.DataFrame) -> Optional[str]:
        """Find optimal temperature range for product sales."""
        if len(sales_weather_data) < 50:
            return None
        
        # Group by temperature bands and calculate average sales
        temp_bands = sales_weather_data.groupby('temp_band')['sales_amount'].mean()
        
        if len(temp_bands) < 3:
            return None
        
        # Find temperature band with highest average sales
        optimal_band = temp_bands.idxmax()
        return optimal_band
    
    def classify_store_types(self, store_data: pd.DataFrame, 
                           product_mix: pd.DataFrame) -> pd.DataFrame:
        """
        Classify stores by type based on their product mix trendiness.
        
        Args:
            store_data: Store information
            product_mix: Product mix data with trendiness classifications
            
        Returns:
            DataFrame with store type classifications
        """
        store_classifications = []
        
        for store_id in store_data.index:
            store_products = product_mix[product_mix.get('store_id') == store_id]
            
            if len(store_products) == 0:
                store_classifications.append({
                    'store_id': store_id,
                    'store_type': 'UNKNOWN',
                    'fashion_ratio': 0,
                    'basic_ratio': 0,
                    'hybrid_ratio': 0,
                    'classification_confidence': 0
                })
                continue
            
            # Calculate product mix ratios
            fashion_ratio = (store_products['trendiness_category'] == 'FASHION').mean()
            basic_ratio = (store_products['trendiness_category'] == 'BASIC').mean()
            hybrid_ratio = (store_products['trendiness_category'] == 'HYBRID').mean()
            
            # Classify store type
            store_type = self._classify_store_type(fashion_ratio, basic_ratio, hybrid_ratio)
            
            # Calculate classification confidence
            confidence = self._calculate_store_classification_confidence(
                fashion_ratio, basic_ratio, hybrid_ratio
            )
            
            store_classifications.append({
                'store_id': store_id,
                'store_type': store_type,
                'fashion_ratio': fashion_ratio,
                'basic_ratio': basic_ratio,
                'hybrid_ratio': hybrid_ratio,
                'classification_confidence': confidence
            })
        
        classification_df = pd.DataFrame(store_classifications)
        if not classification_df.empty:
            classification_df = classification_df.set_index('store_id')
        
        logger.info(f"Classified {len(classification_df)} stores by type")
        return classification_df
    
    def _classify_store_type(self, fashion_ratio: float, basic_ratio: float, 
                           hybrid_ratio: float) -> str:
        """Classify store type based on product mix ratios."""
        if fashion_ratio >= self.store_type_thresholds['FASHION']:
            return 'FASHION'
        elif basic_ratio >= self.store_type_thresholds['BASIC']:
            return 'BASIC'
        else:
            return 'HYBRID'
    
    def _calculate_store_classification_confidence(self, fashion_ratio: float, 
                                                 basic_ratio: float, 
                                                 hybrid_ratio: float) -> float:
        """Calculate confidence score for store classification."""
        # Higher confidence when one category dominates
        max_ratio = max(fashion_ratio, basic_ratio, hybrid_ratio)
        
        # Distance from decision boundaries
        fashion_dist = abs(fashion_ratio - self.store_type_thresholds['FASHION'])
        basic_dist = abs(basic_ratio - self.store_type_thresholds['BASIC'])
        
        confidence = max_ratio + min(fashion_dist, basic_dist)
        return np.clip(confidence, 0, 1)
    
    def generate_trendiness_insights(self, product_data: pd.DataFrame, 
                                   store_classifications: pd.DataFrame = None,
                                   weather_correlations: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Generate comprehensive trendiness analysis insights.
        
        Args:
            product_data: Product data with trendiness classifications
            store_classifications: Store type classifications (optional)
            weather_correlations: Weather correlation data (optional)
            
        Returns:
            Dictionary with comprehensive insights
        """
        insights = {}
        
        # Product trendiness distribution
        trendiness_dist = product_data['trendiness_category'].value_counts()
        insights['product_distribution'] = {
            'fashion_products': trendiness_dist.get('FASHION', 0),
            'basic_products': trendiness_dist.get('BASIC', 0),
            'hybrid_products': trendiness_dist.get('HYBRID', 0),
            'total_products': len(product_data)
        }
        
        # Average trendiness scores by category
        insights['average_scores'] = {
            'fashion_avg': product_data[product_data['trendiness_category'] == 'FASHION']['trendiness_score'].mean(),
            'basic_avg': product_data[product_data['trendiness_category'] == 'BASIC']['trendiness_score'].mean(),
            'hybrid_avg': product_data[product_data['trendiness_category'] == 'HYBRID']['trendiness_score'].mean(),
            'overall_avg': product_data['trendiness_score'].mean()
        }
        
        # Store type distribution (if available)
        if store_classifications is not None:
            store_dist = store_classifications['store_type'].value_counts()
            insights['store_distribution'] = {
                'fashion_stores': store_dist.get('FASHION', 0),
                'basic_stores': store_dist.get('BASIC', 0),
                'hybrid_stores': store_dist.get('HYBRID', 0),
                'total_stores': len(store_classifications)
            }
        
        # Weather sensitivity insights (if available)
        if weather_correlations is not None:
            sensitivity_dist = weather_correlations['weather_sensitivity'].value_counts()
            insights['weather_sensitivity'] = {
                'high_sensitivity': sensitivity_dist.get('HIGH', 0),
                'medium_sensitivity': sensitivity_dist.get('MEDIUM', 0),
                'low_sensitivity': sensitivity_dist.get('LOW', 0),
                'avg_temp_correlation': weather_correlations['temp_correlation'].mean()
            }
        
        # Classification confidence
        insights['classification_quality'] = {
            'avg_product_confidence': product_data['classification_confidence'].mean(),
            'high_confidence_products': (product_data['classification_confidence'] > 0.7).sum(),
            'low_confidence_products': (product_data['classification_confidence'] < 0.3).sum()
        }
        
        logger.info("Generated comprehensive trendiness insights")
        return insights
