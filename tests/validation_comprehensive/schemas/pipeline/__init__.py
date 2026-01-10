import pandas as pd
#!/usr/bin/env python3
"""
Pipeline Schema Package

This package contains pipeline-specific validation schemas organized by pipeline step.

Author: Data Pipeline
Date: 2025-01-03
"""

# Import all pipeline schemas for easy access
from .step6_clustering_schemas import (
    ClusterProfilesSchema,
    ClusteringResultsSchema,
    PerClusterMetricsSchema
)

from .step7_missing_spu_schemas import (
    MissingSPURuleSchema
)

from .step8_imbalanced_spu_schemas import (
    ImbalancedSPURuleSchema
)

from .step9_below_minimum_schemas import (
    BelowMinimumRuleSchema,
    BelowMinimumOpportunitiesSchema,
    BelowMinimumSubcategorySchema
)

from .step11_missed_sales_schemas import (
    MissedSalesOpportunitySchema
)

from .step13_consolidated_rules_schemas import (
    ConsolidatedSPURulesSchema
)

from .step14_fast_fish_schemas import (
    FastFishFormatSchema
)

from .step15_historical_baseline_schemas import (
    HistoricalBaselineSchema,
    HistoricalSPUCountSchema,
    HistoricalSalesPerformanceSchema
)

from .step16_comparison_tables_schemas import (
    ComparisonTableSchema,
    StoreGroupComparisonSchema,
    CategoryComparisonSchema
)

from .step17_augment_recommendations_schemas import (
    AugmentedRecommendationsSchema,
    RecommendationEnhancementSchema,
    MarketAnalysisSchema
)

from .step18_validate_results_schemas import (
    ValidationResultsSchema,
    DataQualityReportSchema,
    BusinessLogicValidationSchema
)

from .step19_detailed_spu_breakdown_schemas import (
    DetailedSPUBreakdownSchema,
    SPUPerformanceAnalysisSchema,
    StoreSPUAnalysisSchema
)

from .step20_data_validation_schemas import (
    DataValidationReportSchema,
    DataQualityIssueSchema,
    ValidationRuleSchema
)

from .step21_label_tag_recommendations_schemas import (
    LabelTagRecommendationsSchema,
    TagAnalysisSchema,
    TagRecommendationEngineSchema
)

from .step22_store_attribute_enrichment_schemas import (
    StoreAttributeEnrichmentSchema,
    StoreDemographicAnalysisSchema,
    StorePerformanceEnrichmentSchema
)

from .step23_update_clustering_features_schemas import (
    ClusteringFeaturesUpdateSchema,
    ClusteringFeatureSchema,
    ClusterUpdateSummarySchema
)

from .step24_comprehensive_cluster_labeling_schemas import (
    ComprehensiveClusterLabelingSchema,
    ClusterLabelAnalysisSchema,
    ClusterLabelingEngineSchema
)

from .step25_product_role_classifier_schemas import (
    ProductRoleClassificationSchema,
    ProductRoleAnalysisReportSchema,
    ProductRoleSummarySchema
)

from .step27_gap_matrix_generator_schemas import (
    GapMatrixSchema,
    GapAnalysisDetailedSchema,
    GapMatrixAnalysisReportSchema,
    GapMatrixSummarySchema
)

from .step26_price_elasticity_analyzer_schemas import (
    PriceBandAnalysisSchema,
    SubstitutionElasticityMatrixSchema,
    PriceElasticityAnalysisReportSchema,
    PriceElasticitySummarySchema
)

from .step28_scenario_analyzer_schemas import (
    ScenarioAnalysisResultsSchema,
    ScenarioAnalysisReportSchema,
    ScenarioRecommendationsSchema,
    ScenarioBaselineMetricsSchema,
    ScenarioOptimizationSchema
)

from .step29_supply_demand_gap_analysis_schemas import (
    SPUVarietyGapsAnalysisSchema,
    GapAnalysisDetailedSchema as SupplyDemandGapAnalysisDetailedSchema,
    SupplyDemandGapReportSchema,
    SupplyDemandGapSummarySchema,
    ClusterGapAnalysisSchema
)

from .step30_sellthrough_optimization_engine_schemas import (
    SellthroughOptimizationResultsSchema,
    SellthroughOptimizationReportSchema,
    BeforeAfterOptimizationComparisonSchema,
    OptimizationConstraintsSchema,
    OptimizationMetricsSchema
)

from .step31_gap_analysis_workbook_schemas import (
    GapAnalysisWorkbookExcelSchema,
    GapAnalysisWorkbookCSVSchema,
    ExecutiveSummarySchema,
    ClusterCoverageMatrixSchema,
    StoreLevelDisaggregationSchema
)

from .step32_store_allocation_schemas import (
    StoreLevelAllocationResultsSchema,
    StoreAllocationSummarySchema,
    StoreAllocationValidationSchema,
    StoreAllocationAddsSchema,
    StoreAllocationReducesSchema
)

from .step33_store_level_merchandising_rules_schemas import (
    StoreLevelMerchandisingRulesSchema,
    StoreLevelMerchandisingRulesReportSchema,
    MerchandisingRuleValidationSchema,
    StoreClusterMerchandisingProfileSchema
)

from .step36_unified_delivery_builder_schemas import (
    UnifiedDeliveryCSVSchema,
    UnifiedDeliveryExcelSchema,
    UnifiedDeliveryValidationSchema,
    UnifiedDeliveryClusterCSVSchema,
    UnifiedDeliveryDataDictionarySchema
)

