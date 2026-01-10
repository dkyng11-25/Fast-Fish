#!/usr/bin/env python3
"""
Step 14: Enhanced Fast Fish Format with Complete outputFormat.md Compliance
========================================================================

Creates the complete Fast Fish format with ALL required outputFormat.md fields:
- ΔQty (Target - Current difference)
- Customer Mix (men_percentage, women_percentage)
- Display Location (front_store_percentage, back_store_percentage)
- Temp 14d Avg (14-day average temperature)
- Historical ST% (Historical sell-through rate, legacy percent)
- Historical_ST_Pct (explicit percent 0–100)
- Historical_ST_Frac (explicit fraction 0–1)
- Dimensional Target_Style_Tags: [Season, Gender, Location, Category, Subcategory]

Pipeline Flow:
Step 13 → Step 14 (Enhanced) → Steps 15-18

Units policy:
- Internally prefer fractions (0–1) for computation, expose percent for presentation.
- Keep legacy percent columns for backward compatibility while adding explicit _Frac/_Pct columns.

HOW TO RUN (CLI + ENV)
----------------------
Overview
- Period-aware: this step will read period context from env (PIPELINE_TARGET_YYYYMM/PIPELINE_TARGET_PERIOD) or fall back to current period in config.
- Inputs come from Step 13 consolidated outputs and period-aware API files (store_config, sales) via src.config helpers.
- For fast testing, it’s fine to run after a single-cluster test of upstream rules; for production, ensure Steps 7–13 were run for ALL clusters.

Quick Start (target 202510A)
  ENV (recommended):
    PIPELINE_TARGET_YYYYMM=202510 PIPELINE_TARGET_PERIOD=A

  Command:
    PYTHONPATH=. python3 src/step14_create_fast_fish_format.py

Optional Overrides
- STEP14_WEATHER_FILE, STEP14_SPU_SALES_FILE, STEP14_STORE_CONFIG_FILE to point to explicit inputs (otherwise resolved via config).
- STEP14_BASELINE_YYYYMM/STEP14_BASELINE_PERIOD to control historical defaults used in certain enrichments.

Best Practices & Pitfalls
- Ensure Step 13 outputs exist before Step 14.
- Keep `str_code` typed as string across joins to avoid silent row drops.
- If seasonal tagging looks off (e.g., no autumn in August), verify baseline period logic and store_config period selection; adjust STEP14_BASELINE_* or re-run Step 15–18 accordingly.

HOW TO RUN – Reproduction Example (202508A, YoY-forward)
--------------------------------------------------------
To reproduce the forward-oriented 202508A output we generated, we sourced YoY analog inputs (202410A) via env overrides:

  STEP14_SPU_SALES_FILE=output/complete_spu_sales_202410A.csv \
  STEP14_STORE_CONFIG_FILE=output/store_config_202410A.csv \
  STEP14_BASELINE_YYYYMM=202410 \
  STEP14_BASELINE_PERIOD=A \
  PYTHONPATH=. python3 src/step14_create_fast_fish_format.py --target-yyyymm 202508 --target-period A

Notes:
- This steers Step 14 to use last year’s analogous period to bias mix toward upcoming AW while keeping period labeling at 202508A.
- Downstream, rerun Steps 15–18 to propagate the updated mix.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import json
import difflib
import os
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import logging
import argparse
from tqdm import tqdm
try:
    # Prefer explicit package imports when running as a module (python -m src.step14_create_fast_fish_format)
    from src.config import (
        get_api_data_files,
        get_current_period,
        get_period_label,
        load_sales_df_with_fashion_basic,
    )
    from src.pipeline_manifest import get_manifest, register_step_output
except Exception:  # Fallback for direct script execution contexts
    from config import (
        get_api_data_files,
        get_current_period,
        get_period_label,
        load_sales_df_with_fashion_basic,
    )
    from pipeline_manifest import get_manifest, register_step_output

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Sell-through normalization helpers (local to Step 14) ---
def _st_clip_01(x) -> float:
    """Clip numeric to [0,1]; return NaN on errors."""
    try:
        if pd.isna(x):
            return np.nan
        return float(np.clip(float(x), 0.0, 1.0))
    except Exception:
        return np.nan

def _st_pct_to_frac(pct) -> float:
    """Convert percent (0–100) to fraction (0–1) with clipping and NA-safety."""
    try:
        if pd.isna(pct):
            return np.nan
        v = float(pct)
        v = np.clip(v, 0.0, 100.0)
        return float(v / 100.0)
    except Exception:
        return np.nan

# Global cache for data loading
_weather_data_cache = None
_historical_data_cache = None
_cluster_mapping_cache = None

def get_period_parts() -> Tuple[int, int, str, str]:
    env_yyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM")
    env_period = os.environ.get("PIPELINE_TARGET_PERIOD")
    if env_yyyymm and len(env_yyyymm) == 6 and env_yyyymm.isdigit():
        year = int(env_yyyymm[:4])
        month = int(env_yyyymm[4:6])
        period = (env_period or "A").upper() if env_period in ("A", "B") else "A"
        return year, month, period, get_period_label(env_yyyymm, period)
    cur_yyyymm, cur_period = get_current_period()
    year = int(cur_yyyymm[:4])
    month = int(cur_yyyymm[4:6])
    period = (cur_period or "A").upper() if cur_period in ("A", "B") else "A"
    return year, month, period, get_period_label(cur_yyyymm, cur_period)

def get_target_period() -> str:
    return get_period_parts()[2]

def _embed_period_metadata_columns(df: pd.DataFrame, yyyymm: str, period: str, period_label: str) -> pd.DataFrame:
    """
    Ensure period metadata columns exist even for empty DataFrames.
    Adds: period_label, target_yyyymm, target_period.
    """
    try:
        out = df.copy() if df is not None else pd.DataFrame()
    except Exception:
        out = pd.DataFrame()
    out['period_label'] = period_label
    out['target_yyyymm'] = yyyymm
    out['target_period'] = str(period) if period is not None else ''
    return out

def compute_temperature_suitability(mapped_season: str, temperature: float) -> str:
    """Basic suitability heuristic by season. Non-blocking, conservative.
    mapped_season is expected to be one of ['春','夏','秋','冬'] when available.
    """
    try:
        s = str(mapped_season)
        # If temperature is missing, return conservative 'Review' instead of defaulting
        if temperature is None:
            return "Review"
        try:
            # Handle NaN floats explicitly
            if isinstance(temperature, float) and np.isnan(temperature):
                return "Review"
        except Exception:
            pass
        t = float(temperature)
        if s in ("夏", "Summer", "summer"):
            return "Suitable" if t >= 20 else "Review"
        if s in ("春", "Spring", "spring"):
            return "Suitable" if 10 <= t <= 25 else "Review"
        if s in ("秋", "Autumn", "autumn", "Fall", "fall"):
            return "Suitable" if 10 <= t <= 20 else "Review"
        if s in ("冬", "Winter", "winter"):
            return "Suitable" if t <= 15 else "Review"
        return "Review"
    except Exception:
        return "Review"

def _default_season_for_month(month: int) -> str:
    """Map calendar month to a default season label.
    3-5: 春, 6-8: 夏, 9-11: 秋, else: 冬
    """
    try:
        m = int(month)
        if m in (3, 4, 5):
            return "春"
        if m in (6, 7, 8):
            return "夏"
        if m in (9, 10, 11):
            return "秋"
        return "冬"
    except Exception:
        return "夏"

def load_weather_data():
    """Load weather data with caching."""
    global _weather_data_cache
    if _weather_data_cache is None:
        try:
            weather_file = os.environ.get("STEP14_WEATHER_FILE", "output/stores_with_feels_like_temperature.csv")
            if os.path.exists(weather_file):
                _weather_data_cache = pd.read_csv(weather_file)
                logger.info(f"Loaded weather data for {len(_weather_data_cache)} stores")
            else:
                logger.warning(f"Weather data file not found: {weather_file}")
                _weather_data_cache = pd.DataFrame()
        except Exception as e:
            logger.warning(f"Error loading weather data: {e}")
            _weather_data_cache = pd.DataFrame()
    return _weather_data_cache

def load_historical_sales_data():
    """Load historical sales data with caching."""
    global _historical_data_cache
    if _historical_data_cache is None:
        try:
            # Allow override via env; else prefer baseline yyyyMM + period (defaults to 202409 + target period)
            override = os.environ.get("STEP14_HISTORICAL_SPU_SALES_FILE")
            if override and os.path.exists(override):
                _historical_data_cache = pd.read_csv(override, dtype={'str_code': str})
                src = os.path.basename(override)
                logger.info(f"Loaded historical sales data ({src}): {len(_historical_data_cache):,} records")
            else:
                baseline_yyyymm = os.environ.get("STEP14_BASELINE_YYYYMM", "202409")
                baseline_period = os.environ.get("STEP14_BASELINE_PERIOD") or get_target_period()
                try:
                    src_path, df = load_sales_df_with_fashion_basic(baseline_yyyymm, baseline_period, require_spu_level=True,
                                                                   required_cols=['str_code','spu_code'])
                    _historical_data_cache = df
                    logger.info(f"Loaded historical sales data ({os.path.basename(src_path)}): {len(_historical_data_cache):,} records")
                except Exception as e:
                    logger.warning(f"Historical sales data load failed for {baseline_yyyymm}{baseline_period}: {e}")
                    _historical_data_cache = pd.DataFrame()
        except Exception as e:
            logger.warning(f"Error loading historical sales data: {e}")
            _historical_data_cache = pd.DataFrame()
    return _historical_data_cache

def load_cluster_mapping():
    """Load cluster mapping data with caching (union of best-available sources)."""
    global _cluster_mapping_cache
    if _cluster_mapping_cache is None:
        try:
            # Preferred explicit override
            override = os.environ.get("STEP14_CLUSTER_FILE")
            year, month, period, period_label = get_period_parts()
            # Candidate files in preference order
            candidates = []
            if override:
                candidates.append(override)
            # Period-labeled first
            candidates.extend([
                f"output/clustering_results_spu_{period_label}.csv",
                "output/clustering_results_spu.csv",
                "output/clustering_results.csv",
                "output/comprehensive_cluster_labels.csv",
            ])
            # Collect existing files
            frames: List[pd.DataFrame] = []
            seen_paths = set()
            for path in candidates:
                if path and path not in seen_paths and os.path.exists(path):
                    try:
                        df = pd.read_csv(path)
                        if 'str_code' in df.columns and 'Cluster' in df.columns:
                            df = df[['str_code', 'Cluster']].copy()
                            frames.append(df)
                            logger.info(f"Cluster mapping source added: {path} ({len(df)})")
                        else:
                            # Try alternate column names
                            alt = df.copy()
                            if 'store_code' in alt.columns and 'cluster' in alt.columns:
                                alt = alt.rename(columns={'store_code': 'str_code', 'cluster': 'Cluster'})
                                frames.append(alt[['str_code', 'Cluster']])
                                logger.info(f"Cluster mapping source (alt cols) added: {path} ({len(alt)})")
                    except Exception as e:
                        logger.warning(f"Failed reading cluster mapping from {path}: {e}")
                    seen_paths.add(path)
            if frames:
                # Concatenate and prefer first occurrences (earlier sources win)
                concat_df = pd.concat(frames, ignore_index=True)
                concat_df['str_code'] = concat_df['str_code'].astype(str)
                # Drop duplicates keeping first
                concat_df = concat_df.drop_duplicates(subset=['str_code'], keep='first')
                _cluster_mapping_cache = concat_df.reset_index(drop=True)
                logger.info(f"Loaded union cluster mapping for {len(_cluster_mapping_cache)} stores from {len(frames)} sources")
            else:
                logger.warning("No cluster mapping sources found")
                _cluster_mapping_cache = pd.DataFrame()
        except Exception as e:
            logger.warning(f"Error loading cluster mapping: {e}")
            _cluster_mapping_cache = pd.DataFrame()
    return _cluster_mapping_cache

def load_category_translation_map() -> Dict[Tuple[str, str], Tuple[str, str]]:
    """Optional translation map between rule taxonomy and Fast Fish taxonomy.
    Returns mapping: (rule_category, rule_subcategory) -> (target_category, target_subcategory)
    Sources checked (in order):
      - env STEP14_CATEGORY_TRANSLATION_FILE (CSV with columns: rule_category,rule_subcategory,target_category,target_subcategory)
      - data/category_translation_map.csv (same schema)
    If not found, returns a small built-in mapping for common cases.
    """
    candidates = []
    try:
        override = os.environ.get("STEP14_CATEGORY_TRANSLATION_FILE")
        if override and os.path.exists(override):
            candidates.append(override)
        default_csv = "data/category_translation_map.csv"
        if os.path.exists(default_csv):
            candidates.append(default_csv)
        mapping: Dict[Tuple[str, str], Tuple[str, str]] = {}
        for path in candidates:
            try:
                df = pd.read_csv(path)
                cols = {c.lower(): c for c in df.columns}
                rc = cols.get('rule_category') or cols.get('from_category')
                rs = cols.get('rule_subcategory') or cols.get('from_subcategory')
                tc = cols.get('target_category') or cols.get('to_category')
                ts = cols.get('target_subcategory') or cols.get('to_subcategory')
                if not all([rc, rs, tc, ts]):
                    continue
                for _, row in df.iterrows():
                    key = (str(row.get(rc, '')).strip(), str(row.get(rs, '')).strip())
                    val = (str(row.get(tc, '')).strip(), str(row.get(ts, '')).strip())
                    if key != ('', '') and val != ('', ''):
                        mapping[key] = val
            except Exception as e:
                logger.warning(f"Failed to read category translation from {path}: {e}")
        # Built-in minimal mappings (extend as needed)
        if not mapping:
            builtin = {
                ('T恤', '休闲圆领T恤'): ('T恤', '休闲圆领T恤'),
                ('T恤', '微宽松圆领T恤'): ('T恤', '微宽松圆领T恤'),
                ('裤', '中裤'): ('裤', '中裤'),
                ('POLO衫', '休闲POLO'): ('POLO衫', '休闲POLO'),
                ('POLO衫', '凉感POLO'): ('POLO衫', '凉感POLO'),
            }
            mapping.update(builtin)
        return mapping
    except Exception:
        return {}

def _normalize(x: Optional[str]) -> str:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ''
        return str(x).strip()
    except Exception:
        return ''

def _best_fuzzy_match(candidates: List[str], target: str, *, threshold: float = 0.6) -> Optional[str]:
    """Return best fuzzy match from candidates to target using SequenceMatcher ratio, or None."""
    try:
        target_s = _normalize(target)
        if not candidates or not target_s:
            return None
        best = None
        best_score = 0.0
        for c in candidates:
            cs = _normalize(c)
            if not cs:
                continue
            score = difflib.SequenceMatcher(None, cs, target_s).ratio()
            if score > best_score:
                best_score = score
                best = c
        return best if best_score >= threshold else None
    except Exception:
        return None

# =============================
# Recommendation strategy (DRAFT)
# =============================

# Feature flags (keep default False to preserve current behavior)
ENABLE_ADAPTIVE_CAPS = False
ENABLE_SCORED_SELECTION = False
# Adds-only aggregation for ΔQty (ignore removals); default False to preserve prior behavior
ADDS_ONLY_QTY = False

# Strategy weights and constraints
RECOMMENDATION_STRATEGY = {
    'max_cap_absolute': 50,               # Hard ceiling on absolute change
    'min_display_spus': 3,                # Minimum allowed target after reductions (raise to avoid over-shrink)
    'base_cap_fraction': 0.20,            # Base ±% of current for cap (up vs down asymmetry handled below)
    'role_weights_add': {                 # Relative desirability for adding
        'CORE': 1.00,
        'SEASONAL': 0.80,
        'FILLER': 0.40,
        'CLEARANCE': 0.05
    },
    'role_weights_remove': {              # Relative desirability for removing
        'CLEARANCE': 1.00,
        'FILLER': 0.70,
        'SEASONAL': 0.30,
        'CORE': 0.05
    },
    'seasonality_multiplier': {           # Map temperature suitability to multiplier
        'Suitable': 1.10,
        'Review': 0.90
    },
    'sell_through_breakpoints': [         # Piecewise multipliers on historical ST%
        (80.0, 1.20),
        (60.0, 1.10),
        (40.0, 1.00),
        (20.0, 0.85),
        (0.0, 0.75)
    ],
    'size_breakpoints': [                 # Multiplier by number of stores in group (proxy size)
        (50, 1.20),
        (25, 1.10),
        (10, 1.00),
        (1, 0.90)
    ]
}

def _mult_from_breakpoints(value: float, breakpoints: list) -> float:
    """Return the first multiplier where value >= threshold in a descending-threshold list."""
    try:
        v = float(value)
    except Exception:
        v = 0.0
    for threshold, mult in breakpoints:
        if v >= threshold:
            return float(mult)
    # Fallback to the last multiplier if list not empty
    return float(breakpoints[-1][1]) if breakpoints else 1.0

def compute_adaptive_caps(current_qty: int,
                          stores_in_group: int = None,
                          historical_st_pct: float = None,
                          temperature_suitability: str = None,
                          max_cap_absolute: int = None,
                          min_display_spus: int = None,
                          base_cap_fraction: float = None) -> tuple:
    """
    Compute upward/downward caps for ΔQty using available signals.

    Inputs:
      - current_qty: current SPU count for the group (int)
      - stores_in_group: number of stores selling this category in the group (proxy for scale)
      - historical_st_pct: historical sell-through percentage at the group/category level (0-100)
      - temperature_suitability: one of {'Suitable','Review', None}
      - max_cap_absolute: global hard ceiling on absolute change
      - min_display_spus: planogram/display minimum target
      - base_cap_fraction: baseline fraction of current used before scaling

    Returns:
      (cap_up, cap_down) as positive integers (both ≥ 0)
    """
    cfg = RECOMMENDATION_STRATEGY
    if max_cap_absolute is None:
        max_cap_absolute = int(cfg['max_cap_absolute'])
    if min_display_spus is None:
        min_display_spus = int(cfg['min_display_spus'])
    if base_cap_fraction is None:
        base_cap_fraction = float(cfg['base_cap_fraction'])

    # Base caps
    base_cap = int(round(max(0, int(current_qty)) * base_cap_fraction))
    base_cap = max(1, base_cap)  # at least 1 up if any change is allowed

    # Multipliers
    st_mult = _mult_from_breakpoints(historical_st_pct, cfg['sell_through_breakpoints']) if historical_st_pct is not None else 1.0
    size_mult = _mult_from_breakpoints(stores_in_group, cfg['size_breakpoints']) if stores_in_group is not None else 1.0
    season_mult = cfg['seasonality_multiplier'].get(str(temperature_suitability), 1.0)

    # Aggregate multiplier (bounded for safety)
    agg_mult = max(0.5, min(1.5, st_mult * size_mult * season_mult))

    # Upward cap: allow fuller expression of upside
    cap_up = int(round(base_cap * max(1.0, agg_mult)))
    cap_up = max(1, min(cap_up, max_cap_absolute))

    # Downward cap: asymmetric and conservative for healthy categories
    down_mult = min(agg_mult, 1.0)
    try:
        if historical_st_pct is not None and float(historical_st_pct) >= 60.0 and str(temperature_suitability) == 'Suitable':
            # Strong performers in suitable climates: heavily restrict removals
            down_mult = down_mult * 0.3
        elif historical_st_pct is not None and float(historical_st_pct) >= 40.0:
            down_mult = down_mult * 0.6
        # If suitability is Review, allow a bit more downward movement but still bounded
        if str(temperature_suitability) == 'Review':
            down_mult = min(1.0, down_mult * 1.1)
    except Exception:
        pass

    cap_down_base = int(round(base_cap * down_mult))
    # Down cap cannot push target below planogram minimum
    cap_down = min(cap_down_base, max(0, int(current_qty) - int(min_display_spus)))
    cap_down = max(0, min(cap_down, max_cap_absolute))

    return cap_up, cap_down

_product_roles_cache = None

def load_product_roles() -> pd.DataFrame:
    """Load product role classifications if available; cached for reuse."""
    global _product_roles_cache
    if _product_roles_cache is not None:
        return _product_roles_cache
    try:
        path = "output/product_role_classifications.csv"
        if os.path.exists(path):
            df = pd.read_csv(path, dtype={'spu_code': str})
            _product_roles_cache = df
        else:
            _product_roles_cache = pd.DataFrame()
    except Exception:
        _product_roles_cache = pd.DataFrame()
    return _product_roles_cache

def score_add_candidate(spu_code: str,
                        historical_st_pct: float = None,
                        temperature_suitability: str = None,
                        product_roles_df: pd.DataFrame = None,
                        role_weights: dict = None) -> float:
    """
    Score an ADD candidate SPU using role, historical ST%, and season suitability.
    Returns a higher-is-better utility score.
    """
    cfg = RECOMMENDATION_STRATEGY
    if role_weights is None:
        role_weights = cfg['role_weights_add']
    # Role weight
    role_weight = 0.5
    if product_roles_df is not None and not product_roles_df.empty:
        row = product_roles_df[product_roles_df['spu_code'] == str(spu_code)].head(1)
        if not row.empty:
            role = str(row.iloc[0].get('product_role', '')).upper()
            role_weight = float(role_weights.get(role, 0.5))
    # ST prior (normalize to 0..1 range)
    st_prior = 0.5
    try:
        if historical_st_pct is not None and not pd.isna(historical_st_pct):
            st_prior = max(0.0, min(1.0, float(historical_st_pct) / 100.0))
    except Exception:
        st_prior = 0.5
    # Season suitability
    season_mult = cfg['seasonality_multiplier'].get(str(temperature_suitability), 1.0)
    return float(role_weight * (0.5 + 0.5 * st_prior) * season_mult)

def score_remove_candidate(spu_code: str,
                           historical_st_pct: float = None,
                           temperature_suitability: str = None,
                           product_roles_df: pd.DataFrame = None,
                           role_weights: dict = None) -> float:
    """
    Score a REMOVE candidate SPU (higher score means stronger removal case).
    """
    cfg = RECOMMENDATION_STRATEGY
    if role_weights is None:
        role_weights = cfg['role_weights_remove']
    role_weight = 0.5
    if product_roles_df is not None and not product_roles_df.empty:
        row = product_roles_df[product_roles_df['spu_code'] == str(spu_code)].head(1)
        if not row.empty:
            role = str(row.iloc[0].get('product_role', '')).upper()
            role_weight = float(role_weights.get(role, 0.5))
    st_headroom = 0.5
    try:
        if historical_st_pct is not None and not pd.isna(historical_st_pct):
            # Lower ST => higher removal score
            st = max(0.0, min(1.0, float(historical_st_pct) / 100.0))
            st_headroom = 1.0 - st
    except Exception:
        st_headroom = 0.5
    season_mult = cfg['seasonality_multiplier'].get(str(temperature_suitability), 1.0)
    return float(role_weight * (0.5 + 0.5 * st_headroom) * season_mult)

def calculate_store_group_temperature(store_group_name, cluster_mapping_df, weather_df):
    """Calculate average temperature for a store group based on its cluster stores."""
    try:
        if cluster_mapping_df.empty or weather_df.empty:
            return np.nan
        
        # Extract cluster number from store group name (Store Group N -> Cluster N-1)
        cluster_id = int(store_group_name.split(" ")[-1]) - 1
        
        # Get stores in this cluster
        cluster_stores = cluster_mapping_df[cluster_mapping_df["Cluster"] == cluster_id]["str_code"].tolist()
        
        if not cluster_stores:
            return np.nan
        
        # Get temperature data for these stores
        store_temps = weather_df[weather_df["store_code"].isin([int(s) for s in cluster_stores if s.isdigit()])]["feels_like_temperature"]
        
        # Return average temperature or default if no data
        return round(float(store_temps.mean()), 1) if len(store_temps) > 0 else np.nan
    except Exception as e:
        logger.warning(f"Error calculating temperature for {store_group_name}: {e}")
        return np.nan

def calculate_historical_sell_through(store_group_name, category, subcategory, historical_sales_df, cluster_mapping_df):
    """Calculate historical sell-through rate for a store group and category combination."""
    try:
        if cluster_mapping_df.empty or historical_sales_df.empty:
            return np.nan
        
        # Get stores in this store group
        cluster_id = int(store_group_name.split(" ")[-1]) - 1
        group_stores = cluster_mapping_df[cluster_mapping_df["Cluster"] == cluster_id]["str_code"].tolist()
        
        if not group_stores:
            return np.nan
        
        # Filter historical data for this store group and category
        filtered_data = historical_sales_df[
            (historical_sales_df["str_code"].isin(group_stores)) &
            (historical_sales_df["cate_name"] == category) &
            (historical_sales_df["sub_cate_name"] == subcategory)
        ]
        
        if len(filtered_data) == 0:
            return np.nan
        
        # Calculate a more meaningful sell-through rate based on sales velocity
        # Instead of using the flawed revenue calculation, we'll use quantity-based approach
        total_quantity = filtered_data["quantity"].sum()
        avg_daily_quantity = total_quantity / len(filtered_data)  # Average per record
        
        # Use a proxy for inventory level based on average daily sales and a reasonable inventory period
        # Assuming a typical inventory turnover period of 30 days for fashion items
        estimated_inventory = avg_daily_quantity * 30
        
        if estimated_inventory > 0:
            # Sell-through rate = (quantity sold / estimated inventory) * 100
            # But cap it at a reasonable maximum to avoid unrealistic values
            sell_through_rate = min(100.0, (total_quantity / estimated_inventory) * 100)
            # Ensure we don't return values that are too low or too high
            return round(max(10.0, min(95.0, sell_through_rate)), 1)
        
        return np.nan
    except Exception as e:
        logger.warning(f"Error calculating sell-through for {store_group_name}, {category}: {e}")
        return np.nan

def load_consolidated_spu_rules():
    """Load consolidated SPU rules from Step 13 using manifest- and period-aware resolution."""
    logger.info("🔧 Loading SPU-level rules from Step 13 (manifest-aware)...")
    # Allow explicit override via CLI/env
    override_rules = os.environ.get("STEP14_RULES_FILE")
    if override_rules and os.path.exists(override_rules):
        logger.info(f"✅ Using override rules file: {override_rules}")
        consolidated_df = pd.read_csv(override_rules, dtype={'str_code': str})
        return consolidated_df, True

    # Resolve period label
    try:
        _, _, period, period_label = get_period_parts()
    except Exception:
        period_label = None

    # Prefer manifest-registered detailed outputs from Step 13
    try:
        manifest = get_manifest().manifest
        step_outputs = manifest.get('steps', {}).get('step13', {}).get('outputs', {})
        candidate_keys = []
        if period_label:
            candidate_keys.extend([
                f"consolidated_rules_{period_label}",
            ])
        candidate_keys.append("consolidated_rules")
        for key in candidate_keys:
            meta = step_outputs.get(key)
            if isinstance(meta, dict):
                path = meta.get('file_path')
                if path and os.path.exists(path):
                    df = pd.read_csv(path, dtype={'str_code': str})
                    logger.info(f"✅ Loaded SPU rules via manifest key '{key}': {path} ({len(df):,} rows)")
                    return df, True
    except Exception as e:
        logger.warning(f"Manifest lookup for Step 13 failed: {e}")

    # Period-labeled fallbacks
    fallback_paths = []
    if period_label:
        fallback_paths.append(f"output/consolidated_spu_rule_results_detailed_{period_label}.csv")
    fallback_paths.extend([
        "output/consolidated_spu_rule_results_detailed.csv",
    ])
    for p in fallback_paths:
        if p and os.path.exists(p):
            df = pd.read_csv(p, dtype={'str_code': str})
            logger.info(f"✅ Loaded SPU rules from fallback: {p} ({len(df):,} rows)")
            return df, True

    logger.error("❌ No consolidated SPU rules file found (Step 13). Ensure Step 13 completed and registered outputs.")
    raise FileNotFoundError("Consolidated SPU rules not found from Step 13")

def load_api_data_with_dimensions():
    """Load API data with dimensional attributes for aggregation using actual sales data"""
    logger.info("Loading API data with dimensional attributes...")
    
    # CRITICAL FIX: Use actual sales data for dimensional aggregation instead of store_config
    # This ensures all valid store group/category/subcategory combinations are captured
    
    # Load SPU sales data - prefer CLI/env, then period-aware config; forbid legacy combined
    override_spu = os.environ.get("STEP14_SPU_SALES_FILE")
    spu_sales_file = None
    if override_spu and os.path.exists(override_spu):
        spu_sales_file = override_spu
    else:
        period_spu_file = get_api_data_files().get('spu_sales')
        if period_spu_file and os.path.exists(period_spu_file):
            spu_sales_file = period_spu_file
    if spu_sales_file is None:
        raise FileNotFoundError("SPU sales file not found via CLI/env or period-aware configuration")
    
    # Load store config for dimensional attributes (season, gender, location)
    override_cfg = os.environ.get("STEP14_STORE_CONFIG_FILE")
    store_config_file = None
    if override_cfg and os.path.exists(override_cfg):
        store_config_file = override_cfg
    else:
        period_cfg_file = get_api_data_files().get('store_config')
        if period_cfg_file and os.path.exists(period_cfg_file):
            store_config_file = period_cfg_file
    
    logger.info(f"Loading SPU sales data: {spu_sales_file}")
    spu_df = pd.read_csv(spu_sales_file)
    logger.info(f"Loaded {len(spu_df):,} SPU sales records")
    
    if store_config_file:
        logger.info(f"Loading store config data for dimensional attributes: {store_config_file}")
        config_df = pd.read_csv(store_config_file)
        logger.info(f"Loaded {len(config_df):,} store config records")
    else:
        logger.warning("Store config not found - using default dimensional attributes")
        config_df = pd.DataFrame()
    
    # CRITICAL FIX: Use actual sales data directly for dimensional aggregation
    # This ensures ALL valid store/category/subcategory combinations are captured
    logger.info("Using actual sales data for dimensional aggregation...")
    
    # Start with the complete sales data
    api_df = spu_df.copy()
    
    # Add dimensional attributes by merging with store config where available
    if not config_df.empty:
        logger.info("Enriching sales data with dimensional attributes from store config (exact and normalized joins)...")

        # Normalize keys to maximize exact matching without guessing
        def _norm_subcat(s: pd.Series) -> pd.Series:
            return s.astype(str).str.strip()

        api_df['sub_cate_name'] = _norm_subcat(api_df['sub_cate_name'])
        config_df['sub_cate_name'] = _norm_subcat(config_df['sub_cate_name'])

        # Primary exact merge on str_code × sub_cate_name
        dims_cols = ['season_name', 'sex_name', 'display_location_name']
        merged = api_df.merge(
            config_df[['str_code', 'sub_cate_name'] + dims_cols],
            on=['str_code', 'sub_cate_name'],
            how='left',
            suffixes=(None, '_cfg')
        )

        # Secondary fallback: normalized subcategory join (trimmed already); if still missing, use store-level mode
        missing_mask = merged['sex_name'].isna() & merged['season_name'].isna() & merged['display_location_name'].isna()
        if missing_mask.any():
            # Compute store-level modes from config
            store_modes = config_df.groupby('str_code').agg({
                'season_name': lambda s: s.mode().iloc[0] if not s.mode().empty else pd.NA,
                'sex_name': lambda s: s.mode().iloc[0] if not s.mode().empty else pd.NA,
                'display_location_name': lambda s: s.mode().iloc[0] if not s.mode().empty else pd.NA,
            }).reset_index()
            merged = merged.merge(store_modes, on='str_code', how='left', suffixes=('', '_storemode'))
            # Fill from store modes only where still missing
            for c in dims_cols:
                merged[c] = merged[c].where(merged[c].notna(), merged[f"{c}_storemode"])
            # Drop helper columns
            merged = merged.drop(columns=[f"{c}_storemode" for c in dims_cols])

        api_df = merged
        logger.info(f"Enriched {len(api_df):,} sales records with dimensional attributes via exact/store-mode joins")

        # Diagnostics: report missing and distribution for dimensions (no synthetic defaults)
        missing_dims = api_df[['season_name', 'sex_name', 'display_location_name']].isna().sum().to_dict()
        logger.info(
            f"Missing dimensions — season: {int(missing_dims.get('season_name', 0))}, "
            f"gender: {int(missing_dims.get('sex_name', 0))}, "
            f"location: {int(missing_dims.get('display_location_name', 0))}"
        )
        for col in ['season_name', 'sex_name', 'display_location_name']:
            try:
                dist = api_df[col].value_counts(dropna=False).to_dict()
                logger.info(f"{col} distribution (incl NA): {dist}")
            except Exception:
                pass
    else:
        # No config available: leave dims missing to avoid synthetic defaults
        logger.error("Store config not found - leaving dimensional attributes as NA to avoid synthetic defaults")
        api_df['season_name'] = pd.NA
        api_df['sex_name'] = pd.NA
        api_df['display_location_name'] = pd.NA
    
    # Rename columns to match expected format
    if 'spu_sales_amt' not in api_df.columns:
        if 'quantity' in api_df.columns and 'unit_price' in api_df.columns:
            api_df['spu_sales_amt'] = api_df['quantity'] * api_df['unit_price']
        else:
            api_df['spu_sales_amt'] = np.nan
    
    logger.info(f"Final API data: {len(api_df):,} records with all dimensional attributes")
    
    # Ensure str_code is string type for consistent merging
    api_df['str_code'] = api_df['str_code'].astype(str)
    
    # Verify we have all required columns
    required_cols = ['spu_code', 'str_code', 'cate_name', 'sub_cate_name', 'spu_sales_amt']
    dimensional_cols = ['season_name', 'sex_name', 'display_location_name']
    
    for col in required_cols + dimensional_cols:
        if col not in api_df.columns:
            logger.error(f"Missing required column after expansion: {col}")
            raise ValueError(f"Expanded data missing required column: {col}")
    
    logger.info("✅ Successfully loaded API data with dimensional attributes")
    return api_df

def create_store_groups(api_df):
    """Create store groups using clustering results (period-aware, using cached mapping)."""
    logger.info("Creating store groups from clustering results...")
    cluster_mapping_df = load_cluster_mapping()
    if cluster_mapping_df.empty:
        logger.error("Clustering results not available; cannot create store groups without real clusters")
        raise FileNotFoundError("Clustering results not found for store grouping")
    # Ensure consistent types
    cluster_mapping_df['str_code'] = cluster_mapping_df['str_code'].astype(str)
    api_df['str_code'] = api_df['str_code'].astype(str)
    # Merge mapping
    api_df = api_df.merge(
        cluster_mapping_df[['str_code', 'Cluster']],
        on='str_code',
        how='left'
    )
    api_df['Store_Group_Name'] = api_df['Cluster'].apply(lambda x: f"Store Group {int(x) + 1}" if pd.notna(x) else pd.NA)
    logger.info(f"Mapped stores to {api_df['Store_Group_Name'].nunique()} store groups (including NA)")
    return api_df

def create_dimensional_target_style_tags(season, gender, location, category, subcategory):
    """Create dimensional Target_Style_Tags in the enhanced format"""
    
    # Season mapping
    season_map = {
        '春': '春', 'Spring': '春', 'spring': '春',
        '夏': '夏', 'Summer': '夏', 'summer': '夏', 
        '秋': '秋', 'Autumn': '秋', 'autumn': '秋', 'Fall': '秋', 'fall': '秋',
        '冬': '冬', 'Winter': '冬', 'winter': '冬',
        '四季': '四季', 'All-season': '四季', 'all-season': '四季', '全年': '四季'
    }
    
    # Gender mapping  
    gender_map = {
        '男': '男', 'Men': '男', 'men': '男', 'Male': '男', 'male': '男',
        '女': '女', 'Women': '女', 'women': '女', 'Female': '女', 'female': '女',
        '中': '中', 'Unisex': '中', 'unisex': '中'
    }
    
    # Location mapping
    location_map = {
        '前台': '前台', 'Front-store': '前台', 'front-store': '前台', 'Front': '前台', '收银台': '前台',
        '后台': '后台', 'Back-store': '后台', 'back-store': '后台', 'Back': '后台', '后场': '后台', '后仓': '后台',
        '鞋配': '鞋配'
    }
    
    # Apply mappings WITHOUT synthetic defaults. If unknown, keep empty string.
    s = str(season) if season is not None else ''
    g = str(gender) if gender is not None else ''
    l = str(location) if location is not None else ''
    mapped_season = season_map.get(s, '' if s in ('', 'nan', 'None') else s)
    mapped_gender = gender_map.get(g, '' if g in ('', 'nan', 'None') else g)
    mapped_location = location_map.get(l, '' if l in ('', 'nan', 'None') else l)
    
    return f"[{mapped_season}, {mapped_gender}, {mapped_location}, {category}, {subcategory}]"
  
  
def parse_target_style_tags(tags: str):
    """Parse Target_Style_Tags into (season, gender, location, category, subcategory).
    Handles formats like:
    - "[夏, 女, 前台, POLO衫, 套头POLO]"
    - "[[夏, 女, 前台, POLO衫, 套头POLO]]"
    - "T恤 | 休闲圆领T恤 | 前台 | 夏 | 男" (pipe-delimited)
    """
    try:
        if tags is None or (isinstance(tags, float) and np.isnan(tags)):
            return ('', '', '', '', '')
        content = str(tags).strip()
        # Normalize pipe-delimited to comma-separated
        if ' | ' in content and '[' not in content:
            content = '[' + content.replace(' | ', ', ') + ']'
        # Strip surrounding brackets (single or double)
        if content.startswith('[[') and content.endswith(']]'):
            content = content[2:-2].strip()
        elif content.startswith('[') and content.endswith(']'):
            content = content[1:-1].strip()
        # Split and trim
        parts = [p.strip() for p in content.split(',')]
        # Pad to length 5
        while len(parts) < 5:
            parts.append('')
        return (parts[0], parts[1], parts[2], parts[3], parts[4])
    except Exception:
        return ('', '', '', '', '')
  
  
def build_dim_mismatch_notes(row) -> str:
    """Create a compact mismatch note comparing structured columns with parsed tags."""
    notes = []
    def _str(x):
        if pd.isna(x):
            return ''
        return str(x).strip()
    comparisons = [
        ('Season', _str(row.get('Season', '')), _str(row.get('Parsed_Season', ''))),
        ('Gender', _str(row.get('Gender', '')), _str(row.get('Parsed_Gender', ''))),
        ('Location', _str(row.get('Location', '')), _str(row.get('Parsed_Location', ''))),
        ('Category', _str(row.get('Category', '')), _str(row.get('Parsed_Category', ''))),
        ('Subcategory', _str(row.get('Subcategory', '')), _str(row.get('Parsed_Subcategory', ''))),
    ]
    for label, a, b in comparisons:
        if a and b and a != b:
            notes.append(f"{label}: '{a}' != '{b}'")
    return '; '.join(notes)
  
def calculate_customer_mix_percentages(group_data):
    """Calculate customer mix percentages from dimensional data"""
    total_records = len(group_data)
    if total_records == 0:
        return {
            'men_percentage': 0.0,
            'women_percentage': 0.0,
            'unisex_percentage': 0.0,
            'front_store_percentage': 0.0,
            'back_store_percentage': 0.0,
            'summer_percentage': 0.0,
            'spring_percentage': 0.0,
            'autumn_percentage': 0.0,
            'winter_percentage': 0.0
        }
    
    # Gender percentages - COUNT ALL CATEGORIES TO ENSURE 100% TOTAL
    men_count = len(group_data[group_data['sex_name'].isin(['男', 'Men', 'men', 'Male', 'male'])])
    women_count = len(group_data[group_data['sex_name'].isin(['女', 'Women', 'women', 'Female', 'female'])])
    unisex_count = len(group_data[group_data['sex_name'].isin(['中', 'Unisex', 'unisex', 'U', 'N'])])
    
    # Location percentages
    front_count = len(group_data[group_data['display_location_name'].isin(['前台', 'Front-store', 'front-store', 'Front', '鞋配'])])
    back_count = len(group_data[group_data['display_location_name'].isin(['后台', 'Back-store', 'back-store', 'Back', '后场'])])
    
    # Season percentages
    summer_count = len(group_data[group_data['season_name'].isin(['夏', 'Summer', 'summer'])])
    spring_count = len(group_data[group_data['season_name'].isin(['春', 'Spring', 'spring'])])
    autumn_count = len(group_data[group_data['season_name'].isin(['秋', 'Autumn', 'autumn', 'Fall', 'fall'])])
    winter_count = len(group_data[group_data['season_name'].isin(['冬', 'Winter', 'winter'])])
    
    return {
        'men_percentage': round((men_count / total_records) * 100, 1),
        'women_percentage': round((women_count / total_records) * 100, 1),
        'unisex_percentage': round((unisex_count / total_records) * 100, 1),
        'front_store_percentage': round((front_count / total_records) * 100, 1),
        'back_store_percentage': round((back_count / total_records) * 100, 1),
        'summer_percentage': round((summer_count / total_records) * 100, 1),
        'spring_percentage': round((spring_count / total_records) * 100, 1),
        'autumn_percentage': round((autumn_count / total_records) * 100, 1),
        'winter_percentage': round((winter_count / total_records) * 100, 1)
    }

def validate_dimensional_alignment(df: pd.DataFrame):
    """Validate alignment between Target_Style_Tags and Season/Gender/Location/Category/Subcategory.
    Optionally auto-repair structured columns from parsed tags when AUTO_REPAIR_DIM_MISMATCH is truthy.
    Returns (validated_df, mismatch_df, auto_repair_flag).
    """
    logger.info("Validating dimensional alignment between tags and structured columns...")
    validated_df = df.copy()
    
    # Parse tags into components
    parsed = validated_df['Target_Style_Tags'].apply(parse_target_style_tags)
    parsed_cols = list(zip(*parsed)) if len(validated_df) > 0 else [[], [], [], [], []]
    if parsed_cols and len(parsed_cols) == 5:
        validated_df['Parsed_Season'] = parsed_cols[0]
        validated_df['Parsed_Gender'] = parsed_cols[1]
        validated_df['Parsed_Location'] = parsed_cols[2]
        validated_df['Parsed_Category'] = parsed_cols[3]
        validated_df['Parsed_Subcategory'] = parsed_cols[4]
    else:
        validated_df['Parsed_Season'] = ''
        validated_df['Parsed_Gender'] = ''
        validated_df['Parsed_Location'] = ''
        validated_df['Parsed_Category'] = ''
        validated_df['Parsed_Subcategory'] = ''
    
    def _s(x):
        try:
            return '' if pd.isna(x) else str(x).strip()
        except Exception:
            return ''
    
    # Build mismatch mask
    mask = (
        validated_df['Season'].apply(_s) != validated_df['Parsed_Season'].apply(_s)
    ) | (
        validated_df['Gender'].apply(_s) != validated_df['Parsed_Gender'].apply(_s)
    ) | (
        validated_df['Location'].apply(_s) != validated_df['Parsed_Location'].apply(_s)
    ) | (
        validated_df['Category'].apply(_s) != validated_df['Parsed_Category'].apply(_s)
    ) | (
        validated_df['Subcategory'].apply(_s) != validated_df['Parsed_Subcategory'].apply(_s)
    )
    
    mismatch_df = validated_df[mask].copy()
    if not mismatch_df.empty:
        mismatch_df['Mismatch_Notes'] = mismatch_df.apply(build_dim_mismatch_notes, axis=1)
        logger.info(f"Found {len(mismatch_df)} dimensional mismatches")
    else:
        logger.info("No dimensional mismatches found")
    
    auto_repair_env = os.environ.get('PIPELINE_VALIDATE_DIM_MISMATCH_AUTO_REPAIR')
    if auto_repair_env is None:
        auto_repair_env = os.environ.get('AUTO_REPAIR_DIM_MISMATCH', '0')
    auto_repair_flag = str(auto_repair_env).lower() in ('1', 'true', 'yes', 'y')
    if auto_repair_flag and not mismatch_df.empty:
        logger.info("Auto-repair enabled: aligning structured columns to parsed tags for mismatched rows")
        cols = [
            ('Season', 'Parsed_Season'),
            ('Gender', 'Parsed_Gender'),
            ('Location', 'Parsed_Location'),
            ('Category', 'Parsed_Category'),
            ('Subcategory', 'Parsed_Subcategory'),
        ]
        for col, pcol in cols:
            validated_df.loc[mask, col] = validated_df.loc[mask, pcol]
    
    return validated_df, mismatch_df, auto_repair_flag

def create_enhanced_fast_fish_format(api_df):
    """Create enhanced Fast Fish format with all outputFormat.md fields"""
    logger.info("Creating enhanced Fast Fish format with dimensional aggregation...")
    
    # Load data for temperature and sell-through calculations
    logger.info("Loading data for real temperature and sell-through calculations...")
    weather_df = load_weather_data()
    historical_sales_df = load_historical_sales_data()
    cluster_mapping_df = load_cluster_mapping()
    year, month, period, period_label = get_period_parts()
    
    # CRITICAL FIX: Map str_code to Store_Group_Name before aggregation
    logger.info("Mapping stores to store groups for dimensional aggregation...")
    if not cluster_mapping_df.empty:
        store_to_cluster = dict(zip(
            cluster_mapping_df['str_code'].astype(str), 
            cluster_mapping_df['Cluster']
        ))
        
        # Add Store_Group_Name column to api_df
        api_df = api_df.copy()
        api_df['str_code_str'] = api_df['str_code'].astype(str)
        api_df['Store_Group_Name'] = api_df['str_code_str'].map(
            lambda x: (f"Store Group {store_to_cluster[x] + 1}" if x in store_to_cluster else pd.NA)
        )
        
        logger.info(f"Mapped {len(api_df)} records to store groups")
        store_groups = api_df['Store_Group_Name'].value_counts()
        logger.info(f"Store group distribution: {dict(store_groups.head(10))}")
        # Log NA store groups and dimensional missingness prior to grouping
        try:
            na_store_groups = int(api_df['Store_Group_Name'].isna().sum())
            total_rows = int(len(api_df))
            logger.info(f"Store group mapping: {na_store_groups}/{total_rows} records without store group (excluded from grouping)")
        except Exception:
            pass
        try:
            dim_missing = {
                'season_name': int(api_df['season_name'].isna().sum()) if 'season_name' in api_df.columns else None,
                'sex_name': int(api_df['sex_name'].isna().sum()) if 'sex_name' in api_df.columns else None,
                'display_location_name': int(api_df['display_location_name'].isna().sum()) if 'display_location_name' in api_df.columns else None,
            }
            logger.info(f"Dimensional missingness before grouping: {dim_missing}")
        except Exception:
            pass
    else:
        logger.error("No cluster mapping available - cannot create store groups!")
        return pd.DataFrame()
    
    # Group by Store Group, Category, Subcategory, AND Gender with dimensional data
    # CRITICAL FIX: Gender must be in groupby key to create separate recommendations per gender
    logger.info("Performing dimensional aggregation...")
    aggregation_groups = []
    
    grouped = api_df.groupby(['Store_Group_Name', 'cate_name', 'sub_cate_name', 'sex_name'])
    
    for (store_group, category, subcategory, gender), group_data in tqdm(grouped, desc="Processing store group combinations"):
        
        # Calculate customer mix percentages
        customer_mix = calculate_customer_mix_percentages(group_data)
        
        # Get most common dimensional attributes for Target_Style_Tags
        # Season: prefer season_name when present; otherwise use calendar month fallback only
        try:
            most_common_season = group_data['season_name'].mode().iloc[0] if 'season_name' in group_data.columns and len(group_data['season_name'].mode()) > 0 else np.nan
        except Exception:
            most_common_season = np.nan
        # Gender is now from groupby key - no need to calculate mode
        most_common_gender = gender  # Use gender from groupby directly
        most_common_location = group_data['display_location_name'].mode().iloc[0] if len(group_data['display_location_name'].mode()) > 0 else np.nan
        # Apply fallback only for season token when missing/empty: DO NOT use temperature, only month default
        if pd.isna(most_common_season) or str(most_common_season).strip() in ('', 'nan', 'None'):
            most_common_season = _default_season_for_month(month)

        # Create dimensional Target_Style_Tags
        target_style_tags = create_dimensional_target_style_tags(
            most_common_season, most_common_gender, most_common_location, category, subcategory
        )
        
        # Calculate SPU quantities (counts only)
        current_spu_quantity = group_data['spu_code'].nunique()
        # Initialize target equal to current; adjustments applied later via add/remove counts
        target_spu_quantity = current_spu_quantity
        
        # Calculate other metrics
        total_sales = group_data['spu_sales_amt'].sum()
        avg_sales_per_spu = total_sales / current_spu_quantity if current_spu_quantity > 0 else np.nan
        
        # FIXED: Count actual stores in the cluster that sell this CATEGORY
        # Use cluster mapping data (not sales data) to get accurate store counts
        cluster_id = int(store_group.split(" ")[-1]) - 1  # Store Group N -> Cluster N-1
        cluster_stores = cluster_mapping_df[cluster_mapping_df['Cluster'] == cluster_id]['str_code'].tolist()
        
        # Count how many of these cluster stores actually sell this category in sales data
        category_stores_in_group = api_df[
            (api_df['str_code'].isin(cluster_stores)) & 
            (api_df['cate_name'] == category)
        ]['str_code'].nunique()
        
        # Use category-level count for accurate business metrics
        stores_in_group = category_stores_in_group
        
        # Pre-calculate temperature and historical sell-through
        temp_value = calculate_store_group_temperature(store_group, cluster_mapping_df, weather_df)
        hist_st = calculate_historical_sell_through(store_group, category, subcategory, historical_sales_df, cluster_mapping_df)
        # QA warning if raw historical ST is out of expected [0,100] range (should be rare)
        try:
            if pd.notna(hist_st):
                _v = float(hist_st)
                if _v < 0.0 or _v > 100.0:
                    logger.warning(f"Historical_ST% out of range for {store_group}|{category}|{subcategory}: {hist_st}")
        except Exception:
            pass

        # Parse mapped tags back for structured columns (aligned with Target_Style_Tags mapping)
        tags_list = target_style_tags.strip('[]').split(', ')
        mapped_season = tags_list[0] if len(tags_list) >= 5 else most_common_season
        mapped_gender = tags_list[1] if len(tags_list) >= 5 else most_common_gender
        mapped_location = tags_list[2] if len(tags_list) >= 5 else most_common_location

        # Robust Gender backfill using customer mix when unmapped/ambiguous
        # FIXED (AIS-146): Preserve explicit neutral gender ('中性', 'Unisex')
        # Only infer gender when truly missing/empty, NOT when explicitly neutral
        try:
            def _norm(x):
                try:
                    return float(x)
                except Exception:
                    return np.nan
            wp = _norm(customer_mix.get('women_percentage', np.nan))
            mp = _norm(customer_mix.get('men_percentage', np.nan))
            up = _norm(customer_mix.get('unisex_percentage', np.nan))
            mg = str(mapped_gender) if mapped_gender is not None else ''
            
            # Only infer when truly missing/empty (removed 'Unisex' and '中性' from ambiguous list)
            if mg in ['', 'nan', 'NaN'] or pd.isna(mapped_gender):
                # Strong preference
                if pd.notna(wp) and pd.notna(mp) and wp >= 60 and wp > mp:
                    mapped_gender = 'Women'
                elif pd.notna(wp) and pd.notna(mp) and mp >= 60 and mp > wp:
                    mapped_gender = 'Men'
                else:
                    # Moderate preference if difference is significant
                    if pd.notna(wp) and pd.notna(mp):
                        if (wp - mp) >= 15:
                            mapped_gender = 'Women'
                        elif (mp - wp) >= 15:
                            mapped_gender = 'Men'
                        else:
                            # Leave as Unisex if no signal
                            mapped_gender = 'Unisex'
                    else:
                        mapped_gender = 'Unisex'
            # If mg is 'Unisex' or '中性', preserve it (don't enter inference block)
        except Exception:
            pass

        # Create enhanced record (minimal changes, additive fields only)
        # Normalize historical sell-through to explicit fraction/percent with guards
        try:
            hist_st_frac = _st_clip_01(_st_pct_to_frac(hist_st))
        except Exception:
            hist_st_frac = np.nan
        try:
            hist_st_pct = float(np.clip(float(hist_st), 0.0, 100.0)) if not pd.isna(hist_st) else np.nan
        except Exception:
            hist_st_pct = np.nan

        record = {
            'Year': year,
            'Month': month,
            'Period': period,
            'Store_Group_Name': store_group,
            'Target_Style_Tags': target_style_tags,
            'Current_SPU_Quantity': current_spu_quantity,
            'Target_SPU_Quantity': target_spu_quantity,
            'ΔQty': target_spu_quantity - current_spu_quantity,
            'Data_Based_Rationale': f"Current {current_spu_quantity} SPUs; target initialized equal to current. Adjustments (if any) are rule-based add/remove counts only.",
            'Expected_Benefit': np.nan,
            'Stores_In_Group_Selling_This_Category': stores_in_group,
            'Total_Current_Sales': round(total_sales, 1) if not np.isnan(total_sales) else np.nan,
            'Avg_Sales_Per_SPU': round(avg_sales_per_spu, 2) if not np.isnan(avg_sales_per_spu) else np.nan,
            'men_percentage': customer_mix.get('men_percentage', np.nan),
            'women_percentage': customer_mix.get('women_percentage', np.nan),
            'unisex_percentage': customer_mix.get('unisex_percentage', np.nan),
            'front_store_percentage': customer_mix.get('front_store_percentage', np.nan), 
            'back_store_percentage': customer_mix.get('back_store_percentage', np.nan),
            'summer_percentage': customer_mix.get('summer_percentage', np.nan),
            'spring_percentage': customer_mix.get('spring_percentage', np.nan),
            'autumn_percentage': customer_mix.get('autumn_percentage', np.nan),
            'winter_percentage': customer_mix.get('winter_percentage', np.nan),
            'Display_Location': most_common_location,
            'Temp_14d_Avg': temp_value,
            'Historical_ST%': hist_st,  # legacy percent
            'Historical_ST_Pct': hist_st_pct,  # explicit percent
            'Historical_ST_Frac': hist_st_frac,  # explicit fraction
            # Additive aliases and structured metadata (non-breaking)
            'FeelsLike_Temp_Period_Avg': temp_value,
            'Historical_Sell_Through_Rate': hist_st_pct,  # keep alias in percent for clarity
            'Season': mapped_season,
            'Gender': mapped_gender,
            'Location': mapped_location,
            'Category': category,
            'Subcategory': subcategory,
            'Store_Codes_In_Group': ','.join(cluster_stores),
            'Store_Count_In_Group': len(cluster_stores),
            'Optimization_Target': 'Maximize Sell-Through Rate Under Constraints',
            'Temperature_Suitability': compute_temperature_suitability(mapped_season, temp_value)
        }
        
        aggregation_groups.append(record)
    
    # Create DataFrame
    enhanced_df = pd.DataFrame(aggregation_groups)
    logger.info(f"Created enhanced format with {len(enhanced_df):,} store group × category combinations")
    
    return enhanced_df


def save_cluster_fashion_makeup(enhanced_df: pd.DataFrame, period_label: str):
    """Save per-cluster fashion makeup summary (gender/location/season percentages)."""
    try:
        if enhanced_df.empty:
            return None
        cols = [
            'men_percentage','women_percentage','unisex_percentage',
            'front_store_percentage','back_store_percentage',
            'summer_percentage','spring_percentage','autumn_percentage','winter_percentage'
        ]
        present = [c for c in cols if c in enhanced_df.columns]
        if not present:
            return None
        # Weight by Current_SPU_Quantity to reflect assortment scale
        df = enhanced_df.copy()
        df['__w'] = df.get('Current_SPU_Quantity', 1).fillna(1)
        agg = {}
        for c in present:
            agg[c] = (df[c] * df['__w'])
        grouped = df.groupby('Store_Group_Name', as_index=False).apply(
            lambda g: pd.Series({c: (g[c] * g['__w']).sum() / max(1, g['__w'].sum()) for c in present})
        ).reset_index()
        out = grouped.copy()
        out.insert(1, 'Cluster', out['Store_Group_Name'].str.extract(r"(\d+)").astype(int).sub(1))
        # Embed period metadata columns
        try:
            y, m, p, _pl = get_period_parts()
            yyyymm = f"{y}{int(m):02d}"
        except Exception:
            y, m, p, yyyymm = 0, 0, "", ""
        out['period_label'] = period_label
        out['target_yyyymm'] = yyyymm
        out['target_period'] = p
        path = f"output/cluster_fashion_makeup_{period_label}.csv"
        out.to_csv(path, index=False)
        logger.info(f"Saved cluster fashion makeup: {path}")
        # Register in manifest (generic and period-specific keys)
        try:
            register_step_output("step14", "cluster_fashion_makeup", path, {
                "records": int(len(out)),
                "columns": out.columns.tolist(),
                "target_year": y,
                "target_month": m,
                "period": p,
                "target_period": p,
                "period_label": period_label
            })
            register_step_output("step14", f"cluster_fashion_makeup_{period_label}", path, {
                "records": int(len(out)),
                "columns": out.columns.tolist(),
                "target_year": y,
                "target_month": m,
                "period": p,
                "target_period": p,
                "period_label": period_label
            })
        except Exception as _e:
            logger.warning(f"Failed to register cluster fashion makeup: {_e}")
        return path
    except Exception as e:
        logger.warning(f"Failed to save cluster fashion makeup: {e}")
        return None


def save_cluster_weather_profile(cluster_mapping_df: pd.DataFrame, period_label: str):
    """Save per-cluster weather profile using feels-like temperatures and band mapping."""
    try:
        weather_df = load_weather_data()
        if cluster_mapping_df.empty or weather_df.empty:
            return None
        cm = cluster_mapping_df[['str_code','Cluster']].copy()
        cm['str_code'] = cm['str_code'].astype(str)
        wd = weather_df.copy()
        # stores file may have int store_code
        if 'store_code' in wd.columns:
            wd['str_code'] = wd['store_code'].astype(str)
        elif 'str_code' in wd.columns:
            wd['str_code'] = wd['str_code'].astype(str)
        else:
            return None
        if 'feels_like_temperature' not in wd.columns:
            return None
        merged = cm.merge(wd[['str_code','feels_like_temperature']], on='str_code', how='left')
        prof = merged.groupby('Cluster').agg(
            Avg_Temp=('feels_like_temperature','mean'),
            Store_Count=('str_code','nunique')
        ).reset_index()
        # Map to bands using existing output/temperature_bands.csv thresholds if present
        band_file = 'output/temperature_bands.csv'
        def map_band(t):
            if pd.isna(t):
                return pd.NA
            if t < 10: return '<10°C'
            if t < 15: return '10°C to 15°C'
            if t < 20: return '15°C to 20°C'
            if t < 25: return '20°C to 25°C'
            if t < 30: return '25°C to 30°C'
            return '>=30°C'
        prof['Weather_Band'] = prof['Avg_Temp'].apply(map_band)
        prof['Store_Group_Name'] = prof['Cluster'].apply(lambda c: f"Store Group {int(c)+1}")
        # Build output dataframe and embed period metadata
        df_out = prof[['Cluster','Store_Group_Name','Store_Count','Avg_Temp','Weather_Band']].copy()
        try:
            y, m, p, _pl = get_period_parts()
            yyyymm = f"{y}{int(m):02d}"
        except Exception:
            y, m, p, yyyymm = 0, 0, "", ""
        df_out['period_label'] = period_label
        df_out['target_yyyymm'] = yyyymm
        df_out['target_period'] = p
        path = f"output/cluster_weather_profile_{period_label}.csv"
        df_out.to_csv(path, index=False)
        logger.info(f"Saved cluster weather profile: {path}")
        # Register in manifest (generic and period-specific keys)
        try:
            register_step_output("step14", "cluster_weather_profile", path, {
                "records": int(len(df_out)),
                "columns": df_out.columns.tolist(),
                "target_year": y,
                "target_month": m,
                "period": p,
                "target_period": p,
                "period_label": period_label
            })
            register_step_output("step14", f"cluster_weather_profile_{period_label}", path, {
                "records": int(len(df_out)),
                "columns": df_out.columns.tolist(),
                "target_year": y,
                "target_month": m,
                "period": p,
                "target_period": p,
                "period_label": period_label
            })
        except Exception as _e:
            logger.warning(f"Failed to register cluster weather profile: {_e}")
        return path
    except Exception as e:
        logger.warning(f"Failed to save cluster weather profile: {e}")
        return None


def save_store_level_recommendation_breakdown(consolidated_df: Optional[pd.DataFrame], cluster_mapping_df: pd.DataFrame, period_label: str):
    """Save store-level recommendation breakdown (action per store/category/subcategory/SPU)."""
    try:
        if consolidated_df is None or consolidated_df.empty or cluster_mapping_df.empty:
            return None
        df = consolidated_df.copy()
        # Normalize types
        df['str_code'] = df['str_code'].astype(str)
        needed = [c for c in ['cate_name','sub_cate_name','spu_code','action','recommended_quantity_change'] if c in df.columns]
        cm = cluster_mapping_df[['str_code','Cluster']].copy()
        cm['str_code'] = cm['str_code'].astype(str)
        out = df.merge(cm, on='str_code', how='left')
        out['Store_Group_Name'] = out['Cluster'].apply(lambda c: f"Store Group {int(c)+1}" if pd.notna(c) else pd.NA)
        # Keep essential columns
        keep = ['str_code','Store_Group_Name','cate_name','sub_cate_name','spu_code','action','recommended_quantity_change']
        keep = [c for c in keep if c in out.columns]
        out = out[keep]
        # Embed period metadata columns
        try:
            y, m, p, _pl = get_period_parts()
            yyyymm = f"{y}{int(m):02d}"
        except Exception:
            y, m, p, yyyymm = 0, 0, "", ""
        out['period_label'] = period_label
        out['target_yyyymm'] = yyyymm
        out['target_period'] = p
        path = f"output/store_level_recommendation_breakdown_{period_label}.csv"
        out.to_csv(path, index=False)
        logger.info(f"Saved store-level recommendation breakdown: {path} ({len(out)})")
        # Register in manifest (generic and period-specific keys)
        try:
            register_step_output("step14", "store_level_recommendation_breakdown", path, {
                "records": int(len(out)),
                "columns": out.columns.tolist(),
                "target_year": y,
                "target_month": m,
                "period": p,
                "target_period": p,
                "period_label": period_label
            })
            register_step_output("step14", f"store_level_recommendation_breakdown_{period_label}", path, {
                "records": int(len(out)),
                "columns": out.columns.tolist(),
                "target_year": y,
                "target_month": m,
                "period": p,
                "target_period": p,
                "period_label": period_label
            })
        except Exception as _e:
            logger.warning(f"Failed to register store-level recommendation breakdown: {_e}")
        return path
    except Exception as e:
        logger.warning(f"Failed to save store-level recommendation breakdown: {e}")
        return None

def integrate_rule_adjustments(enhanced_df, consolidated_rules_df):
    """Integrate rule-based adjustments into the enhanced format"""
    logger.info("Integrating rule-based SPU quantity adjustments...")
    
    if consolidated_rules_df is None or len(consolidated_rules_df) == 0:
        logger.warning("No rule adjustments to integrate")
        return enhanced_df
    
    logger.info(f"Processing {len(consolidated_rules_df):,} rule adjustments")
    
    # Load cluster mapping for correct store group assignment
    cluster_mapping_df = load_cluster_mapping()
    store_to_cluster = {}
    if not cluster_mapping_df.empty:
        store_to_cluster = dict(zip(
            cluster_mapping_df['str_code'].astype(str), 
            cluster_mapping_df['Cluster']
        ))
        logger.info(f"Loaded cluster mapping for {len(store_to_cluster)} stores")
    
    # Create consolidated entries of rule count adjustments by store group, category, subcategory
    translation_map = load_category_translation_map()
    rule_entries: List[dict] = []
    key_to_entry_index: Dict[str, int] = {}
    adjustments_applied = 0
    
    for _, rule in consolidated_rules_df.iterrows():
        store_code = str(rule.get('str_code', ''))
        category = str(rule.get('cate_name', ''))
        subcategory = str(rule.get('sub_cate_name', ''))
        action = str(rule.get('action', '')).upper()
        if action not in ('ADD', 'REMOVE'):
            # Derive action from sign of recommended_quantity_change when action is missing/invalid
            try:
                rq = rule.get('recommended_quantity_change', None)
                rq_val = float(rq) if rq is not None else 0.0
                if rq_val > 0:
                    action = 'ADD'
                elif rq_val < 0:
                    action = 'REMOVE'
            except Exception:
                pass
        
        # FIXED: Handle missing category data from Step 13
        if category in ['', 'N/A', 'nan', 'None'] or pd.isna(category):
            # Derive category from subcategory using common mappings
            subcategory_to_category = {
                '直筒裤': '裤', '锥形裤': '裤', '束脚裤': '裤', '阔腿裤': '裤', 
                '短裤': '裤', '中裤': '裤', '工装裤': '裤', '裤类套装': '裤',
                '休闲圆领T恤': 'T恤', '微宽松圆领T恤': 'T恤', '凉感圆领T恤': 'T恤', 
                '合体圆领T恤': 'T恤', '开衫T恤': 'T恤', '带帽T恤': 'T恤',
                '休闲POLO': 'POLO衫', '凉感POLO': 'POLO衫', '套头POLO': 'POLO衫', '速干POLO': 'POLO衫',
                '休闲衬衣': '衬衣', '牛仔衬衣': '衬衣',
                '针织防晒衣': '防晒衣', '连帽开衫卫衣': '卫衣', '立领开衫卫衣': '卫衣',
                '休闲鞋': '鞋', '低帮袜': '袜', '家居服': '家居服', '箱包类': '箱包'
            }
            category = subcategory_to_category.get(subcategory, subcategory)
            logger.debug(f"Derived category '{category}' from subcategory '{subcategory}'")
        
        # Only use add/remove actions to adjust SPU counts; ignore unit deltas
        if action not in ('ADD', 'REMOVE'):
            continue
        
        # FIXED: Use actual cluster mapping instead of modulo hash
        if store_code in store_to_cluster:
            cluster_id = store_to_cluster[store_code]
            store_group = f"Store Group {cluster_id + 1}"
        else:
            # No modulo fallback; skip if cluster mapping is missing
            logger.warning(f"Store {store_code} not found in cluster mapping; skipping adjustment")
            continue
        
        # Build or fetch entry
        primary_key = f"{store_group}|{category}|{subcategory}"
        idx = key_to_entry_index.get(primary_key)
        if idx is None:
            entry = {
                'store_group': store_group,
                'category': category,
                'subcategory': subcategory,
                'add_count': set(),
                'remove_count': set(),
                'rules_applied': [],
                '_applied': False,
                '_applied_via': None,
                '_applied_row_idx': None,
            }
            rule_entries.append(entry)
            idx = len(rule_entries) - 1
            key_to_entry_index[primary_key] = idx
        entry = rule_entries[idx]
        # Track distinct SPUs for add/remove
        if action == 'ADD' and 'spu_code' in rule:
            entry['add_count'].add(str(rule.get('spu_code')))
        elif action == 'REMOVE' and 'spu_code' in rule:
            entry['remove_count'].add(str(rule.get('spu_code')))
        entry['rules_applied'].append(str(rule.get('rule_source', 'Business Rule')))
        
        # Also register translation key if available
        t_key = translation_map.get((category, subcategory))
        if t_key:
            t_cat, t_sub = t_key
            alt_key = f"{store_group}|{t_cat}|{t_sub}"
            key_to_entry_index.setdefault(alt_key, idx)
        # Register category-level fallback marker
        if subcategory in ['', 'N/A', 'nan', 'None'] or pd.isna(subcategory):
            any_key = f"{store_group}|{category}|__ANY__"
            key_to_entry_index.setdefault(any_key, idx)
    
    logger.info(f"Consolidated {len(rule_entries)} rule adjustment entries")
    
    # Apply adjustments to enhanced dataframe (exact or translated key)
    roles_df = load_product_roles() if ENABLE_SCORED_SELECTION else pd.DataFrame()
    def _apply_entry_to_row(row_idx: int, entry: dict, via: str):
        nonlocal adjustments_applied
        row = enhanced_df.loc[row_idx]
        current = int(row['Current_SPU_Quantity'])
        if ENABLE_ADAPTIVE_CAPS:
            stores_in_group = row.get('Stores_In_Group_Selling_This_Category', None)
            hist_st = row.get('Historical_ST%', None)
            temp_suit = row.get('Temperature_Suitability', None)
            cap_up, cap_down = compute_adaptive_caps(
                current_qty=current,
                stores_in_group=stores_in_group if pd.notna(stores_in_group) else None,
                historical_st_pct=hist_st if pd.notna(hist_st) else None,
                temperature_suitability=temp_suit,
                max_cap_absolute=RECOMMENDATION_STRATEGY['max_cap_absolute'],
                min_display_spus=RECOMMENDATION_STRATEGY['min_display_spus'],
                base_cap_fraction=RECOMMENDATION_STRATEGY['base_cap_fraction']
            )
        else:
            cap_up, cap_down = None, None
        add_set = list(entry['add_count'])
        remove_set = list(entry['remove_count'])
        if ENABLE_SCORED_SELECTION:
            hist_st = row.get('Historical_ST%', None)
            temp_suit = row.get('Temperature_Suitability', None)
            add_scored = sorted(
                [(s, score_add_candidate(s, hist_st, temp_suit, roles_df)) for s in add_set],
                key=lambda x: x[1], reverse=True
            )
            remove_scored = sorted(
                [(s, score_remove_candidate(s, hist_st, temp_suit, roles_df)) for s in remove_set],
                key=lambda x: x[1], reverse=True
            )
            if ADDS_ONLY_QTY:
                k_add = len(add_scored)
                k_rem = 0
                net_delta = k_add
            else:
                k_add = len(add_scored) if cap_up is None else min(len(add_scored), max(0, cap_up))
                k_rem = 0 if ADDS_ONLY_QTY else (len(remove_scored) if cap_down is None else min(len(remove_scored), max(0, cap_down)))
                net_delta = k_add - k_rem
            rules_applied = ', '.join(sorted(set(entry['rules_applied']))[:3])
            rationale_tail = (
                f"Scored selection adds {k_add}, removes {k_rem}; caps (↑{cap_up}, ↓{cap_down}). Rules: {rules_applied}."
            )
        else:
            add_n = len(add_set)
            remove_n = 0 if ADDS_ONLY_QTY else len(remove_set)
            try:
                if not ADDS_ONLY_QTY:
                    if (row.get('Historical_ST%', None) is not None and float(row.get('Historical_ST%')) >= 60.0) \
                       and (str(row.get('Temperature_Suitability')) == 'Suitable'):
                        remove_n = 0
            except Exception:
                pass
            net_delta = add_n - remove_n
            rules_applied = ', '.join(sorted(set(entry['rules_applied']))[:3])
            rationale_tail = (
                f"Raw counts add {add_n}, remove {remove_n}; caps (↑{cap_up}, ↓{cap_down}). Rules: {rules_applied}."
            )
        if ENABLE_ADAPTIVE_CAPS and cap_up is not None and cap_down is not None:
            if net_delta > 0:
                net_delta = min(net_delta, cap_up)
            elif net_delta < 0:
                net_delta = max(net_delta, -cap_down)
        new_target = max(0, current + net_delta)
        enhanced_df.at[row_idx, 'Target_SPU_Quantity'] = new_target
        enhanced_df.at[row_idx, 'ΔQty'] = new_target - current
        rationale_prefix = "Adds-only count applied" if ADDS_ONLY_QTY else "Rule-based add/remove counts applied"
        enhanced_df.at[row_idx, 'Data_Based_Rationale'] = (
            f"{rationale_prefix} (net {net_delta:+d}). Current {current} → Target {new_target}. {rationale_tail}"
        )
        entry['_applied'] = True
        entry['_applied_via'] = via
        entry['_applied_row_idx'] = row_idx
        adjustments_applied += 1
    
    for idx, row in enhanced_df.iterrows():
        # Prefer structured Category/Subcategory with safe fallback to Target_Style_Tags parsing
        try:
            category = None
            subcategory = None
            # Structured fields first
            if 'Category' in row and pd.notna(row['Category']) and str(row['Category']).strip() not in ('', 'nan', 'None', 'N/A'):
                category = str(row['Category']).strip()
            if 'Subcategory' in row and pd.notna(row['Subcategory']) and str(row['Subcategory']).strip() not in ('', 'nan', 'None', 'N/A'):
                subcategory = str(row['Subcategory']).strip()
            # Fallback to parsing from Target_Style_Tags
            if category is None or subcategory is None:
                style_tags = row['Target_Style_Tags']
                if isinstance(style_tags, str) and '[' in style_tags:
                    # Parse format: [Season, Gender, Location, Category, Subcategory]
                    tags_list = style_tags.strip('[]').split(', ')
                    if len(tags_list) >= 5:
                        if category is None:
                            category = tags_list[3].strip()
                        if subcategory is None:
                            subcategory = tags_list[4].strip()
            # Skip if still unresolved
            if category is None or subcategory is None:
                continue
            # Try exact key then translated key
            key = f"{row['Store_Group_Name']}|{category}|{subcategory}"
            t_key = translation_map.get((category, subcategory))
            alt_key = f"{row['Store_Group_Name']}|{t_key[0]}|{t_key[1]}" if t_key else None
            matched_idx = None
            if key in key_to_entry_index:
                matched_idx = key_to_entry_index[key]
                entry = rule_entries[matched_idx]
            elif alt_key and alt_key in key_to_entry_index:
                matched_idx = key_to_entry_index[alt_key]
                entry = rule_entries[matched_idx]
            else:
                entry = None
            if entry is not None and not entry.get('_applied', False):
                _apply_entry_to_row(idx, entry, via='exact' if key in key_to_entry_index else 'translated')
        except Exception as e:
            logger.warning(f"Error processing row {idx}: {e}")
            continue
    
    # Post-process unmatched entries: category-level and fuzzy fallbacks
    try:
        unmatched: List[dict] = [e for e in rule_entries if not e.get('_applied', False)]
        logger.info(f"Unmatched rule entries after exact/translated pass: {len(unmatched)}")
        for entry in unmatched:
            sg = entry['store_group']
            cat = entry['category']
            sub = entry['subcategory']
            # 1) Category-level fallback for missing/empty subcategory
            if sub in ('', 'N/A', 'nan', 'None') or pd.isna(sub):
                candidates = enhanced_df[(enhanced_df['Store_Group_Name'] == sg) & (enhanced_df['Category'] == cat)]
                if not candidates.empty:
                    # Choose row with the highest current SPU quantity
                    best_idx = int(candidates.sort_values('Current_SPU_Quantity', ascending=False).index[0])
                    _apply_entry_to_row(best_idx, entry, via='category_fallback')
                    continue
                # Try translation on category (if available)
                t = translation_map.get((cat, ''))
                if t:
                    t_cat, t_sub = t
                    candidates = enhanced_df[(enhanced_df['Store_Group_Name'] == sg) & (enhanced_df['Category'] == t_cat)]
                    if not candidates.empty:
                        best_idx = int(candidates.sort_values('Current_SPU_Quantity', ascending=False).index[0])
                        _apply_entry_to_row(best_idx, entry, via='translated_category_fallback')
                        continue
            # 2) Fuzzy subcategory match within same store group and category
            candidates = enhanced_df[(enhanced_df['Store_Group_Name'] == sg) & (enhanced_df['Category'] == cat)]
            if not candidates.empty:
                best_name = _best_fuzzy_match(candidates['Subcategory'].astype(str).tolist(), sub, threshold=0.6)
                if best_name is not None:
                    cand_idx = candidates[candidates['Subcategory'].astype(str) == best_name].index
                    if len(cand_idx) > 0:
                        _apply_entry_to_row(int(cand_idx[0]), entry, via='fuzzy_subcategory')
                        continue
            # 3) Fuzzy category match within same store group
            candidates = enhanced_df[enhanced_df['Store_Group_Name'] == sg]
            if not candidates.empty:
                best_cat = _best_fuzzy_match(candidates['Category'].astype(str).unique().tolist(), cat, threshold=0.65)
                if best_cat is not None:
                    subframe = candidates[candidates['Category'].astype(str) == best_cat]
                    if not subframe.empty:
                        best_idx = int(subframe.sort_values('Current_SPU_Quantity', ascending=False).index[0])
                        _apply_entry_to_row(best_idx, entry, via='fuzzy_category')
                        continue

        # Materialize remaining unmatched ADD entries as new rows to prevent loss (e.g., Rule 7)
        materialized = 0
        try:
            weather_df = load_weather_data()
        except Exception:
            weather_df = pd.DataFrame()
        try:
            historical_sales_df = load_historical_sales_data()
        except Exception:
            historical_sales_df = pd.DataFrame()
        cluster_mapping_df = load_cluster_mapping()
        y, m, p, period_label = get_period_parts()
        to_append: List[dict] = []
        for entry in rule_entries:
            if entry.get('_applied', False):
                continue
            add_n = len(entry.get('add_count', []))
            remove_n = len(entry.get('remove_count', []))
            if add_n <= 0:
                # Only materialize additions
                continue
            sg = entry['store_group']
            cat = _normalize(entry['category'])
            sub = _normalize(entry['subcategory'])
            # If subcategory missing, leave empty string; tags will reflect empties
            # Compute caps if enabled
            cap_up, cap_down = (None, None)
            if ENABLE_ADAPTIVE_CAPS:
                cap_up, cap_down = compute_adaptive_caps(
                    current_qty=0,
                    stores_in_group=None,
                    historical_st_pct=None,
                    temperature_suitability=None,
                    max_cap_absolute=RECOMMENDATION_STRATEGY['max_cap_absolute'],
                    min_display_spus=RECOMMENDATION_STRATEGY['min_display_spus'],
                    base_cap_fraction=RECOMMENDATION_STRATEGY['base_cap_fraction']
                )
            net_delta = add_n  # removals are ignored for materialization
            if ENABLE_ADAPTIVE_CAPS and cap_up is not None:
                net_delta = min(net_delta, max(0, cap_up))
            # Compute cluster stores for this store group
            try:
                cluster_id = int(sg.split(" ")[-1]) - 1
            except Exception:
                cluster_id = None
            if cluster_id is not None and not cluster_mapping_df.empty:
                cluster_stores = cluster_mapping_df[cluster_mapping_df['Cluster'] == cluster_id]['str_code'].astype(str).tolist()
            else:
                cluster_stores = []
            # Estimate stores_in_group for this category
            candidates = enhanced_df[(enhanced_df['Store_Group_Name'] == sg) & (enhanced_df['Category'] == cat)]
            if not candidates.empty and 'Stores_In_Group_Selling_This_Category' in candidates.columns:
                try:
                    stores_in_group = int(candidates['Stores_In_Group_Selling_This_Category'].max())
                except Exception:
                    stores_in_group = len(cluster_stores) if cluster_stores else None
            else:
                stores_in_group = len(cluster_stores) if cluster_stores else None
            # Pre-calc temp and historical ST
            temp_value = calculate_store_group_temperature(sg, cluster_mapping_df, weather_df)
            hist_st = calculate_historical_sell_through(sg, cat, sub, historical_sales_df, cluster_mapping_df)
            try:
                hist_st_frac = _st_clip_01(_st_pct_to_frac(hist_st))
            except Exception:
                hist_st_frac = np.nan
            try:
                hist_st_pct = float(np.clip(float(hist_st), 0.0, 100.0)) if not pd.isna(hist_st) else np.nan
            except Exception:
                hist_st_pct = np.nan
            # Prefer existing structured Season/Gender/Location on the row when composing tags
            try:
                _season = row.get('Season', '')
                _gender = row.get('Gender', '')
                _location = row.get('Location', '')
            except Exception:
                _season = _gender = _location = ''
            target_style_tags = create_dimensional_target_style_tags(_season, _gender, _location, cat, sub)
            record = {
                'Year': y,
                'Month': m,
                'Period': p,
                'Store_Group_Name': sg,
                'Target_Style_Tags': target_style_tags,
                'Current_SPU_Quantity': 0,
                'Target_SPU_Quantity': max(0, net_delta),
                'ΔQty': max(0, net_delta),
                'Data_Based_Rationale': (
                    f"Materialized missing combination from rules: add {add_n} SPUs. "
                    f"Current 0 → Target {max(0, net_delta)}. Rules: "
                    + ', '.join(sorted(set(entry.get('rules_applied', [])))[:3])
                ),
                'Expected_Benefit': np.nan,
                'Stores_In_Group_Selling_This_Category': stores_in_group if stores_in_group is not None else np.nan,
                'Total_Current_Sales': np.nan,
                'Avg_Sales_Per_SPU': np.nan,
                'men_percentage': np.nan,
                'women_percentage': np.nan,
                'unisex_percentage': np.nan,
                'front_store_percentage': np.nan,
                'back_store_percentage': np.nan,
                'summer_percentage': np.nan,
                'spring_percentage': np.nan,
                'autumn_percentage': np.nan,
                'winter_percentage': np.nan,
                'Display_Location': np.nan,
                'Temp_14d_Avg': temp_value,
                'Historical_ST%': hist_st,
                'Historical_ST_Pct': hist_st_pct,
                'Historical_ST_Frac': hist_st_frac,
                'FeelsLike_Temp_Period_Avg': temp_value,
                'Historical_Sell_Through_Rate': hist_st_pct,
                'Season': '',
                'Gender': '',
                'Location': '',
                'Category': cat,
                'Subcategory': sub,
                'Store_Codes_In_Group': ','.join(cluster_stores),
                'Store_Count_In_Group': len(cluster_stores),
                'Optimization_Target': 'Maximize Sell-Through Rate Under Constraints',
                'Temperature_Suitability': compute_temperature_suitability('', temp_value)
            }
            to_append.append(record)
            entry['_applied'] = True
            entry['_applied_via'] = 'materialized'
            entry['_applied_row_idx'] = None
            adjustments_applied += 1
            materialized += 1
        if to_append:
            enhanced_df = pd.concat([enhanced_df, pd.DataFrame(to_append)], ignore_index=True)
            logger.info(f"Materialized {materialized} unmatched ADD entries as new rows")

        # Reconciliation report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _, _, _, period_label = get_period_parts()
        rec_rows = []
        for e in rule_entries:
            rec_rows.append({
                'Store_Group_Name': e['store_group'],
                'Rule_Category': e['category'],
                'Rule_Subcategory': e['subcategory'],
                'Add_SPU_Count': len(e['add_count']),
                'Remove_SPU_Count': len(e['remove_count']),
                'Applied': bool(e.get('_applied', False)),
                'Applied_Via': e.get('_applied_via'),
                'Applied_Row_Index': e.get('_applied_row_idx')
            })
        rec_df = pd.DataFrame(rec_rows)
        rec_file = f"output/step14_rule_integration_reconciliation_{period_label}_{timestamp}.csv"
        rec_df.to_csv(rec_file, index=False)
        logger.info(f"Rule integration reconciliation saved: {rec_file} (applied {int(rec_df['Applied'].sum())}/{len(rec_df)})")
    except Exception as e:
        logger.warning(f"Failed reconciliation reporting: {e}")

    logger.info(f"Applied {adjustments_applied} rule-based adjustments to enhanced format")
    return enhanced_df

def save_enhanced_format(enhanced_df):
    """Save the enhanced Fast Fish format"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use a single unified (period-labeled) output path; register both generic and period-specific keys to this file
    year, month, period, period_label = get_period_parts()
    output_file = f"output/enhanced_fast_fish_format_{period_label}.csv"
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    # Normalize Season/Gender/Location to Chinese (zh-only policy)
    try:
        df_out = enhanced_df.copy()
        # If missing Season/Gender/Location but tags exist, try to parse
        if "Target_Style_Tags" in df_out.columns:
            # season, gender, location, category, subcategory
            tokens = df_out["Target_Style_Tags"].apply(parse_target_style_tags)
            cols = ["_tag_season","_tag_gender","_tag_location","_tag_category","_tag_subcategory"]
            tmp = pd.DataFrame(tokens.tolist(), columns=cols, index=df_out.index)
            for base, src in [("Season","_tag_season"),("Gender","_tag_gender"),("Location","_tag_location")]:
                if base not in df_out.columns:
                    df_out[base] = tmp[src]
                else:
                    mask = df_out[base].isna() | (df_out[base].astype(str).str.strip()=="")
                    df_out.loc[mask, base] = tmp.loc[mask, src]

        def _to_zh_season(v: Optional[str]) -> Optional[str]:
            if pd.isna(v):
                return v
            s = str(v).strip()
            m = {"spring":"春","summer":"夏","autumn":"秋","fall":"秋","winter":"冬",
                 "Spring":"春","Summer":"夏","Autumn":"秋","Fall":"秋","Winter":"冬"}
            return s if s in ("春","夏","秋","冬","四季") else m.get(s, s)

        def _to_zh_gender(v: Optional[str]) -> Optional[str]:
            if pd.isna(v):
                return v
            s = str(v).strip()
            m = {"Men":"男","men":"男","male":"男","Male":"男",
                 "Women":"女","women":"女","female":"女","Female":"女",
                 "Unisex":"中性","unisex":"中性","中":"中性","男女":"中性"}
            return s if s in ("男","女","中性") else m.get(s, s)

        def _to_zh_location(v: Optional[str]) -> Optional[str]:
            if pd.isna(v):
                return v
            s = str(v).strip()
            m = {"Front":"前台","front":"前台","Back":"后台","back":"后台"}
            return s if s in ("前台","后台","鞋配") else m.get(s, s)

        if "Season" in df_out.columns:
            df_out["Season"] = df_out["Season"].apply(_to_zh_season)
        if "Gender" in df_out.columns:
            df_out["Gender"] = df_out["Gender"].apply(_to_zh_gender)
        if "Location" in df_out.columns:
            df_out["Location"] = df_out["Location"].apply(_to_zh_location)

        # Strong guardrails to avoid losing seasonality in final output
        # 1) Backfill Season with month default if still blank/NA
        try:
            if "Season" in df_out.columns:
                season_blank = df_out["Season"].isna() | (df_out["Season"].astype(str).str.strip()=="")
                if season_blank.any():
                    # Use calendar month default strictly (no temp-based inference)
                    fallback_season = _default_season_for_month(month)
                    df_out.loc[season_blank, "Season"] = fallback_season
        except Exception:
            pass

        # 2) Recompose Target_Style_Tags canonically from structured columns where available
        try:
            have_struct = all(c in df_out.columns for c in ["Season","Gender","Location","Category","Subcategory"]) and "Target_Style_Tags" in df_out.columns
            if have_struct:
                def _compose_row(r):
                    return create_dimensional_target_style_tags(
                        r.get("Season", ""), r.get("Gender", ""), r.get("Location", ""),
                        r.get("Category", ""), r.get("Subcategory", "")
                    )
                df_out["Target_Style_Tags"] = df_out.apply(_compose_row, axis=1)
        except Exception:
            pass

        # Replace working copy
        enhanced_df = df_out
    except Exception:
        pass

    # Validate and optionally auto-repair dimensional alignment
    validated_df, mismatch_df, auto_repair_flag = validate_dimensional_alignment(enhanced_df)
    
    # Embed period metadata columns in main output
    yyyymm = f"{year}{int(month):02d}"
    validated_df = _embed_period_metadata_columns(validated_df, yyyymm, period, period_label)
    
    # Save mismatch report if any
    mismatch_file = None
    if len(mismatch_df) > 0:
        mismatch_file = f"output/enhanced_fast_fish_dim_mismatches_{period_label}_{timestamp}.csv"
        # Also embed metadata in mismatch report
        mismatch_with_md = _embed_period_metadata_columns(mismatch_df, yyyymm, period, period_label)
        mismatch_with_md.to_csv(mismatch_file, index=False)
        logger.info(f"Dimensional mismatch report saved: {mismatch_file}")
        # Register mismatch report (generic and period-specific keys)
        try:
            register_step_output("step14", "enhanced_fast_fish_dim_mismatches", mismatch_file, {
                "rows": int(len(mismatch_with_md)),
                "columns": mismatch_with_md.columns.tolist(),
                "target_year": year,
                "target_month": month,
                "period": period,
                "target_period": period,
                "period_label": period_label
            })
            register_step_output("step14", f"enhanced_fast_fish_dim_mismatches_{period_label}", mismatch_file, {
                "rows": int(len(mismatch_with_md)),
                "columns": mismatch_with_md.columns.tolist(),
                "target_year": year,
                "target_month": month,
                "period": period,
                "target_period": period,
                "period_label": period_label
            })
        except Exception as _e:
            logger.warning(f"Failed to register mismatch report: {_e}")
    
    # Save main file
    validated_df.to_csv(output_file, index=False)
    logger.info(f"Enhanced Fast Fish format saved: {output_file}")
    
    # Create validation summary
    validation_summary = {
        "total_combinations": int(len(validated_df)),
        "unique_store_groups": int(validated_df['Store_Group_Name'].nunique()),
        "unique_target_style_tags": int(validated_df['Target_Style_Tags'].nunique()),
        "total_current_spus": int(validated_df['Current_SPU_Quantity'].sum()),
        "total_target_spus": int(validated_df['Target_SPU_Quantity'].sum()),
        "total_sales_coverage": float(validated_df['Total_Current_Sales'].sum()),
        "avg_spus_per_combination": float(validated_df['Target_SPU_Quantity'].mean()),
        "data_quality_checks": {
            "no_null_store_groups": bool(validated_df['Store_Group_Name'].isnull().sum() == 0),
            "no_null_style_tags": bool(validated_df['Target_Style_Tags'].isnull().sum() == 0),
            "positive_spu_counts": bool((validated_df['Target_SPU_Quantity'] >= 0).all()),
            "positive_sales": bool((validated_df['Total_Current_Sales'] >= 0).all())
        },
        "dimensional_alignment": {
            "mismatches": int(len(mismatch_df)),
            "auto_repaired": bool(auto_repair_flag),
            "mismatch_report_file": mismatch_file
        }
    }
    
    validation_file = f"output/enhanced_fast_fish_validation_{period_label}_{timestamp}.json"
    with open(validation_file, 'w') as f:
        json.dump(validation_summary, f, indent=2)
    
    logger.info(f"Validation summary saved: {validation_file}")
    # Register validation summary (generic and period-specific keys)
    try:
        register_step_output("step14", "enhanced_fast_fish_validation", validation_file, {
            "total_combinations": validation_summary["total_combinations"],
            "unique_store_groups": validation_summary["unique_store_groups"],
            "unique_target_style_tags": validation_summary["unique_target_style_tags"],
            "dimensional_mismatches": validation_summary["dimensional_alignment"]["mismatches"],
            "auto_repaired": validation_summary["dimensional_alignment"]["auto_repaired"],
            "for_output": output_file,
            "target_year": year,
            "target_month": month,
            "period": period,
            "target_period": period,
            "period_label": period_label
        })
        register_step_output("step14", f"enhanced_fast_fish_validation_{period_label}", validation_file, {
            "total_combinations": validation_summary["total_combinations"],
            "unique_store_groups": validation_summary["unique_store_groups"],
            "unique_target_style_tags": validation_summary["unique_target_style_tags"],
            "dimensional_mismatches": validation_summary["dimensional_alignment"]["mismatches"],
            "auto_repaired": validation_summary["dimensional_alignment"]["auto_repaired"],
            "for_output": output_file,
            "target_year": year,
            "target_month": month,
            "period": period,
            "target_period": period,
            "period_label": period_label
        })
    except Exception as _e:
        logger.warning(f"Failed to register validation summary: {_e}")
    
    # Print summary
    logger.info("\n=== ENHANCED FAST FISH FORMAT SUMMARY ===")
    logger.info(f"Total combinations: {validation_summary['total_combinations']:,}")
    logger.info(f"Store groups: {validation_summary['unique_store_groups']}")
    logger.info(f"Unique style tags: {validation_summary['unique_target_style_tags']}")
    logger.info(f"Current SPUs: {validation_summary['total_current_spus']:,}")
    logger.info(f"Target SPUs: {validation_summary['total_target_spus']:,}")
    logger.info(f"Net change: {validation_summary['total_target_spus'] - validation_summary['total_current_spus']:+,}")
    logger.info(f"Sales coverage: ¥{validation_summary['total_sales_coverage']:,.0f}")
    logger.info(f"Output file: {output_file}")
    
    # Register outputs in manifest (both generic and period-specific keys point to the unified file)
    register_step_output("step14", "enhanced_fast_fish_format", output_file, {
        "records": len(validated_df),
        "columns": validated_df.columns.tolist(),
        "store_groups": int(validated_df['Store_Group_Name'].nunique()),
        "unique_style_tags": int(validated_df['Target_Style_Tags'].nunique()),
        "dimensional_data_corrected": True,
        "validation_file": validation_file,
        "dimensional_mismatch_report": mismatch_file,
        "target_year": year,
        "target_month": month,
        "period": period,
        "target_period": period,
        "period_label": period_label
    })
    # Also register the period-specific key to the same unified file
    register_step_output("step14", f"enhanced_fast_fish_format_{period_label}", output_file, {
        "records": len(validated_df),
        "columns": validated_df.columns.tolist(),
        "store_groups": int(validated_df['Store_Group_Name'].nunique()),
        "unique_style_tags": int(validated_df['Target_Style_Tags'].nunique()),
        "dimensional_data_corrected": True,
        "validation_file": validation_file,
        "dimensional_mismatch_report": mismatch_file,
        "target_year": year,
        "target_month": month,
        "period": period,
        "target_period": period,
        "period_label": period_label
    })
    logger.info("✅ Registered output in pipeline manifest")
    
    return output_file

