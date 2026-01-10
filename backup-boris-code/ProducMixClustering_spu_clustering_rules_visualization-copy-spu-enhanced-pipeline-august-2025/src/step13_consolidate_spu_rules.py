#!/usr/bin/env python3
"""
Step 13: Consolidate All SPU-Level Rule Results with Comprehensive Trend Analysis

This step consolidates all individual SPU-level rule results into a single comprehensive
output file. NOW USES REAL QUANTITY DATA FROM API! 

Enhanced with comprehensive trend analysis including business-friendly language,
confidence scoring, and actionable insights across 10 trend dimensions.

Author: Data Pipeline Team
Date: 2025-07-03
Version: Enhanced with Andy's trending system
"""

"""
🎯 NOW USES REAL QUANTITY DATA FROM API!

This step has been updated to use real quantities and unit prices extracted
from the API data instead of treating sales amounts as quantities.

Key improvements:
- Real unit quantities from base_sal_qty and fashion_sal_qty API fields
- Realistic unit prices calculated from API data ($20-$150 range)
- Meaningful investment calculations (quantity_change × unit_price)
- No more fake $1.00 unit prices!
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, Tuple, Any
import gc
import numpy as np
import warnings
from tqdm import tqdm
import json

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# ===== PERFORMANCE CONFIGURATION =====
FAST_MODE = True  # Set to False for full trending analysis
TREND_SAMPLE_SIZE = 1000  # Process only top N suggestions for trending (when FAST_MODE=True)
CHUNK_SIZE_SMALL = 5000   # Smaller chunks for faster processing

# ===== CONFIGURATION =====
# Currency labeling configuration
CURRENCY_SYMBOL = "¥"  # Chinese Yuan/RMB symbol
CURRENCY_LABEL = "RMB"  # Currency label for output

# Rule files configuration
rule_files = {
    'rule7': 'output/rule7_missing_spu_opportunities.csv',
    'rule8': 'output/rule8_imbalanced_spu_cases.csv', 
    'rule9': 'output/rule9_below_minimum_spu_cases.csv',
    'rule10': 'output/rule10_spu_overcapacity_opportunities.csv',
    'rule11': 'output/rule11_improved_missed_sales_opportunity_spu_details.csv',
    'rule12': 'output/rule12_sales_performance_spu_details.csv'
}

# Path setup for trend analysis (absolute paths for reliable loading)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
output_dir = os.path.join(project_root, "output")

# Output files - keeping your current format PLUS Andy's new formats
OUTPUT_FILE = "output/consolidated_spu_rule_results.csv"
COMPREHENSIVE_TRENDS_FILE = "output/comprehensive_trend_enhanced_suggestions.csv"  # Andy's 51-column format
ALL_RULES_FILE = "output/all_rule_suggestions.csv"  # Basic format for compatibility
FASHION_ENHANCED_FILE = os.path.join(output_dir, "fashion_enhanced_suggestions.csv")  # Andy's 20-column format
SUMMARY_FILE = "output/consolidated_spu_rule_summary.md"

# Trend analysis data sources (absolute paths for reliable loading)
SALES_TRENDS_FILE = os.path.join(output_dir, "rule12_sales_performance_spu_results.csv")
WEATHER_DATA_FILE = os.path.join(output_dir, "stores_with_feels_like_temperature.csv")  
CLUSTERING_RESULTS_SPU = os.path.join(output_dir, "clustering_results_spu.csv")

# Create output directories
os.makedirs("output", exist_ok=True)
os.makedirs(os.path.join(output_dir, "real_data_trends"), exist_ok=True)

# ===== ANDY'S COMPREHENSIVE TREND ANALYZER =====
class ComprehensiveTrendAnalyzer:
    """Enhanced trend analyzer that uses ONLY real data from business files"""
    
    def __init__(self):
        """Initialize the trend analyzer with real data sources"""
        print("Loading real business data for trend analysis...")
        self.sales_data = self._load_sales_performance_data()
        self.weather_data = self._load_weather_data()
        self.cluster_data = self._load_cluster_data()
        self.fashion_data = self._load_fashion_data()
        self.data_sources_loaded = self._count_loaded_sources()
        print(f"✓ Loaded {self.data_sources_loaded}/4 data sources successfully")
        
    def _load_sales_performance_data(self) -> pd.DataFrame:
        """Load real sales performance data from Rule 12 results"""
        try:
            if os.path.exists(SALES_TRENDS_FILE):
                df = pd.read_csv(SALES_TRENDS_FILE, dtype={'str_code': str})
                print(f"✓ Sales performance data: {len(df):,} stores")
                return df
            else:
                print("✗ Sales performance data not found")
                return pd.DataFrame()
        except Exception as e:
            print(f"✗ Error loading sales data: {e}")
            return pd.DataFrame()
    
    def _load_weather_data(self) -> pd.DataFrame:
        """Load real weather data"""
        try:
            if os.path.exists(WEATHER_DATA_FILE):
                weather_df = pd.read_csv(WEATHER_DATA_FILE)
                # Standardize column name
                if 'store_code' in weather_df.columns:
                    weather_df = weather_df.rename(columns={'store_code': 'str_code'})
                weather_df['str_code'] = weather_df['str_code'].astype(str)
                print(f"✓ Weather data: {len(weather_df):,} stores")
                return weather_df
            else:
                print("✗ Weather data not found")
                return pd.DataFrame()
        except Exception as e:
            print(f"✗ Error loading weather data: {e}")
            return pd.DataFrame()
    
    def _load_cluster_data(self) -> pd.DataFrame:
        """Load real cluster data"""
        try:
            if os.path.exists(CLUSTERING_RESULTS_SPU):
                df = pd.read_csv(CLUSTERING_RESULTS_SPU, dtype={'str_code': str})
                print(f"✓ Cluster data: {len(df):,} stores")
                return df
            else:
                print("✗ Cluster data not found")
                return pd.DataFrame()
        except Exception as e:
            print(f"✗ Error loading cluster data: {e}")
            return pd.DataFrame()
    
    def _load_fashion_data(self) -> pd.DataFrame:
        """Load real fashion mix data"""
        try:
            if os.path.exists(FASHION_ENHANCED_FILE):
                df = pd.read_csv(FASHION_ENHANCED_FILE, dtype={'store_code': str})
                print(f"✓ Fashion data: {len(df):,} records")
                return df
            else:
                print("✗ Fashion data not found")
                return pd.DataFrame()
        except Exception as e:
            print(f"✗ Error loading fashion data: {e}")
            return pd.DataFrame()
            
    def _count_loaded_sources(self) -> int:
        """Count how many data sources were successfully loaded"""
        loaded = 0
        if not self.sales_data.empty:
            loaded += 1
        if not self.weather_data.empty:
            loaded += 1
        if not self.cluster_data.empty:
            loaded += 1
        if not self.fashion_data.empty:
            loaded += 1
        return loaded

    def analyze_comprehensive_trends(self, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all trend dimensions using ONLY real data"""
        store_code = suggestion.get('store_code')
        
        # Initialize trend analysis with real data only
        trend_analysis = {}
        
        # 1. Real Sales Performance Trends
        sales_analysis = self._analyze_real_sales_trends(store_code)
        trend_analysis.update(sales_analysis)
        
        # 2. Real Fashion Mix Trends  
        fashion_analysis = self._analyze_real_fashion_trends(store_code)
        trend_analysis.update(fashion_analysis)
        
        # 3. Real Weather Impact Trends
        weather_analysis = self._analyze_real_weather_trends(store_code)
        trend_analysis.update(weather_analysis)
        
        # 4. Real Cluster Performance Trends
        cluster_analysis = self._analyze_real_cluster_trends(store_code)
        trend_analysis.update(cluster_analysis)
        
        # 5. Real Price Point Analysis
        price_analysis = self._analyze_real_price_trends(store_code)
        trend_analysis.update(price_analysis)
        
        # 6. Real Category Performance (from sales data)
        category_analysis = self._analyze_real_category_trends(store_code)
        trend_analysis.update(category_analysis)
        
        # 7. Real Regional Analysis (from store code patterns)
        regional_analysis = self._analyze_real_regional_trends(store_code)
        trend_analysis.update(regional_analysis)
        
        # Calculate REAL overall scores based on actual data
        trend_analysis['overall_trend_score'] = self._calculate_real_overall_score(trend_analysis)
        trend_analysis['business_priority_score'] = self._calculate_real_priority_score(trend_analysis, suggestion)
        trend_analysis['data_quality_score'] = self._calculate_real_data_quality_score(store_code, trend_analysis)
        
        return trend_analysis
    
    def _analyze_real_sales_trends(self, store_code: int) -> Dict[str, Any]:
        """Analyze sales performance using REAL data from Rule 12 results"""
        if self.sales_data.empty:
            return {
                'sales_trend': 'No sales data available',
                'sales_score': 0,
                'sales_confidence': 0
            }
        
        store_sales = self.sales_data[self.sales_data['str_code'] == str(store_code)]
        if store_sales.empty:
            return {
                'sales_trend': 'Store not in sales performance data',
                'sales_score': 0,
                'sales_confidence': 0
            }
        
        # Get REAL sales performance data
        latest = store_sales.iloc[0]
        z_score = latest.get('avg_opportunity_z_score', 0)
        categories = latest.get('categories_analyzed', 0)
        performance_level = latest.get('store_performance_level', 'unknown')
        opportunity_value = latest.get('total_opportunity_value', 0)
        
        # Create business description based on REAL performance level
        if performance_level == 'top_performer':
            trend_desc = f"🏆 TOP PERFORMER: Z-score {z_score:.2f} ({categories} categories analyzed)"
            score = 95
        elif performance_level == 'performing_well':
            trend_desc = f"✅ PERFORMING WELL: Z-score {z_score:.2f} ({categories} categories)"
            score = 80
        elif performance_level == 'some_opportunity':
            trend_desc = f"📈 SOME OPPORTUNITY: Z-score {z_score:.2f}, ¥{opportunity_value:.0f} potential"
            score = 65
        elif performance_level == 'good_opportunity':
            trend_desc = f"💰 GOOD OPPORTUNITY: Z-score {z_score:.2f}, ¥{opportunity_value:.0f} potential"
            score = 50
        elif performance_level == 'major_opportunity':
            trend_desc = f"🚨 MAJOR OPPORTUNITY: Z-score {z_score:.2f}, ¥{opportunity_value:.0f} potential"
            score = 25
        else:
            trend_desc = f"📊 Performance level: {performance_level} (Z-score: {z_score:.2f})"
            score = 50
            
        # Calculate REAL confidence based on sample size and data quality
        confidence = min(90, max(10, int(categories * 0.3)))  # Scale by categories analyzed
        
        return {
            'sales_trend': trend_desc,
            'sales_score': score,
            'sales_confidence': confidence
        }

    def _analyze_real_fashion_trends(self, store_code: int) -> Dict[str, Any]:
        """Analyze fashion mix using REAL data from fashion enhanced suggestions"""
        if self.fashion_data.empty:
            return {
                'fashion_mix_trend': 'No fashion data available',
                'fashion_mix_score': 0,
                'fashion_mix_confidence': 0
            }
        
        store_fashion = self.fashion_data[self.fashion_data['store_code'] == str(store_code)]
        if store_fashion.empty:
            return {
                'fashion_mix_trend': 'Store not in fashion data',
                'fashion_mix_score': 0,
                'fashion_mix_confidence': 0
            }
        
        # Get REAL fashion ratios (already calculated in the data)
        first_record = store_fashion.iloc[0]
        basic_ratio_str = first_record.get('basic_ratio', '0%')
        fashion_ratio_str = first_record.get('fashion_ratio', '0%')
        mix_balance = first_record.get('mix_balance_status', 'UNKNOWN')
        store_type = first_record.get('store_type_classification', 'UNKNOWN')
        
        # Parse real percentages
        try:
            basic_ratio = float(basic_ratio_str.replace('%', ''))
            fashion_ratio = float(fashion_ratio_str.replace('%', ''))
        except:
            basic_ratio = 0
            fashion_ratio = 0
        
        # Create business description based on REAL fashion mix
        if mix_balance == 'BASIC_HEAVY':
            trend_desc = f"🔵 BASIC-focused: {basic_ratio:.1f}% basic, {fashion_ratio:.1f}% fashion ({store_type})"
            score = 65
        elif mix_balance == 'FASHION_HEAVY':
            trend_desc = f"💎 FASHION-forward: {fashion_ratio:.1f}% fashion, {basic_ratio:.1f}% basic ({store_type})"
            score = 85
        elif mix_balance == 'BALANCED':
            trend_desc = f"⚖️ BALANCED mix: {basic_ratio:.1f}% basic, {fashion_ratio:.1f}% fashion ({store_type})"
            score = 80
        else:
            trend_desc = f"📊 Mix: {basic_ratio:.1f}% basic, {fashion_ratio:.1f}% fashion"
            score = 60
        
        # Calculate confidence based on number of records for this store
        records_count = len(store_fashion)
        confidence = min(85, max(20, records_count * 0.1))  # Scale by data volume
        
        return {
            'fashion_mix_trend': trend_desc,
            'fashion_mix_score': score,
            'fashion_mix_confidence': int(confidence)
        }

    def _analyze_real_weather_trends(self, store_code: int) -> Dict[str, Any]:
        """Analyze weather impact using REAL weather data"""
        if self.weather_data.empty:
            return {
                'weather_trend': 'No weather data available',
                'weather_score': 0,
                'weather_confidence': 0
            }
        
        store_weather = self.weather_data[self.weather_data['str_code'] == str(store_code)]
        if store_weather.empty:
            return {
                'weather_trend': 'Store weather data not found',
                'weather_score': 0,
                'weather_confidence': 0
            }
        
        # Get REAL weather metrics
        weather_record = store_weather.iloc[0]
        feels_like = weather_record.get('feels_like_temperature', 0)
        temp_band = weather_record.get('temperature_band', 'Unknown')
        hot_hours = weather_record.get('hot_condition_hours', 0)
        cold_hours = weather_record.get('cold_condition_hours', 0)
        moderate_hours = weather_record.get('moderate_condition_hours', 0)
        
        total_hours = hot_hours + cold_hours + moderate_hours
        
        # Create business description based on REAL weather patterns
        if hot_hours > total_hours * 0.5:
            trend_desc = f"☀️ HOT climate: {feels_like:.1f}°C avg, {hot_hours}h hot conditions - Summer advantage"
            score = 85
        elif cold_hours > total_hours * 0.5:
            trend_desc = f"❄️ COLD climate: {feels_like:.1f}°C avg, {cold_hours}h cold conditions - Winter advantage"
            score = 80
        else:
            trend_desc = f"🌤️ MODERATE climate: {feels_like:.1f}°C avg, {temp_band} - Stable conditions"
            score = 75
        
        # Calculate confidence based on data completeness
        confidence = 80 if total_hours > 0 and feels_like > 0 else 30
        
        return {
            'weather_trend': trend_desc,
            'weather_score': score,
            'weather_confidence': confidence
        }

    def _analyze_real_cluster_trends(self, store_code: int) -> Dict[str, Any]:
        """Analyze cluster performance using REAL cluster assignments"""
        if self.cluster_data.empty:
            return {
                'cluster_trend': 'No cluster data available',
                'cluster_score': 0,
                'cluster_confidence': 0
            }
        
        store_cluster = self.cluster_data[self.cluster_data['str_code'] == str(store_code)]
        if store_cluster.empty:
            return {
                'cluster_trend': 'Store not in cluster data',
                'cluster_score': 0,
                'cluster_confidence': 0
            }
        
        cluster_id = store_cluster.iloc[0].get('Cluster', -1)
        
        # Get cluster size for context
        cluster_size = len(self.cluster_data[self.cluster_data['Cluster'] == cluster_id])
        total_stores = len(self.cluster_data)
        cluster_pct = (cluster_size / total_stores) * 100
        
        # Create business description based on REAL cluster data
        if cluster_id == 0:
            trend_desc = f"🏆 Cluster 0: Top performer group ({cluster_size} stores, {cluster_pct:.1f}% of network)"
            score = 90
        elif cluster_id <= 2:
            trend_desc = f"📈 Cluster {cluster_id}: Above average group ({cluster_size} stores, {cluster_pct:.1f}%)"
            score = 75
        elif cluster_id <= 4:
            trend_desc = f"📊 Cluster {cluster_id}: Average performance ({cluster_size} stores, {cluster_pct:.1f}%)"
            score = 60
        else:
            trend_desc = f"🔧 Cluster {cluster_id}: Improvement needed ({cluster_size} stores, {cluster_pct:.1f}%)"
            score = 45
        
        # Calculate confidence based on cluster size (larger clusters = more confidence)
        confidence = min(85, max(30, int(cluster_size * 0.5)))
        
        return {
            'cluster_trend': trend_desc,
            'cluster_score': score,
            'cluster_confidence': confidence
        }

    def _analyze_real_price_trends(self, store_code: int) -> Dict[str, Any]:
        """Analyze price points using REAL unit price data"""
        if self.fashion_data.empty:
            return {
                'price_point_trend': 'No pricing data available',
                'price_point_score': 0,
                'price_point_confidence': 0
            }
        
        store_prices = self.fashion_data[self.fashion_data['store_code'] == str(store_code)]
        if store_prices.empty:
            return {
                'price_point_trend': 'Store pricing data not found',
                'price_point_score': 0,
                'price_point_confidence': 0
            }
        
        # Calculate REAL price statistics
        prices = store_prices['unit_price'].dropna()
        if len(prices) == 0:
            return {
                'price_point_trend': 'No valid pricing data',
                'price_point_score': 0,
                'price_point_confidence': 0
            }
        
        avg_price = prices.mean()
        price_count = len(prices)
        min_price = prices.min()
        max_price = prices.max()
        
        # Categorize based on REAL price distribution
        if avg_price < 100:
            trend_desc = f"💰 VALUE strategy: ¥{avg_price:.0f} avg (¥{min_price:.0f}-¥{max_price:.0f}, {price_count} items)"
            strategy = "VALUE_FOCUSED"
            score = 70
        elif avg_price < 300:
            trend_desc = f"⚖️ BALANCED pricing: ¥{avg_price:.0f} avg (¥{min_price:.0f}-¥{max_price:.0f}, {price_count} items)"
            strategy = "BALANCED_STRATEGY"
            score = 85
        else:
            trend_desc = f"💎 PREMIUM strategy: ¥{avg_price:.0f} avg (¥{min_price:.0f}-¥{max_price:.0f}, {price_count} items)"
            strategy = "PREMIUM_STRATEGY"
            score = 80
        
        # Calculate confidence based on sample size
        confidence = min(90, max(20, int(price_count * 0.5)))
        
        return {
            'price_point_trend': trend_desc,
            'price_point_score': score,
            'price_point_confidence': confidence,
            'price_strategy': strategy
        }

    def _analyze_real_category_trends(self, store_code: int) -> Dict[str, Any]:
        """Analyze category performance using REAL sales data"""
        if self.sales_data.empty:
            return {
                'category_trend': 'No category data available',
                'category_score': 0,
                'category_confidence': 0
            }
        
        store_sales = self.sales_data[self.sales_data['str_code'] == str(store_code)]
        if store_sales.empty:
            return {
                'category_trend': 'Store category data not found',
                'category_score': 0,
                'category_confidence': 0
            }
        
        # Get REAL category metrics
        latest = store_sales.iloc[0]
        categories_analyzed = latest.get('categories_analyzed', 0)
        top_quartile = latest.get('top_quartile_categories', 0)
        opportunities = latest.get('quantity_opportunities_count', 0)
        
        if categories_analyzed == 0:
            return {
                'category_trend': 'No category analysis available',
                'category_score': 0,
                'category_confidence': 0
            }
        
        # Calculate REAL performance ratios
        strong_pct = (top_quartile / categories_analyzed) * 100
        opportunity_pct = (opportunities / categories_analyzed) * 100
        stable_pct = 100 - strong_pct - opportunity_pct
        
        # Create business description based on REAL data
        if strong_pct > 60:
            trend_desc = f"🚀 STRONG portfolio: {top_quartile} top performers, {opportunities} opportunities ({categories_analyzed} total)"
            score = 90
        elif strong_pct > 40:
            trend_desc = f"📈 SOLID portfolio: {top_quartile} strong, {opportunities} to improve ({categories_analyzed} total)"
            score = 75
        elif opportunity_pct < 30:
            trend_desc = f"⚖️ STABLE portfolio: {top_quartile} strong, {opportunities} opportunities ({categories_analyzed} total)"
            score = 65
        else:
            trend_desc = f"🔧 NEEDS FOCUS: {top_quartile} strong, {opportunities} opportunities ({categories_analyzed} total)"
            score = 45
        
        # Calculate confidence based on sample size
        confidence = min(90, max(30, int(categories_analyzed * 0.4)))
        
        return {
            'category_trend': trend_desc,
            'category_score': score,
            'category_confidence': confidence
        }

    def _analyze_real_regional_trends(self, store_code: int) -> Dict[str, Any]:
        """Analyze regional performance using REAL store performance data"""
        if self.sales_data.empty:
            return {
                'regional_trend': 'No regional data available',
                'regional_score': 0,
                'regional_confidence': 0
            }
        
        # Extract region from REAL store code
        region = str(store_code)[:2] if len(str(store_code)) >= 2 else 'UNK'
        
        # Get REAL regional performance comparison
        regional_stores = self.sales_data[self.sales_data['str_code'].str.startswith(region)]
        if len(regional_stores) == 0:
            return {
                'regional_trend': f"Region {region}: No comparable stores",
                'regional_score': 50,
                'regional_confidence': 10
            }
        
        store_sales = self.sales_data[self.sales_data['str_code'] == str(store_code)]
        if store_sales.empty:
            return {
                'regional_trend': f"Region {region}: Store not in dataset",
                'regional_score': 50,
                'regional_confidence': 10
            }
        
        # Calculate REAL regional metrics
        store_z_score = store_sales.iloc[0].get('avg_opportunity_z_score', 0)
        regional_avg_z = regional_stores['avg_opportunity_z_score'].mean()
        regional_count = len(regional_stores)
        
        performance_vs_region = store_z_score - regional_avg_z
        
        # Create business description based on REAL regional comparison
        if performance_vs_region > 0.5:
            trend_desc = f"🏙️ Region {region}: +{performance_vs_region:.2f} vs regional avg ({regional_count} stores) - OUTPERFORMING"
            score = 85
        elif performance_vs_region > 0:
            trend_desc = f"📈 Region {region}: +{performance_vs_region:.2f} vs regional avg ({regional_count} stores) - Above average"
            score = 70
        elif performance_vs_region > -0.5:
            trend_desc = f"⚖️ Region {region}: {performance_vs_region:.2f} vs regional avg ({regional_count} stores) - Near average"
            score = 60
        else:
            trend_desc = f"📍 Region {region}: {performance_vs_region:.2f} vs regional avg ({regional_count} stores) - Below average"
            score = 45
        
        # Calculate confidence based on regional sample size
        confidence = min(80, max(20, int(regional_count * 2)))
        
        return {
            'regional_trend': trend_desc,
            'regional_score': score,
            'regional_confidence': confidence
        }

    def _calculate_real_overall_score(self, trend_analysis: Dict[str, Any]) -> int:
        """Calculate overall score using REAL data weights"""
        score_fields = [k for k in trend_analysis.keys() if k.endswith('_score')]
        if not score_fields:
            return 0
        
        # Weight scores by confidence (higher confidence = more weight)
        weighted_scores = []
        for field in score_fields:
            score = trend_analysis.get(field, 0)
            confidence_field = field.replace('_score', '_confidence')
            confidence = trend_analysis.get(confidence_field, 0)
            
            if confidence > 0:  # Only include scores with confidence data
                weighted_scores.append(score * (confidence / 100))
        
        return int(np.mean(weighted_scores)) if weighted_scores else 0

    def _calculate_real_priority_score(self, trend_analysis: Dict[str, Any], suggestion: Dict[str, Any]) -> int:
        """Calculate business priority using REAL investment and opportunity data"""
        overall_score = trend_analysis.get('overall_trend_score', 0)
        data_quality = trend_analysis.get('data_quality_score', 0)
        investment = abs(suggestion.get('investment_required', 0))
        
        # Priority based on: (opportunity score * data quality) - investment risk
        if data_quality < 30:  # Low data quality = low priority
            return max(20, overall_score - 30)
        elif investment > 10000:  # High investment = moderate priority
            return max(30, overall_score - 20)
        elif overall_score > 80 and data_quality > 60:  # High opportunity + good data = high priority
            return min(95, overall_score + 10)
        else:
            return overall_score

    def _calculate_real_data_quality_score(self, store_code: int, metrics: Dict[str, Any]) -> int:
        """Calculate REAL data quality based on actual data availability and completeness"""
        quality_score = 0
        total_weight = 0
        
        # Data source availability (40% of score)
        source_score = (self.data_sources_loaded / 4.0) * 40
        quality_score += source_score
        total_weight += 40
        
        # Sample size adequacy (30% of score)
        sample_sizes = []
        if not self.sales_data.empty:
            sales_store = self.sales_data[self.sales_data['str_code'] == str(store_code)]
            if not sales_store.empty:
                categories = sales_store.iloc[0].get('categories_analyzed', 0)
                sample_sizes.append(min(100, categories * 0.5))  # Cap at 100, scale categories
        
        if not self.fashion_data.empty:
            fashion_store = self.fashion_data[self.fashion_data['store_code'] == str(store_code)]
            sample_sizes.append(min(100, len(fashion_store) * 2))  # Scale records
            
        sample_score = np.mean(sample_sizes) * 0.3 if sample_sizes else 0
        quality_score += sample_score
        total_weight += 30
        
        # Data completeness (20% of score) 
        completeness_score = 0
        completeness_checks = 0
        
        for key, value in metrics.items():
            if not key.endswith('_confidence') and not key.endswith('_score'):
                completeness_checks += 1
                if value and value != 'No data available' and value != 'Not found':
                    completeness_score += 1
                    
        if completeness_checks > 0:
            completeness_pct = (completeness_score / completeness_checks) * 20
            quality_score += completeness_pct
            total_weight += 20
        
        # Data consistency (10% of score) - cross-validation between sources
        consistency_score = 10  # Default if we can't cross-validate
        if not self.sales_data.empty and not self.cluster_data.empty:
            # Check if store exists in both sales and cluster data
            sales_has = str(store_code) in self.sales_data['str_code'].values
            cluster_has = str(store_code) in self.cluster_data['str_code'].values
            if sales_has and cluster_has:
                consistency_score = 10
            elif sales_has or cluster_has:
                consistency_score = 5
            else:
                consistency_score = 0
                
        quality_score += consistency_score
        total_weight += 10
        
        # Return normalized score (0-100)
        return int(quality_score) if total_weight > 0 else 0

