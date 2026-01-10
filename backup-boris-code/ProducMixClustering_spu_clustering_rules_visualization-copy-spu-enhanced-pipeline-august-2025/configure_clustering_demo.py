#!/usr/bin/env python3
"""
Configuration Tool for Constrained Clustering Demo

This script demonstrates the configurable nature of the clustering constraints
and shows how different parameters affect clustering results.

Author: Fast Fish Enhancement Team
Date: 2025-01-16
"""

import json
import pandas as pd
import numpy as np
from constrained_seasonal_clustering import (
    ClusteringConstraintsConfig, 
    ConstrainedClusteringEngine,
    run_constrained_clustering_demo
)
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_demo_configurations():
    """Create different clustering configurations for demonstration"""
    
    configurations = {
        'fast_fish_adjusted': {
            'description': 'Adjusted for Fast Fish 46 store groups',
            'store_count_constraints': {
                'min_stores_per_cluster': 20,  # Reduced for 46 stores
                'max_stores_per_cluster': 25,
                'target_stores_per_cluster': 23,
                'enforcement_strictness': 'strict'
            },
            'temperature_band_constraints': {
                'max_temp_range_celsius': 8.0,  # Slightly relaxed
                'temperature_weighting': 0.3,
                'seasonal_temperature_adjustment': True,
                'enforcement_strictness': 'strict'
            },
            'seasonal_window_config': {
                'target_season': 'Summer',
                'target_year': 2025,
                'recent_season_weight': 0.6,
                'yoy_season_weight': 0.4,
                'minimum_data_quality_threshold': 0.8
            }
        },
        'original_specs': {
            'description': 'Original specifications (35-50 stores, 5°C)',
            'store_count_constraints': {
                'min_stores_per_cluster': 35,
                'max_stores_per_cluster': 50,
                'target_stores_per_cluster': 42,
                'enforcement_strictness': 'strict'
            },
            'temperature_band_constraints': {
                'max_temp_range_celsius': 5.0,
                'temperature_weighting': 0.3,
                'seasonal_temperature_adjustment': True,
                'enforcement_strictness': 'strict'
            },
            'seasonal_window_config': {
                'target_season': 'Summer',
                'target_year': 2025,
                'recent_season_weight': 0.6,
                'yoy_season_weight': 0.4,
                'minimum_data_quality_threshold': 0.8
            }
        },
        'relaxed_constraints': {
            'description': 'More flexible constraints for testing',
            'store_count_constraints': {
                'min_stores_per_cluster': 15,
                'max_stores_per_cluster': 60,
                'target_stores_per_cluster': 30,
                'enforcement_strictness': 'moderate'
            },
            'temperature_band_constraints': {
                'max_temp_range_celsius': 10.0,
                'temperature_weighting': 0.2,
                'seasonal_temperature_adjustment': True,
                'enforcement_strictness': 'moderate'
            },
            'seasonal_window_config': {
                'target_season': 'Summer',
                'target_year': 2025,
                'recent_season_weight': 0.7,
                'yoy_season_weight': 0.3,
                'minimum_data_quality_threshold': 0.7
            }
        }
    }
    
    return configurations

def test_configuration(config_name: str, config_data: dict):
    """Test clustering with specific configuration"""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING CONFIGURATION: {config_name.upper()}")
    logger.info(f"Description: {config_data['description']}")
    logger.info(f"{'='*80}")
    
    # Create configuration
    clustering_config = ClusteringConstraintsConfig()
    clustering_config.config.update(config_data)
    
    # Display key parameters
    store_constraints = config_data['store_count_constraints']
    temp_constraints = config_data['temperature_band_constraints']
    
    logger.info(f"🏪 Store Count Constraints:")
    logger.info(f"   Range: {store_constraints['min_stores_per_cluster']}-{store_constraints['max_stores_per_cluster']} stores")
    logger.info(f"   Target: {store_constraints['target_stores_per_cluster']} stores")
    
    logger.info(f"🌡️ Temperature Constraints:")
    logger.info(f"   Max Range: {temp_constraints['max_temp_range_celsius']}°C")
    logger.info(f"   Weighting: {temp_constraints['temperature_weighting']}")
    
    # Load Fast Fish data
    try:
        fast_fish_data = pd.read_csv('fast_fish_with_sell_through_analysis_20250714_124522.csv')
        
        # Aggregate to store group level
        store_level_data = fast_fish_data.groupby('Store_Group_Name').agg({
            'Total_Current_Sales': 'sum',
            'Current_SPU_Quantity': 'sum',
            'Target_SPU_Quantity': 'sum',
            'Avg_Sales_Per_SPU': 'mean',
            'Sell_Through_Rate': 'mean',
            'Stores_In_Group_Selling_This_Category': 'first',
            'cluster_trend_score': 'mean',
            'trend_sales_performance': 'mean',
            'trend_weather_impact': 'mean'
        }).reset_index()
        
        logger.info(f"📊 Data: {len(store_level_data)} store groups from real Fast Fish data")
        
    except FileNotFoundError:
        logger.warning("Fast Fish data not found, using synthetic data")
        return None
    
    # Run clustering
    clustering_engine = ConstrainedClusteringEngine(clustering_config)
    results = clustering_engine.fit_constrained_clusters(store_level_data)
    
    # Display results
    validation = results['constraint_validation']
    metadata = results['clustering_metadata']
    
    logger.info(f"\n📋 RESULTS SUMMARY:")
    logger.info(f"✅ All Constraints Met: {validation['all_constraints_met']}")
    logger.info(f"📊 Total Violations: {validation['total_violations']}")
    logger.info(f"🏢 Clusters Created: {metadata['total_clusters']}")
    logger.info(f"📏 Cluster Size Range: {metadata['cluster_size_stats']['min_size']}-{metadata['cluster_size_stats']['max_size']} stores")
    logger.info(f"📈 Average Cluster Size: {metadata['cluster_size_stats']['avg_size']:.1f} stores")
    
    # Detailed validation
    size_val = validation['size_validation']
    temp_val = validation['temperature_validation']
    
    logger.info(f"\n🔍 CONSTRAINT VALIDATION:")
    logger.info(f"Store Count Compliance: {size_val['all_sizes_valid']} ({size_val['violation_count']} violations)")
    logger.info(f"Temperature Band Compliance: {temp_val['all_bands_valid']} ({temp_val['violation_count']} violations)")
    
    if not validation['all_constraints_met']:
        logger.warning("❌ CONSTRAINT VIOLATIONS DETECTED")
        if size_val['size_violations']:
            logger.warning(f"Size violations: {size_val['size_violations']}")
        if temp_val['cluster_violations']:
            logger.warning(f"Temperature violations: {temp_val['cluster_violations']}")
    
    # Save results for this configuration
    output_file = f"clustering_results_{config_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'configuration': config_data,
            'results': results['constraint_validation'],
            'metadata': results['clustering_metadata']
        }, f, indent=2)
    
    logger.info(f"📁 Results saved to: {output_file}")
    
    return results