from .step37_customer_delivery_formatter_schemas import (
    CustomerDeliveryFormattedSchema,
    CustomerDeliverySummarySchema,
    CustomerDeliveryValidationSchema,
    CustomerDeliveryReportSchema,
    CustomerDeliveryMetricsSchema
)

from .additional_analysis_schemas import (
    ClusterStyleVarietySchema,
    ClusterSubcategoryVarietySchema,
    TopPerformersByClusterSchema
)

__all__ = [
    # Step 6 schemas
    'ClusterProfilesSchema',
    'ClusteringResultsSchema',
    'PerClusterMetricsSchema',
    
    # Step 7 schemas
    'MissingSPURuleSchema',
    
    # Step 8 schemas
    'ImbalancedSPURuleSchema',
    
    # Step 9 schemas
    'BelowMinimumRuleSchema',
    'BelowMinimumOpportunitiesSchema',
    'BelowMinimumSubcategorySchema',
    
    # Step 11 schemas
    'MissedSalesOpportunitySchema',
    
    # Step 13 schemas
    'ConsolidatedSPURulesSchema',
    
    # Step 14 schemas
    'FastFishFormatSchema',
    
    # Step 15 schemas
    'HistoricalBaselineSchema',
    'HistoricalSPUCountSchema',
    'HistoricalSalesPerformanceSchema',
    
    # Step 16 schemas
    'ComparisonTableSchema',
    'StoreGroupComparisonSchema',
    'CategoryComparisonSchema',
    
    # Step 17 schemas
    'AugmentedRecommendationsSchema',
    'RecommendationEnhancementSchema',
    'MarketAnalysisSchema',
    
    # Step 18 schemas
    'ValidationResultsSchema',
    'DataQualityReportSchema',
    'BusinessLogicValidationSchema',
    
    # Step 19 schemas
    'DetailedSPUBreakdownSchema',
    'SPUPerformanceAnalysisSchema',
    'StoreSPUAnalysisSchema',
    
    # Step 20 schemas
    'DataValidationReportSchema',
    'DataQualityIssueSchema',
    'ValidationRuleSchema',
    
    # Step 21 schemas
    'LabelTagRecommendationsSchema',
    'TagAnalysisSchema',
    'TagRecommendationEngineSchema',
    
    # Step 22 schemas
    'StoreAttributeEnrichmentSchema',
    'StoreDemographicAnalysisSchema',
    'StorePerformanceEnrichmentSchema',
    
    # Step 23 schemas
    'ClusteringFeaturesUpdateSchema',
    'ClusteringFeatureSchema',
    'ClusterUpdateSummarySchema',
    
    # Step 24 schemas
    'ComprehensiveClusterLabelingSchema',
    'ClusterLabelAnalysisSchema',
    'ClusterLabelingEngineSchema',
    
    # Step 25 schemas
    'ProductRoleClassificationSchema',
    'ProductRoleAnalysisReportSchema',
    'ProductRoleSummarySchema',
    
    # Step 27 schemas
    'GapMatrixSchema',
    'GapAnalysisDetailedSchema',
    'GapMatrixAnalysisReportSchema',
    'GapMatrixSummarySchema',
    
    # Step 26 schemas
    'PriceBandAnalysisSchema',
    'SubstitutionElasticityMatrixSchema',
    'PriceElasticityAnalysisReportSchema',
    'PriceElasticitySummarySchema',
    
    # Step 28 schemas
    'ScenarioAnalysisResultsSchema',
    'ScenarioAnalysisReportSchema',
    'ScenarioRecommendationsSchema',
    'ScenarioBaselineMetricsSchema',
    'ScenarioOptimizationSchema',
    
    # Step 29 schemas
    'SPUVarietyGapsAnalysisSchema',
    'SupplyDemandGapAnalysisDetailedSchema',
    'SupplyDemandGapReportSchema',
    'SupplyDemandGapSummarySchema',
    'ClusterGapAnalysisSchema',
    
    # Step 30 schemas
    'SellthroughOptimizationResultsSchema',
    'SellthroughOptimizationReportSchema',
    'BeforeAfterOptimizationComparisonSchema',
    'OptimizationConstraintsSchema',
    'OptimizationMetricsSchema',
    
    # Step 31 schemas
    'GapAnalysisWorkbookExcelSchema',
    'GapAnalysisWorkbookCSVSchema',
    'ExecutiveSummarySchema',
    'ClusterCoverageMatrixSchema',
    'StoreLevelDisaggregationSchema',
    
    # Step 32 schemas
    'StoreLevelAllocationResultsSchema',
    'StoreAllocationSummarySchema',
    'StoreAllocationValidationSchema',
    'StoreAllocationAddsSchema',
    'StoreAllocationReducesSchema',
    
    # Step 33 schemas
    'StoreLevelMerchandisingRulesSchema',
    'StoreLevelMerchandisingRulesReportSchema',
    'MerchandisingRuleValidationSchema',
    'StoreClusterMerchandisingProfileSchema',
    
    # Step 36 schemas
    'UnifiedDeliveryCSVSchema',
    'UnifiedDeliveryExcelSchema',
    'UnifiedDeliveryValidationSchema',
    'UnifiedDeliveryClusterCSVSchema',
    'UnifiedDeliveryDataDictionarySchema',
    
    # Step 37 schemas
    'CustomerDeliveryFormattedSchema',
    'CustomerDeliverySummarySchema',
    'CustomerDeliveryValidationSchema',
    'CustomerDeliveryReportSchema',
    'CustomerDeliveryMetricsSchema',
    
    # Additional analysis schemas
    'ClusterStyleVarietySchema',
    'ClusterSubcategoryVarietySchema',
    'TopPerformersByClusterSchema'
]

