import pandas as pd
#!/usr/bin/env python3
"""
Comprehensive Validation Schemas

This module contains comprehensive validation schemas generated from EDA analysis
across multiple time periods. These schemas are more robust and data-driven than
static schemas.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series, DataFrame
from typing import Optional, Dict, Any, List
import json
import os
from pathlib import Path

class ComprehensiveSchemaGenerator:
    """
    Generates comprehensive validation schemas based on EDA insights.
    """
    
    def __init__(self, eda_results_path: str = "output/eda_reports/comprehensive_analysis_results.json"):
        self.eda_results_path = eda_results_path
        self.eda_results = self._load_eda_results()
        self.schemas = {}
        
    def _load_eda_results(self) -> Dict[str, Any]:
        """Load EDA analysis results."""
        if os.path.exists(self.eda_results_path):
            with open(self.eda_results_path, 'r') as f:
                return json.load(f)
        return {}
    
    def generate_store_config_schema(self) -> pa.DataFrameModel:
        """Generate comprehensive store config schema based on EDA."""
        constraints = self._get_merged_constraints('store_config')
        
        class ComprehensiveStoreConfigSchema(pa.DataFrameModel):
            """Comprehensive store configuration schema based on EDA analysis."""
            
            # Core identifiers
            str_code: Series[pa.String] = pa.Field(
                coerce=True,
                description="Store code identifier",
                **constraints.get('str_code', {})
            )
            
            # Store information
            str_name: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Store name",
                **constraints.get('str_name', {})
            )
            
            # Geographic information
            latitude: Series[pa.Float64] = pa.Field(
                coerce=True,
                nullable=True,
                ge=-90,
                le=90,
                description="Store latitude",
                **constraints.get('latitude', {})
            )
            
            longitude: Series[pa.Float64] = pa.Field(
                coerce=True,
                nullable=True,
                ge=-180,
                le=180,
                description="Store longitude",
                **constraints.get('longitude', {})
            )
            
            # Product information
            season_name: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Season name",
                **constraints.get('season_name', {})
            )
            
            sex_name: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Sex category",
                **constraints.get('sex_name', {})
            )
            
            display_location_name: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Display location",
                **constraints.get('display_location_name', {})
            )
            
            big_class_name: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Big class category",
                **constraints.get('big_class_name', {})
            )
            
            sub_cate_name: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Subcategory name",
                **constraints.get('sub_cate_name', {})
            )
            
            # Time information
            yyyy: Series[pa.Int64] = pa.Field(
                coerce=True,
                ge=2020,
                le=2030,
                description="Year",
                **constraints.get('yyyy', {})
            )
            
            mm: Series[pa.Int64] = pa.Field(
                coerce=True,
                ge=1,
                le=12,
                description="Month",
                **constraints.get('mm', {})
            )
            
            mm_type: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Month type",
                **constraints.get('mm_type', {})
            )
            
            # Sales information
            sal_amt: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Sales amount",
                **constraints.get('sal_amt', {})
            )
            
            # Style information
            ext_sty_cnt_avg: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="External style count average",
                **constraints.get('ext_sty_cnt_avg', {})
            )
            
            target_sty_cnt_avg: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Target style count average",
                **constraints.get('target_sty_cnt_avg', {})
            )
            
            # JSON data (flexible validation)
            sty_sal_amt: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Style sales amount JSON",
                **constraints.get('sty_sal_amt', {})
            )
        
        return ComprehensiveStoreConfigSchema
    
    def generate_spu_sales_schema(self) -> pa.DataFrameModel:
        """Generate comprehensive SPU sales schema based on EDA."""
        constraints = self._get_merged_constraints('spu_sales')
        
        class ComprehensiveSPUSalesSchema(pa.DataFrameModel):
            """Comprehensive SPU sales schema based on EDA analysis."""
            
            # Core identifiers
            str_code: Series[pa.String] = pa.Field(
                coerce=True,
                description="Store code identifier",
                **constraints.get('str_code', {})
            )
            
            spu_code: Series[pa.String] = pa.Field(
                coerce=True,
                description="SPU code identifier",
                **constraints.get('spu_code', {})
            )
            
            # Sales information
            spu_sales_amt: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="SPU sales amount",
                **constraints.get('spu_sales_amt', {})
            )
            
            # Quantity information
            base_sal_qty: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Base sales quantity",
                **constraints.get('base_sal_qty', {})
            )
            
            fashion_sal_qty: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Fashion sales quantity",
                **constraints.get('fashion_sal_qty', {})
            )
            
            sal_qty: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Total sales quantity",
                **constraints.get('sal_qty', {})
            )
            
            quantity: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Quantity",
                **constraints.get('quantity', {})
            )
            
            # Price information
            unit_price: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Unit price",
                **constraints.get('unit_price', {})
            )
            
            # Margin information
            margin_rate: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                le=1,
                nullable=True,
                description="Margin rate",
                **constraints.get('margin_rate', {})
            )
        
        return ComprehensiveSPUSalesSchema
    
    def generate_weather_schema(self) -> pa.DataFrameModel:
        """Generate comprehensive weather schema based on EDA."""
        constraints = self._get_merged_constraints('weather')
        
        class ComprehensiveWeatherSchema(pa.DataFrameModel):
            """Comprehensive weather schema based on EDA analysis."""
            
            # Core identifiers
            str_code: Series[pa.String] = pa.Field(
                coerce=True,
                description="Store code identifier",
                **constraints.get('str_code', {})
            )
            
            # Time information
            date: Series[pa.String] = pa.Field(
                coerce=True,
                description="Date",
                **constraints.get('date', {})
            )
            
            # Temperature information
            temperature: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=-50,
                le=60,
                nullable=True,
                description="Temperature in Celsius",
                **constraints.get('temperature', {})
            )
            
            feels_like: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=-50,
                le=60,
                nullable=True,
                description="Feels like temperature",
                **constraints.get('feels_like', {})
            )
            
            # Precipitation information
            precipitation: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Precipitation amount",
                **constraints.get('precipitation', {})
            )
            
            # Wind information
            wind_speed: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Wind speed",
                **constraints.get('wind_speed', {})
            )
            
            wind_direction: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                le=360,
                nullable=True,
                description="Wind direction in degrees",
                **constraints.get('wind_direction', {})
            )
            
            # Humidity information
            humidity: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                le=100,
                nullable=True,
                description="Humidity percentage",
                **constraints.get('humidity', {})
            )
            
            # Pressure information
            pressure: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=800,
                le=1100,
                nullable=True,
                description="Atmospheric pressure",
                **constraints.get('pressure', {})
            )
            
            # Visibility information
            visibility: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Visibility distance",
                **constraints.get('visibility', {})
            )
            
            # UV index
            uv_index: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                le=15,
                nullable=True,
                description="UV index",
                **constraints.get('uv_index', {})
            )
        
        return ComprehensiveWeatherSchema
    
    def generate_clustering_schema(self) -> pa.DataFrameModel:
        """Generate comprehensive clustering schema based on EDA."""
        constraints = self._get_merged_constraints('clustering')
        
        class ComprehensiveClusteringSchema(pa.DataFrameModel):
            """Comprehensive clustering schema based on EDA analysis."""
            
            # Core identifiers
            str_code: Series[pa.String] = pa.Field(
                coerce=True,
                description="Store code identifier",
                **constraints.get('str_code', {})
            )
            
            # Cluster information
            cluster_id: Series[pa.Int64] = pa.Field(
                coerce=True,
                ge=0,
                description="Cluster ID",
                **constraints.get('cluster_id', {})
            )
            
            Cluster: Series[pa.Int64] = pa.Field(
                coerce=True,
                ge=0,
                description="Cluster ID (legacy)",
                **constraints.get('Cluster', {})
            )
            
            # Geographic information
            latitude: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=-90,
                le=90,
                nullable=True,
                description="Store latitude",
                **constraints.get('latitude', {})
            )
            
            longitude: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=-180,
                le=180,
                nullable=True,
                description="Store longitude",
                **constraints.get('longitude', {})
            )
            
            # Clustering metrics
            silhouette_score: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=-1,
                le=1,
                nullable=True,
                description="Silhouette score",
                **constraints.get('silhouette_score', {})
            )
            
            # Store attributes
            store_size: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                nullable=True,
                description="Store size",
                **constraints.get('store_size', {})
            )
            
            store_type: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Store type",
                **constraints.get('store_type', {})
            )
        
        return ComprehensiveClusteringSchema
    
    def generate_matrix_schema(self) -> pa.DataFrameModel:
        """Generate comprehensive matrix schema based on EDA."""
        constraints = self._get_merged_constraints('matrix')
        
        class ComprehensiveMatrixSchema(pa.DataFrameModel):
            """Comprehensive matrix schema based on EDA analysis."""
            
            # Core identifiers
            str_code: Series[pa.String] = pa.Field(
                coerce=True,
                description="Store code identifier",
                **constraints.get('str_code', {})
            )
            
            # Matrix values (flexible for different matrix types)
            matrix_values: Series[pa.Float64] = pa.Field(
                coerce=True,
                ge=0,
                description="Matrix values",
                **constraints.get('matrix_values', {})
            )
            
            # Category information
            category: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Category",
                **constraints.get('category', {})
            )
            
            subcategory: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="Subcategory",
                **constraints.get('subcategory', {})
            )
            
            spu_code: Series[pa.String] = pa.Field(
                coerce=True,
                nullable=True,
                description="SPU code",
                **constraints.get('spu_code', {})
            )
        
        return ComprehensiveMatrixSchema
    
    def _get_merged_constraints(self, file_type: str) -> Dict[str, Dict[str, Any]]:
        """Get merged constraints for a specific file type."""
        if not self.eda_results or 'schemas' not in self.eda_results:
            return {}
        
        schemas = self.eda_results['schemas']
        if file_type not in schemas:
            return {}
        
        return schemas[file_type].get('constraints', {})
    
    def generate_all_schemas(self) -> Dict[str, pa.DataFrameModel]:
        """Generate all comprehensive schemas."""
        schemas = {
            'store_config': self.generate_store_config_schema(),
            'spu_sales': self.generate_spu_sales_schema(),
            'weather': self.generate_weather_schema(),
            'clustering': self.generate_clustering_schema(),
            'matrix': self.generate_matrix_schema()
        }
        
        self.schemas = schemas
        return schemas


# Export schema generator
__all__ = [
    'ComprehensiveSchemaGenerator'
]

# Lazy schema generation - schemas will be created when needed
def get_comprehensive_store_config_schema():
    """Get comprehensive store config schema."""
    generator = ComprehensiveSchemaGenerator()
    return generator.generate_store_config_schema()

def get_comprehensive_spu_sales_schema():
    """Get comprehensive SPU sales schema."""
    generator = ComprehensiveSchemaGenerator()
    return generator.generate_spu_sales_schema()

def get_comprehensive_weather_schema():
    """Get comprehensive weather schema."""
    generator = ComprehensiveSchemaGenerator()
    return generator.generate_weather_schema()

def get_comprehensive_clustering_schema():
    """Get comprehensive clustering schema."""
    generator = ComprehensiveSchemaGenerator()
    return generator.generate_clustering_schema()

def get_comprehensive_matrix_schema():
    """Get comprehensive matrix schema."""
    generator = ComprehensiveSchemaGenerator()
    return generator.generate_matrix_schema()
