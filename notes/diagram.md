# 📊 Complete Data Flow Graph: Original Pipeline (Step 1 → Step 37)

```mermaid
graph TD
    %% Data Flow Graph: Step 1 → Step 37
    %% Original Pipeline Data Flow

    %% STEP 1: API Data Download
    Step1[Step 1: API Data Download]
    StoreCodes[Input: store_codes.csv]
    API1[API Calls]
    StoreCodes --> Step1
    Step1 --> API1

    %% Step 1 Outputs
    StoreSales[store_sales_{period}.csv]
    CategorySales[complete_category_sales_{period}.csv]
    SPUSales[complete_spu_sales_{period}.csv]
    StoreConfig[store_config_{period}.csv]

    Step1 --> StoreSales
    Step1 --> CategorySales
    Step1 --> SPUSales
    Step1 --> StoreConfig

    %% STEP 2: Extract Coordinates
    Step2[Step 2: Extract Coordinates]
    StoreSales --> Step2
    CategorySales --> Step2
    SPUSales --> Step2

    %% Step 2 Outputs
    Coordinates[store_coordinates_extended.csv]
    SPUMapping[spu_store_mapping.csv]
    SPUMetadata[spu_metadata.csv]

    Step2 --> Coordinates
    Step2 --> SPUMapping
    Step2 --> SPUMetadata

    %% STEP 3: Prepare Matrix
    Step3[Step 3: Prepare Matrix]
    Coordinates --> Step3
    CategorySales --> Step3
    SPUSales --> Step3

    %% Step 3 Outputs
    OriginalMatrix[store_subcategory_matrix.csv]
    NormalizedMatrix[normalized_subcategory_matrix.csv]
    CategoryAggMatrix[store_category_agg_matrix.csv]
    NormalizedCategoryAgg[normalized_category_agg_matrix.csv]
    SubcategoryStoreList[subcategory_store_list.txt]
    CategoryStoreList[category_agg_store_list.txt]

    Step3 --> OriginalMatrix
    Step3 --> NormalizedMatrix
    Step3 --> CategoryAggMatrix
    Step3 --> NormalizedCategoryAgg
    Step3 --> SubcategoryStoreList
    Step3 --> CategoryStoreList

    %% STEP 4: Weather Data
    Step4[Step 4: Weather Data]
    Coordinates --> Step4

    %% Step 4 Outputs
    WeatherData[weather_data_*_{period}.csv files]

    Step4 --> WeatherData

    %% STEP 5: Feels-like Temperature
    Step5[Step 5: Feels-like Temperature]
    WeatherData --> Step5

    %% Step 5 Outputs
    TemperatureData[stores_with_feels_like_temperature.csv]

    Step5 --> TemperatureData

    %% STEP 6: Cluster Analysis
    Step6[Step 6: Cluster Analysis]
    OriginalMatrix --> Step6
    NormalizedMatrix --> Step6
    TemperatureData --> Step6
    Coordinates --> Step6

    %% Step 6 Outputs
    ClusteringResults[clustering_results_{matrix_type}.csv]
    ClusterProfiles[cluster_profiles_{matrix_type}.csv]
    ClusterMetrics[per_cluster_metrics_{matrix_type}.csv]

    Step6 --> ClusteringResults
    Step6 --> ClusterProfiles
    Step6 --> ClusterMetrics

    %% STEPS 7-12: Business Rules Analysis
    %% Step 7: Missing Category Rule
    Step7[Step 7: Missing Category Rule]
    ClusteringResults --> Step7
    CategorySales --> Step7
    SPUSales --> Step7
    Coordinates --> Step7

    %% Step 8: Imbalanced Rule
    Step8[Step 8: Imbalanced Rule]
    ClusteringResults --> Step8
    CategorySales --> Step8
    SPUSales --> Step8

    %% Step 9: Below Minimum Rule
    Step9[Step 9: Below Minimum Rule]
    ClusteringResults --> Step9
    CategorySales --> Step9

    %% Step 10: SPU Assortment Optimization
    Step10[Step 10: SPU Assortment]
    ClusteringResults --> Step10
    SPUSales --> Step10
    SPUMapping --> Step10

    %% Step 11: Missed Sales Opportunity
    Step11[Step 11: Missed Sales]
    ClusteringResults --> Step11
    SPUSales --> Step11
    SPUMetadata --> Step11

    %% Step 12: Sales Performance Rule
    Step12[Step 12: Sales Performance]
    ClusteringResults --> Step12
    SPUSales --> Step12
    SPUMetadata --> Step12

    %% Individual Rule Outputs
    Rule7Output[rule7_missing_{level}_sellthrough_results_{period}.csv]
    Rule8Output[rule8_imbalanced_{level}_results_{period}.csv]
    Rule9Output[rule9_below_minimum_{level}_results_{period}.csv]
    Rule10Output[rule10_spu_assortment_results_{period}.csv]
    Rule11Output[rule11_missed_sales_results_{period}.csv]
    Rule12Output[rule12_sales_performance_results_{period}.csv]

    Step7 --> Rule7Output
    Step8 --> Rule8Output
    Step9 --> Rule9Output
    Step10 --> Rule10Output
    Step11 --> Rule11Output
    Step12 --> Rule12Output

    %% STEP 13: Rule Consolidation
    Step13[Step 13: Rule Consolidation]
    Rule7Output --> Step13
    Rule8Output --> Step13
    Rule9Output --> Step13
    Rule10Output --> Step13
    Rule11Output --> Step13
    Rule12Output --> Step13
    ClusteringResults --> Step13
    CategorySales --> Step13
    SPUSales --> Step13

    %% Step 13 Outputs
    ConsolidatedResults[consolidated_spu_rule_results.csv]
    ConsolidationSummary[consolidated_spu_rule_summary.md]
    AllRulesFile[all_spu_rules_combined.csv]

    Step13 --> ConsolidatedResults
    Step13 --> ConsolidationSummary
    Step13 --> AllRulesFile

    %% STEP 14: Fast Fish Format
    Step14[Step 14: Fast Fish Format]
    ConsolidatedResults --> Step14
    ClusteringResults --> Step14
    Coordinates --> Step14

    %% Step 14 Outputs
    FastFishFormat[enhanced_fast_fish_format_{period}.csv]
    Step14 --> FastFishFormat

    %% STEP 15: Historical Baseline
    Step15[Step 15: Historical Baseline]
    FastFishFormat --> Step15
    ConsolidatedResults --> Step15

    %% Step 15 Outputs
    HistoricalData[historical_baseline_{period}.csv]
    Step15 --> HistoricalData

    %% STEP 16: Comparison Tables
    Step16[Step 16: Comparison Tables]
    HistoricalData --> Step16
    ConsolidatedResults --> Step16
    FastFishFormat --> Step16

    %% Step 16 Outputs
    ComparisonTables[comparison_tables_{period}.xlsx]
    Step16 --> ComparisonTables

    %% STEP 17: Augment Recommendations
    Step17[Step 17: Augment Recommendations]
    ComparisonTables --> Step17
    HistoricalData --> Step17
    ConsolidatedResults --> Step17

    %% Step 17 Outputs
    AugmentedResults[augmented_recommendations_{period}.csv]
    Step17 --> AugmentedResults

    %% STEP 18: Sell-Through Analysis
    Step18[Step 18: Sell-Through Analysis]
    AugmentedResults --> Step18
    ConsolidatedResults --> Step18

    %% Step 18 Outputs
    SellThroughData[sell_through_analysis_{period}.csv]
    Step18 --> SellThroughData

    %% STEP 19: Detailed SPU Breakdown
    Step19[Step 19: Detailed SPU Breakdown]
    SellThroughData --> Step19
    SPUMapping --> Step19
    SPUMetadata --> Step19
    SPUSales --> Step19

    %% Step 19 Outputs
    SPUBreakdown[spu_breakdown_{period}.csv]
    Step19 --> SPUBreakdown

    %% STEP 20: Data Validation
    Step20[Step 20: Data Validation]
    SPUBreakdown --> Step20
    SellThroughData --> Step20
    AugmentedResults --> Step20
    ComparisonTables --> Step20
    HistoricalData --> Step20
    FastFishFormat --> Step20
    ConsolidatedResults --> Step20
    Rule12Output --> Step20
    Rule11Output --> Step20
    Rule10Output --> Step20
    Rule9Output --> Step20
    Rule8Output --> Step20
    Rule7Output --> Step20
    ClusteringResults --> Step20
    ClusterProfiles --> Step20
    ClusterMetrics --> Step20
    OriginalMatrix --> Step20
    NormalizedMatrix --> Step20
    CategoryAggMatrix --> Step20
    NormalizedCategoryAgg --> Step20
    TemperatureData --> Step20
    WeatherData --> Step20
    Coordinates --> Step20
    SPUMetadata --> Step20
    SPUMapping --> Step20
    SPUSales --> Step20
    CategorySales --> Step20
    StoreSales --> Step20

    %% STEPS 21-24: Additional Analysis
    Step21[Step 21: Label Tag Recommendations]
    Step22[Step 22: Store Attribute Enrichment]
    Step23[Step 23: Update Clustering Features]
    Step24[Step 24: Comprehensive Cluster Labeling]

    %% Additional analysis steps
    SPUSales --> Step21
    CategorySales --> Step22
    ClusteringResults --> Step23
    ClusteringResults --> Step24

    %% Step 21-24 Outputs
    LabelTags[label_tag_recommendations_{period}.csv]
    EnrichedAttributes[enriched_store_attributes_{period}.csv]
    UpdatedFeatures[updated_clustering_features_{period}.csv]
    ClusterLabels[comprehensive_cluster_labels_{period}.csv]

    Step21 --> LabelTags
    Step22 --> EnrichedAttributes
    Step23 --> UpdatedFeatures
    Step24 --> ClusterLabels

    %% STEPS 25-30: Advanced Analysis
    Step25[Step 25: Product Role Classifier]
    Step26[Step 26: Price Elasticity Analyzer]
    Step27[Step 27: Gap Matrix Generator]
    Step28[Step 28: Scenario Analyzer]
    Step29[Step 29: Supply Demand Gap Analysis]
    Step30[Step 30: Sell-Through Optimization]

    %% Advanced analysis dependencies
    SPUSales --> Step25
    CategorySales --> Step25
    SPUSales --> Step26
    ConsolidatedResults --> Step27
    SPUSales --> Step28
    CategorySales --> Step29
    SellThroughData --> Step30

    %% Step 25-30 Outputs
    ProductRoles[product_role_classification_{period}.csv]
    PriceElasticity[price_elasticity_analysis_{period}.csv]
    GapMatrix[gap_matrix_{period}.csv]
    Scenarios[scenario_analysis_{period}.csv]
    SupplyDemand[supply_demand_gap_analysis_{period}.csv]
    SellThroughOpt[sellthrough_optimization_{period}.csv]

    Step25 --> ProductRoles
    Step26 --> PriceElasticity
    Step27 --> GapMatrix
    Step28 --> Scenarios
    Step29 --> SupplyDemand
    Step30 --> SellThroughOpt

    %% STEPS 31-37: Final Processing
    Step31[Step 31: Gap Analysis Workbook]
    Step32[Step 32: Store Allocation]
    Step33[Step 33: Store Level Merchandising]
    Step34a[Step 34a: Cluster Strategy Optimization]
    Step34b[Step 34b: Unify Outputs]
    Step35[Step 35: Merchandising Strategy]
    Step36[Step 36: Unified Delivery Builder]
    Step37[Step 37: Customer Delivery Formatter]

    %% Final processing dependencies
    ConsolidatedResults --> Step31
    ClusteringResults --> Step32
    SPUSales --> Step33
    ClusteringResults --> Step34a
    ConsolidatedResults --> Step34b
    ConsolidatedResults --> Step35
    ConsolidatedResults --> Step36
    ConsolidatedResults --> Step37

    %% Final processing outputs
    GapWorkbook[gap_analysis_workbook_{period}.xlsx]
    StoreAllocation[store_allocation_{period}.csv]
    MerchandisingRules[store_level_merchandising_rules_{period}.csv]
    ClusterStrategies[cluster_strategies_{period}.csv]
    UnifiedOutputs[unified_outputs_{period}.csv]
    MerchandisingStrategy[merchandising_strategy_{period}.csv]
    UnifiedDelivery[unified_delivery_{period}.csv]
    CustomerDelivery[customer_delivery_{period}.csv]

    Step31 --> GapWorkbook
    Step32 --> StoreAllocation
    Step33 --> MerchandisingRules
    Step34a --> ClusterStrategies
    Step34b --> UnifiedOutputs
    Step35 --> MerchandisingStrategy
    Step36 --> UnifiedDelivery
    Step37 --> CustomerDelivery

    %% Styling
    classDef stepClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef dataClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef finalClass fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class Step1,Step2,Step3,Step4,Step5,Step6,Step7,Step8,Step9,Step10,Step11,Step12,Step13,Step14,Step15,Step16,Step17,Step18,Step19,Step20,Step21,Step22,Step23,Step24,Step25,Step26,Step27,Step28,Step29,Step30,Step31,Step32,Step33,Step34a,Step34b,Step35,Step36,Step37 stepClass
    class StoreSales,CategorySales,SPUSales,StoreConfig,Coordinates,SPUMapping,SPUMetadata,OriginalMatrix,NormalizedMatrix,CategoryAggMatrix,NormalizedCategoryAgg,SubcategoryStoreList,CategoryStoreList,WeatherData,TemperatureData,ClusteringResults,ClusterProfiles,ClusterMetrics,Rule7Output,Rule8Output,Rule9Output,Rule10Output,Rule11Output,Rule12Output,ConsolidatedResults,ConsolidationSummary,AllRulesFile,FastFishFormat,HistoricalData,ComparisonTables,AugmentedResults,SellThroughData,SPUBreakdown dataClass
    class ComparisonTables,AugmentedResults,SPUBreakdown,GapWorkbook,StoreAllocation,MerchandisingRules,ClusterStrategies,UnifiedOutputs,MerchandisingStrategy,UnifiedDelivery,CustomerDelivery,LabelTags,EnrichedAttributes,UpdatedFeatures,ClusterLabels,ProductRoles,PriceElasticity,GapMatrix,Scenarios,SupplyDemand,SellThroughOpt finalClass
```

