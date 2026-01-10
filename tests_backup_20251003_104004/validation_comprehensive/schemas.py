#!/usr/bin/env python3
"""
Comprehensive Validation Schemas - Main Module

This module imports and re-exports all validation schemas from the modular schema package.
This maintains backward compatibility while providing a comprehensive, organized structure.

Author: Data Pipeline
Date: 2025-01-03
"""

# Import all schemas from the modular package
from .schemas import *

# Re-export for backward compatibility
__all__ = [
    # Time schemas
    'TimeSeriesSchema', 'PeriodSchema', 'DateRangeSchema',
    
    # Weather schemas
    'WeatherDataSchema', 'WeatherMetricsSchema', 'RadiationSchema',
    'TemperatureSchema', 'PrecipitationSchema', 'WindSchema',
    'HumiditySchema', 'PressureSchema', 'VisibilitySchema',
    'StoreAltitudeSchema', 'WeatherExtremesSchema',
    
        # Step 5 schemas
    'FeelsLikeTemperatureSchema', 'TemperatureBandsSchema', 'FeelsLikeCalculationSchema',

    # Step 2 schemas
    'StoreCoordinatesSchema', 'SPUStoreMappingSchema', 'SPUMetadataSchema',

    # Step 2B schemas
    'SeasonalStoreProfilesSchema', 'SeasonalCategoryPatternsSchema', 'SeasonalClusteringFeaturesSchema',

    # Step 3 schemas
    'StoreMatrixSchema', 'SubcategoryMatrixSchema', 'SPUMatrixSchema', 'CategoryAggregatedMatrixSchema',

    # Step 6 schemas
    'ClusteringResultsSchema', 'ClusterProfilesSchema', 'PerClusterMetricsSchema',

    # Product schemas
    'StoreConfigSchema', 'CategorySalesSchema', 'SPUSalesSchema',
    'StoreCodeSchema', 'ProductClassificationSchema',
    'SalesSummarySchema', 'InventorySchema',

    # Common schemas
    'GeographicSchema', 'SalesAmountSchema', 'QuantitySchema',
    'PriceSchema', 'CountSchema', 'CategoricalSchema'
]
