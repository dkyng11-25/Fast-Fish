#!/usr/bin/env python3
"""
Step 15: Download/Create Historical Baseline (Period-Aware)
==========================================================

Creates historical baselines for the specified baseline period (default: last
year same month, same A/B period) to compare against the current target period.

Outputs include:
- Historical SPU counts by Store Group × Sub-Category
- Historical sales performance metrics
- Year-over-year comparison vs. current Step 14 output
- Historical reference compatible with enhanced Fast Fish format

Integrations:
- Reads Step 14 enhanced output via pipeline manifest (or CLI override)
- Registers all outputs in pipeline manifest for downstream steps

Pipeline Flow:
Step 14 → Step 15 → Step 16 → Step 17 → Step 18

 HOW TO RUN (CLI + ENV) — Read this before executing
 ----------------------------------------------------
 Overview
 - Period-aware: Step 15 creates a historical reference for a baseline label (defaults to last-year same month + same half A/B) relative to a target period you specify.
 - Why a YoY baseline: using last year’s same window preserves seasonality and avoids skew (e.g., summer vs winter). This makes downstream comparisons and targets meaningful.

 Quick Start (target 202510A → baseline 202410A by default)
   Command:
     PYTHONPATH=. python3 src/step15_download_historical_baseline.py \
       --target-yyyymm 202510 \
       --target-period A

   Notes
   - This computes the baseline automatically as 202410A. You can override with --baseline-yyyymm/--baseline-period if business requires a different comparison window.

 Overrides (why and when)
 - --baseline-yyyymm/--baseline-period
   Why: If your planning intentionally shifts seasons (e.g., early fall launch using August data), you may need to compare to a different historical window. Document the rationale when overriding.
 - --current-analysis-file
   Why: Step 15 optionally compares baseline to the current Step 14 enhanced output. If the manifest lacks the period-labeled Step 14 file (or you ran a one-off), pass the explicit path here.

 Common failure modes (and what to do)
 - Historical file not found for computed baseline
   • Cause: API data for `complete_spu_sales_{baseline}.csv` not downloaded or not on disk.
   • Fix: run Step 1 for the baseline period (VPN HK if needed) and ensure `data/api_data/complete_spu_sales_{YYYYMMP}.csv` exists.
 - "Current analysis file not found via CLI/manifest; proceeding with historical-only reference"
   • Cause: Step 14 enhanced output not registered in manifest for the target label.
   • Fix: pass --current-analysis-file explicitly or rerun Step 14 to register period-labeled output.
 - Taxonomy mismatches (Category/Subcategory)
   • Cause: differences between historical and current files (naming or normalization).
   • Fix: ensure Step 14 uses consistent taxonomy; when in doubt, verify Category/Subcategory normalization and that Step 1/14 produced the expected columns.

 Why this configuration leads to stable outcomes
 - YoY baseline alignment keeps the comparison window seasonally consistent.
 - Restricting to real, period-labeled SPU sales avoids synthetic totals and ensures store counts and SPU mixes are comparable.
 - Reading Step 14 via manifest ensures we compare against the exact recommendation set intended for the target period.

 Manifest notes
 - This step reads Step 14 from the manifest when available and registers its own outputs (historical_reference_*, yoy_comparison_*, historical_insights_*). Downstream steps should prefer manifest lookups rather than hardcoded paths.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
from typing import Dict, List, Tuple, Optional
import logging
import argparse
# Resilient imports for module vs script execution
try:
    from src.pipeline_manifest import get_step_input, register_step_output
    from src.config import get_api_data_files, get_output_files
    from src.output_utils import create_output_with_symlinks
except ModuleNotFoundError:
    try:
        from pipeline_manifest import get_step_input, register_step_output
        from config import get_api_data_files, get_output_files
        from output_utils import create_output_with_symlinks
    except ModuleNotFoundError:
        # Add project root to path and retry
        import sys
        import os as _os
        _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from src.pipeline_manifest import get_step_input, register_step_output
        from src.config import get_api_data_files, get_output_files
        from src.output_utils import create_output_with_symlinks

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _parse_args():
    """Parse CLI arguments for Step 15."""
    parser = argparse.ArgumentParser(description="Step 15: Download/Create Historical Baseline")
    parser.add_argument("--target-yyyymm", required=True, help="Target year-month for current run, e.g. 202509")
    parser.add_argument("--target-period", choices=["A", "B"], required=True, help="Target period (A or B)")
    parser.add_argument("--baseline-yyyymm", help="Override baseline year-month (defaults to last-year same month)")
    parser.add_argument("--baseline-period", choices=["A", "B"], help="Override baseline period (defaults to target-period)")
    parser.add_argument("--current-analysis-file", help="Path to Step 14 enhanced output; if omitted, uses pipeline manifest or latest enhanced file")
    return parser.parse_args()

def _compute_baseline_yyyymm(target_yyyymm: str) -> str:
    """Compute last year's same month in yyyymm format."""
    if not (isinstance(target_yyyymm, str) and len(target_yyyymm) == 6 and target_yyyymm.isdigit()):
        raise ValueError(f"Invalid target_yyyymm: {target_yyyymm}")
    year = int(target_yyyymm[:4])
    month = int(target_yyyymm[4:6])
    return f"{year - 1}{month:02d}"

