#!/usr/bin/env python3
"""
Step 33: Store-level Merchandising Rule Generation

Builds on Step 32 enhanced clustering results to create individualized merchandising rules
for each store based on their cluster assignment and attributes.

Author: Data Pipeline Team
Date: 2025-01-26
Version: 1.0
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, List
import warnings
import argparse

try:
    from src.config import get_period_label
    from src.pipeline_manifest import get_manifest, register_step_output
    from src.output_utils import create_output_with_symlinks
except Exception:
    from config import get_period_label
    from pipeline_manifest import get_manifest, register_step_output
    from output_utils import create_output_with_symlinks

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
# Input files (period-aware resolution in main)
ENHANCED_CLUSTERING_RESULTS = "output/enhanced_clustering_results.csv"

# Output files (period-labeled in main)
STORE_LEVEL_MERCHANDISING_RULES = "output/store_level_merchandising_rules.csv"
STORE_LEVEL_RULES_REPORT = "output/store_level_merchandising_rules_report.md"

# Create output directory
os.makedirs("output", exist_ok=True)

# ===== BUSINESS RULES CONFIGURATION =====
# Style-based allocation ratios
STYLE_ALLOCATION_RULES = {
    'Fashion-Heavy': {'fashion_ratio': 0.7, 'basic_ratio': 0.3},
    'Balanced-Mix': {'fashion_ratio': 0.5, 'basic_ratio': 0.5},
    'Basic-Focus': {'fashion_ratio': 0.2, 'basic_ratio': 0.8}
}

# Capacity-based guidelines
CAPACITY_GUIDELINES = {
    'Large-Volume': {'utilization_target': 0.85, 'buffer_stock': 0.15},
    'High-Capacity': {'utilization_target': 0.80, 'buffer_stock': 0.20},
    'Efficient-Size': {'utilization_target': 0.90, 'buffer_stock': 0.10}
}

# Temperature adjustment factors
TEMPERATURE_ADJUSTMENTS = {
    'Warm-South': {'seasonal_factor': 1.15, 'fashion_boost': 0.1},
    'Moderate-Central': {'seasonal_factor': 1.0, 'fashion_boost': 0.0},
    'Cool-North': {'seasonal_factor': 0.9, 'fashion_boost': -0.05}
}

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_clustering_results(period_label: str) -> pd.DataFrame:
    """Load enhanced clustering results with merchandising tags (period-aware)."""
    log_progress("📊 Loading enhanced clustering results...")
    
    # Prefer Step 32 manifest-backed period-labeled
    try:
        man = get_manifest().manifest if hasattr(get_manifest(), 'manifest') else (get_manifest() or {})
        step32 = (man.get('steps', {}).get('step32', {}) or {}).get('outputs', {})
        candidates = [
            (step32.get(f'enhanced_clustering_results_{period_label}') or {}).get('file_path') if isinstance(step32.get(f'enhanced_clustering_results_{period_label}'), dict) else step32.get(f'enhanced_clustering_results_{period_label}'),
            (step32.get('enhanced_clustering_results') or {}).get('file_path') if isinstance(step32.get('enhanced_clustering_results'), dict) else step32.get('enhanced_clustering_results'),
            f"output/enhanced_clustering_results_{period_label}.csv",
            ENHANCED_CLUSTERING_RESULTS,
        ]
        path = next((p for p in candidates if p and os.path.exists(p)), ENHANCED_CLUSTERING_RESULTS)
    except Exception:
        path = ENHANCED_CLUSTERING_RESULTS
    
    results_df = pd.read_csv(path)
    if 'str_code' in results_df.columns:
        results_df['str_code'] = results_df['str_code'].astype(str)
    
    log_progress(f"   ✓ Loaded clustering results: {len(results_df):,} stores")
    return results_df

def generate_store_level_rules(results_df: pd.DataFrame) -> pd.DataFrame:
    """Generate individualized merchandising rules for each store"""
    log_progress("🔧 Generating store-level merchandising rules...")
    
    # Create rules dataframe
    rules_data = []
    
    for _, store in results_df.iterrows():
        str_code = store['str_code']
        
        # Extract store attributes
        style_tag = store.get('store_style_profile', 'Balanced-Mix')
        capacity_tag = store.get('size_tier', 'Efficient-Size')
        # Extract geographic tag from temperature_zone
        temp_zone = store.get('temperature_zone', 'Moderate-Central')
        if 'Moderate-Central' in temp_zone:
            geo_tag = 'Moderate-Central'
        elif 'Warm-South' in temp_zone:
            geo_tag = 'Warm-South'
        elif 'Cool-North' in temp_zone:
            geo_tag = 'Cool-North'
        else:
            geo_tag = 'Moderate-Central'
        cluster_name = store.get('cluster_name', 'Unknown')
        operational_tag = store.get('operational_tag', 'Unknown')
        
        # Get allocation ratios based on style
        allocation = STYLE_ALLOCATION_RULES.get(style_tag, {'fashion_ratio': 0.5, 'basic_ratio': 0.5})
        
        # Get capacity guidelines
        capacity_guidelines = CAPACITY_GUIDELINES.get(capacity_tag, {'utilization_target': 0.85, 'buffer_stock': 0.15})
        
        # Get temperature adjustments
        temp_adjustments = TEMPERATURE_ADJUSTMENTS.get(geo_tag, {'seasonal_factor': 1.0, 'fashion_boost': 0.0})
        
        # Apply temperature adjustment to fashion ratio
        adjusted_fashion_ratio = min(1.0, allocation['fashion_ratio'] + temp_adjustments['fashion_boost'])
        adjusted_basic_ratio = 1.0 - adjusted_fashion_ratio
        
        # Calculate inventory recommendations
        estimated_capacity = store.get('estimated_rack_capacity', 400)
        # Handle NaN or missing capacity values
        if pd.isna(estimated_capacity) or estimated_capacity is None:
            estimated_capacity = 400  # Default capacity
        
        # Calculate recommended capacities with proper handling
        fashion_capacity_float = estimated_capacity * adjusted_fashion_ratio * capacity_guidelines['utilization_target']
        basic_capacity_float = estimated_capacity * adjusted_basic_ratio * capacity_guidelines['utilization_target']
        
        # Handle NaN results
        if pd.isna(fashion_capacity_float) or fashion_capacity_float is None:
            recommended_fashion_capacity = 0
        else:
            recommended_fashion_capacity = int(fashion_capacity_float)
            
        if pd.isna(basic_capacity_float) or basic_capacity_float is None:
            recommended_basic_capacity = 0
        else:
            recommended_basic_capacity = int(basic_capacity_float)
        
        # Seasonal adjustment factor
        seasonal_factor = temp_adjustments['seasonal_factor']
        
        # Create rule entry
        rule_entry = {
            'str_code': str_code,
            'cluster_id': store.get('cluster_id', -1),
            'cluster_name': cluster_name,
            'operational_tag': operational_tag,
            'style_tag': style_tag,
            'capacity_tag': capacity_tag,
            'geographic_tag': geo_tag,
            'temperature_zone': store.get('temperature_zone', 'Unknown'),
            'fashion_allocation_ratio': round(adjusted_fashion_ratio, 3),
            'basic_allocation_ratio': round(adjusted_basic_ratio, 3),
            'capacity_utilization_target': capacity_guidelines['utilization_target'],
            'recommended_fashion_capacity': recommended_fashion_capacity,
            'recommended_basic_capacity': recommended_basic_capacity,
            'total_recommended_capacity': recommended_fashion_capacity + recommended_basic_capacity,
            'seasonal_adjustment_factor': seasonal_factor,
            'buffer_stock_percentage': capacity_guidelines['buffer_stock'],
            'estimated_rack_capacity': int(estimated_capacity),
            'priority_score': calculate_priority_score(store),
            'implementation_notes': generate_implementation_notes(style_tag, capacity_tag, geo_tag)
        }
        
        rules_data.append(rule_entry)
    
    rules_df = pd.DataFrame(rules_data)
    log_progress(f"   ✅ Generated rules for {len(rules_df):,} stores")
    
    return rules_df

def calculate_priority_score(store: pd.Series) -> float:
    """Calculate priority score for store merchandising implementation"""
    # Base score on sales performance and cluster importance
    sales_amt = store.get('total_sales_amt', 0)
    cluster_importance = 1.0  # Could be enhanced based on cluster performance
    
    # Normalize sales amount (assuming max ~500K)
    normalized_sales = min(1.0, sales_amt / 500000)
    
    # Priority score combines sales performance and cluster importance
    priority_score = (normalized_sales * 0.7 + cluster_importance * 0.3) * 100
    
    return round(priority_score, 1)

def generate_implementation_notes(style_tag: str, capacity_tag: str, geo_tag: str) -> str:
    """Generate implementation notes based on store characteristics"""
    notes = []
    
    # Style-based recommendations
    if style_tag == 'Fashion-Heavy':
        notes.append("Focus on new arrivals and trend-driven products")
    elif style_tag == 'Basic-Focus':
        notes.append("Emphasize core essentials and staple items")
    else:
        notes.append("Balance fashion and basic product mix")
    
    # Capacity-based recommendations
    if capacity_tag == 'Large-Volume':
        notes.append("Optimize space utilization with vertical displays")
    elif capacity_tag == 'High-Capacity':
        notes.append("Focus on high-turnover SKUs in prime locations")
    else:
        notes.append("Maximize efficiency with compact, curated displays")
    
    # Geographic/temperature recommendations
    if geo_tag == 'Warm-South':
        notes.append("Seasonal: Increase summer collection allocation")
    elif geo_tag == 'Cool-North':
        notes.append("Seasonal: Boost winter collection and layering items")
    else:
        notes.append("Seasonal: Maintain balanced year-round assortment")
    
    return "; ".join(notes)

def create_rules_report(rules_df: pd.DataFrame) -> None:
    """Create comprehensive report on store-level merchandising rules"""
    log_progress("📝 Creating store-level merchandising rules report...")
    
    # Define generic rules report path
    generic_rules_report = "output/store_level_merchandising_rules_report.md"
    
    # Generate summary statistics
    total_stores = len(rules_df)
    avg_fashion_ratio = rules_df['fashion_allocation_ratio'].mean()
    avg_capacity = rules_df['estimated_rack_capacity'].mean()
    avg_priority = rules_df['priority_score'].mean()
    
    # Style distribution
    style_distribution = rules_df['style_tag'].value_counts()
    
    # Capacity distribution
    capacity_distribution = rules_df['capacity_tag'].value_counts()
    
    # Geographic distribution
    geo_distribution = rules_df['geographic_tag'].value_counts()
    
    report_content = f"""# Store-Level Merchandising Rules Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Stores Analyzed:** {total_stores:,}