## 📋 Data Flow Summary

### **Input → Processing → Output Flow:**

1. **Step 1**: `store_codes.csv` → API calls → Multiple CSV files (`store_sales_{period}.csv`, `complete_category_sales_{period}.csv`, `complete_spu_sales_{period}.csv`)
2. **Step 2**: Sales data → Coordinate extraction → Coordinate files (`store_coordinates_extended.csv`, `spu_store_mapping.csv`, `spu_metadata.csv`)
3. **Step 3**: Coordinates + Sales data → Matrix preparation → Matrix files (`store_subcategory_matrix.csv`, `normalized_subcategory_matrix.csv`, `store_category_agg_matrix.csv`, etc.)
4. **Step 4**: Coordinates → Weather data download → Weather data files (`weather_data_*_{period}.csv`)
5. **Step 5**: Weather data → Temperature calculation → Temperature files (`stores_with_feels_like_temperature.csv`)
6. **Step 6**: Matrices + Temperature → Cluster analysis → Clustering results (`clustering_results_{matrix_type}.csv`, `cluster_profiles_{matrix_type}.csv`)
7. **Steps 7-12**: Clustering + Sales data → Business rule analysis → Individual rule results (`rule{7-12}_*_results_{period}.csv`)
8. **Step 13**: All rule results → Consolidation → Consolidated results (`consolidated_spu_rule_results.csv`)
9. **Step 14**: Consolidated results → Formatting → Fast Fish format files (`enhanced_fast_fish_format_{period}.csv`)
10. **Step 15**: Formatted data → Historical comparison → Historical baseline (`historical_baseline_{period}.csv`)
11. **Step 16**: Historical + Current → Comparison tables → Excel comparison tables (`comparison_tables_{period}.xlsx`)
12. **Step 17**: Comparison data → Recommendation augmentation → Augmented recommendations (`augmented_recommendations_{period}.csv`)
13. **Step 18**: Augmented data → Sell-through analysis → Sell-through analysis files (`sell_through_analysis_{period}.csv`)
14. **Step 19**: Sell-through data → SPU breakdown → Detailed SPU breakdown (`spu_breakdown_{period}.csv`)
15. **Step 20**: All outputs → Validation → Comprehensive validation results
16. **Steps 21-37**: Various analysis and optimization → Final deliverables (`*_optimization_{period}.csv`, `*_strategy_{period}.csv`, etc.)

### **🔗 Key Data Dependencies:**

- **Coordinates** flow from Step 2 → Steps 3, 4, 6, 7-12, 14, 20
- **SPU data** flows from Step 1 → Steps 2, 3, 7-12, 21-30, 33
- **Matrices** flow from Step 3 → Step 6
- **Weather data** flows from Step 4 → Step 5
- **Temperature data** flows from Step 5 → Step 6
- **Clustering results** flow from Step 6 → Steps 7-12, 13, 14, 20, 23, 24, 32, 34a
- **Business rule results** flow from Steps 7-12 → Step 13 → Steps 14-20, 27
- **Consolidated results** flow from Step 13 → Steps 14-20, 31-37

### **📊 Output Categories:**

- **Core Data**: Store sales, coordinates, matrices, clustering
- **Business Rules**: 6 optimization rule results
- **Consolidated**: Combined rule analysis
- **Formatted**: Client-ready output formats
- **Comparative**: Historical and trending analysis
- **Validation**: Data quality and integrity checks

This diagram shows the complete data transformation pipeline from raw API data through 37 processing steps to final business deliverables.
