import pandas as pd
"""
Modular Schema Package

This package contains modular validation schemas organized by domain:
- time: Time-related schemas
- weather: Weather and meteorological schemas  
- product: Product and sales schemas
- common: Common reusable schemas

Author: Data Pipeline
Date: 2025-01-03
"""

# Import all schemas for easy access
from .time_schemas import *
from .product_schemas import *
from .common_schemas import *
from .pipeline_schemas import *

# Import from new modular weather schemas
from .weather import *
from .geographic import *
from .seasonal import *
from .matrix import *
from .clustering import *
from .pipeline import *

# Import step-specific schemas
from .pipeline.step10_step12_schemas import SPUAssortmentOptimizationSchema, SalesPerformanceRuleSchema
from .step5_schemas import *
from .step6_schemas import *
from .step7_schemas import *
from .step8_schemas import *
from .step9_schemas import *
from .step10_schemas import *
from .step11_schemas import *
from .step12_schemas import *
from .step13_schemas import *
from .step14_schemas import *
from .step15_schemas import *
from .step36_schemas import *

# Import advanced schemas for steps 15-36
from .advanced_schemas import *

__all__ = [
    # Time schemas
    'TimeSeriesSchema', 'PeriodSchema', 'DateRangeSchema',
    
    # Weather schemas
    'WeatherDataSchema', 'WeatherMetricsSchema', 'RadiationSchema',
    'TemperatureSchema', 'PrecipitationSchema', 'WindSchema',
    'HumiditySchema', 'PressureSchema', 'VisibilitySchema',
    'StoreAltitudeSchema', 'WeatherExtremesSchema',
    
    # Step 5 schemas
    'WeatherDataSchema', 'StoreAltitudeSchema', 'FeelsLikeTemperatureSchema', 'TemperatureBandsSchema', 
    'FeelsLikeCalculationSchema', 'Step5InputSchema', 'Step5OutputSchema', 'Step5ValidationSchema',
    
    # Step 2 schemas
    'StoreCoordinatesSchema', 'SPUStoreMappingSchema', 'SPUMetadataSchema',
    
    # Step 2B schemas
    'SeasonalStoreProfilesSchema', 'SeasonalCategoryPatternsSchema', 'SeasonalClusteringFeaturesSchema',
    
    # Step 3 schemas
    'StoreMatrixSchema', 'SubcategoryMatrixSchema', 'SPUMatrixSchema', 'CategoryAggregatedMatrixSchema',
    
    # Step 6 schemas
    'ClusteringInputSchema', 'ClusteringResultsSchema', 'ClusterProfilesSchema', 'PerClusterMetricsSchema',
    'ClusteringParametersSchema', 'MatrixValidationSchema', 'Step6InputSchema', 'Step6OutputSchema', 
    'Step6ValidationSchema', 'ClusteringVisualizationSchema',
    
    # Pipeline schemas (Steps 6-14)
    'MissingSPURuleSchema', 'ImbalancedSPURuleSchema', 'BelowMinimumRuleSchema',
    'BelowMinimumOpportunitiesSchema', 'BelowMinimumSubcategorySchema', 'MissedSalesOpportunitySchema',
    'ConsolidatedSPURulesSchema', 'FastFishFormatSchema', 'ClusterStyleVarietySchema',
    'ClusterSubcategoryVarietySchema', 'TopPerformersByClusterSchema',
    'SPUAssortmentOptimizationSchema', 'SalesPerformanceRuleSchema',
    
    # Step 7 schemas
    'Step7ClusteringInputSchema',
    'Step7SPUSalesInputSchema',
    'Step7CategorySalesInputSchema',
    'Step7QuantityInputSchema',
    'Step7StoreResultsSchema',
    'Step7OpportunitiesSchema',
    'Step7SubcategoryOpportunitiesSchema',
    'Step7BusinessLogicSchema',
    'Step7PeriodFlexibleSchema',
    
    # Step 8 schemas
    'Step8ResultsSchema',
    'Step8CasesSchema',
    'Step8ZScoreAnalysisSchema',
    'Step8InputClusteringSchema',
    'Step8InputStoreConfigSchema',
    'Step8InputQuantitySchema',
    
    # Step 9 schemas
    'Step9ResultsSchema',
    'Step9OpportunitiesSchema',
    'Step9SummarySchema',
    'Step9InputClusteringSchema',
    'Step9InputStoreConfigSchema',
    'Step9InputQuantitySchema',
    
    # Step 10 schemas
    'Step10ResultsSchema',
    'Step10OpportunitiesSchema',
    'Step10InputClusteringSchema',
    'Step10InputStoreConfigSchema',
    'Step10InputQuantitySchema',
    
    # Step 11 schemas
    'Step11ResultsSchema',
    'Step11DetailsSchema',
    'Step11TopPerformersSchema',
    'Step11InputClusteringSchema',
    'Step11InputQuantitySchema',
    
    # Step 12 schemas
    'Step12ResultsSchema',
    'Step12DetailsSchema',
    'Step12InputClusteringSchema',
    'Step12InputStoreConfigSchema',
    'Step12InputQuantitySchema',
    
    # Step 13 schemas
    'StoreLevelResultsSchema', 'DetailedSPUResultsSchema', 'ClusterSubcategoryResultsSchema',
    'SeasonalFeaturesSchema', 'InputRuleResultsSchema', 'CommonColumns as Step13CommonColumns',
    
    # Step 14 schemas
    'FastFishFormatSchema', 'FastFishValidationSchema', 'FastFishMismatchSchema',
    'InputConsolidatedResultsSchema', 'InputClusterMappingSchema', 'CommonColumns as Step14CommonColumns',
    
    # Step 15 schemas
    'HistoricalBaselineSchema', 'HistoricalInsightsSchema', 'BaselineComparisonSchema',
    'Step15InputSchema', 'Step15OutputSchema', 'Step15ValidationSchema', 'HistoricalDataQualitySchema',
    
    # Step 36 schemas
    'UnifiedDeliverySchema', 'DeliveryContentSchema', 'DeliveryMetadataSchema',
    'Step36InputSchema', 'Step36OutputSchema', 'Step36ValidationSchema', 'DeliveryQualitySchema',
    
    # Product schemas
    'StoreConfigSchema', 'CategorySalesSchema', 'SPUSalesSchema',
    'StoreCodeSchema', 'ProductClassificationSchema',
    
    # Common schemas
    'GeographicSchema', 'SalesAmountSchema', 'QuantitySchema',
    'PriceSchema', 'CountSchema', 'CategoricalSchema',
    'SPUCodeSchema', 'SubcategorySchema', 'ClusterIdSchema',
    
    # Advanced schemas (Steps 15-36)
    'HistoricalBaselineSchema', 'HistoricalInsightsSchema',
    'ComparisonTableSchema', 'ComparisonMetricsSchema',
    'AugmentedRecommendationSchema', 'RecommendationMetadataSchema',
    'ValidationSummarySchema', 'ValidationDetailsSchema',
    'DetailedSPUBreakdownSchema', 'SPUPerformanceMetricsSchema',
    'DataQualityMetricsSchema', 'DataValidationErrorsSchema',
    'LabelTagRecommendationSchema', 'StoreAttributeEnrichmentSchema',
    'ClusteringFeaturesSchema', 'ComprehensiveClusterLabelsSchema',
    'ProductRoleClassifierSchema', 'PriceElasticityAnalysisSchema',
    'GapMatrixSchema', 'ScenarioAnalysisSchema', 'SupplyDemandGapSchema',
    'SellthroughOptimizationSchema', 'GapAnalysisWorkbookSchema',
    'EnhancedStoreClusteringSchema', 'StoreAllocationSchema',
    'StoreLevelMerchandisingSchema', 'ClusterLevelMerchandisingSchema',
    'UnifiedDeliverySchema', 'CustomerDeliveryFormatSchema',
    'DashboardDataSchema', 'InteractiveMapDataSchema'
]
