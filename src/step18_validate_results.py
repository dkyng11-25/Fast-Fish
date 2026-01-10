#!/usr/bin/env python3
"""
Step 18: Add Sell-Through Rate Analysis
=======================================

Add client-requested sell-through rate calculations with normalized units and clear columns:
1. SPU_Store_Days_Inventory (recommendation calculation)
2. SPU_Store_Days_Sales (historical sales)
3. Sell_Through_Rate_Frac (sell-through as fraction, 0–1)
4. Sell_Through_Rate_Pct (sell-through as percent, 0–100)
5. Sell_Through_Rate (legacy; mirrored percent for backward compatibility)

Formula:
Sell-Through Rate (fraction) = SPU-store-day with sales ÷ SPU-store-day with inventory
Sell-Through Rate (percent) = Sell-Through Rate (fraction) × 100

Example:
- 6 SPUs × 40 stores × 15 days = 3,600 SPU-store-days inventory
- 4 SPUs sold/day × 40 stores × 15 days = 2,400 SPU-store-days sales  
- Sell-Through Rate (fraction) = 2,400 ÷ 3,600 = 0.667 (clipped to [0,1])
- Sell-Through Rate (percent) = 66.7% (clipped to [0,100])

Pipeline Flow:
Step 17 → Step 18 (Sell-Through Rate Enhancement). Internally we use fractions for computation and maintain percent strictly for presentation/export.

 HOW TO RUN (CLI + ENV) — Read this before executing
 ----------------------------------------------------
 Overview
 - Period-aware: this step takes the period-labeled Step 17 output for the specific half-month (e.g., 202510A) and augments it with sell-through metrics.
 - Why Step 17 period label must match: the store-group/category/subcategory rows in Step 17 reflect a specific half-month’s recommendations and dimensional joins. If you pass a mismatched label, joins to historical baselines and enrichment fields will silently degrade.

 Quick Start (target 202510A)
   Command (manifest-driven):
     PYTHONPATH=. python3 src/step18_validate_results.py \
       --target-yyyymm 202510 \
       --target-period A

   Notes
   - This resolves the Step 17 period-labeled input from the manifest. If not registered, pass --input-file explicitly.

 Inputs and Baseline Handling
 - Step 17 input: must be period-labeled (e.g., fast_fish_with_historical_and_cluster_trending_analysis_202510A_*.csv)
   Why: fields like Season, Gender, Location, cluster/trending metrics are bound to that half-month. Mixing labels causes misalignment.
 - Historical baseline (Step 15): inferred year-ago month with same half (YoY) unless overridden.
   Why: sell-through targets should be comparable across similar seasonality windows; YoY preserves comparable demand patterns.

 Common failure modes (and what to do)
 - "Period-specific Step 17 augmented file not found in manifest"
   • Cause: Step 17 didn’t register its 202510A output or you ran a one-off without manifest updates.
   • Fix: rerun Step 17 with manifest registration, or pass --input-file to Step 18 explicitly.
 - Historical reference not found for computed baseline
   • Cause: Step 15 for the inferred baseline label hasn’t been produced/registered.
   • Fix: run Step 15 for the baseline (e.g., 202409A for 202509A targets), or pass --baseline-period to override.
 - Low/zero coverage in sell-through columns
   • Cause: missing/different Category/Subcategory naming vs historical summary, or empty historical scope.
   • Fix: verify taxonomy alignment; confirm Step 14/17 produced consistent Category/Subcategory; ensure Step 15 covers the same taxonomy.

 Why this configuration leads to stable outcomes
 - Using the exact Step 17 period label ensures we calculate SPU-store-days on the same universe of recommendations (same cluster/subcategory context).
 - YoY baseline alignment avoids seasonal skew (e.g., August vs. November). If your planning window intentionally shifts seasons, pass --baseline-period carefully and document the rationale.

 Manifest notes
 - This step looks up Step 17 input and registers its own outputs with period labels. Downstream steps (32–36) should resolve inputs via the manifest rather than hardcoded filenames.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import glob
import os
import argparse
from typing import Tuple, Dict, Optional
# Robust imports for both package and script execution
try:
    from src.config import get_period_label, get_api_data_files, get_output_files  # when running with -m src.module
    from src.pipeline_manifest import register_step_output, get_step_input, get_manifest
except ImportError:
    try:
        # Add parent directory to path for direct execution
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
        from src.config import get_period_label, get_api_data_files, get_output_files
        from src.pipeline_manifest import register_step_output, get_step_input, get_manifest
    except ImportError:
        # Fallback to direct imports
        from config import get_period_label, get_api_data_files
        from pipeline_manifest import register_step_output, get_step_input, get_manifest

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Sell-through normalization helpers (local to Step 18) ---
def _st_clip_01(x) -> float:
    """Clip a numeric value to [0, 1]. Returns NaN on errors."""
    try:
        if pd.isna(x):
            return np.nan
        return float(np.clip(float(x), 0.0, 1.0))
    except Exception:
        return np.nan

def _st_frac_to_pct(frac) -> float:
    """Convert fraction (0–1) to percent (0–100) with clipping and NA-safety."""
    if pd.isna(frac):
        return np.nan
    try:
        return float(np.clip(float(frac), 0.0, 1.0) * 100.0)
    except Exception:
        return np.nan

def _parse_args():
    """Parse CLI arguments for period-aware execution."""
    parser = argparse.ArgumentParser(
        description="Step 18: Sell-Through Rate Enhancement (period-aware)")
    parser.add_argument(
        "--target-yyyymm",
        required=True,
        help="Target year-month for current run, e.g. 202509",
    )
    parser.add_argument(
        "--target-period",
        choices=["A", "B"],
        required=True,
        help="Target period (A or B)",
    )
    parser.add_argument(
        "--input-file",
        required=False,
        help="Path to Step 17 augmented CSV (optional, overrides manifest/env)",
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Show progress bars during row-wise calculations (optional)",
    )
    parser.add_argument(
        "--baseline-period",
        help="Override baseline period (e.g., 202409B) instead of computed value",
    )
    return parser.parse_args()

def _compute_baseline_yyyymm(target_yyyymm: str) -> str:
    if not (isinstance(target_yyyymm, str) and len(target_yyyymm) == 6 and target_yyyymm.isdigit()):
        raise ValueError(f"Invalid target_yyyymm: {target_yyyymm}")
    year = int(target_yyyymm[:4])
    month = int(target_yyyymm[4:6])
    return f"{year - 1}{month:02d}"

def _load_step15_historical_reference(target_yyyymm: str, target_period: str, override_baseline_label: Optional[str] = None) -> pd.DataFrame:
    if override_baseline_label:
        baseline_label = override_baseline_label
    else:
        baseline_yyyymm = _compute_baseline_yyyymm(target_yyyymm)
        baseline_label = f"{baseline_yyyymm}{target_period}"
    manifest = get_manifest().manifest
    step15_outputs = manifest.get("steps", {}).get("step15", {}).get("outputs", {})
    specific_key = f"historical_reference_{baseline_label}"
    if specific_key in step15_outputs:
        path = step15_outputs[specific_key]["file_path"]
    else:
        meta = step15_outputs.get("historical_reference", {}).get("metadata", {})
        if meta.get("baseline") == baseline_label:
            path = step15_outputs.get("historical_reference", {}).get("file_path")
        else:
            path = None
    # Fallback to looking for files in output directory
    if not path or not os.path.exists(path):
        # Look for files matching the baseline label pattern
        import glob
        pattern = f"output/historical_reference_{baseline_label}*.csv"
        matches = glob.glob(pattern)
        if matches:
            # Use the most recent file
            path = sorted(matches)[-1]
            logger.info(f"⚠️  Step 15 historical reference not in manifest, using file: {path}")
        else:
            # Try without timestamp pattern
            fallback_path = f"output/historical_reference_{baseline_label}.csv"
            if os.path.exists(fallback_path):
                path = fallback_path
                logger.info(f"⚠️  Step 15 historical reference not in manifest, using file: {path}")
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Step 15 historical_reference not found for baseline {baseline_label}")
    logger.info(f"✅ Loading Step 15 historical reference: {path}")
    return pd.read_csv(path)

def load_files(target_yyyymm: str, target_period: str, input_file: Optional[str] = None, override_baseline_label: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load the augmented file from Step 17 and Step 15 historical reference.

    Enforces period-specific Step 17 input unless CLI override is provided.
    """
    # Resolve Step 17 augmented input
    augmented_file = input_file or os.environ.get('STEP18_INPUT_FILE')
    if not augmented_file:
        period_label = get_period_label(target_yyyymm, target_period)
        manifest = get_manifest().manifest
        step17_outputs = manifest.get("steps", {}).get("step17", {}).get("outputs", {})
        specific_key = f"augmented_recommendations_{period_label}"
        if specific_key in step17_outputs:
            augmented_file = step17_outputs[specific_key]["file_path"]
        else:
            logger.error("❌ Period-specific Step 17 augmented file not found in manifest")
            raise FileNotFoundError("Step 17 period-specific augmented file required for Step 18")
    if not os.path.exists(augmented_file):
        raise FileNotFoundError(f"Augmented file path does not exist: {augmented_file}")

    logger.info(f"✅ Loading augmented file: {augmented_file}")
    augmented_df = pd.read_csv(augmented_file)

    # Load Step 15 historical reference for baseline
    historical_ref_df = _load_step15_historical_reference(target_yyyymm, target_period, override_baseline_label)
    return augmented_df, historical_ref_df