def _load_cluster_mapping(yyyymm: Optional[str] = None, period: Optional[str] = None) -> pd.DataFrame:
    """Load cluster mapping to create consistent Store Group names (aligns with Step 14).
    Prefer period-labeled cluster results via config output helpers; fallback to generic file.
    """
    candidates: List[str] = []
    try:
        if yyyymm and period:
            cfg = get_output_files('spu', yyyymm, period)
            labeled = cfg.get('clustering_results')
            if labeled:
                candidates.append(labeled)
    except Exception:
        pass
    candidates.extend([
        "output/clustering_results_spu.csv",
        "output/clustering_results.csv",
    ])
    for path in candidates:
        if path and os.path.exists(path):
            try:
                df = pd.read_csv(path)
                if 'str_code' in df.columns:
                    df['str_code'] = df['str_code'].astype(str)
                logger.info(f"Loaded cluster mapping from: {path} ({len(df)})")
                return df
            except Exception as e:
                logger.warning(f"Error loading cluster mapping from {path}: {e}")
                continue
    logger.warning("Clustering results not found; will mark groups as Unknown")
    return pd.DataFrame()

def load_historical_data(baseline_yyyymm: str, baseline_period: str) -> pd.DataFrame:
    """Load the historical SPU data for the requested baseline period, e.g., 202409A (period-aware)."""
    try:
        api = {}
        try:
            api = get_api_data_files(baseline_yyyymm, baseline_period)
        except Exception:
            api = {}
        candidates: List[str] = []
        # Prefer explicit keys from config helpers
        for key in [
            'spu_sales',
            'complete_spu_sales',
        ]:
            path = api.get(key)
            if path:
                candidates.append(path)
        # Fallback direct path (still period-specific, forbidden combined avoided)
        candidates.append(f"data/api_data/complete_spu_sales_{baseline_yyyymm}{baseline_period}.csv")
        historical_file = next((p for p in candidates if p and os.path.exists(p)), None)
        if not historical_file:
            raise FileNotFoundError(f"Historical data file not found for baseline {baseline_yyyymm}{baseline_period}")
        logger.info(f"Loading historical data from: {historical_file}")
        df = pd.read_csv(historical_file, dtype={'str_code': str, 'spu_code': str})
        logger.info(f"Loaded {len(df):,} historical SPU sales records for {baseline_yyyymm}{baseline_period}")
        logger.info(f"Categories: {df['cate_name'].nunique()}")
        logger.info(f"Sub-categories: {df['sub_cate_name'].nunique()}")
        logger.info(f"Stores: {df['str_code'].nunique()}")
        logger.info(f"SPUs: {df['spu_code'].nunique()}")
        return df
    except Exception as e:
        logger.error(f"Error loading historical data: {e}")
        raise