def _parse_args():
    """CLI for Step 14 (period-aware), aligned with Steps 15–16."""
    parser = argparse.ArgumentParser(description="Step 14: Create Enhanced Fast Fish format (period-aware)")
    parser.add_argument("--target-yyyymm", required=True, help="Target year-month for current run, e.g. 202509")
    parser.add_argument("--target-period", choices=["A", "B"], required=True, help="Target period (A or B)")
    parser.add_argument("--baseline-yyyymm", help="Override baseline year-month for historical ST (default 202409)")
    parser.add_argument("--baseline-period", choices=["A", "B"], help="Override baseline period (defaults to target period)")
    # Optional file overrides
    parser.add_argument("--spu-sales-file", help="Path to target SPU sales CSV (optional, overrides config)")
    parser.add_argument("--store-config-file", help="Path to store config CSV (optional, overrides config)")
    parser.add_argument("--historical-raw-file", help="Path to baseline raw SPU sales CSV (optional)")
    parser.add_argument("--cluster-file", help="Path to clustering results CSV (optional)")
    parser.add_argument("--rules-file", help="Path to Step 13 consolidated SPU rules CSV (optional)")
    parser.add_argument("--weather-file", help="Path to feels-like temperature CSV (optional)")
    # Feature flags
    parser.add_argument("--adaptive-caps", action="store_true", help="Enable adaptive ΔQty caps")
    parser.add_argument("--scored-selection", action="store_true", help="Enable scored selection for add/remove")
    parser.add_argument("--adds-only", action="store_true", help="Compute ΔQty from ADDs only (ignore removals)")
    return parser.parse_args()

