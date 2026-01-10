#!/usr/bin/env python3
"""
Step 23: Update Clustering Features to Include Store Attributes

This step updates the clustering configuration to include the new store attributes:
- Store type/style (Fashion/Basic/Balanced)
- Rack capacity/size tier
- Enhanced temperature zone integration

Updates both YAML/JSON configuration files and clustering logic to incorporate
the enriched store attributes for improved clustering quality.

Author: Data Pipeline Team
Date: 2025-07-23
Version: 1.0 - Store Attribute Integration
"""

import pandas as pd
import numpy as np
import os
import json
# Resilient imports for module vs script execution
try:
    from src.config import get_period_label
    from src.pipeline_manifest import register_step_output, get_step_input
except ModuleNotFoundError:
    try:
        from config import get_period_label
        from pipeline_manifest import register_step_output, get_step_input
    except ModuleNotFoundError:
        import sys as _sys
        import os as _os
        _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        from src.config import get_period_label
        from src.pipeline_manifest import register_step_output, get_step_input
try:
    import yaml
    _YAML_AVAILABLE = True
except Exception:
    yaml = None
    _YAML_AVAILABLE = False
from datetime import datetime
from typing import Dict, List, Any, Optional
import warnings

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
# Input files
ENRICHED_STORE_ATTRIBUTES_FILE = "output/enriched_store_attributes.csv"
CLUSTERING_CONFIG_FILE = "config/clustering_config.yaml"
CLUSTERING_CONFIG_JSON = "config/clustering_config.json"

# Clustering step files to update
CLUSTERING_STEP_FILE = "src/step6_clustering.py"

# Output files
UPDATED_CONFIG_FILE = "output/updated_clustering_config.yaml"
FEATURE_INTEGRATION_REPORT = "output/clustering_feature_integration_report.md"

# Create directories
os.makedirs("output", exist_ok=True)
os.makedirs("config", exist_ok=True)

# ===== PERIOD-AWARE HELPERS =====
def _parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Step 23: Update clustering features (period-aware)")
    parser.add_argument("--target-yyyymm", required=False, help="Target YYYYMM, e.g., 202509")
    parser.add_argument("--target-period", required=False, choices=["A","B"], help="Target period (A/B)")
    return parser.parse_args()

def _resolve_enriched_attributes_path(period_label: str) -> str:
    """Resolve enriched store attributes via manifest (step22), then period-labeled files, then generic."""
    # Manifest first
    try:
        path = get_step_input("step22", f"enriched_store_attributes_{period_label}")
        if path and os.path.exists(path):
            return path
    except Exception:
        pass
    # Period-labeled fallback by pattern
    try:
        import glob
        candidates = sorted(glob.glob(f"output/enriched_store_attributes_{period_label}_*.csv"), key=os.path.getctime, reverse=True)
        if candidates:
            return candidates[0]
    except Exception:
        pass
    # Generic fallback
    return ENRICHED_STORE_ATTRIBUTES_FILE