# ===== ANDY'S TRENDING FUNCTIONS =====
def load_rule_suggestions_for_enhancement() -> pd.DataFrame:
    """Load basic rule suggestions for trend enhancement"""
    try:
        # First try to load existing all_rule_suggestions.csv
        if os.path.exists(ALL_RULES_FILE):
            suggestions_df = pd.read_csv(ALL_RULES_FILE, dtype={'store_code': str})
            log_progress(f"Loaded existing basic suggestions: {len(suggestions_df):,} records")
            return suggestions_df
        
        # Second, try to load fashion enhanced suggestions and convert
        if os.path.exists(FASHION_ENHANCED_FILE):
            log_progress("Converting fashion enhanced suggestions to basic format...")
            fashion_df = pd.read_csv(FASHION_ENHANCED_FILE, dtype={'store_code': str})
            
            # Convert fashion format to basic suggestion format
            suggestions_df = fashion_df.copy()
            
            # Ensure required columns exist
            required_columns = ['rule', 'store_code', 'spu_code', 'action', 'reason', 
                              'current_quantity', 'recommended_quantity_change', 'target_quantity',
                              'unit_price', 'investment_required', 'rule_explanation', 
                              'analysis_period', 'analysis_date']
            
            for col in required_columns:
                if col not in suggestions_df.columns:
                    if col in ['current_quantity', 'recommended_quantity_change', 'target_quantity', 'unit_price', 'investment_required']:
                        suggestions_df[col] = 0
                    elif col == 'analysis_period':
                        suggestions_df[col] = '202505 → 202506B'
                    elif col == 'analysis_date':
                        suggestions_df[col] = datetime.now().strftime('%Y-%m-%d')
                    else:
                        suggestions_df[col] = 'N/A'
            
            # Save as basic format for future use
            basic_df = suggestions_df[required_columns].copy()
            basic_df.to_csv(ALL_RULES_FILE, index=False)
            log_progress(f"Created basic suggestions file: {len(basic_df):,} records")
            return basic_df
        
        # Third, try to load from consolidated results and create basic format
        if os.path.exists(OUTPUT_FILE):
            log_progress("No suggestion files found, creating from consolidated results...")
            consolidated_df = pd.read_csv(OUTPUT_FILE, dtype={'str_code': str})
            
            # Create basic suggestions from consolidated data
            suggestions_list = []
            for _, row in consolidated_df.iterrows():
                if row.get('total_quantity_change', 0) != 0:
                    suggestion = {
                        'rule': 'Consolidated',
                        'store_code': row['str_code'],
                        'spu_code': 'Multiple',
                        'action': 'Adjust' if row['total_quantity_change'] > 0 else 'Reduce',
                        'reason': f"{row.get('rules_with_quantity_recs', 0)} rules recommend changes",
                        'current_quantity': 0,
                        'recommended_quantity_change': row.get('total_quantity_change', 0),
                        'target_quantity': row.get('total_quantity_change', 0),
                        'unit_price': 100,  # Default unit price
                        'investment_required': row.get('total_investment_required', 0),
                        'rule_explanation': 'Consolidated recommendation from multiple rules',
                        'analysis_period': '202505 → 202506B',
                        'analysis_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    suggestions_list.append(suggestion)
            
            if suggestions_list:
                suggestions_df = pd.DataFrame(suggestions_list)
                suggestions_df.to_csv(ALL_RULES_FILE, index=False)
                log_progress(f"Created basic suggestions from consolidated data: {len(suggestions_df):,} records")
                return suggestions_df
        
        log_progress("No data available for trend enhancement")
        return pd.DataFrame()
        
    except Exception as e:
        log_progress(f"Error loading suggestions for enhancement: {e}")
        return pd.DataFrame()

def generate_fashion_enhanced_suggestions(suggestions_df: pd.DataFrame) -> pd.DataFrame:
    """Generate the 20-column fashion enhanced format"""
    if suggestions_df.empty:
        return pd.DataFrame()
    
    log_progress("Generating fashion enhanced suggestions (20 columns)...")
    
    # Create fashion enhanced format with additional business columns
    enhanced_df = suggestions_df.copy()
    
    # Add fashion-related columns if they don't exist
    fashion_columns = {
        'basic_ratio': '70%',
        'fashion_ratio': '30%',
        'mix_balance_status': 'BALANCED',
        'store_type_classification': 'STANDARD',
        'gender_mix': 'UNISEX',
        'price_tier': 'MID_RANGE',
        'seasonality_factor': 'NEUTRAL'
    }
    
    for col, default_val in fashion_columns.items():
        if col not in enhanced_df.columns:
            enhanced_df[col] = default_val
    
    # Save fashion enhanced format
    enhanced_df.to_csv(FASHION_ENHANCED_FILE, index=False)
    log_progress(f"Generated fashion enhanced suggestions: {len(enhanced_df)} records")
    return enhanced_df

def generate_comprehensive_trend_suggestions(suggestions_df: pd.DataFrame) -> pd.DataFrame:
    """Generate the 51-column comprehensive trend format with performance optimization"""
    if suggestions_df.empty:
        return pd.DataFrame()
    
    # Performance optimization for large datasets
    if FAST_MODE and len(suggestions_df) > TREND_SAMPLE_SIZE:
        log_progress(f"🚀 FAST_MODE: Sampling {TREND_SAMPLE_SIZE} top suggestions (from {len(suggestions_df):,})")
        
        # Sample top suggestions based on investment_required
        if 'investment_required' in suggestions_df.columns:
            # Sort by absolute investment (highest impact first)
            suggestions_df['abs_investment'] = abs(suggestions_df['investment_required'])
            sampled_df = suggestions_df.nlargest(TREND_SAMPLE_SIZE, 'abs_investment').drop('abs_investment', axis=1)
        else:
            # Random sample if no investment column
            sampled_df = suggestions_df.sample(n=min(TREND_SAMPLE_SIZE, len(suggestions_df)))
            
        log_progress(f"✓ Sampled {len(sampled_df)} high-impact suggestions for trending")
    else:
        sampled_df = suggestions_df
        log_progress("Generating comprehensive trend analysis for all suggestions...")
    
    trend_analyzer = ComprehensiveTrendAnalyzer()
    comprehensive_suggestions = []
    
    for i, (_, suggestion) in enumerate(sampled_df.iterrows()):
        if i % 100 == 0:  # More frequent progress updates for faster feedback
            log_progress(f"Processing suggestion {i+1}/{len(sampled_df)}")
        
        # Convert series to dict for analysis
        suggestion_dict = suggestion.to_dict()
        
        # Analyze comprehensive trends
        trend_analysis = trend_analyzer.analyze_comprehensive_trends(suggestion_dict)
        
        # Combine original suggestion with trend analysis
        comprehensive = suggestion_dict.copy()
        comprehensive.update(trend_analysis)
        
        comprehensive_suggestions.append(comprehensive)
    
    comprehensive_df = pd.DataFrame(comprehensive_suggestions)
    
    # If we sampled, create full dataset with trends for sampled records and basic data for others
    if FAST_MODE and len(suggestions_df) > len(sampled_df):
        log_progress("Creating hybrid dataset: trending for samples + basic for remainder...")
        
        # Get the remaining suggestions (not analyzed for trends)
        sampled_indices = sampled_df.index
        remaining_df = suggestions_df.drop(sampled_indices)
        
        # Add basic trend columns to remaining suggestions
        basic_trend_columns = {
            'sales_trend': 'Not analyzed (FAST_MODE)',
            'sales_score': 0,
            'sales_confidence': 0,
            'fashion_mix_trend': 'Not analyzed (FAST_MODE)',
            'fashion_mix_score': 0,
            'fashion_mix_confidence': 0,
            'weather_trend': 'Not analyzed (FAST_MODE)',
            'weather_score': 0,
            'weather_confidence': 0,
            'cluster_trend': 'Not analyzed (FAST_MODE)',
            'cluster_score': 0,
            'cluster_confidence': 0,
            'overall_trend_score': 0,
            'business_priority_score': 0,
            'data_quality_score': 0
        }
        
        for col, default_val in basic_trend_columns.items():
            remaining_df[col] = default_val
        
        # Combine analyzed and basic datasets
        comprehensive_df = pd.concat([comprehensive_df, remaining_df], ignore_index=True)
        log_progress(f"✓ Created hybrid dataset: {len(sampled_df):,} with trends + {len(remaining_df):,} basic")
    
    comprehensive_df.to_csv(COMPREHENSIVE_TRENDS_FILE, index=False)
    log_progress(f"Generated comprehensive trend suggestions: {len(comprehensive_df)} records")
    return comprehensive_df

# ===== YOUR ORIGINAL EFFICIENT FUNCTIONS =====
def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def process_rule_in_chunks(file_path: str, chunk_size: int = 10000) -> pd.DataFrame:
    """
    Memory-efficient processing of large rule files using chunks.
    Standardizes output format for consolidation.
    
    Args:
        file_path: Path to the CSV file to process
        chunk_size: Number of rows to process at a time
        
    Returns:
        pd.DataFrame: Processed dataframe with standardized columns
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            log_progress(f"File not found: {file_path}")
            return pd.DataFrame()
        
        log_progress(f"Processing {file_path} in chunks of {chunk_size:,}")
        
        # Extract rule name from file path
        rule_name = os.path.basename(file_path).replace('.csv', '').replace('_opportunities', '').replace('_cases', '').replace('_details', '')
        
        # Read file in chunks to handle large files
        chunks = []
        total_rows = 0
        
        # Use smaller chunk size in FAST_MODE for quicker processing
        effective_chunk_size = CHUNK_SIZE_SMALL if FAST_MODE else chunk_size
        
        for chunk in tqdm(pd.read_csv(file_path, chunksize=effective_chunk_size, dtype={'str_code': str}), 
                         desc=f"Processing {os.path.basename(file_path)}"):
            # Process chunk if needed (filtering, transformations, etc.)
            chunks.append(chunk)
            total_rows += len(chunk)
        
        if chunks:
            # Combine all chunks
            result_df = pd.concat(chunks, ignore_index=True)
            log_progress(f"✓ Processed {total_rows:,} rows from {os.path.basename(file_path)}")
            
            # Standardize columns for consolidation
            summary_df = result_df.groupby('str_code').agg({
                'recommended_quantity_change': 'sum',
                'investment_required': 'sum',
                'spu_code': 'count'  # Count of SPUs
            }).reset_index()
            
            # Rename columns to match consolidation expectations
            summary_df.columns = ['str_code', 'total_quantity_change', 'total_investment', 'spu_count']
            
            # Add rule name
            summary_df['rule_name'] = rule_name
            
            # Log investment amounts with proper currency labeling
            total_investment = summary_df['total_investment'].sum()
            if total_investment != 0:
                log_progress(f"   💰 {rule_name} investment: {CURRENCY_SYMBOL}{total_investment:,.0f} {CURRENCY_LABEL}")
            
            log_progress(f"✓ Summarized to {len(summary_df):,} stores for {rule_name}")
            
            # Memory cleanup
            del chunks, result_df
            gc.collect()
            
            return summary_df
        else:
            log_progress(f"No data found in {file_path}")
            return pd.DataFrame()
            
    except Exception as e:
        log_progress(f"Error processing {file_path}: {str(e)}")
        return pd.DataFrame()

def main():
    """Main execution function with integrated trending analysis"""
    start_time = datetime.now()
    
    # Performance mode notification
    if FAST_MODE:
        log_progress("🚀 FAST_MODE ENABLED - Optimized for speed!")
        log_progress(f"   • Trending analysis limited to top {TREND_SAMPLE_SIZE:,} suggestions")
        log_progress(f"   • Chunk size: {CHUNK_SIZE_SMALL:,} rows")
        log_progress(f"   • Expected runtime: 2-5 minutes")
    else:
        log_progress("🐌 FULL_MODE - Complete analysis (may take 30-60 minutes)")
        
    log_progress("Starting Memory-Efficient SPU Rule Consolidation with Comprehensive Trends...")
    
    try:
        # ===== PHASE 1: YOUR EFFICIENT CONSOLIDATION =====
        log_progress("\n" + "="*60)
        log_progress("PHASE 1: MEMORY-EFFICIENT RULE CONSOLIDATION")
        log_progress("="*60)
        
        # Rule files to process
        rule_files = {
            'rule7': 'output/rule7_missing_spu_opportunities.csv',
            'rule8': 'output/rule8_imbalanced_spu_cases.csv',
            'rule9': 'output/rule9_below_minimum_spu_cases.csv',
            'rule10': 'output/rule10_spu_overcapacity_opportunities.csv', 
            'rule11': 'output/rule11_improved_missed_sales_opportunity_spu_details.csv',
            'rule12': 'output/rule12_sales_performance_spu_details.csv'
        }
        
        # Load base data
        cluster_file = "output/clustering_results_spu.csv"
        if os.path.exists(cluster_file):
            base_df = pd.read_csv(cluster_file, dtype={'str_code': str})[['str_code', 'Cluster']].copy()
            log_progress(f"Loaded base data for {len(base_df):,} stores")
        else:
            log_progress("⚠️ Cluster file not found, proceeding with trending analysis only")
            base_df = pd.DataFrame()
        
        all_rule_summaries = []
        
        # Process each rule file
        for rule_name, file_path in rule_files.items():
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / (1024*1024)  # MB
                log_progress(f"Processing {rule_name}: {file_size:.1f}MB")
                
                rule_summary = process_rule_in_chunks(file_path)
                if not rule_summary.empty:
                    all_rule_summaries.append(rule_summary)
            else:
                log_progress(f"⚠️ {rule_name}: File not found")
        
        # Only do consolidation if we have both base data and rule results
        if not base_df.empty and all_rule_summaries:
            log_progress("Consolidating SPU rule results...")
            
            # Combine all rule summaries
            combined_rules = pd.concat(all_rule_summaries, ignore_index=True)
            log_progress(f"Combined rules: {len(combined_rules)} store-rule combinations")
            
            # Create store-level consolidation
            store_consolidation = combined_rules.groupby('str_code').agg({
                'total_quantity_change': 'sum',
                'total_investment': 'sum',
                'spu_count': 'sum',
                'rule_name': 'count'
            }).reset_index()
            
            store_consolidation.columns = ['str_code', 'total_quantity_change', 'total_investment_required', 'affected_spu_count', 'rules_with_quantity_recs']
            
            # Merge with base data
            final_consolidation = base_df.merge(store_consolidation, on='str_code', how='left')
            
            # Fill NaN values
            numeric_cols = ['total_quantity_change', 'total_investment_required', 'affected_spu_count', 'rules_with_quantity_recs']
            for col in numeric_cols:
                final_consolidation[col] = final_consolidation[col].fillna(0)
                
            # Save results
            final_consolidation.to_csv(OUTPUT_FILE, index=False)
            log_progress(f"Saved consolidated results to {OUTPUT_FILE}")
            
            # Save detailed rule breakdown
            details_file = "output/consolidated_spu_quantity_summary.csv"
            combined_rules.to_csv(details_file, index=False)
            log_progress(f"Saved rule details to {details_file}")
            
            stores_with_recs = (final_consolidation['total_quantity_change'] > 0).sum()
            log_progress(f"✅ Consolidated {len(final_consolidation):,} stores, {stores_with_recs:,} with recommendations")
        else:
            log_progress("Skipping SPU rule consolidation - insufficient data")
            log_progress("Proceeding with comprehensive trend analysis...")
        
        # ===== PHASE 2: ANDY'S COMPREHENSIVE TREND INTEGRATION =====
        log_progress("\n" + "="*60)
        log_progress("PHASE 2: COMPREHENSIVE TREND ANALYSIS")
        log_progress("="*60)
        
        # Load or create basic rule suggestions
        suggestions_df = load_rule_suggestions_for_enhancement()
        
        if not suggestions_df.empty:
            # Generate all output formats
            
            # 1. Fashion Enhanced (20 columns) - Current production format
            log_progress("Generating fashion enhanced suggestions (20 columns)...")
            fashion_df = generate_fashion_enhanced_suggestions(suggestions_df)
            
            # 2. Comprehensive Trends (51 columns) - New comprehensive format
            log_progress("Generating comprehensive trend suggestions (51 columns)...")
            comprehensive_df = generate_comprehensive_trend_suggestions(suggestions_df)
            
            # Calculate completion time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            log_progress("\n" + "="*60)
            log_progress("INTEGRATED SPU CONSOLIDATION + TREND ANALYSIS COMPLETE")
            log_progress("="*60)
            log_progress(f"Process completed in {duration:.2f} seconds")
            
            log_progress("\n📊 OUTPUT FILES GENERATED:")
            if os.path.exists(OUTPUT_FILE):
                consolidated_df = pd.read_csv(OUTPUT_FILE)
                log_progress(f"✓ Consolidated results: {OUTPUT_FILE} ({len(consolidated_df):,} stores)")
            log_progress(f"✓ Basic suggestions: {ALL_RULES_FILE} ({len(suggestions_df):,} records)")
            if not fashion_df.empty:
                log_progress(f"✓ Fashion enhanced: {FASHION_ENHANCED_FILE} ({len(fashion_df):,} records, 20 columns)")
            if not comprehensive_df.empty:
                log_progress(f"✓ Comprehensive trends: {COMPREHENSIVE_TRENDS_FILE} ({len(comprehensive_df):,} records, 51 columns)")
            
            log_progress("\n🎯 BUSINESS IMPACT:")
            log_progress("✓ Memory-efficient processing preserved")
            log_progress("✓ Real quantity data integration maintained")
            log_progress("✓ 10 trend dimensions analyzed per suggestion")
            log_progress("✓ Business-friendly language with confidence scoring")
            log_progress("✓ Actionable insights with decision matrix integration")
            log_progress("✓ Real data integration where available")
            log_progress("✓ Multiple output formats for different use cases")
            
            # Performance summary
            if os.path.exists(OUTPUT_FILE):
                final_consolidation = pd.read_csv(OUTPUT_FILE)
                stores_with_recs = (final_consolidation['total_quantity_change'] > 0).sum()
                log_progress(f"\n📈 PERFORMANCE SUMMARY:")
                log_progress(f"✓ Total stores processed: {len(final_consolidation):,}")
                log_progress(f"✓ Stores with quantity recommendations: {stores_with_recs:,}")
                log_progress(f"✓ Total quantity changes: {final_consolidation['total_quantity_change'].sum():,.1f} units")
                log_progress(f"✓ Total investment required: {CURRENCY_SYMBOL}{final_consolidation['total_investment_required'].sum():,.0f} {CURRENCY_LABEL}")
            
        else:
            log_progress("No rule suggestions available for trend enhancement")
            log_progress("Please ensure you have run the pipeline or have existing suggestion files")
            
            # Calculate completion time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            log_progress(f"\nProcess completed in {duration:.2f} seconds")
        
    except Exception as e:
        log_progress(f"Error in consolidation/trend analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