def _enrich_dims_from_store_config(df: pd.DataFrame, target_yyyymm: str, target_period: str) -> pd.DataFrame:
    """Precisely enrich Season/Gender/Location using store_config via exact str_code × sub_cate_name joins.

    For each group-level recommendation row, derive dimensional modes from all stores in Store_Codes_In_Group
    that have matching sub_cate_name in store_config. Falls back to store-level modes when subcategory mapping
    isn't present. Does not synthesize values; uses upstream data only.
    """
    try:
        api = get_api_data_files(target_yyyymm, target_period)
        cfg_path = api.get('store_config')
        if not cfg_path or not os.path.exists(cfg_path):
            return df
        cfg = pd.read_csv(cfg_path, dtype={'str_code': str})
        # Normalize keys
        cfg['sub_cate_name'] = cfg['sub_cate_name'].astype(str).str.strip()
        cfg['str_code'] = cfg['str_code'].astype(str)
        # Mode maps per (store, subcategory) and per store
        def _mode(s: pd.Series):
            s = s.dropna().astype(str).str.strip()
            return s.mode().iloc[0] if not s.mode().empty else np.nan
        keys = ['str_code', 'sub_cate_name']
        per_pair = cfg.groupby(keys).agg({
            'season_name': _mode,
            'sex_name': _mode,
            'display_location_name': _mode,
        }).reset_index()
        per_store = cfg.groupby('str_code').agg({
            'season_name': _mode,
            'sex_name': _mode,
            'display_location_name': _mode,
        }).reset_index()

        # Mappers for normalization to unified values
        season_map = {'春': 'Spring', '夏': 'Summer', '秋': 'Autumn', '冬': 'Winter'}
        # FIXED: Preserve Chinese gender values, map both '中' and '中性' to '中性'
        gender_map = {'男': '男', '女': '女', '中': '中性', '中性': '中性'}
        location_map = {'前台': 'Front', '后台': 'Back', '前场': 'Front', '后场': 'Back'}

        def _extract_category_subcategory(row: pd.Series) -> Tuple[str, str]:
            cat = str(row.get('Category', ''))
            sub = str(row.get('Subcategory', ''))
            if cat and sub:
                return cat, sub
            # fallback to tags
            return _robust_extract_category_subcategory(row)

        def _fill_dims(row: pd.Series) -> Tuple[Optional[str], Optional[str], Optional[str]]:
            sub = _extract_category_subcategory(row)[1]
            codes_str = str(row.get('Store_Codes_In_Group', ''))
            try:
                codes = [c.strip() for c in codes_str.split(',') if c.strip()]
            except Exception:
                codes = []
            # Collect pair matches
            sel = per_pair[per_pair['sub_cate_name'] == sub]
            sel = sel[sel['str_code'].isin(codes)] if codes else sel
            seasons = sel['season_name'].dropna().astype(str).tolist()
            genders = sel['sex_name'].dropna().astype(str).tolist()
            locs = sel['display_location_name'].dropna().astype(str).tolist()
            # Fallback to store-level modes if pair empty
            if not seasons or not genders or not locs:
                st = per_store[per_store['str_code'].isin(codes)] if codes else per_store.iloc[0:0]
                if not seasons:
                    seasons = st['season_name'].dropna().astype(str).tolist()
                if not genders:
                    genders = st['sex_name'].dropna().astype(str).tolist()
                if not locs:
                    locs = st['display_location_name'].dropna().astype(str).tolist()
            # Pick simple mode
            def pick(vals: list) -> Optional[str]:
                if not vals:
                    return None
                s = pd.Series(vals)
                m = s.mode()
                return m.iloc[0] if not m.empty else None
            season_raw = pick(seasons)
            gender_raw = pick(genders)
            loc_raw = pick(locs)
            season = season_map.get(season_raw, season_raw) if season_raw else None
            gender = gender_map.get(gender_raw, gender_raw) if gender_raw else None
            location = location_map.get(loc_raw, loc_raw) if loc_raw else None
            return season, gender, location

        # Apply fills only where values are missing or ambiguous
        fills = df.apply(_fill_dims, axis=1)
        season_fill = fills.apply(lambda x: x[0])
        gender_fill = fills.apply(lambda x: x[1])
        location_fill = fills.apply(lambda x: x[2])

        def _is_missing_or_amb(val: str, amb: set) -> bool:
            if pd.isna(val):
                return True
            v = str(val).strip()
            return v == '' or v in amb

        # FIXED: Only truly ambiguous/unknown values, not valid neutral gender
        amb_gender = {'Unknown', ''}
        amb_season = {'Unknown'}
        amb_location = {'Unknown'}

        if 'Season' in df.columns:
            mask = df['Season'].apply(lambda v: _is_missing_or_amb(v, amb_season)) & season_fill.notna()
            df.loc[mask, 'Season'] = season_fill[mask]
        if 'Gender' in df.columns:
            mask = df['Gender'].apply(lambda v: _is_missing_or_amb(v, amb_gender)) & gender_fill.notna()
            df.loc[mask, 'Gender'] = gender_fill[mask]
        if 'Location' in df.columns:
            mask = df['Location'].apply(lambda v: _is_missing_or_amb(v, amb_location)) & location_fill.notna()
            df.loc[mask, 'Location'] = location_fill[mask]
        return df
    except Exception:
        return df