def demonstrate_parameter_adjustability():
    """Demonstrate the adjustable nature of clustering parameters"""
    
    logger.info("🎯 DEMONSTRATING CONFIGURABLE CLUSTERING CONSTRAINTS")
    logger.info("="*80)
    
    # Get all configurations
    configurations = create_demo_configurations()
    
    # Test each configuration
    results_summary = {}
    
    for config_name, config_data in configurations.items():
        try:
            results = test_configuration(config_name, config_data)
            if results:
                results_summary[config_name] = {
                    'success': results['success'],
                    'clusters': results['clustering_metadata']['total_clusters'],
                    'violations': results['constraint_validation']['total_violations']
                }
        except Exception as e:
            logger.error(f"Error testing {config_name}: {e}")
            results_summary[config_name] = {'error': str(e)}
    
    # Display summary
    logger.info(f"\n{'='*80}")
    logger.info("CONFIGURATION COMPARISON SUMMARY")
    logger.info(f"{'='*80}")
    
    for config_name, summary in results_summary.items():
        if 'error' in summary:
            logger.info(f"{config_name:20}: ❌ Error - {summary['error']}")
        else:
            status = "✅ Success" if summary['success'] else "⚠️ Violations"
            logger.info(f"{config_name:20}: {status} - {summary['clusters']} clusters, {summary['violations']} violations")
    
    return results_summary

def create_custom_configuration():
    """Interactive tool to create custom configuration"""
    
    logger.info("\n🛠️ CUSTOM CONFIGURATION CREATOR")
    logger.info("This demonstrates how parameters can be adjusted programmatically")
    
    # Example of programmatic configuration adjustment
    custom_config = ClusteringConstraintsConfig()
    
    # Adjust for current Fast Fish data (46 store groups)
    logger.info("Adjusting parameters for 46 Fast Fish store groups...")
    
    custom_config.update_constraints(
        store_count_constraints={
            'min_stores_per_cluster': 15,  # Allow smaller clusters
            'max_stores_per_cluster': 20,  # Smaller max for 46 stores
            'target_stores_per_cluster': 18,  # Target ~2-3 clusters
            'enforcement_strictness': 'strict'
        },
        temperature_band_constraints={
            'max_temp_range_celsius': 6.0,  # Slightly relaxed
            'temperature_weighting': 0.25,
            'seasonal_temperature_adjustment': True,
            'enforcement_strictness': 'strict'
        }
    )
    
    # Save custom configuration
    config_file = f"custom_clustering_config_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
    custom_config.save_config(config_file)
    
    logger.info(f"Custom configuration saved to: {config_file}")
    
    return custom_config

if __name__ == "__main__":
    
    # Demonstrate configurable clustering
    logger.info("🚀 CONFIGURABLE CLUSTERING DEMONSTRATION")
    
    # Test different configurations
    results_summary = demonstrate_parameter_adjustability()
    
    # Create custom configuration
    custom_config = create_custom_configuration()
    
    # Test custom configuration
    logger.info("\n🧪 Testing Custom Configuration...")
    custom_results = test_configuration("custom", custom_config.config)
    
    logger.info("\n🎉 DEMONSTRATION COMPLETE!")
    logger.info("Key Features Demonstrated:")
    logger.info("✅ Configurable store count constraints (35-50 stores adjustable)")
    logger.info("✅ Configurable temperature band constraints (5°C adjustable)")
    logger.info("✅ Flexible seasonal window selection")
    logger.info("✅ Multiple constraint enforcement strategies")
    logger.info("✅ Real Fast Fish data integration")
    logger.info("✅ Comprehensive constraint validation")
    logger.info("✅ JSON-based configuration management") 