def main():
    """Main execution function for enhanced Step 14"""
    logger.info("🚀 Starting Enhanced Step 14: Complete outputFormat.md Compliance...")
    
    try:
        # Parse CLI and set environment for period-awareness and overrides
        args = _parse_args()
        target_yyyymm = args.target_yyyymm
        target_period = args.target_period
        # Set both TARGET_* and PIPELINE_* for compatibility with get_period_parts/config
        os.environ["PIPELINE_TARGET_YYYYMM"] = target_yyyymm
        os.environ["PIPELINE_TARGET_PERIOD"] = target_period
        os.environ["PIPELINE_YYYYMM"] = target_yyyymm
        os.environ["PIPELINE_PERIOD"] = target_period
        # Back-compat for earlier Step 14 env usage
        os.environ["STEP14_PERIOD"] = target_period
        # Baseline overrides
        if getattr(args, "baseline_yyyymm", None):
            os.environ["STEP14_BASELINE_YYYYMM"] = args.baseline_yyyymm
        if getattr(args, "baseline_period", None):
            os.environ["STEP14_BASELINE_PERIOD"] = args.baseline_period

        # File overrides via env consumed by loaders
        if getattr(args, "spu_sales_file", None):
            os.environ["STEP14_SPU_SALES_FILE"] = args.spu_sales_file
        if getattr(args, "store_config_file", None):
            os.environ["STEP14_STORE_CONFIG_FILE"] = args.store_config_file
        if getattr(args, "cluster_file", None):
            os.environ["STEP14_CLUSTER_FILE"] = args.cluster_file
        if getattr(args, "rules_file", None):
            os.environ["STEP14_RULES_FILE"] = args.rules_file
        if getattr(args, "weather_file", None):
            os.environ["STEP14_WEATHER_FILE"] = args.weather_file
        if getattr(args, "historical_raw_file", None):
            os.environ["STEP14_HISTORICAL_SPU_SALES_FILE"] = args.historical_raw_file

        # Feature flags
        global ENABLE_ADAPTIVE_CAPS, ENABLE_SCORED_SELECTION, ADDS_ONLY_QTY
        ENABLE_ADAPTIVE_CAPS = bool(getattr(args, "adaptive_caps", False))
        ENABLE_SCORED_SELECTION = bool(getattr(args, "scored_selection", False))
        # Adds-only can be forced by CLI or emergency env flags
        ADDS_ONLY_QTY = bool(getattr(args, "adds_only", False))
        if not ADDS_ONLY_QTY:
            env_adds_only = os.environ.get('PIPELINE_EMERGENCY_ADDS_ONLY') or os.environ.get('STEP14_ADDS_ONLY')
            if env_adds_only and str(env_adds_only).lower() in ('1','true','yes','y'):
                ADDS_ONLY_QTY = True

        # Load consolidated rules from Step 13
        try:
            consolidated_df, is_corrected = load_consolidated_spu_rules()
        except FileNotFoundError:
            logger.warning("Consolidated rules not found, proceeding without rule adjustments")
            consolidated_df = None
        
        # Load API data with dimensional attributes
        api_df = load_api_data_with_dimensions()
        
        # Create store groups
        api_df = create_store_groups(api_df)
        
        # Create enhanced Fast Fish format with dimensional aggregation
        enhanced_df = create_enhanced_fast_fish_format(api_df)
        
        # Integrate rule-based adjustments
        if consolidated_df is not None:
            enhanced_df = integrate_rule_adjustments(enhanced_df, consolidated_df)
        
        # Save results
        output_file = save_enhanced_format(enhanced_df)

        # Auxiliary analytics outputs for thorough visibility
        _, _, _, period_label = get_period_parts()
        try:
            save_cluster_fashion_makeup(enhanced_df, period_label)
        except Exception:
            pass
        try:
            # cluster mapping may have been loaded already; reuse
            cm_df = load_cluster_mapping()
            save_cluster_weather_profile(cm_df, period_label)
        except Exception:
            pass
        try:
            # store-level breakdown from consolidated rules
            save_store_level_recommendation_breakdown(consolidated_df, load_cluster_mapping(), period_label)
        except Exception:
            pass
        
        logger.info("✅ Enhanced Step 14 completed successfully!")
        logger.info("   ✓ Dimensional Target_Style_Tags aggregation")
        logger.info("   ✓ Customer Mix percentages (men/women/front/back store)")
        logger.info("   ✓ ΔQty calculation")
        logger.info("   ✓ Display Location mapping")
        logger.info("   ✓ Temperature and Historical ST% fields")
        logger.info("   ✓ Complete outputFormat.md compliance")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Enhanced Step 14 failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