def create_store_groups(df: pd.DataFrame, cluster_mapping_df: pd.DataFrame) -> pd.DataFrame:
    """Create store groups using real clustering only (no synthetic fallback)."""
    df_with_groups = df.copy()
    if not cluster_mapping_df.empty and 'Cluster' in cluster_mapping_df.columns:
        mapping = dict(zip(cluster_mapping_df['str_code'].astype(str), cluster_mapping_df['Cluster']))
        def map_group(code: str) -> str:
            code_s = str(code)
            if code_s in mapping and pd.notna(mapping[code_s]):
                return f"Store Group {int(mapping[code_s]) + 1}"
            return "Store Group Unknown"
        df_with_groups['store_group'] = df_with_groups['str_code'].apply(map_group)
        # Diagnostics: coverage of real cluster mapping
        try:
            unknown_count = int(df_with_groups['store_group'].eq('Store Group Unknown').sum())
            total_rows = int(len(df_with_groups))
            logger.info(
                f"Cluster mapping coverage: {total_rows - unknown_count}/{total_rows} mapped, {unknown_count} Unknown"
            )
        except Exception:
            pass
    else:
        logger.error("Cluster mapping unavailable; assigning all rows to 'Store Group Unknown'")
        df_with_groups['store_group'] = "Store Group Unknown"
        try:
            logger.info(f"Cluster mapping coverage: 0/{len(df_with_groups)} mapped, {len(df_with_groups)} Unknown")
        except Exception:
            pass
    return df_with_groups

def analyze_historical_spu_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze historical SPU counts by Store Group × Sub-Category."""
    
    logger.info("Analyzing historical SPU counts by Store Group × Sub-Category...")
    
    # Ensure expected columns exist and are numeric where applicable
    for col in ['quantity', 'spu_sales_amt']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = np.nan
    # Group by Store Group × Sub-Category and count distinct SPUs; NA-safe sums
    historical_counts = df.groupby(['store_group', 'cate_name', 'sub_cate_name']).agg({
        'spu_code': 'nunique',
        'quantity': (lambda s: s.sum(min_count=1)),
        'spu_sales_amt': (lambda s: s.sum(min_count=1)),
        'str_code': 'nunique'
    }).reset_index()
    
    historical_counts.columns = ['store_group', 'category', 'sub_category', 'historical_spu_count', 
                                'historical_total_quantity', 'historical_total_sales', 'historical_store_count']
    
    # Calculate performance metrics (NA-safe; no divide-by-zero)
    with np.errstate(divide='ignore', invalid='ignore'):
        historical_counts['historical_avg_sales_per_spu'] = (
            historical_counts['historical_total_sales'] / historical_counts['historical_spu_count']
        )
        historical_counts['historical_avg_quantity_per_spu'] = (
            historical_counts['historical_total_quantity'] / historical_counts['historical_spu_count']
        )
        historical_counts['historical_sales_per_store'] = (
            historical_counts['historical_total_sales'] / historical_counts['historical_store_count']
        )
    
    logger.info(f"Found {len(historical_counts)} historical Store Group × Sub-Category combinations")
    
    return historical_counts

def load_current_analysis(current_file: Optional[str], preferred_period: Optional[str], target_yyyymm: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Load the current Step 14 enhanced output for comparison.
    If current_file is None, try manifest; then fallback to latest enhanced file in output/.
    If preferred_period is provided, attempt to select a file whose Period matches it."""
    try:
        path = current_file
        if not path:
            # Prefer Step 14 enhanced output from manifest (period-labeled first)
            if target_yyyymm and preferred_period:
                try:
                    period_label = f"{str(target_yyyymm)}{str(preferred_period)}"
                    path = get_step_input("step14", f"enhanced_fast_fish_format_{period_label}")
                except Exception:
                    path = None
            if not path:
                try:
                    path = get_step_input("step14", "enhanced_fast_fish_format")
                except Exception:
                    path = None
        if not path:
            # Fallback to latest enhanced fast fish file
            import glob
            candidates = glob.glob("output/enhanced_fast_fish_format_*.csv")
            path = max(candidates, key=os.path.getctime) if candidates else None
        if not path or not os.path.exists(path):
            logger.warning("Current analysis file not found via CLI/manifest; proceeding with historical-only reference")
            return None
        logger.info(f"Loading current analysis from: {path}")
        df = pd.read_csv(path)
        # If a preferred period is specified and does not match, try to find a matching file
        if preferred_period and 'Period' in df.columns:
            file_period = str(df['Period'].iloc[0]) if not df.empty else None
            if file_period and file_period != preferred_period:
                logger.info(
                    f"Manifest/CLI file Period {file_period} != preferred {preferred_period}; searching for a matching enhanced file"
                )
                import glob
                candidates = sorted(
                    glob.glob("output/enhanced_fast_fish_format_*.csv"),
                    key=os.path.getctime,
                    reverse=True
                )
                for cand in candidates:
                    try:
                        probe = pd.read_csv(cand, nrows=1)
                        if 'Period' in probe.columns and str(probe['Period'].iloc[0]) == preferred_period:
                            logger.info(f"Selected period-matching current analysis file: {cand}")
                            df = pd.read_csv(cand)
                            path = cand
                            break
                    except Exception:
                        continue
        # Normalize category/subcategory columns
        if {'Category', 'Subcategory'}.issubset(df.columns):
            df = df.rename(columns={'Category': 'category', 'Subcategory': 'sub_category'})
        elif 'Target_Style_Tags' in df.columns:
            # Parse from dimensional or legacy format
            def parse_tags(val: str) -> Tuple[str, str]:
                try:
                    s = str(val)
                    if s.startswith('[') and s.endswith(']'):
                        inner = s.strip('[]')
                        parts = [p.strip() for p in inner.split(',')]
                        if len(parts) >= 5:
                            return parts[3], parts[4]
                    if '|' in s:
                        parts = [p.strip() for p in s.split('|')]
                        if len(parts) >= 2:
                            return parts[0], parts[1]
                except Exception:
                    pass
                return '', ''
            cat_sub = df['Target_Style_Tags'].apply(parse_tags)
            df['category'] = [c for c, _ in cat_sub]
            df['sub_category'] = [sc for _, sc in cat_sub]
        else:
            logger.warning("Could not determine category/sub_category in current analysis")
        logger.info(f"Loaded {len(df)} current recommendations from {os.path.basename(path)}")
        return df
    except Exception as e:
        logger.warning(f"Could not load current analysis: {e}")
        return None