## 📊 **SUMMARY STATISTICS**

- **Average Fashion Allocation:** {avg_fashion_ratio:.1%}
- **Average Rack Capacity:** {avg_capacity:,.0f} units
- **Average Priority Score:** {avg_priority:.1f}/100

## 🏷️ **STYLE DISTRIBUTION**
"""
    
    for style, count in style_distribution.items():
        percentage = (count / total_stores) * 100
        report_content += f"- **{style}:** {count:,} stores ({percentage:.1f}%)\n"
    
    report_content += """\n## 📦 **CAPACITY DISTRIBUTION**\n"""
    
    for capacity, count in capacity_distribution.items():
        percentage = (count / total_stores) * 100
        report_content += f"- **{capacity}:** {count:,} stores ({percentage:.1f}%)\n"
    
    report_content += """\n## 🌡️ **GEOGRAPHIC DISTRIBUTION**\n"""
    
    for geo, count in geo_distribution.items():
        percentage = (count / total_stores) * 100
        report_content += f"- **{geo}:** {count:,} stores ({percentage:.1f}%)\n"
    
    report_content += """\n## 🎯 **KEY RECOMMENDATIONS**\n\n### **Implementation Priority**\n1. **High Priority Stores:** " + str(len(rules_df[rules_df['priority_score'] >= 80])) + " stores (Priority Score ≥ 80)\n2. **Medium Priority Stores:** " + str(len(rules_df[(rules_df['priority_score'] >= 60) & (rules_df['priority_score'] < 80)])) + " stores (Priority Score 60-79)\n3. **Standard Implementation:** " + str(len(rules_df[rules_df['priority_score'] < 60])) + " stores (Priority Score < 60)\n\n### **Resource Allocation**\n- **Fashion-Focused Stores:** Increase new arrival frequency by 25%\n- **Basic-Focused Stores:** Optimize core SKU selection and pricing\n- **High-Capacity Stores:** Implement advanced space management strategies\n- **Temperature-Zone Stores:** Apply seasonal adjustment factors\n\n## 📋 **DELIVERABLES**\n\n- ✅ Store-level merchandising rules generated for all " + str(total_stores) + " stores\n- ✅ Individual capacity recommendations with utilization targets\n- ✅ Seasonal adjustment factors for climate-appropriate planning\n- ✅ Priority scoring for implementation sequencing\n\n## 🚀 **NEXT STEPS**\n\n1. **Step 34:** Cluster-level merchandising optimization\n2. **Deployment:** Integrate rules into store management systems\n3. **Monitoring:** Track implementation effectiveness and ROI\n4. **Refinement:** Update rules based on performance data\n\n*Report generated by Store-Level Merchandising Rules Generator v1.0*\n"""
    
    # Save report (DUAL OUTPUT PATTERN)
    # Save timestamped version (for backup/inspection)
    with open(STORE_LEVEL_RULES_REPORT, 'w') as f:
        f.write(report_content)
    log_progress(f"   ✅ Created timestamped rules report: {STORE_LEVEL_RULES_REPORT}")
    
    # Save generic version (for pipeline flow)
    with open(generic_rules_report, 'w') as f:
        f.write(report_content)
    log_progress(f"   ✅ Created generic rules report: {generic_rules_report}")