# ===== CLUSTERING FEATURE CONFIGURATION =====
def create_enhanced_clustering_config() -> Dict[str, Any]:
    """
    Create enhanced clustering configuration including store attributes.
    
    Returns:
        Dictionary containing complete clustering configuration
    """
    config = {
        "clustering_features": {
            "sales_features": {
                "enabled": True,
                "features": [
                    "spu_sales_amt",
                    "spu_sales_qty", 
                    "category_sales_amt",
                    "subcategory_sales_amt"
                ],
                "normalization": "min_max",
                "weight": 0.4
            },
            "store_attributes": {
                "enabled": True,
                "features": [
                    "fashion_ratio",
                    "basic_ratio",
                    "estimated_rack_capacity",
                    "sku_diversity",
                    "avg_price_per_unit"
                ],
                "normalization": "standard",
                "weight": 0.3
            },
            "temperature_features": {
                "enabled": True,
                "features": [
                    "feels_like_temperature",
                    "temperature_band_encoded"
                ],
                "normalization": "standard",
                "weight": 0.2
            },
            "geographic_features": {
                "enabled": True,
                "features": [
                    "latitude",
                    "longitude"
                ],
                "normalization": "min_max",
                "weight": 0.1
            }
        },
        "clustering_parameters": {
            "algorithm": "kmeans",
            "n_clusters": "auto",
            "max_clusters": 50,
            "min_cluster_size": 50,
            "max_cluster_size": 50,
            "random_state": 42,
            "n_init": 10,
            "max_iter": 300
        },
        "preprocessing": {
            "pca_enabled": True,
            "pca_components": {
                "spu_matrix": 100,
                "subcategory_matrix": 50,
                "category_matrix": 20
            },
            "feature_selection": {
                "enabled": True,
                "method": "variance_threshold",
                "threshold": 0.01
            }
        },
        "constraints": {
            "temperature_aware": True,
            "temperature_band_constraint": True,
            "store_type_balance": True,
            "capacity_balance": True
        },
        "quality_metrics": {
            "target_silhouette_score": 0.5,
            "target_calinski_harabasz_score": 100,
            "max_davies_bouldin_score": 2.0
        }
    }
    
    return config

def encode_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode categorical store attributes for clustering.
    
    Args:
        df: DataFrame with store attributes
        
    Returns:
        DataFrame with encoded categorical features
    """
    df_encoded = df.copy()
    
    # Encode store type (Fashion=2, Balanced=1, Basic=0)
    if 'store_type' in df_encoded.columns:
        type_mapping = {'Fashion': 2, 'Balanced': 1, 'Basic': 0}
        df_encoded['store_type_encoded'] = df_encoded['store_type'].map(type_mapping).fillna(1)
    
    # Encode size tier (Large=2, Medium=1, Small=0)
    if 'size_tier' in df_encoded.columns:
        size_mapping = {'Large': 2, 'Medium': 1, 'Small': 0}
        df_encoded['size_tier_encoded'] = df_encoded['size_tier'].map(size_mapping).fillna(1)
    
    # Encode temperature bands numerically
    if 'temperature_band' in df_encoded.columns:
        # Extract temperature values from band strings like "15°C to 20°C"
        def extract_temp_value(band_str):
            if pd.isna(band_str):
                return 20  # Default temperature
            try:
                # Extract the lower bound temperature
                temp_str = str(band_str).split('°C')[0]
                return float(temp_str)
            except:
                return 20
        
        df_encoded['temperature_band_encoded'] = df_encoded['temperature_band'].apply(extract_temp_value)
    
    return df_encoded

def create_clustering_feature_matrix(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Create feature matrix for clustering based on configuration.
    
    Args:
        df: DataFrame with store attributes
        config: Clustering configuration
        
    Returns:
        Feature matrix ready for clustering
    """
    feature_matrix = pd.DataFrame()
    feature_matrix['str_code'] = df['str_code']
    
    # Add sales features
    if config['clustering_features']['sales_features']['enabled']:
        sales_features = config['clustering_features']['sales_features']['features']
        for feature in sales_features:
            if feature in df.columns:
                feature_matrix[feature] = df[feature].fillna(0)
    
    # Add store attribute features
    if config['clustering_features']['store_attributes']['enabled']:
        attr_features = config['clustering_features']['store_attributes']['features']
        for feature in attr_features:
            if feature in df.columns:
                feature_matrix[feature] = df[feature].fillna(df[feature].median())
    
    # Add temperature features
    if config['clustering_features']['temperature_features']['enabled']:
        temp_features = config['clustering_features']['temperature_features']['features']
        for feature in temp_features:
            if feature in df.columns:
                feature_matrix[feature] = df[feature].fillna(df[feature].median())
    
    # Add geographic features if available
    if config['clustering_features']['geographic_features']['enabled']:
        geo_features = config['clustering_features']['geographic_features']['features']
        for feature in geo_features:
            if feature in df.columns:
                feature_matrix[feature] = df[feature].fillna(df[feature].median())
    
    return feature_matrix

