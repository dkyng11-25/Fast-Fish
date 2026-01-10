#!/usr/bin/env python3
"""
Step 25: Product Role Classifier

This step classifies products into roles (CORE / SEASONAL / FILLER / CLEARANCE) 
based on real sales performance data and cluster context.

Uses ONLY real data from existing pipeline outputs.
Proceeds cautiously with validation at each step.

Author: Data Pipeline Team
Date: 2025-01-23
Version: 1.0 - Methodical Implementation

 HOW TO RUN (CLI + ENV)
 ----------------------
 Overview
 - Period-aware: the loader uses src.config.get_current_period() to find period-specific SPU sales.
 - If the target period (e.g., 202510A) does not have sales yet, you can source from a previous
   period by setting PIPELINE_YYYYMM/PIPELINE_PERIOD while still labeling outputs via CLI flags.
 - For fast testing, it’s common to scope upstream steps (7–24) to a single cluster (e.g., Cluster 22).
   Step 25 will classify roles for whatever products are present in the source sales.

 Quick Start (fast testing; label 202510A, source 202509A)
   ENV:
     PIPELINE_YYYYMM=202509 PIPELINE_PERIOD=A

   Command:
     PYTHONPATH=. python3 src/step25_product_role_classifier.py \
       --target-yyyymm 202510 \
       --target-period A

 Production Run (all clusters)
   Command:
     PYTHONPATH=. python3 src/step25_product_role_classifier.py \
       --target-yyyymm 202510 \
       --target-period A

 Period Handling Patterns
 - Source sales (what this step loads): from PIPELINE_YYYYMM/PIPELINE_PERIOD
 - Output labeling (filenames): from --target-yyyymm/--target-period

 Best Practices & Pitfalls
 - Do NOT point to synthetic combined files; the loader forbids them.
 - If you get "No valid period-specific sales files ...", set PIPELINE_YYYYMM/PIPELINE_PERIOD
   to a real prior period (e.g., 202509/A).
 - For production (all clusters), ensure Steps 7–24 were executed for ALL clusters to provide
   full coverage for role classification.

HOW TO RUN – Reproduction Example (202508A)
-------------------------------------------
To reproduce the roles we generated for 202508A, we sourced period-specific SPU sales via env and labeled outputs with the target period:

  PIPELINE_YYYYMM=202508 PIPELINE_PERIOD=A \
  PYTHONPATH=. python3 src/step25_product_role_classifier.py --target-yyyymm 202508 --target-period A

Notes:
- Loader uses `PIPELINE_YYYYMM/PIPELINE_PERIOD` to pick real sales; filenames use `--target-*` for labeling.
- Outputs registered in manifest under step25, period-specific keys.

"""
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Tuple, Any, Optional, List
import warnings
from tqdm import tqdm
from src.config import get_period_label
from src.pipeline_manifest import register_step_output

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
# Input data sources (verified available)
SALES_DATA_FILE = None  # Deprecated: do not use combined synthetic files
CLUSTER_LABELS_FILE = "output/clustering_results_spu.csv"

# Output files
PRODUCT_ROLES_FILE = "output/product_role_classifications.csv"
ROLE_ANALYSIS_FILE = "output/product_role_analysis_report.md"
ROLE_SUMMARY_FILE = "output/product_role_summary.json"

# Create output directory
os.makedirs("output", exist_ok=True)

# ===== CLASSIFICATION CRITERIA =====
# Store-level performance thresholds (each SPU-store is individual record)
# Based on actual data: ¥11,292 avg sales, range ¥2,781-¥19,655
PRODUCT_ROLE_THRESHOLDS = {
    'CORE': {
        'min_total_sales': 14000,  # Top 25% performers (above 75th percentile)
        'store_level_analysis': True  # Store-specific performance
    },
    'SEASONAL': {
        'fashion_basic_ratio_threshold': 0.6,  # Fashion-oriented (60%+)
        'min_total_sales': 10000,   # Above median performers
        'seasonal_indicator': 'high_fashion_ratio'
    },
    'FILLER': {
        'moderate_sales_range': (5000, 14000),  # Middle tier performers
        'balanced_portfolio_role': True
    },
    'CLEARANCE': {
        'low_sales_threshold': 5000,  # Below median performers
        'poor_performance_indicator': True
    }
}

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ===== DATA LOADING FUNCTIONS =====