def create_year_over_year_comparison(historical_df: pd.DataFrame, baseline_label: str, current_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Create year-over-year comparison between baseline period and current analysis."""
    
    logger.info(f"Creating year-over-year comparison for baseline {baseline_label}...")
    
    if current_df is None:
        logger.info("No current analysis available, creating historical reference only")
        comparison_df = historical_df.copy()
        comparison_df['period'] = f"{baseline_label}_Historical"
        return comparison_df
    
    # Merge historical and current data
    comparison_df = historical_df.merge(
        current_df[['Store_Group_Name', 'category', 'sub_category', 'Current_SPU_Quantity', 
                   'Target_SPU_Quantity', 'Stores_In_Group_Selling_This_Category', 
                   'Total_Current_Sales', 'Avg_Sales_Per_SPU']],
        left_on=['store_group', 'category', 'sub_category'],
        right_on=['Store_Group_Name', 'category', 'sub_category'],
        how='outer',
        suffixes=('_historical', '_current')
    )
    
    # Calculate year-over-year changes (NA-safe; avoid div-by-zero)
    comparison_df['yoy_spu_count_change'] = comparison_df['Current_SPU_Quantity'] - comparison_df['historical_spu_count']
    denom = comparison_df['historical_spu_count']
    comparison_df['yoy_spu_count_change_pct'] = np.where(denom > 0, (comparison_df['yoy_spu_count_change'] / denom) * 100, np.nan)

    comparison_df['yoy_sales_change'] = comparison_df['Total_Current_Sales'] - comparison_df['historical_total_sales']
    denom = comparison_df['historical_total_sales']
    comparison_df['yoy_sales_change_pct'] = np.where(denom > 0, (comparison_df['yoy_sales_change'] / denom) * 100, np.nan)

    comparison_df['yoy_avg_sales_per_spu_change'] = comparison_df['Avg_Sales_Per_SPU'] - comparison_df['historical_avg_sales_per_spu']
    denom = comparison_df['historical_avg_sales_per_spu']
    comparison_df['yoy_avg_sales_per_spu_change_pct'] = np.where(denom > 0, (comparison_df['yoy_avg_sales_per_spu_change'] / denom) * 100, np.nan)

    # Diagnostics: count rows where denominators were zero/NA
    zero_spu = int((comparison_df['historical_spu_count'] <= 0).fillna(True).sum())
    zero_sales = int((comparison_df['historical_total_sales'] <= 0).fillna(True).sum())
    zero_avg = int((comparison_df['historical_avg_sales_per_spu'] <= 0).fillna(True).sum())
    logger.info(f"YoY percent NA due to zero/NA denominators — spu_count: {zero_spu}, sales: {zero_sales}, avg_sales_per_spu: {zero_avg}")
    
    logger.info(f"Created year-over-year comparison for {len(comparison_df)} combinations")
    
    return comparison_df

def create_historical_fast_fish_format(historical_df: pd.DataFrame, baseline_year: int, baseline_month: int, baseline_period: str) -> pd.DataFrame:
    """Create Fast Fish-like format using historical data as baseline (period-aware)."""
    logger.info("Creating historical Fast Fish format...")
    output_df = pd.DataFrame({
        'Year': baseline_year,
        'Month': baseline_month,
        'Period': baseline_period,
        'Store_Group_Name': historical_df['store_group'],
        'Target_Style_Tags': historical_df['category'] + ' | ' + historical_df['sub_category'],
        'Category': historical_df['category'],
        'Subcategory': historical_df['sub_category'],
        'Historical_SPU_Quantity': historical_df['historical_spu_count'],
        'Historical_Total_Sales': historical_df['historical_total_sales'].round(2),
        'Historical_Avg_Sales_Per_SPU': historical_df['historical_avg_sales_per_spu'].round(2),
        'Historical_Store_Count': historical_df['historical_store_count'],
        'Store_Count_In_Group': historical_df['historical_store_count'],
        'Historical_Total_Quantity': historical_df['historical_total_quantity'].round(1),
        'Historical_Sales_Per_Store': historical_df['historical_sales_per_store'].round(2)
    })
    output_df = output_df[
        (output_df['Historical_SPU_Quantity'] >= 1) &
        (output_df['Historical_Store_Count'] >= 2)
    ].copy()
    output_df = output_df.sort_values(['Store_Group_Name', 'Historical_Total_Sales'], ascending=[True, False])
    logger.info(f"Created {len(output_df)} historical Fast Fish format records")
    return output_df

def generate_historical_insights(historical_df: pd.DataFrame) -> Dict:
    """Generate key insights from historical data."""
    insights = {
        'total_combinations': int(len(historical_df)),
        'unique_store_groups': int(historical_df['store_group'].nunique()),
        'unique_categories': int(historical_df['category'].nunique()),
        'unique_subcategories': int(historical_df['sub_category'].nunique()),
        'total_historical_spus': int(historical_df['historical_spu_count'].sum()),
        'avg_spus_per_combination': float(historical_df['historical_spu_count'].mean()),
        'total_historical_sales': float(historical_df['historical_total_sales'].sum()),
        'avg_sales_per_spu_overall': float((historical_df['historical_total_sales'].sum() / historical_df['historical_spu_count'].sum())),
        'top_performing_categories': [],
        'top_performing_store_groups': []
    }
    category_performance = historical_df.groupby('category').agg({
        'historical_total_sales': 'sum',
        'historical_spu_count': 'sum'
    })
    category_performance['avg_sales_per_spu'] = category_performance['historical_total_sales'] / category_performance['historical_spu_count']
    top_categories = category_performance.sort_values('avg_sales_per_spu', ascending=False).head(5)
    insights['top_performing_categories'] = [
        {'category': cat, 'avg_sales_per_spu': float(row['avg_sales_per_spu'])}
        for cat, row in top_categories.iterrows()
    ]
    group_performance = historical_df.groupby('store_group').agg({
        'historical_total_sales': 'sum',
        'historical_spu_count': 'sum'
    })
    group_performance['avg_sales_per_spu'] = group_performance['historical_total_sales'] / group_performance['historical_spu_count']
    top_groups = group_performance.sort_values('avg_sales_per_spu', ascending=False).head(5)
    insights['top_performing_store_groups'] = [
        {'store_group': group, 'avg_sales_per_spu': float(row['avg_sales_per_spu'])}
        for group, row in top_groups.iterrows()
    ]
    return insights

def save_results(
    historical_ff_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    insights: Dict,
    baseline_label: str,
    target_year: int,
    target_month: int,
    target_period: str,
) -> List[str]:
    """Save all historical analysis results and register outputs."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_files: List[str] = []
    # Embed standardized period metadata columns (baseline_* and target_*) into CSVs
    try:
        baseline_yyyymm = str(baseline_label)[:6]
        baseline_period = str(baseline_label)[6:]
        target_yyyymm = f"{int(target_year)}{int(target_month):02d}"
        for df in (historical_ff_df, comparison_df):
            if df is None:
                continue
            df["baseline_label"] = baseline_label
            df["baseline_yyyymm"] = baseline_yyyymm
            df["baseline_period"] = baseline_period
            df["target_yyyymm"] = target_yyyymm
            df["target_period"] = target_period
        logger.info(
            "Embedded standardized metadata columns into Step 15 CSV outputs: "
            "baseline_label, baseline_yyyymm, baseline_period, target_yyyymm, target_period"
        )
    except Exception as e:
        logger.warning(f"Could not embed standardized period metadata columns: {e}")
    # Historical Fast Fish-like format with dual output pattern
    timestamped, symlink, generic = create_output_with_symlinks(
        historical_ff_df,
        os.path.join(output_dir, "historical_reference"),
        baseline_label
    )
    output_files.append(timestamped)
    logger.info(f"Saved historical Fast Fish format: {timestamped}")
    logger.info(f"   Period symlink: {symlink}")
    logger.info(f"   Generic symlink: {generic}")
    
    # Use timestamped version for manifest registration
    historical_ff_file = timestamped
    hist_meta = {
        "records": int(len(historical_ff_df)),
        "baseline": baseline_label,
        "target_year": target_year,
        "target_month": target_month,
        "target_period": target_period,
    }
    # Generic key (latest)
    register_step_output(
        "step15",
        "historical_reference",
        historical_ff_file,
        hist_meta,
    )
    # Period-specific key for disambiguation
    register_step_output(
        "step15",
        f"historical_reference_{baseline_label}",
        historical_ff_file,
        hist_meta,
    )
    # Year-over-year comparison with dual output pattern
    timestamped_yoy, symlink_yoy, generic_yoy = create_output_with_symlinks(
        comparison_df,
        os.path.join(output_dir, "year_over_year_comparison"),
        baseline_label
    )
    output_files.append(timestamped_yoy)
    logger.info(f"Saved YoY comparison: {timestamped_yoy}")
    logger.info(f"   Period symlink: {symlink_yoy}")
    logger.info(f"   Generic symlink: {generic_yoy}")
    
    # Use timestamped version for manifest registration
    comparison_file = timestamped_yoy
    yoy_meta = {
        "records": int(len(comparison_df)),
        "baseline": baseline_label,
        "target_year": target_year,
        "target_month": target_month,
        "target_period": target_period,
    }
    # Generic key (latest)
    register_step_output(
        "step15",
        "yoy_comparison",
        comparison_file,
        yoy_meta,
    )
    # Period-specific key for disambiguation
    register_step_output(
        "step15",
        f"yoy_comparison_{baseline_label}",
        comparison_file,
        yoy_meta,
    )
    # Insights JSON (DUAL OUTPUT PATTERN)
    # Timestamped version (for backup/inspection)
    timestamped_insights_file = os.path.join(output_dir, f"historical_insights_{baseline_label}_{timestamp}.json")
    with open(timestamped_insights_file, 'w') as f:
        json.dump(insights, f, indent=2)
    output_files.append(timestamped_insights_file)
    logger.info(f"Saved timestamped historical insights to: {timestamped_insights_file}")
    
    # Generic version (for pipeline flow)
    generic_insights_file = os.path.join(output_dir, f"historical_insights_{baseline_label}.json")
    with open(generic_insights_file, 'w') as f:
        json.dump(insights, f, indent=2)
    output_files.append(generic_insights_file)
    logger.info(f"Saved generic historical insights to: {generic_insights_file}")
    
    # Use timestamped version for manifest registration
    insights_file = timestamped_insights_file
    insights_meta = {
        "baseline": baseline_label,
        "target_year": target_year,
        "target_month": target_month,
        "target_period": target_period,
        "summary": {
            "total_combinations": insights.get('total_combinations', 0),
            "unique_store_groups": insights.get('unique_store_groups', 0),
        },
    }
    # Generic key (latest)
    register_step_output(
        "step15",
        "historical_insights",
        insights_file,
        insights_meta,
    )
    # Period-specific key
    register_step_output(
        "step15",
        f"historical_insights_{baseline_label}",
        insights_file,
        insights_meta,
    )
    # Console summary
    print(f"\n=== STEP 15: HISTORICAL REFERENCE ANALYSIS ({baseline_label}) ===")
    print(f"Total combinations: {insights['total_combinations']:,}")
    print(f"Store groups: {insights['unique_store_groups']}")
    print(f"Sub-categories: {insights['unique_subcategories']}")
    print(f"Historical SPUs: {insights['total_historical_spus']:,}")
    print(f"Historical sales: ¥{insights['total_historical_sales']:,.0f}")
    print(f"Avg sales per SPU: ¥{insights['avg_sales_per_spu_overall']:.2f}")
    print(f"\nTop performing categories ({baseline_label}):")
    for cat in insights['top_performing_categories'][:3]:
        print(f"  • {cat['category']}: ¥{cat['avg_sales_per_spu']:.0f} avg per SPU")
    print(f"\nOutput files: {len(output_files)} files created")
    return output_files

def main():
    """Main execution function."""
    args = _parse_args()
    target_yyyymm = args.target_yyyymm
    target_period = args.target_period
    baseline_yyyymm = args.baseline_yyyymm or _compute_baseline_yyyymm(target_yyyymm)
    baseline_period = args.baseline_period or target_period
    baseline_label = f"{baseline_yyyymm}{baseline_period}"
    logger.info(f"Starting Step 15: Historical Reference Analysis for baseline {baseline_label} (target {target_yyyymm}{target_period})")
    try:
        # Load historical data for baseline period
        historical_df = load_historical_data(baseline_yyyymm, baseline_period)
        # Create store groups aligned with clustering results
        cluster_mapping_df = _load_cluster_mapping(target_yyyymm, target_period)
        historical_grouped_df = create_store_groups(historical_df, cluster_mapping_df)
        # Analyze historical SPU counts
        historical_analysis = analyze_historical_spu_counts(historical_grouped_df)
        # Load current (Step 14) analysis for comparison
        current_analysis = load_current_analysis(args.current_analysis_file, target_period, target_yyyymm)
        # Create year-over-year comparison
        comparison_df = create_year_over_year_comparison(historical_analysis, baseline_label, current_analysis)
        # Create historical Fast Fish-like format
        b_year = int(baseline_yyyymm[:4])
        b_month = int(baseline_yyyymm[4:6])
        historical_ff_df = create_historical_fast_fish_format(historical_analysis, b_year, b_month, baseline_period)
        # Generate insights
        insights = generate_historical_insights(historical_analysis)
        # Save and register results
        t_year = int(target_yyyymm[:4])
        t_month = int(target_yyyymm[4:6])
        output_files = save_results(
            historical_ff_df,
            comparison_df,
            insights,
            baseline_label,
            t_year,
            t_month,
            target_period,
        )
        logger.info("Step 15: Historical Reference Analysis completed successfully!")
        return output_files
    except Exception as e:
        logger.error(f"Error in Step 15: {e}")
        raise

if __name__ == "__main__":
    main()