def validate_feature_integration(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that store attributes are properly integrated for clustering.
    
    Args:
        df: DataFrame with store attributes
        config: Clustering configuration
        
    Returns:
        Validation results dictionary
    """
    validation_results = {
        'total_stores': len(df),
        'total_features': 0,
        'feature_coverage': {},
        'data_quality': {},
        'clustering_readiness': True,
        'issues': []
    }
    
    # Check sales features
    if config['clustering_features']['sales_features']['enabled']:
        sales_features = config['clustering_features']['sales_features']['features']
        for feature in sales_features:
            if feature in df.columns:
                coverage = (df[feature].notna().sum() / len(df)) * 100
                validation_results['feature_coverage'][feature] = coverage
                validation_results['total_features'] += 1
                
                if coverage < 80:
                    validation_results['issues'].append(f"Low coverage for {feature}: {coverage:.1f}%")
    
    # Check store attribute features
    if config['clustering_features']['store_attributes']['enabled']:
        attr_features = config['clustering_features']['store_attributes']['features']
        for feature in attr_features:
            if feature in df.columns:
                coverage = (df[feature].notna().sum() / len(df)) * 100
                validation_results['feature_coverage'][feature] = coverage
                validation_results['total_features'] += 1
                
                if coverage < 90:
                    validation_results['issues'].append(f"Store attribute {feature} has {coverage:.1f}% coverage")
    
    # Check temperature features
    if config['clustering_features']['temperature_features']['enabled']:
        temp_features = config['clustering_features']['temperature_features']['features']
        for feature in temp_features:
            if feature in df.columns:
                coverage = (df[feature].notna().sum() / len(df)) * 100
                validation_results['feature_coverage'][feature] = coverage
                validation_results['total_features'] += 1
    
    # Overall data quality assessment
    validation_results['data_quality'] = {
        'store_type_coverage': (df['store_type'].notna().sum() / len(df)) * 100 if 'store_type' in df.columns else 0,
        'capacity_coverage': (df['estimated_rack_capacity'].notna().sum() / len(df)) * 100 if 'estimated_rack_capacity' in df.columns else 0,
        'temperature_coverage': (df['feels_like_temperature'].notna().sum() / len(df)) * 100 if 'feels_like_temperature' in df.columns else 0,
        'fashion_ratio_coverage': (df['fashion_ratio'].notna().sum() / len(df)) * 100 if 'fashion_ratio' in df.columns else 0
    }
    
    # Determine clustering readiness
    if validation_results['total_features'] < 5:
        validation_results['clustering_readiness'] = False
        validation_results['issues'].append("Insufficient features for clustering (minimum 5 required)")
    
    if len(validation_results['issues']) > 5:
        validation_results['clustering_readiness'] = False
    
    return validation_results

def generate_integration_report(df: pd.DataFrame, config: Dict[str, Any], 
                              validation: Dict[str, Any]) -> None:
    """Generate comprehensive feature integration report."""
    print("Generating clustering feature integration report...")
    
    with open(FEATURE_INTEGRATION_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Clustering Feature Integration Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Stores:** {validation['total_stores']:,}\n")
        f.write(f"**Total Features:** {validation['total_features']}\n")
        f.write(f"**Clustering Ready:** {'✅ Yes' if validation['clustering_readiness'] else '❌ No'}\n\n")
        
        # Feature Coverage Analysis
        f.write("## Feature Coverage Analysis\n\n")
        for feature, coverage in validation['feature_coverage'].items():
            status = "✅" if coverage >= 90 else "⚠️" if coverage >= 80 else "❌"
            f.write(f"- **{feature}:** {coverage:.1f}% {status}\n")
        
        # Store Attribute Integration
        f.write("\n## Store Attribute Integration Status\n\n")
        f.write(f"- **Store Type Classification:** {validation['data_quality']['store_type_coverage']:.1f}% coverage\n")
        f.write(f"- **Capacity Estimation:** {validation['data_quality']['capacity_coverage']:.1f}% coverage\n")
        f.write(f"- **Temperature Integration:** {validation['data_quality']['temperature_coverage']:.1f}% coverage\n")
        f.write(f"- **Fashion/Basic Ratios:** {validation['data_quality']['fashion_ratio_coverage']:.1f}% coverage\n")
        
        # Configuration Summary
        f.write("\n## Clustering Configuration Summary\n\n")
        f.write("### Feature Groups and Weights\n")
        for group_name, group_config in config['clustering_features'].items():
            if group_config.get('enabled', False):
                weight = group_config.get('weight', 0)
                features = group_config.get('features', [])
                f.write(f"- **{group_name.replace('_', ' ').title()}:** {weight:.1%} weight, {len(features)} features\n")
        
        # Clustering Parameters
        f.write("\n### Clustering Parameters\n")
        params = config['clustering_parameters']
        f.write(f"- **Algorithm:** {params['algorithm']}\n")
        f.write(f"- **Target Clusters:** {params['n_clusters']}\n")
        f.write(f"- **Cluster Size:** {params['min_cluster_size']}-{params['max_cluster_size']} stores\n")
        
        # Issues and Recommendations
        if validation['issues']:
            f.write("\n## Issues and Recommendations\n\n")
            for issue in validation['issues']:
                f.write(f"- ⚠️ {issue}\n")
        
        # Sample Feature Matrix
        if not df.empty:
            f.write("\n## Sample Feature Matrix\n\n")
            sample_df = df.head(3)
            key_columns = ['str_code', 'store_type', 'fashion_ratio', 'basic_ratio', 
                          'size_tier', 'estimated_rack_capacity', 'sku_diversity']
            available_columns = [col for col in key_columns if col in sample_df.columns]
            
            f.write("```\n")
            f.write(sample_df[available_columns].to_string(index=False))
            f.write("\n```\n")

def main():
    """Main execution function."""
    print("=" * 60)
    print("CLUSTERING FEATURE INTEGRATION")
    print("=" * 60)
    
    # Period-aware resolution of enriched attributes for alignment with Step 35
    args = _parse_args()
    if getattr(args, 'target_yyyymm', None) and getattr(args, 'target_period', None):
        period_label = get_period_label(args.target_yyyymm, args.target_period)
    else:
        # No CLI period provided: try to infer latest period-labeled file via manifest fallback logic
        period_label = None
    enriched_path = _resolve_enriched_attributes_path(period_label) if period_label else ENRICHED_STORE_ATTRIBUTES_FILE
    if not os.path.exists(enriched_path):
        print(f"❌ ERROR: Enriched store attributes file not found: {enriched_path}")
        print("Please run step22_store_attribute_enrichment.py first.")
        return
    
    print(f"Loading enriched store attributes: {enriched_path}")
    df = pd.read_csv(enriched_path, dtype={'str_code': str})
    print(f"✓ Loaded {len(df):,} stores with {len(df.columns)} attributes")
    
    # Encode categorical features
    print("Encoding categorical features for clustering...")
    df_encoded = encode_categorical_features(df)
    
    # Create enhanced clustering configuration
    print("Creating enhanced clustering configuration...")
    config = create_enhanced_clustering_config()
    
    # Create feature matrix
    print("Creating clustering feature matrix...")
    feature_matrix = create_clustering_feature_matrix(df_encoded, config)
    print(f"✓ Created feature matrix: {len(feature_matrix)} stores × {len(feature_matrix.columns)-1} features")
    
    # Validate feature integration
    print("Validating feature integration...")
    validation = validate_feature_integration(df_encoded, config)
    
    # Save updated configuration
    print("Saving updated clustering configuration...")
    if _YAML_AVAILABLE:
        with open(UPDATED_CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        print(f"✅ Saved configuration: {UPDATED_CONFIG_FILE}")
        config_json_file = UPDATED_CONFIG_FILE.replace('.yaml', '.json')
    else:
        print("⚠️ PyYAML not available; skipping YAML. Saving JSON only.")
        config_json_file = UPDATED_CONFIG_FILE.replace('.yaml', '.json')
    
    # Save JSON for compatibility (always)
    config_json_file = UPDATED_CONFIG_FILE.replace('.yaml', '.json')
    with open(config_json_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ Saved JSON configuration: {config_json_file}")
    
    # Generate integration report
    generate_integration_report(df_encoded, config, validation)
    print(f"✅ Generated integration report: {FEATURE_INTEGRATION_REPORT}")
    
    # Save enhanced feature matrix for clustering (period-aware filename if period provided)
    feature_matrix_file = (
        f"output/enhanced_clustering_feature_matrix_{period_label}.csv" if period_label else
        "output/enhanced_clustering_feature_matrix.csv"
    )
    feature_matrix.to_csv(feature_matrix_file, index=False)
    print(f"✅ Saved feature matrix: {feature_matrix_file}")

    # Register outputs for downstream consumption (including Step 35)
    try:
        metadata = {
            "records": int(len(feature_matrix)),
            "columns": int(len(feature_matrix.columns)),
        }
        register_step_output("step23", "enhanced_clustering_feature_matrix", feature_matrix_file, metadata)
        if period_label:
            register_step_output("step23", f"enhanced_clustering_feature_matrix_{period_label}", feature_matrix_file, metadata)
        # Config files
        register_step_output("step23", "updated_clustering_config_yaml", UPDATED_CONFIG_FILE, {})
        register_step_output("step23", "updated_clustering_config_json", UPDATED_CONFIG_FILE.replace('.yaml', '.json'), {})
        register_step_output("step23", "clustering_feature_integration_report", FEATURE_INTEGRATION_REPORT, {})
    except Exception:
        pass
    
    # Display summary
    print("\n" + "=" * 60)
    print("FEATURE INTEGRATION SUMMARY")
    print("=" * 60)
    print(f"Total Stores: {validation['total_stores']:,}")
    print(f"Total Features: {validation['total_features']}")
    print(f"Clustering Ready: {'✅ Yes' if validation['clustering_readiness'] else '❌ No'}")
    
    # Feature group summary
    print("\nFeature Groups:")
    for group_name, group_config in config['clustering_features'].items():
        if group_config.get('enabled', False):
            weight = group_config.get('weight', 0)
            features = group_config.get('features', [])
            print(f"  {group_name.replace('_', ' ').title()}: {len(features)} features ({weight:.1%} weight)")
    
    # Data quality summary
    print("\nData Quality:")
    quality = validation['data_quality']
    print(f"  Store Type Coverage: {quality['store_type_coverage']:.1f}%")
    print(f"  Capacity Coverage: {quality['capacity_coverage']:.1f}%")
    print(f"  Temperature Coverage: {quality['temperature_coverage']:.1f}%")
    print(f"  Fashion Ratio Coverage: {quality['fashion_ratio_coverage']:.1f}%")
    
    if validation['issues']:
        print(f"\nIssues Found: {len(validation['issues'])}")
        for issue in validation['issues'][:3]:  # Show first 3 issues
            print(f"  ⚠️ {issue}")
        if len(validation['issues']) > 3:
            print(f"  ... and {len(validation['issues']) - 3} more issues (see report)")
    
    print("\n✅ Clustering feature integration completed successfully!")
    print("Next steps:")
    print("1. Review the integration report for any issues")
    print("2. Update step6_clustering.py to use the new configuration")
    print("3. Run clustering with enhanced store attributes")

if __name__ == "__main__":
    main()