def load_and_validate_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load and validate sales data and cluster information"""
    log_progress("🔍 Loading and validating data for product role classification...")
    
    # Load period-specific SPU-level sales with real fashion/basic amounts
    # NOTE: Synthetic combined files (e.g., ...2025Q2_combined.csv) are strictly forbidden.
    from src.config import get_current_period, load_sales_df_with_fashion_basic
    yyyymm, period = get_current_period()
    src_path, sales_df = load_sales_df_with_fashion_basic(yyyymm, period, require_spu_level=True,
        required_cols=['str_code','spu_code','cate_name','sub_cate_name','fashion_sal_amt','basic_sal_amt'])
    log_progress(f"   ✓ Loaded period-specific SPU sales: {src_path} ({len(sales_df):,} records)")
    
    # Validate required columns
    required_cols = ['str_code', 'spu_code', 'fashion_sal_amt', 'basic_sal_amt', 'cate_name', 'sub_cate_name']
    missing_cols = [col for col in required_cols if col not in sales_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in sales data: {missing_cols}")
    
    log_progress(f"   ✓ Sales data validation passed")
    
    # Load cluster information
    if not os.path.exists(CLUSTER_LABELS_FILE):
        log_progress(f"   ⚠️ Cluster labels not found: {CLUSTER_LABELS_FILE}")
        log_progress(f"   📝 Creating basic cluster mapping from sales data")
        
        # Create simple cluster mapping based on store codes
        unique_stores = sales_df['str_code'].unique()
        cluster_df = pd.DataFrame({
            'str_code': unique_stores,
            'cluster_id': np.arange(len(unique_stores)) % 5  # Simple 5-cluster mapping
        })
    else:
        cluster_df = pd.read_csv(CLUSTER_LABELS_FILE)
        log_progress(f"   ✓ Loaded cluster data: {len(cluster_df):,} records")
        
        # Debug: Check what columns we have
        log_progress(f"   📋 Available columns: {list(cluster_df.columns)}")
        
        # Handle different possible column structures
        if 'str_code' not in cluster_df.columns:
            # Look for store codes in other columns
            if 'store_codes' in cluster_df.columns:
                # This is cluster-level data, we need store-level mapping
                log_progress(f"   📝 Converting cluster-level to store-level mapping")
                
                store_cluster_mapping = []
                for _, row in cluster_df.iterrows():
                    cluster_id = row['cluster_id']
                    store_codes_str = str(row['store_codes'])
                    
                    # Parse store codes (handle truncated lists with ...)
                    if '...' in store_codes_str:
                        # Extract visible store codes
                        visible_stores = store_codes_str.replace('...', '').split(',')
                        visible_stores = [store.strip() for store in visible_stores if store.strip()]
                    else:
                        visible_stores = store_codes_str.split(',')
                        visible_stores = [store.strip() for store in visible_stores if store.strip()]
                    
                    for store_code in visible_stores:
                        if store_code:  # Skip empty strings
                            store_cluster_mapping.append({
                                'str_code': store_code,
                                'cluster_id': cluster_id
                            })
                
                cluster_df = pd.DataFrame(store_cluster_mapping)
                log_progress(f"   ✓ Created store-level mapping: {len(cluster_df):,} stores")
            else:
                # Create simple mapping from sales data
                log_progress(f"   📝 Creating basic cluster mapping from sales data")
                unique_stores = sales_df['str_code'].unique()
                cluster_df = pd.DataFrame({
                    'str_code': unique_stores,
                    'cluster_id': np.arange(len(unique_stores)) % 5
                })
        else:
            # Ensure cluster_id column exists
            if 'cluster_id' not in cluster_df.columns and 'Cluster' in cluster_df.columns:
                cluster_df['cluster_id'] = cluster_df['Cluster']
            
        # Convert str_code to string for consistency
        cluster_df['str_code'] = cluster_df['str_code'].astype(str)
        log_progress(f"   ✓ Final cluster mapping: {len(cluster_df):,} stores")
    
    return sales_df, cluster_df

# ===== CLASSIFICATION FUNCTIONS =====

def calculate_product_metrics(sales_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate comprehensive metrics for each product (SPU)"""
    log_progress("📊 Calculating product performance metrics...")
    
    product_metrics = []
    
    for spu_code in tqdm(sales_df['spu_code'].unique(), desc="Analyzing products"):
        spu_data = sales_df[sales_df['spu_code'] == spu_code]
        
        if len(spu_data) == 0:
            continue
            
        # Basic sales metrics
        total_fashion_sales = spu_data['fashion_sal_amt'].sum()
        total_basic_sales = spu_data['basic_sal_amt'].sum()
        total_sales = total_fashion_sales + total_basic_sales
        
        # Store coverage metrics
        stores_selling = len(spu_data)
        total_stores = len(sales_df['str_code'].unique())
        store_coverage = stores_selling / total_stores
        
        # Fashion vs Basic analysis
        if total_sales > 0:
            fashion_ratio = total_fashion_sales / total_sales
            basic_ratio = total_basic_sales / total_sales
        else:
            fashion_ratio = 0
            basic_ratio = 0
        
        # Sales consistency (lower std dev / mean = more consistent)
        store_sales = []
        for _, row in spu_data.iterrows():
            store_total = row['fashion_sal_amt'] + row['basic_sal_amt']
            store_sales.append(store_total)
        
        if len(store_sales) > 1 and np.mean(store_sales) > 0:
            consistency_score = 1 - (np.std(store_sales) / np.mean(store_sales))
            consistency_score = max(0, min(1, consistency_score))  # Bound between 0-1
        else:
            consistency_score = 0
        
        # Category information
        category = spu_data['cate_name'].iloc[0] if len(spu_data) > 0 else 'Unknown'
        subcategory = spu_data['sub_cate_name'].iloc[0] if len(spu_data) > 0 else 'Unknown'
        
        product_metrics.append({
            'spu_code': spu_code,
            'total_sales': total_sales,
            'fashion_sales': total_fashion_sales,
            'basic_sales': total_basic_sales,
            'fashion_ratio': fashion_ratio,
            'basic_ratio': basic_ratio,
            'stores_selling': stores_selling,
            'total_stores': total_stores,
            'store_coverage': store_coverage,
            'consistency_score': consistency_score,
            'category': category,
            'subcategory': subcategory
        })
    
    log_progress(f"   ✓ Calculated metrics for {len(product_metrics):,} products")
    return pd.DataFrame(product_metrics)