def main() -> None:
    """Main function for store-level merchandising rule generation (period-aware)."""
    start_time = datetime.now()
    log_progress("🚀 Starting Step 33: Store-level Merchandising Rule Generation...")
    
    try:
        parser = argparse.ArgumentParser(description='Step 33: Store-level Merchandising Rules (period-aware)')
        parser.add_argument('--target-yyyymm', required=True)
        parser.add_argument('--target-period', required=True, choices=['A','B'])
        args = parser.parse_args()
        period_label = get_period_label(args.target_yyyymm, args.target_period)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # DUAL OUTPUT PATTERN - Define both timestamped and generic versions
        global STORE_LEVEL_MERCHANDISING_RULES, STORE_LEVEL_RULES_REPORT
        
        # Timestamped versions (for backup/inspection)
        timestamped_rules_output = f"output/store_level_merchandising_rules_{period_label}_{ts}.csv"
        timestamped_rules_report = f"output/store_level_merchandising_rules_report_{period_label}_{ts}.md"
        
        # Generic versions (for pipeline flow)
        generic_rules_output = "output/store_level_merchandising_rules.csv"
        generic_rules_report = "output/store_level_merchandising_rules_report.md"
        
        # Use timestamped versions for manifest registration
        STORE_LEVEL_MERCHANDISING_RULES = timestamped_rules_output
        STORE_LEVEL_RULES_REPORT = timestamped_rules_report
        
        # Load clustering results
        results_df = load_clustering_results(period_label)
        
        # Generate store-level rules
        rules_df = generate_store_level_rules(results_df)
        
        # Save rules (DUAL OUTPUT PATTERN)
        # Use create_output_with_symlinks to create all three outputs:
        # 1. Timestamped file: store_level_merchandising_rules_202510A_20251003_105008.csv
        # 2. Period symlink: store_level_merchandising_rules_202510A.csv
        # 3. Generic symlink: store_level_merchandising_rules.csv
        base_path = "output/store_level_merchandising_rules"
        timestamped_file, period_file, generic_file = create_output_with_symlinks(
            df=rules_df,
            base_path=base_path,
            period_label=period_label
        )
        log_progress(f"✅ Saved merchandising rules with dual output pattern:")
        log_progress(f"   Timestamped: {timestamped_file}")
        log_progress(f"   Period: {period_file}")
        log_progress(f"   Generic: {generic_file}")
        
        # Create comprehensive report
        create_rules_report(rules_df)
        
        # Register outputs
        try:
            meta = {
                'target_year': int(args.target_yyyymm[:4]),
                'target_month': int(args.target_yyyymm[4:]),
                'target_period': args.target_period,
                'records': len(rules_df),
                'columns': len(rules_df.columns),
            }
            register_step_output('step33', 'store_level_merchandising_rules', STORE_LEVEL_MERCHANDISING_RULES, meta)
            register_step_output('step33', f'store_level_merchandising_rules_{period_label}', STORE_LEVEL_MERCHANDISING_RULES, meta)
            register_step_output('step33', 'store_level_merchandising_rules_report', STORE_LEVEL_RULES_REPORT, meta)
            register_step_output('step33', f'store_level_merchandising_rules_report_{period_label}', STORE_LEVEL_RULES_REPORT, meta)
        except Exception:
            pass
        
        # Summary
        log_progress(f"\n🎯 STORE-LEVEL RULES GENERATION COMPLETE:")
        log_progress(f"   📊 Stores Processed: {len(rules_df):,}")
        log_progress(f"   📋 Rules Generated: {len(rules_df.columns)} rule dimensions per store")
        log_progress(f"   📁 Output Files:")
        log_progress(f"      • {STORE_LEVEL_MERCHANDISING_RULES}")
        log_progress(f"      • {STORE_LEVEL_RULES_REPORT}")
        
        log_progress(f"\n✅ Step 33 completed in {(datetime.now() - start_time).total_seconds():.1f} seconds")
        
    except Exception as e:
        log_progress(f"❌ Error in store-level rule generation: {e}")
        raise

if __name__ == "__main__":
    main()