def _build_historical_summary(historical_ref_df: pd.DataFrame, period_days: int = 15) -> pd.DataFrame:
    """Prepare historical summary keyed by Store_Group_Name × Category × Subcategory with NA-safe metrics."""
    df = historical_ref_df.copy()
    required = {"Store_Group_Name", "Category", "Subcategory", "Historical_Total_Quantity", "Historical_Store_Count"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Historical reference missing required columns: {sorted(missing)}")
    # Coerce numerics
    df["Historical_Total_Quantity"] = pd.to_numeric(df["Historical_Total_Quantity"], errors="coerce")
    df["Historical_Store_Count"] = pd.to_numeric(df["Historical_Store_Count"], errors="coerce")
    # avg daily per store
    with np.errstate(divide='ignore', invalid='ignore'):
        df["Avg_Daily_SPUs_Sold_Per_Store"] = df["Historical_Total_Quantity"] / (df["Historical_Store_Count"] * period_days)
    return df[[
        "Store_Group_Name", "Category", "Subcategory",
        "Historical_Total_Quantity", "Historical_Store_Count", "Avg_Daily_SPUs_Sold_Per_Store"
    ]]

def _robust_extract_category_subcategory(row: pd.Series) -> Tuple[str, str]:
    # Prefer explicit columns if present
    if 'Category' in row and 'Subcategory' in row and pd.notna(row['Category']) and pd.notna(row['Subcategory']):
        return str(row['Category']), str(row['Subcategory'])
    # Fallback to parsing Target_Style_Tags
    tags = str(row.get('Target_Style_Tags', ''))
    try:
        s = tags.strip()
        if s.startswith('[') and s.endswith(']'):
            inner = s.strip('[]')
            parts = [p.strip().strip('"\'') for p in inner.split(',')]
            if len(parts) >= 5:
                return parts[3], parts[4]
            if len(parts) >= 2:
                return parts[0], parts[1]
        if '|' in s:
            parts = [p.strip() for p in s.split('|')]
            if len(parts) >= 2:
                return parts[0], parts[1]
    except Exception:
        pass
    return '', ''

def add_sell_through_calculations(augmented_df: pd.DataFrame, historical_summary: pd.DataFrame, show_progress: bool = False) -> pd.DataFrame:
    """
    Add the 3 new sell-through rate columns to the augmented DataFrame.
    
    Args:
        augmented_df: Enhanced recommendations from Step 17
        sales_data: Historical sales data for calculations
        
    Returns:
        DataFrame with new sell-through rate columns added
    """
    logger.info("Adding sell-through rate calculations...")
    
    # Create a copy for modifications
    enhanced_df = augmented_df.copy()
    
    # Constants
    PERIOD_DAYS = 15  # Half-month period as specified by client
    
    # Initialize new columns NA-preserving
    enhanced_df['SPU_Store_Days_Inventory'] = np.nan
    enhanced_df['SPU_Store_Days_Sales'] = np.nan
    # Normalized sell-through outputs
    enhanced_df['Sell_Through_Rate_Frac'] = np.nan  # 0–1 internal
    enhanced_df['Sell_Through_Rate_Pct'] = np.nan   # 0–100 presentation
    # Legacy column retained for backward compatibility (percent)
    enhanced_df['Sell_Through_Rate'] = np.nan
    enhanced_df['Historical_Avg_Daily_SPUs_Sold_Per_Store'] = np.nan
    
    # Optional progress bar
    iterator = enhanced_df.iterrows()
    if show_progress:
        try:
            from tqdm import tqdm  # local import to avoid hard dependency
            iterator = tqdm(iterator, total=len(enhanced_df), desc="Calculating sell-through")
        except Exception:
            pass

    # Process each row
    for idx, row in iterator:
        store_group = row['Store_Group_Name']
        target_spu_quantity = row['Target_SPU_Quantity']
        stores_in_group = row.get('Stores_In_Group_Selling_This_Category', np.nan)

        category, sub_category = _robust_extract_category_subcategory(row)
        
        # CALCULATION 1: SPU-Store-Days Inventory (Recommendation)
        # Formula: Target SPU Quantity × Stores in Group × Period Days
        inv = np.nan
        if pd.notna(target_spu_quantity) and pd.notna(stores_in_group):
            inv = target_spu_quantity * stores_in_group * PERIOD_DAYS
            enhanced_df.at[idx, 'SPU_Store_Days_Inventory'] = inv
        
        # CALCULATION 2: SPU-Store-Days Sales (Historical)
        # Look up historical sales data for this store group + category combination
        hs = historical_summary
        match = hs[(hs['Store_Group_Name'] == store_group) & (hs['Category'] == category) & (hs['Subcategory'] == sub_category)]
        if not match.empty:
            m = match.iloc[0]
            avg_daily = m['Avg_Daily_SPUs_Sold_Per_Store']
            if pd.notna(avg_daily) and pd.notna(stores_in_group):
                sales_spu_store_days = avg_daily * stores_in_group * PERIOD_DAYS
                enhanced_df.at[idx, 'SPU_Store_Days_Sales'] = sales_spu_store_days
                enhanced_df.at[idx, 'Historical_Avg_Daily_SPUs_Sold_Per_Store'] = avg_daily
        
        # CALCULATION 3: Sell-Through Rate (fraction + percent with guards)
        # Formula: SPU-store-day with sales / SPU-store-day with inventory
        sales_val = enhanced_df.at[idx, 'SPU_Store_Days_Sales']
        if pd.notna(inv) and inv > 0 and pd.notna(sales_val) and sales_val > 0:
            frac = _st_clip_01(sales_val / inv)
            pct = _st_frac_to_pct(frac)
            enhanced_df.at[idx, 'Sell_Through_Rate_Frac'] = frac
            enhanced_df.at[idx, 'Sell_Through_Rate_Pct'] = pct
            # Maintain legacy column in percent
            enhanced_df.at[idx, 'Sell_Through_Rate'] = pct
    
    # Log summary statistics and coverage
    valid_rates = enhanced_df['Sell_Through_Rate'].dropna()
    inv_notna = int(enhanced_df['SPU_Store_Days_Inventory'].notna().sum())
    sales_notna = int(enhanced_df['SPU_Store_Days_Sales'].notna().sum())
    logger.info(f"Historical coverage: inventory_notna={inv_notna}, sales_notna={sales_notna}, total={len(enhanced_df)}")
    if len(valid_rates) > 0:
        logger.info(f"Sell-through rate summary:")
        logger.info(f"  Records with rates: {len(valid_rates):,}")
        logger.info(f"  Average rate: {valid_rates.mean():.1f}%")
        logger.info(f"  Median rate: {valid_rates.median():.1f}%")
        logger.info(f"  Range: {valid_rates.min():.1f}% - {valid_rates.max():.1f}%")
    
    return enhanced_df

def save_enhanced_file(enhanced_df: pd.DataFrame, target_yyyymm: str, target_period: str) -> str:
    """Save the enhanced file with sell-through rate analysis (period-aware)."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    period_label = get_period_label(target_yyyymm, target_period)
    
    # DUAL OUTPUT PATTERN - Define both timestamped and generic versions
    timestamped_output_file = f"output/fast_fish_with_sell_through_analysis_{period_label}_{timestamp}.csv"
    generic_output_file = f"output/fast_fish_with_sell_through_analysis_{period_label}.csv"

    logger.info(f"Saving enhanced file with sell-through analysis to: {timestamped_output_file}")
    logger.info(f"Output contains {len(enhanced_df.columns)} columns including sell-through metrics")

    # Save timestamped version (for backup/inspection)
    enhanced_df.to_csv(timestamped_output_file, index=False)
    logger.info(f"✅ Saved timestamped enhanced file: {timestamped_output_file}")
    
    # Create symlink for generic version (for pipeline flow)
    if os.path.exists(generic_output_file) or os.path.islink(generic_output_file):
        os.remove(generic_output_file)
    os.symlink(os.path.basename(timestamped_output_file), generic_output_file)
    logger.info(f"✅ Created generic symlink: {generic_output_file} -> {timestamped_output_file}")

    # Return timestamped version for manifest registration
    return timestamped_output_file

def print_analysis_summary(enhanced_df: pd.DataFrame):
    """Print comprehensive analysis summary."""
    
    print("\n" + "="*80)

def add_optimization_visibility_fields(enhanced_df: pd.DataFrame) -> pd.DataFrame:
    """Add optimization-target visibility columns required by output design.

    Columns added (best-effort, with safe fallbacks):
    - Optimization_Target
    - Current_Sell_Through_Rate
    - Target_Sell_Through_Rate
    - Sell_Through_Improvement
    - Constraint_Status
    - Capacity_Utilization
    - Store_Type_Alignment
    - Temperature_Suitability
    - Optimization_Rationale
    - Trade_Off_Analysis
    - Confidence_Score
    - Inventory_Velocity_Gain
    """

    df = enhanced_df.copy()

    # Core target fields
    df["Optimization_Target"] = "Maximize Sell-Through Rate Under Constraints"
    df["Current_Sell_Through_Rate"] = df.get("Sell_Through_Rate", np.nan)

    # Target: use historical sell-through when higher than current (real-data only), else keep current
    hist_col_candidates = [
        "Historical_Sell_Through_Rate",  # percent
        "Historical_ST_Pct",            # percent
        "Historical_ST_Frac"            # fraction 0-1
    ]
    hist_col = next((c for c in hist_col_candidates if c in df.columns), None)
    if hist_col is not None:
        hist_vals = pd.to_numeric(df[hist_col], errors='coerce')
        # Normalize fraction to percent if needed
        if hist_col == "Historical_ST_Frac":
            hist_vals = hist_vals * 100.0
        curr_vals = pd.to_numeric(df["Current_Sell_Through_Rate"], errors='coerce')
        target_vals = np.where(
            (hist_vals.notna()) & (curr_vals.notna()),
            np.maximum(hist_vals, curr_vals),
            curr_vals
        )
        df["Target_Sell_Through_Rate"] = pd.Series(target_vals).clip(upper=100.0)
    else:
        # Fallback: keep current
        df["Target_Sell_Through_Rate"] = df["Current_Sell_Through_Rate"].clip(upper=100.0)
    df["Sell_Through_Improvement"] = (pd.to_numeric(df["Target_Sell_Through_Rate"], errors='coerce') - pd.to_numeric(df["Current_Sell_Through_Rate"], errors='coerce')).round(2)

    # Capacity utilization: sold category stores vs total stores in group if available
    num_col = "Stores_In_Group_Selling_This_Category" if "Stores_In_Group_Selling_This_Category" in df.columns else None
    denom_col = None
    for candidate in ["Store_Count_In_Group", "total_stores_in_group", "Stores_In_Group", "stores_analyzed"]:
        if candidate in df.columns:
            denom_col = candidate
            break

    if num_col and denom_col:
        denom_vals = pd.to_numeric(df[denom_col], errors='coerce').replace({0: np.nan})
        num_vals = pd.to_numeric(df[num_col], errors='coerce')
        df["Capacity_Utilization"] = (num_vals / denom_vals).clip(upper=1.0)
    else:
        df["Capacity_Utilization"] = np.nan

    # Store type alignment - use store_config mapping if available
    try:
        # Strictly period-aware resolution; forbid combined
        store_cfg_path = os.environ.get("STEP18_STORE_CONFIG_FILE")
        if not store_cfg_path:
            # Try to infer from target env
            tyyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM") or os.environ.get("PIPELINE_YYYYMM")
            tperiod = os.environ.get("PIPELINE_TARGET_PERIOD") or os.environ.get("PIPELINE_PERIOD")
            try:
                api = get_api_data_files(tyyyymm, tperiod) if tyyyymm and tperiod else get_api_data_files()
                store_cfg_path = api.get('store_config')
            except Exception:
                store_cfg_path = None
        if store_cfg_path and os.path.exists(store_cfg_path):
            cfg = pd.read_csv(store_cfg_path, dtype={'str_code': str})
            # Build store->type map using a stable column if present
            type_col = next((c for c in ['store_type_classification','Store_Type','store_type','Store_Type_Category'] if c in cfg.columns), None)
            if type_col is not None:
                type_map = cfg.groupby('str_code')[type_col].agg(lambda s: s.dropna().mode().iloc[0] if not s.dropna().mode().empty else np.nan).to_dict()
            else:
                type_map = {}
        else:
            type_map = {}

        # Prefer manifest period-specific enriched attributes when available
        if not type_map:
            try:
                tyyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM") or os.environ.get("PIPELINE_YYYYMM")
                tperiod = os.environ.get("PIPELINE_TARGET_PERIOD") or os.environ.get("PIPELINE_PERIOD")
                period_label = get_period_label(tyyyymm, tperiod) if tyyyymm and tperiod else None
                man = get_manifest().manifest
                if isinstance(man, dict):
                    step22 = man.get("steps", {}).get("step22", {}).get("outputs", {})
                    key = f"enriched_store_attributes_{period_label}" if period_label else "enriched_store_attributes"
                    candidate = step22.get(key) or step22.get("enriched_store_attributes")
                    path = candidate.get("file_path") if isinstance(candidate, dict) else candidate
                    if path and os.path.exists(path):
                        enriched = pd.read_csv(path, dtype={'str_code': str})
                        if 'str_code' in enriched.columns and 'store_type' in enriched.columns:
                            tm = enriched.groupby('str_code')['store_type'].agg(lambda s: s.dropna().mode().iloc[0] if not s.dropna().mode().empty else np.nan).to_dict()
                            if tm:
                                type_map = tm
            except Exception:
                pass
        # Fallback: search glob for enriched attributes
        if not type_map:
            import glob
            candidates = sorted(glob.glob('output/enriched_store_attributes_*.csv'))
            enriched_path = candidates[-1] if candidates else ('output/enriched_store_attributes.csv' if os.path.exists('output/enriched_store_attributes.csv') else None)
            if enriched_path and os.path.exists(enriched_path):
                try:
                    enriched = pd.read_csv(enriched_path, dtype={'str_code': str})
                    if 'str_code' in enriched.columns and 'store_type' in enriched.columns:
                        tm = enriched.groupby('str_code')['store_type'].agg(lambda s: s.dropna().mode().iloc[0] if not s.dropna().mode().empty else np.nan).to_dict()
                        if tm:
                            type_map = tm
                except Exception:
                    pass
    except Exception:
        type_map = {}

    # If we have Store_Codes_In_Group, propagate alignment as present/unknown; else fall back to potential cols
    if 'Store_Codes_In_Group' in df.columns and type_map:
        def _align_from_codes(codes: str):
            try:
                codes_list = [c.strip() for c in str(codes).split(',') if c and c.strip()]
                types = [type_map.get(c) for c in codes_list]
                types = [t for t in types if pd.notna(t) and str(t).strip() != ""]
                return "Aligned" if len(types) > 0 else "Unknown"
            except Exception:
                return "Unknown"
        df['Store_Type_Alignment'] = df['Store_Codes_In_Group'].apply(_align_from_codes)
    else:
        potential_cols = ['store_type_classification', 'Store_Type', 'Target_Store_Type', 'store_type', 'Store_Type_Category']
        found_col = next((c for c in potential_cols if c in df.columns), None)
        if found_col is not None:
            df["Store_Type_Alignment"] = df[found_col].apply(lambda x: "Aligned" if pd.notna(x) and str(x).strip() != "" else "Unknown")
        else:
            df["Store_Type_Alignment"] = "Unknown"

    # Group-level fallback: derive alignment by Store_Group_Name using clustering results + store_config
    try:
        # Prefer period-labeled cluster file via config helpers
        cluster_path = None
        tyyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM") or os.environ.get("PIPELINE_YYYYMM")
        tperiod = os.environ.get("PIPELINE_TARGET_PERIOD") or os.environ.get("PIPELINE_PERIOD")
        try:
            if tyyyymm and tperiod:
                out = get_output_files('spu', tyyyymm, tperiod)
                cluster_path = out.get('clustering_results')
        except Exception:
            cluster_path = None
        if not cluster_path or not os.path.exists(cluster_path):
            import glob
            cluster_candidates = sorted(glob.glob('output/clustering_results_spu_*.csv')) or \
                                (['output/clustering_results_spu.csv'] if os.path.exists('output/clustering_results_spu.csv') else [])
            cluster_path = cluster_candidates[-1] if cluster_candidates else None
        if cluster_path and os.path.exists(cluster_path) and type_map:
            cl = pd.read_csv(cluster_path)
            if 'Cluster' in cl.columns:
                cl['Store_Group_Name'] = cl['Cluster'].apply(lambda c: f"Store Group {int(c)+1}" if pd.notna(c) else 'Store Group Unknown')
            if 'str_code' in cl.columns:
                cl['str_code'] = cl['str_code'].astype(str)
            # Map store type
            cl['store_type_present'] = cl['str_code'].map(lambda x: type_map.get(x))
            # Group-level presence of any non-null type
            grp_has_type = cl.groupby('Store_Group_Name')['store_type_present'].apply(lambda s: s.dropna().shape[0] > 0)
            grp_has_type = grp_has_type.to_dict()
            # Only fill Unknowns using group presence
            if 'Store_Group_Name' in df.columns:
                def _align_from_group(sg, cur):
                    if str(cur) == 'Unknown' and sg in grp_has_type and grp_has_type[sg]:
                        return 'Aligned'
                    return cur
                df['Store_Type_Alignment'] = [
                    _align_from_group(sg, cur) for sg, cur in zip(df['Store_Group_Name'], df['Store_Type_Alignment'])
                ]
    except Exception:
        pass

    # Temperature suitability: preserve existing if present, else derive from weather impact or feels-like temp
    if "Temperature_Suitability" in df.columns:
        temp_existing = df["Temperature_Suitability"].copy()
    else:
        temp_existing = pd.Series([np.nan] * len(df))

    if temp_existing.notna().any():
        df["Temperature_Suitability"] = temp_existing
    elif "weather_impact" in df.columns and pd.api.types.is_numeric_dtype(df["weather_impact"]):
        def _temp_suitability(x):
            try:
                if pd.isna(x):
                    return "Unknown"
                if x >= 70:
                    return "High"
                if x >= 40:
                    return "Medium"
                return "Low"
            except Exception:
                return "Unknown"
        df["Temperature_Suitability"] = df["weather_impact"].apply(_temp_suitability)
    elif "FeelsLike_Temp_Period_Avg" in df.columns:
        def _temp_from_feelslike(v):
            try:
                v = float(v)
            except Exception:
                return "Unknown"
            if np.isnan(v):
                return "Unknown"
            # Simple bands; no synthetic defaults
            if v >= 28:
                return "High"
            if v >= 20:
                return "Medium"
            if v >= 10:
                return "Low"
            return "Review"
        df["Temperature_Suitability"] = df["FeelsLike_Temp_Period_Avg"].apply(_temp_from_feelslike)
    else:
        df["Temperature_Suitability"] = "Unknown"

    # Confidence score: use trending confidence when available, else derive from real signals
    if "cluster_trend_confidence" in df.columns and pd.api.types.is_numeric_dtype(df["cluster_trend_confidence"]):
        df["Confidence_Score"] = df["cluster_trend_confidence"].clip(lower=0, upper=100)
    else:
        # Derive from capacity utilization and temperature suitability using real fields
        def _conf(row):
            score = 50.0
            cap = row.get("Capacity_Utilization")
            try:
                cap = float(cap)
            except Exception:
                cap = np.nan
            if not np.isnan(cap):
                score += min(20.0, max(0.0, cap * 20.0))  # up to +20
            temp = str(row.get("Temperature_Suitability", "Unknown"))
            if temp == "High":
                score += 20.0
            elif temp == "Medium":
                score += 10.0
            elif temp == "Low":
                score -= 10.0
            # Historical availability adds confidence
            hist_avail = pd.notna(row.get("Historical_Sell_Through_Rate")) or pd.notna(row.get("Historical_ST_Pct")) or pd.notna(row.get("Historical_ST_Frac"))
            if hist_avail:
                score += 10.0
            return max(0.0, min(100.0, score))
        df["Confidence_Score"] = df.apply(_conf, axis=1)

    # Inventory velocity gain proxy: historical avg sold per store per day
    if "Historical_Avg_Daily_SPUs_Sold_Per_Store" in df.columns and pd.api.types.is_numeric_dtype(df["Historical_Avg_Daily_SPUs_Sold_Per_Store"]):
        df["Inventory_Velocity_Gain"] = df["Historical_Avg_Daily_SPUs_Sold_Per_Store"].round(3)
    else:
        df["Inventory_Velocity_Gain"] = np.nan

    # Constraint Status and Trade-off analysis based on simple rules
    def _constraint_status(row):
        cap = row.get("Capacity_Utilization", np.nan)
        temp = row.get("Temperature_Suitability", "Unknown")
        flags = []
        if pd.notna(cap):
            flags.append("Capacity Tight" if cap >= 0.9 else "Capacity OK")
        else:
            flags.append("Capacity Unknown")
        flags.append("Temp OK" if temp in ("High", "Medium") else ("Temp Risk" if temp == "Low" else "Temp Unknown"))
        return ", ".join(flags)

    def _trade_off(row):
        rate = row.get("Current_Sell_Through_Rate", 0.0)
        inv = row.get("SPU_Store_Days_Inventory", 0.0)
        sales = row.get("SPU_Store_Days_Sales", 0.0)
        if rate >= 90:
            msg = "High sell-through; risk of stockout if inventory not replenished"
        elif rate <= 40:
            msg = "Low sell-through; risk of overstock and markdowns"
        else:
            msg = "Balanced; monitor inventory vs demand"
        return f"{msg} (inv={inv:.0f}, sales={sales:.0f})"

    df["Constraint_Status"] = df.apply(_constraint_status, axis=1)
    df["Trade_Off_Analysis"] = df.apply(_trade_off, axis=1)

    # Rationale
    df["Optimization_Rationale"] = (
        "Align inventory exposure (SPU-store-days) to historical sales patterns at store-group level "
        "to maximize sell-through rate while respecting capacity and environmental suitability"
    )

    # Backfill trend_inventory_turnover from sell-through components when missing
    try:
        if 'trend_inventory_turnover' not in df.columns:
            df['trend_inventory_turnover'] = np.nan
        sales = pd.to_numeric(df.get('SPU_Store_Days_Sales'), errors='coerce')
        inv = pd.to_numeric(df.get('SPU_Store_Days_Inventory'), errors='coerce')
        with np.errstate(divide='ignore', invalid='ignore'):
            turnover_score = (sales / inv) * 100.0
        turnover_score = turnover_score.where((inv > 0) & (sales.notna()), np.nan).clip(lower=0.0, upper=100.0)
        mask = df['trend_inventory_turnover'].isna()
        df.loc[mask, 'trend_inventory_turnover'] = turnover_score[mask]
    except Exception:
        pass

    # Backfill trend_sales_performance from SPU_Change_vs_Historical_Pct when missing
    try:
        if 'trend_sales_performance' not in df.columns:
            df['trend_sales_performance'] = np.nan
        pct = pd.to_numeric(df.get('SPU_Change_vs_Historical_Pct'), errors='coerce')
        # Map delta percent to 0-100 score centered at 50
        sales_perf = (50.0 + (pct / 2.0)).clip(lower=0.0, upper=100.0)
        mask = df['trend_sales_performance'].isna() & pct.notna()
        df.loc[mask, 'trend_sales_performance'] = sales_perf[mask]
    except Exception:
        pass

    # Expected_Benefit: derive from positive ΔQty and Avg_Sales_Per_SPU when missing
    try:
        if 'Expected_Benefit' not in df.columns:
            df['Expected_Benefit'] = np.nan
        # Find delta qty column
        delta_col = next((c for c in ['ΔQty','Delta_Qty','Qty_Delta','DeltaQty'] if c in df.columns), None)
        if delta_col is not None and 'Avg_Sales_Per_SPU' in df.columns:
            dq = pd.to_numeric(df[delta_col], errors='coerce')
            avg_sales = pd.to_numeric(df['Avg_Sales_Per_SPU'], errors='coerce')
            benefit = np.where((dq > 0) & (~pd.isna(avg_sales)), dq * avg_sales, np.nan)
            # Only fill when currently NaN to avoid overwriting any upstream real value
            mask = df['Expected_Benefit'].isna()
            df.loc[mask, 'Expected_Benefit'] = benefit[mask]
    except Exception:
        pass

    return df
    print("SELL-THROUGH RATE ANALYSIS SUMMARY")
    print("="*80)
    
    total_records = len(enhanced_df)
    records_with_rates = len(enhanced_df[enhanced_df['Sell_Through_Rate'] > 0])
    
    print(f"📊 Total Records: {total_records:,}")
    print(f"📈 Records with Sell-Through Rates: {records_with_rates:,} ({records_with_rates/total_records*100:.1f}%)")
    
    if records_with_rates > 0:
        valid_rates = enhanced_df[enhanced_df['Sell_Through_Rate'] > 0]
        
        print(f"\n🎯 SELL-THROUGH RATE STATISTICS:")
        print(f"   Average: {valid_rates['Sell_Through_Rate'].mean():.1f}%")
        print(f"   Median:  {valid_rates['Sell_Through_Rate'].median():.1f}%")
        print(f"   Min:     {valid_rates['Sell_Through_Rate'].min():.1f}%")
        print(f"   Max:     {valid_rates['Sell_Through_Rate'].max():.1f}%")
        
        # Rate distribution
        print(f"\n📊 SELL-THROUGH RATE DISTRIBUTION:")
        rate_bins = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
        for min_rate, max_rate in rate_bins:
            count = len(valid_rates[
                (valid_rates['Sell_Through_Rate'] >= min_rate) & 
                (valid_rates['Sell_Through_Rate'] < max_rate)
            ])
            pct = count / records_with_rates * 100 if records_with_rates > 0 else 0
            print(f"   {min_rate:2d}-{max_rate:2d}%: {count:4d} records ({pct:4.1f}%)")
        
        # Top and bottom performers
        print(f"\n🏆 TOP 5 HIGHEST SELL-THROUGH RATES:")
        top_5 = valid_rates.nlargest(5, 'Sell_Through_Rate')[
            ['Store_Group_Name', 'Target_Style_Tags', 'Target_SPU_Quantity', 'Sell_Through_Rate']
        ]
        for _, row in top_5.iterrows():
            tags_short = row['Target_Style_Tags'][:50] + "..." if len(str(row['Target_Style_Tags'])) > 50 else row['Target_Style_Tags']
            print(f"   {row['Sell_Through_Rate']:5.1f}% - {row['Store_Group_Name']} - {tags_short}")
        
        print(f"\n⚠️  BOTTOM 5 LOWEST SELL-THROUGH RATES:")
        bottom_5 = valid_rates.nsmallest(5, 'Sell_Through_Rate')[
            ['Store_Group_Name', 'Target_Style_Tags', 'Target_SPU_Quantity', 'Sell_Through_Rate']
        ]
        for _, row in bottom_5.iterrows():
            tags_short = row['Target_Style_Tags'][:50] + "..." if len(str(row['Target_Style_Tags'])) > 50 else row['Target_Style_Tags']
            print(f"   {row['Sell_Through_Rate']:5.1f}% - {row['Store_Group_Name']} - {tags_short}")
    
    print(f"\n💡 NEW COLUMNS ADDED:")
    print(f"   • SPU_Store_Days_Inventory: Target SPU Quantity × Stores × 15 days")
    print(f"   • SPU_Store_Days_Sales: Historical daily SPU sales × Stores × 15 days")  
    print(f"   • Sell_Through_Rate: (Sales ÷ Inventory) × 100%")
    print(f"   • Historical_Avg_Daily_SPUs_Sold_Per_Store: Average SPUs sold per store per day")
    
    print("\n" + "="*80)

def main():
    """Main execution function (period-aware)."""

    try:
        args = _parse_args()
        target_yyyymm = args.target_yyyymm
        target_period = args.target_period
        period_label = get_period_label(target_yyyymm, target_period)

        print("🚀 Starting Step 18: Sell-Through Rate Analysis")
        print("=" * 60)
        print(f"🗓️  Period: {period_label} (target_yyyymm={target_yyyymm}, period={target_period})")

        # Load files
        print("📂 Loading files...")
        augmented_df, historical_ref_df = load_files(target_yyyymm, target_period, args.input_file, args.baseline_period)
        print(f"✅ Loaded augmented file: {len(augmented_df):,} records")
        print(f"✅ Loaded historical data: {len(historical_ref_df):,} records")

        # Calculate historical sales data
        print("\n📊 Processing historical sales data...")
        historical_summary = _build_historical_summary(historical_ref_df, period_days=15)
        print(f"✅ Prepared historical summary for {len(historical_summary):,} combinations")

        # Add sell-through calculations
        print("\n🧮 Adding sell-through rate calculations...")
        enhanced_df = add_sell_through_calculations(augmented_df, historical_summary, show_progress=getattr(args, 'show_progress', False))
        print(f"✅ Enhanced {len(enhanced_df):,} records with sell-through metrics")

        # Add optimization visibility fields
        print("\n🔎 Adding optimization visibility fields...")
        enhanced_df = add_optimization_visibility_fields(enhanced_df)
        # Align Season/Gender/Location using store_config (exact joins), no guesswork
        enhanced_df = _enrich_dims_from_store_config(enhanced_df, target_yyyymm, target_period)
        print("✅ Optimization visibility columns added")

        # Save enhanced file (period-aware)
        print("\n💾 Saving enhanced file...")
        output_file = save_enhanced_file(enhanced_df, target_yyyymm, target_period)
        print(f"✅ Saved to: {output_file}")

        # Register outputs (generic + period-specific)
        target_year = int(target_yyyymm[:4])
        target_month = int(target_yyyymm[4:6])
        metadata = {
            "target_year": target_year,
            "target_month": target_month,
            "target_period": target_period,
            "records": len(enhanced_df),
            "columns": len(enhanced_df.columns),
            "sell_through_metrics": True,
            "optimization_visibility": True,
        }
        register_step_output("step18", "sell_through_analysis", output_file, metadata)
        register_step_output("step18", f"sell_through_analysis_{period_label}", output_file, metadata)

        # Print analysis summary
        print_analysis_summary(enhanced_df)

        print(f"\n🎉 Step 18 completed successfully!")
        print(f"📁 Output: {output_file}")
        print(f"📊 Total records: {len(enhanced_df):,}")
        print(f"📈 Columns: {len(enhanced_df.columns)} (including new sell-through metrics)")

        return output_file

    except Exception as e:
        logger.error(f"Step 18 failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