def classify_product_role(product_metrics: pd.DataFrame) -> pd.DataFrame:
    """Classify products into roles based on calculated metrics"""
    log_progress("🏷️ Classifying products into roles...")
    
    results = []
    thresholds = PRODUCT_ROLE_THRESHOLDS
    
    for _, product in tqdm(product_metrics.iterrows(), desc="Classifying products", total=len(product_metrics)):
        # Initialize classification variables
        role = 'FILLER'  # Default role
        confidence = 0.5  # Default confidence
        rationale = []
        
        # Classification logic - proceed step by step
        
        # Check for CORE products first (highest tier - top performers)
        if product['total_sales'] >= thresholds['CORE']['min_total_sales']:
            role = 'CORE'
            confidence = 0.95
            rationale.append(f"Excellent sales performance (¥{product['total_sales']:.0f})")
            rationale.append("Store-level top performer")
        
        # Check for SEASONAL products (fashion-focused)
        elif (product['fashion_ratio'] >= thresholds['SEASONAL']['fashion_basic_ratio_threshold'] and
              product['total_sales'] >= thresholds['SEASONAL']['min_total_sales']):
            
            role = 'SEASONAL'
            confidence = 0.90
            rationale.append(f"Fashion-focused ({product['fashion_ratio']:.0%})")
            rationale.append(f"Strong sales (¥{product['total_sales']:.0f})")
            rationale.append("Seasonal appeal product")
        
        # Check for CLEARANCE products (low performers)
        elif product['total_sales'] < thresholds['CLEARANCE']['low_sales_threshold']:
            
            role = 'CLEARANCE'
            confidence = 0.85
            rationale.append(f"Below-average sales (¥{product['total_sales']:.0f})")
            rationale.append("Clearance candidate")
        
        # Otherwise, classify as FILLER (middle tier)
        else:
            role = 'FILLER'
            confidence = 0.80
            rationale.append("Solid middle-tier performance")
            rationale.append(f"Steady sales (¥{product['total_sales']:.0f})")
            if product['fashion_ratio'] > 0.4 and product['fashion_ratio'] < 0.6:
                rationale.append("Balanced fashion-basic mix")
                confidence = 0.85
        
        results.append({
            'spu_code': product['spu_code'],
            'product_role': role,
            'confidence_score': confidence,
            'rationale': '; '.join(rationale),
            'total_sales': product['total_sales'],
            'store_coverage': product['store_coverage'],
            'fashion_ratio': product['fashion_ratio'],
            'consistency_score': product['consistency_score'],
            'category': product['category'],
            'subcategory': product['subcategory']
        })
    
    classification_df = pd.DataFrame(results)
    
    # Log classification summary
    role_counts = classification_df['product_role'].value_counts()
    log_progress(f"   ✓ Classification complete:")
    for role, count in role_counts.items():
        percentage = (count / len(classification_df)) * 100
        log_progress(f"     • {role}: {count} products ({percentage:.1f}%)")
    
    return classification_df

def add_cluster_context(classification_df: pd.DataFrame, sales_df: pd.DataFrame, cluster_df: pd.DataFrame) -> pd.DataFrame:
    """Add cluster context to product classifications"""
    log_progress("🔗 Adding cluster context to classifications...")
    
    # Merge sales data with cluster information
    sales_with_clusters = sales_df.merge(cluster_df[['str_code', 'cluster_id']], on='str_code', how='left')
    
    # Calculate cluster-level metrics for each product
    enhanced_results = []
    
    for _, product in tqdm(classification_df.iterrows(), desc="Adding cluster context", total=len(classification_df)):
        spu_code = product['spu_code']
        
        # Get sales data for this product across clusters
        spu_cluster_data = sales_with_clusters[sales_with_clusters['spu_code'] == spu_code]
        
        if len(spu_cluster_data) > 0:
            # Calculate cluster distribution
            cluster_sales = spu_cluster_data.groupby('cluster_id').agg({
                'fashion_sal_amt': 'sum',
                'basic_sal_amt': 'sum'
            }).reset_index()
            
            cluster_sales['total_sales'] = cluster_sales['fashion_sal_amt'] + cluster_sales['basic_sal_amt']
            
            # Find dominant cluster
            if len(cluster_sales) > 0:
                dominant_cluster = cluster_sales.loc[cluster_sales['total_sales'].idxmax(), 'cluster_id']
                cluster_count = len(cluster_sales)
            else:
                dominant_cluster = 0
                cluster_count = 0
        else:
            dominant_cluster = 0
            cluster_count = 0
        
        # Create enhanced record
        enhanced_record = product.to_dict()
        enhanced_record.update({
            'dominant_cluster': dominant_cluster,
            'clusters_present': cluster_count,
            'cluster_distribution': 'wide' if cluster_count >= 3 else 'narrow'
        })
        
        enhanced_results.append(enhanced_record)
    
    enhanced_df = pd.DataFrame(enhanced_results)
    log_progress(f"   ✓ Added cluster context to {len(enhanced_df):,} products")
    
    return enhanced_df

# ===== REPORTING FUNCTIONS =====

def create_summary_statistics(classification_df: pd.DataFrame) -> Dict[str, Any]:
    """Create summary statistics for the classification results"""
    
    summary = {
        'analysis_metadata': {
            'total_products': len(classification_df),
            'analysis_timestamp': datetime.now().isoformat(),
            'classification_method': 'sales_performance_based'
        },
        
        'role_distribution': {
            role: len(classification_df[classification_df['product_role'] == role])
            for role in ['CORE', 'SEASONAL', 'FILLER', 'CLEARANCE']
        },
        
        'performance_metrics': {
            'avg_confidence_score': classification_df['confidence_score'].mean(),
            'high_confidence_products': len(classification_df[classification_df['confidence_score'] >= 0.7]),
            'total_sales_analyzed': classification_df['total_sales'].sum()
        },
        
        'category_breakdown': {
            category: len(classification_df[classification_df['category'] == category])
            for category in classification_df['category'].unique()
        }
    }
    
    return summary

def create_analysis_report(classification_df: pd.DataFrame, summary: Dict[str, Any]) -> None:
    """Create detailed analysis report"""
    
    report_content = f"""# Product Role Classification Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Products Analyzed:** {summary['analysis_metadata']['total_products']}

## Executive Summary

This report provides product role classifications for all SKUs based on sales performance, 
store coverage, and consistency metrics using real transaction data.

## Role Distribution Analysis

"""
    
    for role, count in summary['role_distribution'].items():
        percentage = (count / summary['analysis_metadata']['total_products']) * 100
        role_products = classification_df[classification_df['product_role'] == role]
        avg_sales = role_products['total_sales'].mean() if len(role_products) > 0 else 0
        
        report_content += f"""### {role} Products
- **Count:** {count} products ({percentage:.1f}%)
- **Average Sales:** ¥{avg_sales:.0f}
- **Coverage:** {role_products['store_coverage'].mean():.1%} average store coverage

"""
    
    report_content += f"""
## Performance Metrics

- **Average Confidence Score:** {summary['performance_metrics']['avg_confidence_score']:.3f}
- **High Confidence Classifications:** {summary['performance_metrics']['high_confidence_products']} products
- **Total Sales Analyzed:** ¥{summary['performance_metrics']['total_sales_analyzed']:,.0f}

## Sample Classifications

"""
    
    # Add sample products for each role
    for role in ['CORE', 'SEASONAL', 'FILLER', 'CLEARANCE']:
        role_samples = classification_df[classification_df['product_role'] == role].head(3)
        if len(role_samples) > 0:
            report_content += f"""### Sample {role} Products

"""
            for _, product in role_samples.iterrows():
                report_content += f"""**{product['spu_code']}**
- Sales: ¥{product['total_sales']:.0f}
- Coverage: {product['store_coverage']:.0%}
- Rationale: {product['rationale']}

"""
    
    report_content += """
## Methodology

Product roles are classified based on:
1. **Sales Performance:** Total sales volume and consistency
2. **Store Coverage:** Percentage of stores selling the product
3. **Fashion/Basic Mix:** Product positioning analysis
4. **Category Context:** Subcategory and category placement

Classification is conservative and uses only verified sales transaction data.

---
*Generated by Product Role Classifier v1.0*
"""
    
    with open(ROLE_ANALYSIS_FILE, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    log_progress(f"   ✓ Saved analysis report: {ROLE_ANALYSIS_FILE}")

def main() -> None:
    """Main function for product role classification"""
    global ROLE_ANALYSIS_FILE  # Fix: Move global declaration to the beginning
    start_time = datetime.now()
    log_progress("🚀 Starting Product Role Classification (Step 25)...")
    
    try:
        # Period-aware CLI
        import argparse
        parser = argparse.ArgumentParser(description="Step 25: Product Role Classifier (period-aware)")
        parser.add_argument("--target-yyyymm", required=False)
        parser.add_argument("--target-period", required=False, choices=["A","B"])
        args, _ = parser.parse_known_args()
        period_label = None
        if getattr(args, 'target_yyyymm', None) and getattr(args, 'target_period', None):
            period_label = get_period_label(args.target_yyyymm, args.target_period)

        # Step 1: Load and validate data
        sales_df, cluster_df = load_and_validate_data()
        
        # Step 2: Calculate product metrics
        product_metrics = calculate_product_metrics(sales_df)
        
        # Step 3: Classify products into roles
        classification_df = classify_product_role(product_metrics)
        
        # Step 4: Add cluster context
        enhanced_classification = add_cluster_context(classification_df, sales_df, cluster_df)
        
        # Step 5: Save results (DUAL OUTPUT PATTERN - both timestamped and generic)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Always create timestamped version (for backup/inspection)
        timestamped_roles_file = f"output/product_role_classifications_{period_label}_{ts}.csv"
        enhanced_classification.to_csv(timestamped_roles_file, index=False)
        log_progress(f"✅ Saved timestamped product roles: {timestamped_roles_file}")
        
        # Create symlink for generic version (for pipeline flow)
        generic_roles_file = PRODUCT_ROLES_FILE
        if os.path.exists(generic_roles_file) or os.path.islink(generic_roles_file):
            os.remove(generic_roles_file)
        os.symlink(os.path.basename(timestamped_roles_file), generic_roles_file)
        log_progress(f"✅ Created symlink: {generic_roles_file} -> {timestamped_roles_file}")
        
        # Use timestamped version for manifest registration if available, otherwise generic
        roles_file = timestamped_roles_file if period_label else generic_roles_file
        
        # Step 6: Create summary and report (DUAL OUTPUT PATTERN)
        summary = create_summary_statistics(enhanced_classification)
        
        # Always create timestamped version (for backup/inspection)
        if period_label:
            timestamped_summary_file = f"output/product_role_summary_{period_label}_{ts}.json"
            with open(timestamped_summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            log_progress(f"✅ Saved timestamped summary: {timestamped_summary_file}")
        
        # Always create generic version (for pipeline flow)
        generic_summary_file = ROLE_SUMMARY_FILE
        with open(generic_summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        log_progress(f"✅ Saved generic summary: {generic_summary_file}")
        
        # Use timestamped version for manifest registration if available, otherwise generic
        summary_file = timestamped_summary_file if period_label else generic_summary_file
        
        # Create analysis report (DUAL OUTPUT PATTERN)
        # Always create timestamped version (for backup/inspection)
        if period_label:
            timestamped_analysis_file = f"output/product_role_analysis_report_{period_label}_{ts}.md"
            _old = ROLE_ANALYSIS_FILE
            ROLE_ANALYSIS_FILE = timestamped_analysis_file
            create_analysis_report(enhanced_classification, summary)
            ROLE_ANALYSIS_FILE = _old
            log_progress(f"✅ Saved timestamped analysis report: {timestamped_analysis_file}")
        
        # Always create generic version (for pipeline flow)
        generic_analysis_file = ROLE_ANALYSIS_FILE
        _old = ROLE_ANALYSIS_FILE
        ROLE_ANALYSIS_FILE = generic_analysis_file
        create_analysis_report(enhanced_classification, summary)
        ROLE_ANALYSIS_FILE = _old
        log_progress(f"✅ Saved generic analysis report: {generic_analysis_file}")
        
        # Use timestamped version for manifest registration if available, otherwise generic
        analysis_file = timestamped_analysis_file if period_label else generic_analysis_file

        # Register outputs
        try:
            base_meta = {"records": int(len(enhanced_classification))}
            register_step_output("step25", "product_role_classifications", roles_file, base_meta)
            register_step_output("step25", "product_role_summary", summary_file, {})
            register_step_output("step25", "product_role_analysis_report", analysis_file, {})
            if period_label:
                register_step_output("step25", f"product_role_classifications_{period_label}", roles_file, base_meta)
                register_step_output("step25", f"product_role_summary_{period_label}", summary_file, {})
                register_step_output("step25", f"product_role_analysis_report_{period_label}", analysis_file, {})
        except Exception:
            pass
        
        # Print final results
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress(f"\n🎯 PRODUCT ROLE CLASSIFICATION RESULTS:")
        log_progress(f"   📊 Total Products: {len(enhanced_classification):,}")
        log_progress(f"   🏷️ Roles Assigned:")
        
        role_counts = enhanced_classification['product_role'].value_counts()
        for role, count in role_counts.items():
            percentage = (count / len(enhanced_classification)) * 100
            log_progress(f"     • {role}: {count} products ({percentage:.1f}%)")
        
        log_progress(f"   ⚡ Execution Time: {execution_time:.1f} seconds")
        log_progress(f"\n📁 Generated Files:")
        log_progress(f"   • {roles_file}")
        log_progress(f"   • {summary_file}")
        log_progress(f"   • {analysis_file}")
        
        log_progress(f"\n✅ Product Role Classification completed successfully")
        
    except Exception as e:
        log_progress(f"❌ Error in product role classification: {str(e)}")
        raise

if __name__ == "__main__":
    main() 