#!/usr/bin/env python3
"""
Step 36: Unified Delivery Builder

Creates one concise, business-ready file per period at store × recommendation grain by
joining group-level recommendations, store-level allocation, and store meta/classifications.

Inputs (resolved via manifest with period-aware fallbacks):
- Step 32: store_level_allocation_results_{period_label}_*.csv
- Step 18: fast_fish_with_sell_through_analysis_{period_label}_*.csv (sell-through enriched)
           or manifest key sell_through_analysis_{period_label}
- Step 14: enhanced_fast_fish_format_{period_label}.csv (fallback if Step 18 not found)
- Step 33: store_level_plugin_output_{period_label}_*.csv (store meta, constraints)
- Step 24: comprehensive_cluster_labels_{period_label}.csv (optional for tags)
- Step 27/29: gap analysis summary (optional minimal fields if present)

Outputs:
- output/unified_delivery_{period_label}_{timestamp}.csv
- output/unified_delivery_{period_label}_{timestamp}.xlsx (if openpyxl available)
- output/unified_delivery_validation_{period_label}_{timestamp}.json (QA report)

Manifest registrations:
- step36: unified_delivery_csv(_{period_label}), unified_delivery_xlsx(_{period_label}),
          unified_delivery_validation(_{period_label}), unified_delivery_data_dictionary(_{period_label})
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
import re
import numpy as np
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    from src.pipeline_manifest import get_manifest, register_step_output
    from src.output_utils import create_output_with_symlinks
    from src.config import get_period_label, get_api_data_files
except Exception:
    from pipeline_manifest import get_manifest, register_step_output
    from output_utils import create_output_with_symlinks
    from config import get_period_label, get_api_data_files


def log(message: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {message}")


def _latest_from_manifest(step: str, key_prefix: str, period_label: str) -> Optional[str]:
    man = get_manifest()
    try:
        return man.get_latest_output(step, key_prefix=key_prefix, period_label=period_label)
    except Exception:
        # Graceful fallback
        return None


def _resolve_step35_recs_path(period_label: str) -> Optional[str]:
    """Resolve latest Step 35 store-level merchandising recommendations for the period."""
    try:
        man = get_manifest()
        path = _latest_from_manifest("step35", "store_level_merchandising_recommendations", period_label)
        if path and os.path.exists(path):
            return path
    except Exception:
        pass
    # Fallback to glob by timestamp
    import glob
    candidates = sorted(glob.glob(f"output/store_level_merchandising_recommendations_{period_label}_*.csv"))
    if candidates:
        return candidates[-1]
    return None

def _resolve_step18_path(yyyymm: str, period: str, period_label: str) -> Optional[str]:
    # Test/fixture override
    ov = os.environ.get("STEP36_OVERRIDE_STEP18")
    if ov and os.path.exists(ov):
        print(f"[Step36] Using Step18 (override): {ov}")
        return ov
    # Prefer manifest registration
    path = _latest_from_manifest("step18", "sell_through_analysis", period_label)
    if path and os.path.exists(path):
        print(f"[Step36] Using Step18 (manifest): {path}")
        return path
    # Fallback to known pattern(s)
    candidates = [
        f"output/fast_fish_with_sell_through_analysis_{period_label}.csv",
    ]
    for p in candidates:
        if os.path.exists(p):
            print(f"[Step36] Using Step18 (fallback): {p}")
            return p
    return None


def _resolve_step14_path(yyyymm: str, period: str, period_label: str) -> Optional[str]:
    path = _latest_from_manifest("step14", "enhanced_fast_fish_format", period_label)
    if path and os.path.exists(path):
        return path
    p = f"output/enhanced_fast_fish_format_{period_label}.csv"
    return p if os.path.exists(p) else None


def _resolve_step32_allocation_path(period_label: str) -> str:
    # Test/fixture override
    ov = os.environ.get("STEP36_OVERRIDE_ALLOC")
    if ov and os.path.exists(ov):
        print(f"[Step36] Using Allocation (override): {ov}")
        return ov
    # Take the latest allocation result for period
    path = _latest_from_manifest("step32", "store_level_allocation_results", period_label)
    if path and os.path.exists(path):
        print(f"[Step36] Using Allocation (manifest): {path}")
        return path
    # Conservative fallback to most recent file by mtime pattern
    import glob
    candidates = sorted(glob.glob(f"output/store_level_allocation_results_{period_label}_*.csv"))
    if candidates:
        sel = candidates[-1]
        print(f"[Step36] Using Allocation (latest by glob): {sel}")
        return sel
    raise FileNotFoundError(f"Step 32 allocation file not found for {period_label}")


def _resolve_step33_store_meta_path(period_label: str) -> Optional[str]:
    path = _latest_from_manifest("step33", "store_level_output_csv", period_label)
    if path and os.path.exists(path):
        return path
    import glob
    candidates = sorted(glob.glob(f"output/store_level_plugin_output_{period_label}_*.csv"))
    if candidates:
        return candidates[-1]
    return None


def _resolve_step24_labels_path(period_label: str) -> Optional[str]:
    path = _latest_from_manifest("step24", "comprehensive_cluster_labels", period_label)
    if path and os.path.exists(path):
        return path
    p = f"output/comprehensive_cluster_labels_{period_label}.csv"
    return p if os.path.exists(p) else None

def _resolve_step22_attrs_path(period_label: str) -> Optional[str]:
    ov = os.environ.get("STEP36_OVERRIDE_ATTRS")
    if ov and os.path.exists(ov):
        print(f"[Step36] Using Store Attributes (override): {ov}")
        return ov
    candidates = [
        f"output/enriched_store_attributes_{period_label}.csv",
        "output/enriched_store_attributes.csv",
    ]
    for p in candidates:
        if os.path.exists(p):
            print(f"[Step36] Using Store Attributes (fallback): {p}")
            return p
    return None

def _resolve_step24_store_tags(period_label: str) -> Optional[str]:
    ov = os.environ.get("STEP36_OVERRIDE_STORE_TAGS")
    if ov and os.path.exists(ov):
        print(f"[Step36] Using Store Tags (override): {ov}")
        return ov
    # Try manifest first
    man = get_manifest().manifest if hasattr(get_manifest(), 'manifest') else (get_manifest() or {})
    step24 = (man.get('steps', {}).get('step24', {}) or {}).get('outputs', {})
    candidates = [
        (step24.get(f"store_tags_{period_label}") or {}).get("file_path") if isinstance(step24.get(f"store_tags_{period_label}"), dict) else step24.get(f"store_tags_{period_label}"),
        (step24.get("store_tags") or {}).get("file_path") if isinstance(step24.get("store_tags"), dict) else step24.get("store_tags"),
        f"output/store_tags_{period_label}.csv",
        "output/store_tags.csv",
    ]
    for p in candidates:
        if p and os.path.exists(p):
            print(f"[Step36] Using Store Tags (fallback/manifest): {p}")
            return p
    return None


def _resolve_gap_summary_path(period_label: str) -> Optional[str]:
    # Step 27 or 29 outputs may contain detailed gap fields
    for step, key in [("step27", "gap_analysis_detailed"), ("step29", "gap_analysis_detailed")]:
        path = _latest_from_manifest(step, key, period_label)
        if path and os.path.exists(path):
            return path
    import glob
    candidates = sorted(glob.glob(f"output/gap_analysis_detailed_{period_label}_*.csv"))
    if candidates:
        return candidates[-1]
    return None


def _read_group_recs_df(yyyymm: str, period: str, period_label: str) -> pd.DataFrame:
    # Prefer Step 18 enriched
    st18 = _resolve_step18_path(yyyymm, period, period_label)
    if st18:
        log(f"✓ Using Step 18 sell-through enriched file: {st18}")
        df = pd.read_csv(st18)
        if "Period" not in df.columns:
            df["Period"] = period
        return df
    # Fallback to Step 14 enhanced
    st14 = _resolve_step14_path(yyyymm, period, period_label)
    if not st14:
        raise FileNotFoundError(f"Neither Step 18 nor Step 14 group file found for {period_label}")
    log(f"✓ Using Step 14 enhanced file: {st14}")
    df = pd.read_csv(st14)
    if "Period" not in df.columns:
        df["Period"] = period
    return df


def _largest_remainder_round(df: pd.DataFrame, qty_col: str, group_qty: float) -> pd.Series:
    """Round allocations to integers with exact sum match via largest remainder method."""
    base = df[qty_col].fillna(0.0)
    try:
        import numpy as _np
        floors = _np.floor(base.astype(float)).astype(int)
    except Exception:
        # Safe fallback using math.floor for correctness with negatives
        import math as _math
        floors = base.apply(lambda x: int(_math.floor(float(x))))
    remainder = base.astype(float) - floors.astype(float)
    target_sum = int(round(group_qty))
    floor_sum = int(floors.sum())
    delta = target_sum - floor_sum
    if delta == 0:
        return floors
    # Multi-pass distribution to allow delta larger than row count
    pos_order = remainder.sort_values(ascending=False).index.tolist()
    neg_order = remainder.sort_values(ascending=True).index.tolist()
    order = pos_order if delta > 0 else neg_order
    result = floors.copy()
    step = 1 if delta > 0 else -1
    remain = abs(delta)
    n = len(order)
    if n == 0:
        return result
    # Cycle through indices until delta exhausted
    k = 0
    while remain > 0:
        idx = order[k % n]
        result.at[idx] = int(result.at[idx]) + step
        remain -= 1
        k += 1
    return result


def _build_unified(
    yyyymm: str,
    period: str,
    period_label: str,
    out_ts: str,
) -> Tuple[str, Optional[str], str]:
    # Load inputs
    group_df = _read_group_recs_df(yyyymm, period, period_label)
    allocation_path = _resolve_step32_allocation_path(period_label)
    allocation_df = pd.read_csv(allocation_path)
    log(f"✓ Loaded Step 32 allocation: {len(allocation_df):,} rows from {allocation_path}")

    store_meta_path = _resolve_step33_store_meta_path(period_label)
    store_meta_df = pd.read_csv(store_meta_path) if store_meta_path else pd.DataFrame()
    if store_meta_path:
        log(f"✓ Loaded Step 33 store meta: {len(store_meta_df):,} rows from {store_meta_path}")
    else:
        log("⚠️ Step 33 store meta not found; continuing without additional meta columns")

    labels_path = _resolve_step24_labels_path(period_label)
    labels_df = pd.read_csv(labels_path) if labels_path else pd.DataFrame()
    if labels_path:
        log(f"✓ Loaded Step 24 labels: {len(labels_df):,} rows from {labels_path}")

    gap_path = _resolve_gap_summary_path(period_label)
    gap_df = pd.read_csv(gap_path) if gap_path else pd.DataFrame()
    if gap_path:
        log(f"✓ Loaded gap analysis: {len(gap_df):,} rows from {gap_path}")

    # Load store-level tags if available (Season/Gender/Location at store grain)
    store_tags_path = _resolve_step24_store_tags(period_label)
    store_tags_df = pd.read_csv(store_tags_path) if store_tags_path else pd.DataFrame()
    if store_tags_path:
        log(f"✓ Loaded store tags: {len(store_tags_df):,} rows from {store_tags_path}")

    # Load Step 22 enriched store attributes for store-level climate/fashion profile
    attrs_path2 = _resolve_step22_attrs_path(period_label)
    attrs2_df = pd.read_csv(attrs_path2) if attrs_path2 else pd.DataFrame()
    if attrs_path2:
        log(f"✓ Loaded store attributes for climate/profile: {len(attrs2_df):,} rows from {attrs_path2}")

    # Prepare attrs2_small for merge: normalize join key and keep temperature-related columns
    attrs2_small = pd.DataFrame()
    try:
        if not attrs2_df.empty:
            a2 = attrs2_df.copy()
            # Normalize join key to Store_Code
            if "Store_Code" not in a2.columns and "str_code" in a2.columns:
                a2["Store_Code"] = a2["str_code"]
            if "Store_Code" in a2.columns:
                a2["Store_Code"] = a2["Store_Code"].astype(str)
            # Prefer Store_Temperature_Band, but allow generic temperature_band too
            keep_cols = [c for c in [
                "Store_Code",
                "Store_Temperature_Band",
                "temperature_band",
                "feels_like_temperature",
                "Temperature_Zone"
            ] if c in a2.columns]
            if keep_cols:
                attrs2_small = a2[keep_cols].drop_duplicates()
    except Exception:
        pass

    # Normalize join key dtypes (prevent NaNs due to type mismatch)
    if "Store_Code" in allocation_df.columns:
        allocation_df["Store_Code"] = allocation_df["Store_Code"].astype(str)
    if not store_meta_df.empty and "Store_Code" in store_meta_df.columns:
        store_meta_df["Store_Code"] = store_meta_df["Store_Code"].astype(str)

    # Select minimal columns from group_df for join and business visibility; compute ΔQty if needed
    keep_group_cols = [
        c for c in [
            "Store_Group_Name",
            "Target_Style_Tags",
            "ΔQty",
            "Current_SPU_Quantity",
            "Target_SPU_Quantity",
            "Expected_Benefit",
            "Confidence_Score",
            "Optimization_Target",
            "Current_Sell_Through_Rate",
            "Target_Sell_Through_Rate",
            "Sell_Through_Improvement",
            "Constraint_Status",
            "Capacity_Utilization",
            "Store_Type_Alignment",
            "Temperature_Suitability",
            "Optimization_Rationale",
            "Trade_Off_Analysis",
            "Season",
            "Gender",
            "Location",
            "Category",
            "Subcategory",
            "Data_Based_Rationale",
            "Store_Codes_In_Group",
            "Store_Count_In_Group",
        ] if c in group_df.columns
    ]
    group_view = group_df[keep_group_cols].copy()
    group_qty_source = 'unknown'
    if "ΔQty" in group_view.columns:
        group_view = group_view.rename(columns={"ΔQty": "Group_ΔQty"})
        group_qty_source = 'step18'
    else:
        # derive ΔQty from target-current when explicit ΔQty missing
        if all(c in group_view.columns for c in ["Target_SPU_Quantity", "Current_SPU_Quantity"]):
            group_view["Group_ΔQty"] = (
                pd.to_numeric(group_view["Target_SPU_Quantity"], errors="coerce")
                - pd.to_numeric(group_view["Current_SPU_Quantity"], errors="coerce")
            )
            group_qty_source = 'derived_target_minus_current'
    # Prefer Step 14 ΔQty/targets when available to avoid sell-through-only skews
    try:
        step14_path = _latest_from_manifest('step14', 'enhanced_fast_fish_format', period_label)
        if step14_path and os.path.exists(step14_path):
            step14_cols = [c for c in [
                'Store_Group_Name','Target_Style_Tags','Category','Subcategory',
                'ΔQty','Current_SPU_Quantity','Target_SPU_Quantity','Data_Based_Rationale',
                'Season','Gender','Location'
            ] if c in pd.read_csv(step14_path, nrows=0).columns]
            if step14_cols:
                step14_df = pd.read_csv(step14_path, usecols=step14_cols)
                # Merge minimal keys
                on_cols = [c for c in ['Store_Group_Name','Target_Style_Tags','Category','Subcategory'] if c in group_view.columns and c in step14_df.columns]
                if on_cols:
                    group_view = group_view.merge(step14_df, on=on_cols, how='left', suffixes=('', '_ff14'))
                    # Override with Step 14 deltas/targets when present
                    if 'ΔQty_ff14' in group_view.columns:
                        group_view['Group_ΔQty'] = group_view.get('Group_ΔQty')
                        group_view.loc[group_view['ΔQty_ff14'].notna(), 'Group_ΔQty'] = group_view.loc[group_view['ΔQty_ff14'].notna(), 'ΔQty_ff14']
                        group_qty_source = 'step14'
                    for col in ['Current_SPU_Quantity','Target_SPU_Quantity','Data_Based_Rationale','Season','Gender','Location']:
                        src = f"{col}_ff14"
                        if src in group_view.columns:
                            group_view[col] = group_view[col].where(group_view[col].notna(), group_view[src])
                    # Prefer Step 14 product season explicitly if present: Parsed_Season then Season
                    try:
                        # Seed existing Product_Season if present
                        if 'Product_Season' not in group_view.columns:
                            group_view['Product_Season'] = pd.NA
                        if 'Product_Season_source' not in group_view.columns:
                            group_view['Product_Season_source'] = 'Unknown'

                        def _apply_seed(col_name, label):
                            if col_name in group_view.columns:
                                m = group_view['Product_Season'].isna() | (group_view['Product_Season'] == 'Unknown')
                                vals = group_view.loc[m, col_name].apply(_norm_season_en)
                                # only set where source has something non-Unknown
                                m2 = m & (vals != 'Unknown')
                                group_view.loc[m2, 'Product_Season'] = vals[m2]
                                group_view.loc[m2, 'Product_Season_source'] = label

                        _apply_seed('Parsed_Season_ff14', 'Step14_Parsed_Season')
                        _apply_seed('Season_ff14', 'Step14_Season')
                    except Exception:
                        pass
                    # Drop helper suffix cols
                    dropc = [c for c in group_view.columns if c.endswith('_ff14')]
                    if dropc:
                        group_view = group_view.drop(columns=dropc)
    except Exception:
        pass


    # Join allocation to group-level recs using robust fallback strategy
    # 1) Prefer full key when available
    rich_keys = [c for c in ["Store_Group_Name", "Target_Style_Tags", "Category", "Subcategory"] if c in allocation_df.columns and c in group_view.columns]
    if not rich_keys:
        rich_keys = ["Store_Group_Name", "Target_Style_Tags"]
    base = allocation_df.merge(group_view, on=rich_keys, how="left", suffixes=("_alloc", "_grp"))
    # Coalesce dimensional columns from allocation (preferred) over group to preserve upstream attribution
    def _coalesce_col(df: pd.DataFrame, base_name: str) -> None:
        a = f"{base_name}_alloc"
        g = f"{base_name}_grp"
        if a in df.columns or g in df.columns:
            vals = None
            if a in df.columns and g in df.columns:
                vals = df[a].where(df[a].notna(), df[g])
            elif a in df.columns:
                vals = df[a]
            else:
                vals = df[g]
            df[base_name] = vals
    for nm in ["Category","Subcategory","Gender","Season","Location","Product_Season","Product_Season_source"]:
        _coalesce_col(base, nm)

    # Fallback enrichment for Season/Location by parsing Target_Style_Tags tokens (B-period hardening)
    try:
        if "Target_Style_Tags" in base.columns:
            # Season inference
            if "Season" in base.columns:
                miss_season = base["Season"].isna() | (base["Season"].astype(str).str.strip() == "")
                if miss_season.any():
                    def _infer_season_from_tags(s: Optional[str]) -> Optional[str]:
                        if pd.isna(s):
                            return None
                        txt = str(s)
                        if txt.startswith("[") and txt.endswith("]"):
                            txt = txt[1:-1]
                        toks = [t.strip() for t in txt.split(',') if t.strip()]
                        for t in toks:
                            # prioritize Chinese season tokens
                            if t in ("夏","春","秋","冬"):
                                return t
                            # English hints
                            lt = t.lower()
                            if lt in ("summer","spring","autumn","fall","winter"):
                                return {"summer":"夏","spring":"春","autumn":"秋","fall":"秋","winter":"冬"}[lt]
                        return None
                    s_inferred = base.loc[miss_season, "Target_Style_Tags"].apply(_infer_season_from_tags)
                    smask = miss_season & s_inferred.notna()
                    base.loc[smask, "Season"] = s_inferred[smask]
                    if "Season_source" in base.columns:
                        base.loc[smask, "Season_source"] = base.loc[smask, "Season_source"].astype(str).replace({"nan":""}) + "+tags_token_backfill"
            # Location inference
            if "Location" in base.columns:
                miss_loc = base["Location"].isna() | (base["Location"].astype(str).str.strip() == "")
                if miss_loc.any():
                    def _infer_location_from_tags(s: Optional[str]) -> Optional[str]:
                        if pd.isna(s):
                            return None
                        txt = str(s)
                        if txt.startswith("[") and txt.endswith("]"):
                            txt = txt[1:-1]
                        toks = [t.strip() for t in txt.split(',') if t.strip()]
                        # prioritize Chinese location tokens used upstream
                        for t in toks:
                            if t in ("前台","后台","鞋配"):
                                return t
                        # English hints
                        for t in toks:
                            lt = t.lower()
                            if lt in ("front","back"):
                                return {"front":"前台","back":"后台"}[lt]
                        return None
                    l_inferred = base.loc[miss_loc, "Target_Style_Tags"].apply(_infer_location_from_tags)
                    lmask = miss_loc & l_inferred.notna()
                    base.loc[lmask, "Location"] = l_inferred[lmask]
                    if "Location_source" in base.columns:
                        base.loc[lmask, "Location_source"] = base.loc[lmask, "Location_source"].astype(str).replace({"nan":""}) + "+tags_token_backfill"
            # Recompose tags for rows affected by season/location fills
            if "Target_Style_Tags" in base.columns:
                affected = pd.Series(False, index=base.index)
                if 'Season_source' in base.columns:
                    affected |= base['Season_source'].astype(str).str.contains('tags_token_backfill', na=False)
                if 'Location_source' in base.columns:
                    affected |= base['Location_source'].astype(str).str.contains('tags_token_backfill', na=False)
                if affected.any():
                    base.loc[affected, "Target_Style_Tags"] = base.loc[affected].apply(_compose_tags, axis=1)
    except Exception:
        pass
    # 2) Fallback: where Group_ΔQty is missing after the rich merge, try Category/Subcategory-only merge
    try:
        needs_fill = base.get("Group_ΔQty_grp").isna() if "Group_ΔQty_grp" in base.columns else base.get("Group_ΔQty").isna()
        can_fallback = all(c in group_view.columns for c in ["Category", "Subcategory"]) and all(c in allocation_df.columns for c in ["Category", "Subcategory"]) and needs_fill.any()
        if can_fallback:
            fallback_keys = [c for c in ["Category", "Subcategory"] if c in allocation_df.columns and c in group_view.columns]
            fb = allocation_df.merge(group_view, on=fallback_keys, how="left", suffixes=("_alloc", "_grp_fb"))
            # Prefer existing values; fill only where missing
            if "Group_ΔQty_grp" in base.columns and "Group_ΔQty_grp_fb" in fb.columns:
                base.loc[needs_fill, "Group_ΔQty_grp"] = base.loc[needs_fill, "Group_ΔQty_grp"].fillna(fb.loc[needs_fill, "Group_ΔQty_grp_fb"])  # type: ignore
            # Clean up any temporary columns from fallback
            drop_fb = [c for c in base.columns if c.endswith("_grp_fb")]
            if drop_fb:
                base = base.drop(columns=drop_fb)
    except Exception:
        pass

    # Backfill Category/Subcategory from Step 14 taxonomy or tokens in Target_Style_Tags when missing
    try:
        cat_missing = ("Category" in base.columns) and base["Category"].isna().all()
        sub_missing = ("Subcategory" in base.columns) and base["Subcategory"].isna().all()
        if (cat_missing or sub_missing) and ("Target_Style_Tags" in base.columns):
            # Load Step 14 to get authoritative category/subcategory vocab
            step14_path = _latest_from_manifest('step14', 'enhanced_fast_fish_format', period_label)
            cat_vocab, sub_vocab = set(), set()
            if step14_path and os.path.exists(step14_path):
                try:
                    st14 = pd.read_csv(step14_path, usecols=[c for c in ["Category","Subcategory"] if c in pd.read_csv(step14_path, nrows=0).columns])
                    if "Category" in st14.columns:
                        cat_vocab.update([str(x).strip() for x in st14['Category'].dropna().unique().tolist()])
                    if "Subcategory" in st14.columns:
                        sub_vocab.update([str(x).strip() for x in st14['Subcategory'].dropna().unique().tolist()])
                except Exception:
                    pass

            def _parse_tokens(s: Optional[str]) -> list:
                if pd.isna(s):
                    return []
                txt = str(s)
                # strip brackets if present and split by comma
                txt = txt.strip()
                if txt.startswith("[") and txt.endswith("]"):
                    txt = txt[1:-1]
                return [t.strip() for t in txt.split(',') if t.strip()]

            # Work on a mask where either field is missing
            miss_mask = base["Category"].isna() if "Category" in base.columns else pd.Series(False, index=base.index)
            if "Subcategory" in base.columns:
                miss_mask = miss_mask | base["Subcategory"].isna()
            if miss_mask.any():
                tokens = base.loc[miss_mask, "Target_Style_Tags"].apply(_parse_tokens)
                # Try to pick Category/Subcategory tokens by matching vocab; iterate reversed so trailing tokens (cat/subcat) get priority
                new_cat = []
                new_sub = []
                for toks in tokens:
                    pick_cat = None
                    pick_sub = None
                    for tok in reversed(toks):
                        if pick_sub is None and (not sub_vocab or tok in sub_vocab):
                            pick_sub = tok
                            continue
                        if pick_cat is None and (not cat_vocab or tok in cat_vocab):
                            pick_cat = tok
                        if pick_cat and pick_sub:
                            break
                    new_cat.append(pick_cat)
                    new_sub.append(pick_sub)
                base.loc[miss_mask, "Category"] = base.loc[miss_mask, "Category"].fillna(pd.Series(new_cat, index=base.loc[miss_mask].index))
                base.loc[miss_mask, "Subcategory"] = base.loc[miss_mask, "Subcategory"].fillna(pd.Series(new_sub, index=base.loc[miss_mask].index))
    except Exception:
        pass

    # Resolve potential Group_ΔQty column collisions
    if "Group_ΔQty_alloc" in base.columns or "Group_ΔQty_grp" in base.columns:
        grp_alloc = base.get("Group_ΔQty_alloc")
        grp_grp = base.get("Group_ΔQty_grp")
        if grp_alloc is not None and grp_grp is not None:
            # Prefer allocation value; fall back to group when missing
            base["Group_ΔQty"] = grp_alloc.fillna(grp_grp)
            # Optionally, warn if large discrepancies exist (not printed, but could be added to QA)
        elif grp_alloc is not None:
            base["Group_ΔQty"] = grp_alloc
        elif grp_grp is not None:
            base["Group_ΔQty"] = grp_grp
        # Drop suffixed columns
        drop_cols = [c for c in ["Group_ΔQty_alloc", "Group_ΔQty_grp"] if c in base.columns]
        base = base.drop(columns=drop_cols)
    elif "ΔQty" in base.columns and "Group_ΔQty" not in base.columns:
        # As a safeguard, map ΔQty to Group_ΔQty if only ΔQty exists
        base["Group_ΔQty"] = base["ΔQty"]

    # Add store meta (constraints, capacity, tiers)
    if not store_meta_df.empty:
        meta_keep = [
            c for c in [
                "Store_Code",
                "Constraint_Status",
                "Capacity_Utilization",
                "Action_Priority",
                "Performance_Tier",
                "Growth_Potential",
                "Risk_Level",
                "Cluster_ID",
                "Cluster_Name",
                "Operational_Tag",
                "Temperature_Zone",
                # Fallback sources for capacity/diagnostics
                "Estimated_Rack_Capacity",
                "Product_Count",
            ] if c in store_meta_df.columns
        ]
        meta = store_meta_df[meta_keep].copy()
        base = base.merge(meta, on="Store_Code", how="left")

    # Merge prepared Step 22 temperature attributes if available
    try:
        if not attrs2_small.empty and "Store_Code" in base.columns:
            base = base.merge(attrs2_small, on="Store_Code", how="left", suffixes=(None, "_attr"))
    except Exception:
        pass

    # Merge Buffer_Stock_Percentage from Step 35 recommendations when available
    try:
        step35_path = _resolve_step35_recs_path(period_label)
        if step35_path and os.path.exists(step35_path):
            # Load minimally to avoid heavy memory
            step35_head = pd.read_csv(step35_path, nrows=0)
            cols = list(step35_head.columns)
            # Identify available join keys
            join_keys = [k for k in ["Store_Code", "Target_Style_Tags", "Category", "Subcategory"] if k in cols and k in base.columns]
            # Ensure at least Store_Code is present
            if "Store_Code" in join_keys:
                usecols = [c for c in ["Store_Code", "Target_Style_Tags", "Category", "Subcategory", "Buffer_Stock_Percentage"] if c in cols]
                if "Buffer_Stock_Percentage" in usecols:
                    step35_df = pd.read_csv(step35_path, usecols=usecols)
                    # Normalize join key dtype
                    if "Store_Code" in step35_df.columns:
                        step35_df["Store_Code"] = step35_df["Store_Code"].astype(str)
                    # Drop duplicates on join keys to avoid exploding rows
                    if join_keys:
                        step35_df = step35_df.drop_duplicates(subset=join_keys)
                    base = base.merge(step35_df, on=join_keys, how="left")
    except Exception:
        pass

    # Coalesce duplicate-suffixed columns (_x/_y) into canonical names
    def _coalesce(df: pd.DataFrame, canonical: str, candidates: List[str]) -> pd.DataFrame:
        cols = [c for c in candidates if c in df.columns]
        if not cols:
            return df
        def _first(row):
            for c in [canonical] + cols:
                if c in row and pd.notna(row[c]):
                    return row[c]
            return pd.NA
        df[canonical] = df.apply(_first, axis=1)
        drop_cols = [c for c in cols if c != canonical]
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])
        return df

    base = _coalesce(base, "Cluster_ID", ["Cluster_ID_x", "Cluster_ID_y", "cluster_id", "cluster_id_alloc", "cluster_id_grp"])
    base = _coalesce(base, "Constraint_Status", ["Constraint_Status_x", "Constraint_Status_y"])
    base = _coalesce(base, "Capacity_Utilization", ["Capacity_Utilization_x", "Capacity_Utilization_y"])

    # Add cluster labels when available and Cluster_ID missing
    if "Cluster_ID" not in base.columns and not labels_df.empty:
        labels_keep = [c for c in ["cluster_id", "cluster_name"] if c in labels_df.columns]
        lab = labels_df[labels_keep].drop_duplicates().copy()
        lab = lab.rename(columns={"cluster_id": "Cluster_ID", "cluster_name": "Cluster_Name"})
        if "Cluster_ID" in base.columns:
            pass
        else:
            # No store key in labels; skip if merge key absent
            pass

    # Normalize enums for Season/Gender/Location and recompose Target_Style_Tags
    def _norm_season(val: Optional[str]) -> Optional[str]:
        if pd.isna(val):
            return val
        v = str(val).strip()
        # Enforce zh-only: map English tokens to Chinese; preserve Chinese tokens
        lower = v.lower()
        en2zh = {
            'spring': '春',
            'summer': '夏',
            'autumn': '秋',
            'fall': '秋',
            'winter': '冬',
        }
        if v in ("春","夏","秋","冬","四季"):
            return v
        return en2zh.get(lower, v)

    def _norm_gender(val: Optional[str]) -> Optional[str]:
        if pd.isna(val):
            return val
        v = str(val).strip()
        # Enforce zh-only: map English tokens to Chinese; preserve Chinese tokens
        lower = v.lower()
        if v in ("男","女","中性","中"):
            return "中性" if v == "中" else v
        mapping = {
            'unisex': '中性', '男女': '中性',
            'men': '男', 'male': '男',
            'women': '女', 'female': '女',
        }
        return mapping.get(lower, v)

    def _norm_location(val: Optional[str]) -> Optional[str]:
        if pd.isna(val):
            return val
        v = str(val).strip()
        # Enforce zh-only: map English tokens to Chinese; preserve Chinese tokens
        lower = v.lower()
        if v in ("前台","后台","鞋配"):
            return v
        mapping = {'front': '前台', 'back': '后台'}
        return mapping.get(lower, v)

    def _infer_gender_from_tokens(s: Optional[str]) -> Optional[str]:
        if pd.isna(s):
            return pd.NA
        t = str(s)
        if any(x in t for x in ['中性', 'Unisex', '男女']):
            return 'Unisex'
        if any(x in t for x in ['女', 'Women', '女性']):
            return 'Women'
        if any(x in t for x in ['男', 'Men', '男性']):
            return 'Men'
        return pd.NA

    def _infer_location_from_tokens(s: Optional[str]) -> Optional[str]:
        if pd.isna(s):
            return pd.NA
        t = str(s)
        if any(x in t for x in ['前台', 'Front']):
            return '前台'
        if any(x in t for x in ['后台', 'Back']):
            return '后台'
        return pd.NA

    # --- Product Season derivation helpers (English-normalized) ---
    def _norm_season_en(val: Optional[str]) -> str:
        if pd.isna(val):
            return 'Unknown'
        v = str(val).strip()
        if not v:
            return 'Unknown'
        lv = v.lower()
        # direct zh hits
        if '秋' in v:
            return 'Autumn'
        if '冬' in v:
            return 'Winter'
        if '夏' in v:
            return 'Summer'
        if '春' in v:
            return 'Spring'
        if '四季' in v:
            return 'All-Season'
        # english substring hits (tolerate annotations like '+planning_fill')
        if 'autumn' in lv or 'fall' in lv:
            return 'Autumn'
        if 'winter' in lv:
            return 'Winter'
        if 'summer' in lv:
            return 'Summer'
        if 'spring' in lv:
            return 'Spring'
        if 'all-season' in lv or 'all season' in lv:
            return 'All-Season'
        # final exact map fallbacks
        mapping = {
            'Autumn': 'Autumn', 'Fall': 'Autumn',
            'Winter': 'Winter', 'Summer': 'Summer', 'Spring': 'Spring',
            'All-Season': 'All-Season'
        }
        return mapping.get(v, 'Unknown')

    def _derive_season_from_tags_en(s: Optional[str]) -> str:
        if pd.isna(s):
            return 'Unknown'
        txt = str(s).strip()
        if txt.startswith('[') and txt.endswith(']'):
            txt = txt[1:-1]
        toks = [t.strip() for t in txt.split(',') if t.strip()]
        # prioritize Chinese then English season tokens
        for t in toks:
            if t in ('夏','春','秋','冬','四季','四季款'):
                return _norm_season_en(t)
        for t in toks:
            lt = t.lower()
            if lt in ('summer','spring','autumn','fall','winter','all-season'):
                return _norm_season_en(t)
        return 'Unknown'

    # Sources
    base['Season_source'] = pd.NA
    base['Gender_source'] = pd.NA
    base['Location_source'] = pd.NA

    if 'Season' in base.columns:
        base['Season'] = base['Season'].apply(_norm_season)
        base.loc[base['Season'].notna(), 'Season_source'] = base.loc[base['Season'].notna(), 'Season_source'].fillna('step18')
    if 'Gender' in base.columns:
        base['Gender'] = base['Gender'].apply(_norm_gender)
        base.loc[base['Gender'].notna(), 'Gender_source'] = base.loc[base['Gender'].notna(), 'Gender_source'].fillna('step18')
    if 'Location' in base.columns:
        base['Location'] = base['Location'].apply(_norm_location)
        base.loc[base['Location'].notna(), 'Location_source'] = base.loc[base['Location'].notna(), 'Location_source'].fillna('step18')

    # Populate Planning_Season and Planning_Year with forward-planning defaults
    # - Forward-planning season by target month (Aug–Oct => Autumn, Nov–Feb => Winter,
    #   Mar–May => Spring, Jun–Jul => Summer). This prevents late-summer bias in Aug runs.
    # - Set Planning_Year from the CLI-provided yyyymm (e.g., 202508 -> 2025)
    try:
        if 'Planning_Season' not in base.columns:
            base['Planning_Season'] = pd.NA
        # Derive Planning_Year and forward-planning season from target yyyymm
        plan_year = int(str(yyyymm)[:4]) if yyyymm else pd.NA
        plan_month = int(str(yyyymm)[4:6]) if yyyymm else pd.NA
        def _season_from_month(m):
            try:
                m = int(m)
            except Exception:
                return pd.NA
            if m in (11,12,1,2):
                return 'Winter'
            if m in (3,4,5):
                return 'Spring'
            if m in (6,7):
                return 'Summer'
            if m in (8,9,10):
                return 'Autumn'
            return pd.NA
        plan_season = _season_from_month(plan_month)
        base['Planning_Season'] = plan_season if plan_season is not pd.NA else base['Planning_Season']
        base['Planning_Year'] = plan_year
    except Exception:
        pass

    # Populate Temperature_Zone if missing using Temperature_Band_Simple (case-insensitive)
    # and Chinese hints; fallback to Temperature_Value_C thresholds.
    try:
        if 'Temperature_Zone' not in base.columns:
            base['Temperature_Zone'] = pd.NA
        if 'Temperature_Band_Simple' in base.columns:
            def _map_zone(val):
                if pd.isna(val):
                    return pd.NA
                v = str(val).strip().lower()
                if any(k in v for k in ['cold','寒','冷']):
                    return 'Cool-North'
                if any(k in v for k in ['warm','热','暖']):
                    return 'Warm-South'
                if any(k in v for k in ['moderate','温','适中','中']):
                    return 'Moderate-Central'
                return pd.NA
            need_tz = base['Temperature_Zone'].isna() | (base['Temperature_Zone'].astype(str).str.strip() == '')
            mapped = base.loc[need_tz, 'Temperature_Band_Simple'].apply(_map_zone)
            base.loc[need_tz & mapped.notna(), 'Temperature_Zone'] = mapped[mapped.notna()]
        # Fallback: derive from Temperature_Value_C if still missing
        if ('Temperature_Zone' in base.columns) and (base['Temperature_Zone'].isna().any()):
            if 'Temperature_Value_C' in base.columns:
                def _zone_from_temp(x):
                    try:
                        t = float(x)
                    except Exception:
                        return pd.NA
                    if t <= 12:
                        return 'Cool-North'
                    if t >= 24:
                        return 'Warm-South'
                    return 'Moderate-Central'
                msk = base['Temperature_Zone'].isna() | (base['Temperature_Zone'].astype(str).str.strip()=='')
                tz2 = base.loc[msk, 'Temperature_Value_C'].apply(_zone_from_temp)
                base.loc[msk & tz2.notna(), 'Temperature_Zone'] = tz2[tz2.notna()]
    except Exception:
        pass

    # Targeted enrichment: recover Season/Gender/Location by merging API store_config on Store_Code × Subcategory
    try:
        # Resolve store_config path via manifest-aware helper, with robust fallbacks
        sc_path = None
        try:
            files = get_api_data_files(yyyymm, period)
            sc_path = files.get('store_config') if isinstance(files, dict) else None
        except Exception:
            sc_path = None
        if not sc_path:
            cand = f"data/api_data/store_config_{period_label}.csv"
            sc_path = cand if os.path.exists(cand) else None
        if not sc_path:
            cand2 = "data/api_data/store_config_data.csv"
            sc_path = cand2 if os.path.exists(cand2) else None

        if sc_path and os.path.exists(sc_path):
            sc_df = pd.read_csv(sc_path)
            # Normalize keys in store_config
            if 'str_code' not in sc_df.columns:
                alt = next((c for c in sc_df.columns if c.lower() in ('str_code','store_code','storeid','store_id','strcode','store')), None)
                if alt:
                    sc_df = sc_df.rename(columns={alt: 'str_code'})
            if 'sub_cate_name' not in sc_df.columns:
                alt = next((c for c in sc_df.columns if ('sub' in c.lower() and 'cate' in c.lower() and 'name' in c.lower())), None)
                if alt:
                    sc_df = sc_df.rename(columns={alt: 'sub_cate_name'})
            sc_df['str_code'] = sc_df['str_code'].astype(str).str.strip()

            # Normalizer for subcategory tokens
            import re as _re
            def _norm_sub_tok(s: Optional[str]) -> str:
                if pd.isna(s):
                    return ''
                t = str(s).strip()
                t = _re.sub(r"[\s\u3000]+", '', t)
                t = t.replace('（','(').replace('）',')').replace('–','-').replace('—','-')
                return t.lower()

            sc_df['__sub_norm__'] = sc_df.get('sub_cate_name', pd.Series(index=sc_df.index)).map(_norm_sub_tok)

            # Prepare base keys
            if 'Store_Code' in base.columns:
                base['Store_Code'] = base['Store_Code'].astype(str).str.strip()
            # Prefer Subcategory; fallback to last token of Target_Style_Tags
            if 'Subcategory' in base.columns:
                base['__sub_norm__'] = base['Subcategory'].map(_norm_sub_tok)
            elif 'Target_Style_Tags' in base.columns:
                def _last_token(s: Optional[str]) -> str:
                    if pd.isna(s):
                        return ''
                    txt = str(s).strip()
                    if txt.startswith('[') and txt.endswith(']'):
                        txt = txt[1:-1]
                    toks = [t.strip() for t in txt.split(',') if t.strip()]
                    return toks[-1] if toks else ''
                base['__sub_norm__'] = base['Target_Style_Tags'].apply(_last_token).map(_norm_sub_tok)
            else:
                base['__sub_norm__'] = ''

            # Build minimal mapping from API: season_name, sex_name, display_location_name, big_class_name (category-level)
            keep_cols = [c for c in ['str_code','__sub_norm__','season_name','sex_name','display_location_name','big_class_name'] if c in sc_df.columns]
            sc_small = sc_df[keep_cols].drop_duplicates()

            # Join and backfill only where missing
            if 'Store_Code' in base.columns and '__sub_norm__' in base.columns and not sc_small.empty:
                sc_small = sc_small.rename(columns={'str_code':'Store_Code'})
                base = base.merge(sc_small, on=['Store_Code','__sub_norm__'], how='left', suffixes=(None, '_api'))

                # Fill Season
                if 'Season' in base.columns and 'season_name' in base.columns:
                    miss = base['Season'].isna() | (base['Season'].astype(str).str.strip()=='')
                    if miss.any():
                        base.loc[miss, 'Season'] = base.loc[miss, 'season_name']
                        base.loc[miss, 'Season'] = base.loc[miss, 'Season'].apply(_norm_season)
                        base.loc[miss, 'Season_source'] = base.loc[miss, 'Season_source'].astype(str).replace({'nan':''}) + '+api_store_config'

                # Fill Gender
                if 'Gender' in base.columns and 'sex_name' in base.columns:
                    miss = base['Gender'].isna() | (base['Gender'].astype(str).str.strip()=='')
                    if miss.any():
                        base.loc[miss, 'Gender'] = base.loc[miss, 'sex_name']
                        base.loc[miss, 'Gender'] = base.loc[miss, 'Gender'].apply(_norm_gender)
                        base.loc[miss, 'Gender_source'] = base.loc[miss, 'Gender_source'].astype(str).replace({'nan':''}) + '+api_store_config'

                # Fill Location
                if 'Location' in base.columns and 'display_location_name' in base.columns:
                    miss = base['Location'].isna() | (base['Location'].astype(str).str.strip()=='')
                    if miss.any():
                        base.loc[miss, 'Location'] = base.loc[miss, 'display_location_name']
                        base.loc[miss, 'Location'] = base.loc[miss, 'Location'].apply(_norm_location)
                        base.loc[miss, 'Location_source'] = base.loc[miss, 'Location_source'].astype(str).replace({'nan':''}) + '+api_store_config'

                # Backfill Category from big_class_name if missing; also compute Category_Display for retailer-friendly taxonomy
                if 'big_class_name' in base.columns:
                    if 'Category' in base.columns:
                        miss_cat = base['Category'].isna() | (base['Category'].astype(str).str.strip()=='')
                        if miss_cat.any():
                            base.loc[miss_cat, 'Category'] = base.loc[miss_cat, 'big_class_name']
                    # Always create Category_Display preferring API big_class_name when present
                    base['Category_Display'] = base.get('big_class_name')
                    # Fallback to existing Category where big_class_name is missing/empty
                    if 'Category' in base.columns:
                        empty_disp = base['Category_Display'].isna() | (base['Category_Display'].astype(str).str.strip()=='')
                        base.loc[empty_disp, 'Category_Display'] = base.loc[empty_disp, 'Category']
                # Drop helper columns from join (keep Category_Display)
                drop_helpers = [c for c in ['season_name','sex_name','display_location_name'] if c in base.columns]
                if drop_helpers:
                    base = base.drop(columns=drop_helpers)
                # Promote API pants category label into final Category when explicitly '休闲裤'
                try:
                    if 'Category' in base.columns and 'Category_Display' in base.columns:
                        mask_pants = base['Category_Display'].astype(str) == '休闲裤'
                        if mask_pants.any():
                            base.loc[mask_pants, 'Category'] = base.loc[mask_pants, 'Category_Display']
                except Exception:
                    pass
            # Clean up helper key
            if '__sub_norm__' in base.columns:
                base = base.drop(columns=['__sub_norm__'])
    except Exception:
        # Best-effort enrichment only
        pass

    # No additional Step 14 taxonomy promotion fallback beyond API/manifest sources

    # Compose normalized Target_Style_Tags from Season/Gender/Location + Category/Subcategory + original tokens
    def _normalize_original_tags(val):
        if pd.isna(val):
            return []
        t = str(val).strip()
        if t.startswith("[") and t.endswith("]"):
            t = t[1:-1]
        parts = [p.strip() for p in t.replace("|", ",").split(",") if p.strip()]
        return parts

    def _compose_tags(row):
        parts = []
        if 'Season' in row and pd.notna(row.get('Season')):
            parts.append(str(row.get('Season')).strip())
        if 'Gender' in row and pd.notna(row.get('Gender')):
            parts.append(str(row.get('Gender')).strip())
        if 'Location' in row and pd.notna(row.get('Location')):
            parts.append(str(row.get('Location')).strip())
        if 'Category' in row and pd.notna(row.get('Category')):
            parts.append(str(row.get('Category')).strip())
        if 'Subcategory' in row and pd.notna(row.get('Subcategory')):
            parts.append(str(row.get('Subcategory')).strip())
        orig_tokens = _normalize_original_tags(row.get('Target_Style_Tags'))
        parts.extend(orig_tokens)
        seen = set()
        out = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                out.append(p)
        return ", ".join(out)

    if "Target_Style_Tags" in base.columns:
        base["Target_Style_Tags"] = base.apply(_compose_tags, axis=1)
        # strip any accidental surrounding brackets and leading commas
        def _strip_brackets(s):
            if pd.isna(s):
                return s
            t = str(s)
            t = t.strip()
            if t.startswith("[") and t.endswith("]"):
                t = t[1:-1]
            # collapse redundant commas/spaces
            t = ", ".join([p.strip() for p in t.split(",") if p.strip()])
            return t
        base["Target_Style_Tags"] = base["Target_Style_Tags"].apply(_strip_brackets)
        # Append planning season/year hint into tags if different from Season
        if all(c in base.columns for c in ["Planning_Season","Planning_Year","Season"]):
            def _append_planning(row, s):
                try:
                    ps=row['Planning_Season']; sy=row['Planning_Year']; se=row['Season']
                    if pd.notna(ps) and pd.notna(se) and str(ps)!=str(se):
                        # append like "Autumn 2025"
                        hint=f"{ps} {int(sy)}" if pd.notna(sy) else str(ps)
                        if hint not in s:
                            return (s+", "+hint) if s else hint
                except Exception:
                    pass
                return s
            base["Target_Style_Tags"] = base.apply(lambda r: _append_planning(r, r.get("Target_Style_Tags")), axis=1)
        # Backfill Season from Planning_Season to surface Autumn when missing
        if "Season" in base.columns and "Planning_Season" in base.columns:
            miss = base["Season"].isna() & base["Planning_Season"].notna()
            base.loc[miss, "Season"] = base.loc[miss, "Planning_Season"]
            base.loc[miss, "Season_source"] = base.loc[miss, "Season_source"].astype(str).where(base.loc[miss, "Season_source"].notna(), "")
            base.loc[miss, "Season_source"] = base.loc[miss, "Season_source"].replace({"nan": ""}) + "+planning_fill"

    # Backfill Season/Gender/Location sources
    base['Season_source'] = base['Season_source'].fillna('unknown')
    base['Gender_source'] = base['Gender_source'].fillna('unknown')
    base['Location_source'] = base['Location_source'].fillna('unknown')

    # Planning season fields from period label (do not force Season)
    try:
        _year = int(yyyymm[:4])
        _month = int(yyyymm[4:])
        if _month in [12,1,2]: pl_season = 'Winter'
        elif _month in [3,4,5]: pl_season = 'Spring'
        elif _month in [6,7]: pl_season = 'Summer'
        else: pl_season = 'Autumn'  # Aug–Oct Autumn; Nov–Feb Winter handled above
        base['Planning_Season'] = pl_season
        base['Planning_Year'] = _year
        base['Planning_Period_Label'] = period_label
        # Explicit business-facing date fields
        base['Analysis_Year'] = f"{_year:04d}"
        base['Analysis_Month'] = f"{_month:02d}"
        base['Analysis_Period'] = str(period)
    except Exception:
        base['Planning_Season'] = pd.NA
        base['Planning_Year'] = pd.NA
        base['Planning_Period_Label'] = period_label
        # Best-effort: still set period label; leave analysis fields as NA if parsing failed
        base['Analysis_Year'] = pd.NA
        base['Analysis_Month'] = pd.NA
        base['Analysis_Period'] = str(period)

    # Temperature parsing, detailed banding, and graded suitability
    # Detect temperature band/zone column robustly
    temp_col = None
    for c in list(base.columns):
        lc = str(c).lower()
        if ('temp' in lc) and ('band' in lc or 'zone' in lc):
            temp_col = c
            break
    if temp_col is None and 'Store_Temperature_Band' in base.columns:
        temp_col = 'Store_Temperature_Band'
    # Ensure Temperature_Zone column exists to avoid KeyError in downstream logic
    if 'Temperature_Zone' not in base.columns:
        try:
            base['Temperature_Zone'] = pd.NA
        except Exception:
            pass
    if temp_col is not None:
        # Extract numeric °C from zone/band strings when present
        def _parse_temp_val(x):
            try:
                s = str(x)
                # e.g., '19.3°C (Moderate-Central)'
                m = __import__('re').search(r"([\-\d\.]+)\s*°?C", s)
                if m:
                    return float(m.group(1))
            except Exception:
                pass
            return pd.NA
        base['Temperature_Value_C'] = base[temp_col].apply(_parse_temp_val)
        
        # FIXED: Classify Temperature_Band_Simple based on numeric temperature value
        # instead of string matching which always returned 'Moderate'
        def _simple_band_from_value(temp_c):
            """Classify temperature into simple bands based on numeric value."""
            if pd.isna(temp_c): 
                return pd.NA
            try:
                t = float(temp_c)
                if t < 10: return 'Cold'
                if t < 18: return 'Cool'
                if t < 23: return 'Moderate'
                if t < 28: return 'Warm'
                return 'Hot'
            except (ValueError, TypeError):
                return 'Moderate'  # Fallback
        
        # Use Temperature_Value_C if available, otherwise fall back to string matching
        if 'Temperature_Value_C' in base.columns and base['Temperature_Value_C'].notna().any():
            base['Temperature_Band_Simple'] = base['Temperature_Value_C'].apply(_simple_band_from_value)
        else:
            # Fallback to original string matching (for backward compatibility)
            def _simple_band(x):
                if pd.isna(x): return pd.NA
                s = str(x)
                if any(k in s for k in ['Cold','冷']): return 'Cold'
                if any(k in s for k in ['Warm','热','Hot']): return 'Warm'
                return 'Moderate'
            base['Temperature_Band_Simple'] = base[temp_col].apply(_simple_band)
        # Immediately backfill Temperature_Zone from the simple band if zone is missing
        try:
            if 'Temperature_Zone' not in base.columns:
                base['Temperature_Zone'] = pd.NA
            need = base['Temperature_Zone'].isna() | (base['Temperature_Zone'].astype(str).str.strip()=='')
            def _zone_from_band(b):
                if pd.isna(b):
                    return pd.NA
                s=str(b)
                if 'Cold' in s:
                    return 'Cool-North'
                if 'Warm' in s:
                    return 'Warm-South'
                if 'Moderate' in s:
                    return 'Moderate-Central'
                return pd.NA
            z = base.loc[need, 'Temperature_Band_Simple'].apply(_zone_from_band)
            base.loc[need & z.notna(), 'Temperature_Zone'] = z[z.notna()]
        except Exception:
            pass
    # derive simple band from Temperature_Zone if still missing
    if 'Temperature_Band_Simple' in base.columns and ('Temperature_Zone' in base.columns or temp_col is not None):
        miss = base['Temperature_Band_Simple'].isna() & base['Temperature_Zone'].notna()
        def _simple_from_zone(z):
            s=str(z)
            if 'Warm' in s or '热' in s: return 'Warm'
            if 'Cold' in s or '冷' in s: return 'Cold'
            return 'Moderate'
        base.loc[miss,'Temperature_Band_Simple'] = base.loc[miss,'Temperature_Zone'].apply(_simple_from_zone)
    if ('Temperature_Band_Simple' in base.columns):
        def _grade_suit(row):
            b = row.get('Temperature_Band_Simple')
            z = row.get('Temperature_Zone')
            if pd.isna(z) or pd.isna(b): return 'Unknown'
            # FIXED: Added 'Cool' matching for proper suitability grading
            if ('Cold' in str(z) and b=='Cold') or ('Cool' in str(z) and b=='Cool') or ('Warm' in str(z) and b=='Warm'):
                return 'High'
            if b=='Moderate':
                return 'Medium'
            return 'Review'
        base['Temperature_Suitability_Graded'] = base.apply(_grade_suit, axis=1)

    # Compute detailed temperature band from numeric value (6 bands)
    if 'Temperature_Value_C' in base.columns:
        def _band_detailed(v):
            try:
                v = float(v)
            except Exception:
                return pd.NA
            # Tunable thresholds (Autumn): Cold <12, Cool 12–16, Mild 16–18, Moderate 18–20, Warm 20–22.5, Hot >22.5
            if v < 12.0: return 'Cold'
            if v < 16.0: return 'Cool'
            if v < 18.0: return 'Mild'
            if v < 20.0: return 'Moderate'
            if v <= 22.5: return 'Warm'
            return 'Hot'
        base['Temperature_Band_Detailed'] = base['Temperature_Value_C'].apply(_band_detailed)

        # Cluster temperature quintiles for finer segmentation
        try:
            if 'Cluster_ID' in base.columns:
                avg_temp = base.groupby('Cluster_ID')['Temperature_Value_C'].mean().reset_index(name='Cluster_Temp_C_Mean')
                # compute quintiles
                if avg_temp['Cluster_Temp_C_Mean'].notna().sum() > 0:
                    q = pd.qcut(avg_temp['Cluster_Temp_C_Mean'], 5, labels=['Q1-Coldest','Q2','Q3','Q4','Q5-Warmest'])
                    avg_temp['Cluster_Temp_Quintile'] = q
                base = base.merge(avg_temp, on='Cluster_ID', how='left')
        except Exception:
            pass

    # Optional join: historical cluster temperature profile
    try:
        hist_path = 'output/historical_cluster_temperature_profile.csv'
        if os.path.exists(hist_path) and 'Cluster_ID' in base.columns:
            hist = pd.read_csv(hist_path)
            base = base.merge(hist, on='Cluster_ID', how='left')
            # Divergence flag between current detailed band and historical
            if 'Temperature_Band_Detailed' in base.columns and 'Historical_Temp_Band_Detailed' in base.columns:
                base['Temp_Band_Divergence'] = (base['Temperature_Band_Detailed'].astype(str) != base['Historical_Temp_Band_Detailed'].astype(str))
    except Exception:
        pass

    # Constraint status enrichment combining capacity and temperature
    if 'Capacity_Utilization' in base.columns:
        cu = pd.to_numeric(base['Capacity_Utilization'], errors='coerce')
        cap_flag = pd.Series(index=base.index, dtype=object)
        cap_flag[:] = pd.NA
        cap_flag = cap_flag.where(~cu.notna(), other='Capacity OK')
        cap_flag = cap_flag.mask((cu.notna()) & (cu >= 0.95), 'Capacity Tight')
        tflag = pd.Series('Temp Unknown', index=base.index)
        if 'Temperature_Suitability_Graded' in base.columns:
            tflag = tflag.mask(base['Temperature_Suitability_Graded']=='High', 'Temp OK')
            tflag = tflag.mask(base['Temperature_Suitability_Graded'].isin(['Medium','Review']), 'Temp Review')
        base['Constraint_Status'] = cap_flag.fillna('Unknown') + ', ' + tflag

    # Robust Store_Fashion_Profile derivation with fallbacks and sources
    def _normalize_ratio_series(s: pd.Series) -> pd.Series:
        v = pd.to_numeric(s, errors='coerce')
        if v.notna().any() and (v.dropna().max() > 1.0):
            v = v / 100.0
        return v.clip(lower=0.0, upper=1.0)

    store_ratio = pd.Series(index=base.index, dtype=float)
    source = pd.Series(index=base.index, dtype=object)

    # 1) Prefer explicit fashion/basic shares if both present
    cand_fashion = [c for c in base.columns if re.search(r"fashion.*ratio|fashion.*share", c, re.I)]
    cand_basic = [c for c in base.columns if re.search(r"basic.*ratio|basic.*share", c, re.I)]
    if cand_fashion and cand_basic:
        f = _normalize_ratio_series(base[cand_fashion[0]])
        b = _normalize_ratio_series(base[cand_basic[0]])
        denom = (f.fillna(0) + b.fillna(0)).replace(0, np.nan)
        r = (f / denom)
        store_ratio = store_ratio.where(store_ratio.notna(), r)
        source = source.where(source.notna(), 'store_fashion_basic_ratios')

    # 2) If only fashion ratio-like exists
    if store_ratio.notna().sum() == 0 and cand_fashion:
        r = _normalize_ratio_series(base[cand_fashion[0]])
        store_ratio = store_ratio.where(store_ratio.notna(), r)
        source = source.where(source.notna(), 'store_fashion_ratio')

    # 3) Fallback to Step 14 cluster fashion makeup if available
    try:
        if store_ratio.notna().sum() == 0 and 'Cluster_ID' in base.columns:
            path_fm = _latest_from_manifest('step14', 'cluster_fashion_makeup', period_label)
            if path_fm and os.path.exists(path_fm):
                fm = pd.read_csv(path_fm)
                cid = next((c for c in fm.columns if c.lower() in ('cluster_id','cluster','clusterid')), None)
                if cid:
                    fm = fm.rename(columns={cid: 'Cluster_ID'})
                    # Try common column names
                    fcol = next((c for c in fm.columns if re.search(r"fashion.*(ratio|share)", c, re.I)), None)
                    if fcol:
                        fm['__cluster_fashion_ratio__'] = _normalize_ratio_series(fm[fcol])
                        fm_small = fm[['Cluster_ID','__cluster_fashion_ratio__']].drop_duplicates()
                        base = base.merge(fm_small, on='Cluster_ID', how='left')
                        store_ratio = store_ratio.where(store_ratio.notna(), base['__cluster_fashion_ratio__'])
                        source = source.where(source.notna(), 'cluster_fashion_makeup')
                        if '__cluster_fashion_ratio__' in base.columns:
                            base = base.drop(columns=['__cluster_fashion_ratio__'])
    except Exception:
        pass

    # 4) Last resort: compute simple store/group-level share if product counts exist
    if store_ratio.notna().sum() == 0:
        try:
            # Look for counts that distinguish fashion vs basic (heuristic: columns with keywords)
            fc = next((c for c in base.columns if re.search(r"fashion.*count", c, re.I)), None)
            bc = next((c for c in base.columns if re.search(r"basic.*count", c, re.I)), None)
            if fc and bc:
                fcnt = pd.to_numeric(base[fc], errors='coerce')
                bcnt = pd.to_numeric(base[bc], errors='coerce')
                denom = (fcnt.fillna(0) + bcnt.fillna(0)).replace(0, np.nan)
                r = (fcnt / denom).clip(0,1)
                store_ratio = store_ratio.where(store_ratio.notna(), r)
                source = source.where(source.notna(), 'store_counts_fashion_basic')
        except Exception:
            pass

    # Classification with auto-tune if overly skewed
    base['Store_Fashion_Ratio_Normalized'] = store_ratio
    base['Store_Fashion_Profile_source'] = source

    def _classify(v, lo=0.35, hi=0.65):
        if pd.isna(v): return pd.NA
        if v >= hi: return 'Fashion-Heavy'
        if v <= lo: return 'Basic-Heavy'
        return 'Balanced'

    prof = store_ratio.apply(_classify)
    # Auto-tune thresholds if >90% in single bucket
    counts = prof.value_counts(dropna=True)
    if not counts.empty and (counts.max() / counts.sum() > 0.90) and store_ratio.notna().sum() > 100:
        q20 = float(store_ratio.quantile(0.20))
        q80 = float(store_ratio.quantile(0.80))
        prof = store_ratio.apply(lambda v: _classify(v, lo=q20, hi=q80))
        base['Store_Fashion_Profile_thresholds'] = f"auto_tuned:{q20:.2f},{q80:.2f}"
    else:
        base['Store_Fashion_Profile_thresholds'] = 'default:0.35,0.65'

    base['Store_Fashion_Profile'] = prof
    # Backfill Unisex for Balanced where Gender missing
    if 'Gender' in base.columns:
        gna = base['Gender'].isna() & (base['Store_Fashion_Profile']=='Balanced')
        base.loc[gna, 'Gender'] = 'Unisex'
        base.loc[gna, 'Gender_source'] = base.loc[gna, 'Gender_source'].fillna('balanced_profile_backfill')

    # Cluster_Fashion_Profile (mean ratio per cluster)
    try:
        if 'Cluster_ID' in base.columns and 'Store_Fashion_Ratio_Normalized' in base.columns:
            cl = base.groupby('Cluster_ID')['Store_Fashion_Ratio_Normalized'].mean().reset_index(name='Cluster_Fashion_Ratio')
            def _cprof(v):
                if pd.isna(v): return pd.NA
                if v >= 0.65: return 'Fashion-Heavy'
                if v <= 0.35: return 'Basic-Heavy'
                return 'Balanced'
            cl['Cluster_Fashion_Profile'] = cl['Cluster_Fashion_Ratio'].apply(_cprof)
            base = base.merge(cl, on='Cluster_ID', how='left')
    except Exception:
        pass

    # Enforce single source of cluster truth from Step 24 store→cluster mapping
    try:
        map_path = f"output/store_cluster_mapping_{period_label}.csv"
        if not os.path.exists(map_path):
            # fallback generic mapping
            map_path = "output/store_cluster_mapping.csv" if os.path.exists("output/store_cluster_mapping.csv") else None
        if map_path:
            scmap = pd.read_csv(map_path)
            if 'Store_Code' not in scmap.columns and 'str_code' in scmap.columns:
                scmap['Store_Code'] = scmap['str_code'].astype(str)
            if 'Cluster_ID' not in scmap.columns and 'cluster_id' in scmap.columns:
                scmap = scmap.rename(columns={'cluster_id':'Cluster_ID'})
            sckeep = [c for c in ['Store_Code','Cluster_ID'] if c in scmap.columns]
            scmap = scmap[sckeep].drop_duplicates()
            base = base.merge(scmap, on='Store_Code', how='left', suffixes=(None, '_map'))
            if 'Cluster_ID_map' in base.columns:
                base['Cluster_ID'] = base['Cluster_ID_map'].where(base['Cluster_ID_map'].notna(), base.get('Cluster_ID'))
                base = base.drop(columns=['Cluster_ID_map'])
    except Exception:
        pass

    # Track group ΔQty provenance on rows
    base["Group_ΔQty_source"] = group_qty_source

    # Prefer Step 18 ΔQty when available unless overridden via env flag
    prefer_step14 = bool(os.environ.get('STEP36_PREFER_STEP14_DQTY', ''))
    if ("ΔQty" in group_df.columns) and (not prefer_step14):
        step18_map_cols = [c for c in ["Store_Group_Name", "Target_Style_Tags", "Category", "Subcategory", "ΔQty"] if c in group_df.columns]
        step18_map = group_df[step18_map_cols].copy().rename(columns={"ΔQty": "Group_ΔQty_step18"})
        base = base.merge(step18_map, on=[c for c in ["Store_Group_Name", "Target_Style_Tags", "Category", "Subcategory"] if c in step18_map.columns], how="left")
        # If step18 value present, override and set source
        has_step18 = base["Group_ΔQty_step18"].notna()
        base.loc[has_step18, "Group_ΔQty"] = base.loc[has_step18, "Group_ΔQty_step18"]
        base.loc[has_step18, "Group_ΔQty_source"] = "step18"
        # Record mismatches between existing and step18 before override
        if "Group_ΔQty_step18" in base.columns:
            comp_step18 = base[[c for c in ["Store_Group_Name", "Target_Style_Tags", "Category", "Subcategory", "Group_ΔQty", "Group_ΔQty_step18"] if c in base.columns]].copy()
            mask_both = comp_step18["Group_ΔQty"].notna() & comp_step18["Group_ΔQty_step18"].notna()
            mism = comp_step18[mask_both & (comp_step18["Group_ΔQty"].round(6) != comp_step18["Group_ΔQty_step18"].round(6))]
            if not mism.empty:
                mpath = os.path.join("output", f"group_dqty_step18_mismatch_{period_label}_{out_ts}.csv")
                mism.to_csv(mpath, index=False)
                log(f"⚠️ Step18 ΔQty mismatches: {len(mism)} rows -> {mpath}")
        # Drop helper column
        if "Group_ΔQty_step18" in base.columns:
            base = base.drop(columns=["Group_ΔQty_step18"])

        # Backfill Gender from percentage columns if available (prefer upstream attribution)
        try:
            # Use women/men/unisex percentage columns when present
            perc_cols = [
                "women_percentage",
                "men_percentage",
                "unisex_percentage",
                "women_percentage_ff14",
                "men_percentage_ff14",
                "unisex_percentage_ff14",
            ]
            present = [c for c in perc_cols if c in base.columns]
            if present and "Gender" in base.columns:
                # Consolidate percentage signals
                def _pick_gender(row: pd.Series) -> Optional[str]:
                    vals = {
                        "Women": max(row.get("women_percentage", pd.NA), row.get("women_percentage_ff14", pd.NA)),
                        "Men": max(row.get("men_percentage", pd.NA), row.get("men_percentage_ff14", pd.NA)),
                        "Unisex": max(row.get("unisex_percentage", pd.NA), row.get("unisex_percentage_ff14", pd.NA)),
                    }
                    try:
                        # Choose the label with the highest share if it is reasonably confident
                        label = max(vals, key=lambda k: (vals[k] if pd.notna(vals[k]) else -1))
                        score = vals[label]
                        if pd.notna(score) and float(score) >= 0.55:
                            return label
                    except Exception:
                        return None
                    return None

                missing_gender = base["Gender"].isna() | (base["Gender"].astype(str).str.strip() == "")
                if missing_gender.any():
                    inferred = base.loc[missing_gender].apply(_pick_gender, axis=1)
                    base.loc[missing_gender & inferred.notna(), "Gender"] = inferred[inferred.notna()]
                    # Track provenance
                    if "Gender_source" in base.columns:
                        base.loc[missing_gender & inferred.notna(), "Gender_source"] = base.loc[missing_gender & inferred.notna(), "Gender_source"].astype(str).replace({"nan": ""}) + "+percentage_backfill"
        except Exception:
            pass

        # Backfill Gender from Subcategory/Category text when still missing
        try:
            if "Gender" in base.columns:
                def _infer_gender_from_text(text: Optional[str]) -> Optional[str]:
                    if pd.isna(text):
                        return None
                    t = str(text).lower()
                    if ("女" in t) or ("women" in t) or ("women's" in t) or ("womens" in t):
                        return "Women"
                    if ("男" in t) or ("men" in t) or ("men's" in t):
                        return "Men"
                    if ("中" in t) or ("unisex" in t):
                        return "Unisex"
                    return None

                missing_gender_mask = base["Gender"].isna() | (base["Gender"].astype(str).str.strip() == "")
                if missing_gender_mask.any():
                    inferred = None
                    if "Subcategory" in base.columns:
                        inferred = base.loc[missing_gender_mask, "Subcategory"].apply(_infer_gender_from_text)
                    if inferred is None and "Category" in base.columns:
                        inferred = base.loc[missing_gender_mask, "Category"].apply(_infer_gender_from_text)
                    if inferred is not None:
                        set_mask = missing_gender_mask & inferred.notna()
                        base.loc[set_mask, "Gender"] = inferred[set_mask]
                        if "Gender_source" in base.columns:
                            base.loc[set_mask, "Gender_source"] = base.loc[set_mask, "Gender_source"].astype(str).replace({"nan": ""}) + "+subcategory_text_backfill"
                        # Recompose tags for affected rows so Gender appears
                        if "Target_Style_Tags" in base.columns:
                            base.loc[set_mask, "Target_Style_Tags"] = base.loc[set_mask].apply(_compose_tags, axis=1)
        except Exception:
            pass

        # Backfill Gender by parsing Target_Style_Tags tokens when still missing
        try:
            if "Gender" in base.columns and "Target_Style_Tags" in base.columns:
                missing_gender_mask = base["Gender"].isna() | (base["Gender"].astype(str).str.strip() == "")
                if missing_gender_mask.any():
                    def _parse_tokens_to_gender(s: Optional[str]) -> Optional[str]:
                        if pd.isna(s):
                            return None
                        txt = str(s).strip()
                        if txt.startswith("[") and txt.endswith("]"):
                            txt = txt[1:-1]
                        tokens = [t.strip().lower() for t in txt.split(',') if t.strip()]
                        for t in tokens:
                            if t in ("women", "女"):
                                return "Women"
                            if t in ("men", "男"):
                                return "Men"
                            if t in ("unisex", "中"):
                                return "Unisex"
                        return None
                    inferred = base.loc[missing_gender_mask, "Target_Style_Tags"].apply(_parse_tokens_to_gender)
                    set_mask = missing_gender_mask & inferred.notna()
                    base.loc[set_mask, "Gender"] = inferred[set_mask]
                    if "Gender_source" in base.columns:
                        base.loc[set_mask, "Gender_source"] = base.loc[set_mask, "Gender_source"].astype(str).replace({"nan": ""}) + "+tags_token_backfill"
                    # Recompose tags for affected rows
                    if "Target_Style_Tags" in base.columns:
                        base.loc[set_mask, "Target_Style_Tags"] = base.loc[set_mask].apply(_compose_tags, axis=1)
        except Exception:
            pass

    # Optional adds-bias rebalancing to ensure actionable positives when overwhelmingly negative
    try:
        ENABLE_ADDS_REBALANCE = bool(os.environ.get('STEP36_ENABLE_ADDS_REBALANCE', ''))
        if not ENABLE_ADDS_REBALANCE:
            raise RuntimeError('disabled')
        # Determine grouping keys consistent with rounding stage
        rebalance_keys = [c for c in ["Store_Group_Name", "Category", "Subcategory"] if c in base.columns]
        if len(rebalance_keys) < 2:
            rebalance_keys = [c for c in ["Store_Group_Name", "Target_Style_Tags"] if c in base.columns]
        grp = base.groupby(rebalance_keys, dropna=False).agg({
            "Group_ΔQty": "first",
            "Sell_Through_Improvement": "mean",
            "Capacity_Utilization": "mean"
        }).reset_index()
        total_groups = len(grp)
        pos_groups = int((grp["Group_ΔQty"] > 0).sum())
        adds_ratio = (pos_groups / total_groups) if total_groups else 1.0
        target_adds_ratio = 0.35
        if adds_ratio < target_adds_ratio and total_groups > 0:
            need = int(max(0, target_adds_ratio * total_groups - pos_groups))
            cand = grp[(grp["Group_ΔQty"] <= 0)].copy()
            cand["Sell_Through_Improvement"] = pd.to_numeric(cand["Sell_Through_Improvement"], errors="coerce")
            cand["Capacity_Utilization"] = pd.to_numeric(cand["Capacity_Utilization"], errors="coerce")
            cand = cand[(cand["Sell_Through_Improvement"] >= 0.08) | (cand["Capacity_Utilization"] <= 0.80)]
            cand = cand.sort_values(["Sell_Through_Improvement", "Capacity_Utilization"], ascending=[False, True])
            promote = cand.head(min(need, 1000)).copy()
            if not promote.empty:
                # Join back and set small positive group delta (+1)
                # scale positive amount by improvement/capacity: base 2, +1 if imp>=0.15, +1 if cu<=0.70
                promote["__pos_amount__"] = 2
                promote.loc[promote["Sell_Through_Improvement"] >= 0.15, "__pos_amount__"] += 1
                promote.loc[promote["Capacity_Utilization"] <= 0.70, "__pos_amount__"] += 1
                prom = promote[rebalance_keys + ["__pos_amount__"]].copy()
                prom["__rb_flag__"] = True
                base = base.merge(prom, on=rebalance_keys, how="left")
                mask = base.get("__rb_flag__", False) == True
                base.loc[mask, "Group_ΔQty"] = base.loc[mask, "Group_ΔQty"].where(base.loc[mask, "Group_ΔQty"] > 0, base.loc[mask, "__pos_amount__"].fillna(1))
                base.loc[mask, "Group_ΔQty_source"] = base.loc[mask, "Group_ΔQty_source"].astype(str).where(base.loc[mask, "Group_ΔQty_source"].notna(), "")
                base.loc[mask, "Group_ΔQty_source"] = base.loc[mask, "Group_ΔQty_source"].replace({"nan": ""}) + "+adds_bias"
                if "__rb_flag__" in base.columns or "__pos_amount__" in base.columns:
                    base = base.drop(columns=[c for c in ["__rb_flag__","__pos_amount__"] if c in base.columns])
                # Write a small report for transparency
                try:
                    out_base = f"output/unified_delivery_{period_label}_{out_ts}"
                    rb_path = out_base + "_adds_rebalance_summary.md"
                    with open(rb_path, 'w') as f:
                        f.write(f"Adds-bias rebalancing applied: +{len(promote)} groups promoted to positive. Adds ratio {adds_ratio:.3f} -> >= {target_adds_ratio:.3f}\n")
                except Exception:
                    pass
    except Exception as e:
        log(f"ℹ️ Adds-bias rebalancing skipped: {e}")

    # Rounding allocations to integer per group to reconcile exactly
    if "Group_ΔQty" in base.columns and "Allocated_ΔQty" in base.columns:
        # Prefer group-by including Category/Subcategory to align with Step 18 granularity
        group_keys = [c for c in ["Store_Group_Name", "Category", "Subcategory"] if c in base.columns]
        if len(group_keys) < 2:
            group_keys = [c for c in ["Store_Group_Name", "Target_Style_Tags"] if c in base.columns]
        rounded_list: List[pd.Series] = []
        for keys, part in base.groupby(group_keys, dropna=False):
            group_qty = part["Group_ΔQty"].iloc[0]
            rounded = _largest_remainder_round(part, "Allocated_ΔQty", group_qty)
            rounded.index = part.index
            rounded_list.append(rounded)
        if rounded_list:
            base["Allocated_ΔQty_Rounded"] = pd.concat(rounded_list).sort_index()
        else:
            base["Allocated_ΔQty_Rounded"] = base["Allocated_ΔQty"].round().astype(int)
        # Post-adjustment to guarantee exact group reconciliation
        try:
            import numpy as _np
            group_keys = [c for c in ["Store_Group_Name", "Category", "Subcategory"] if c in base.columns]
            if group_keys:
                for keys, part_idx in base.groupby(group_keys, dropna=False).groups.items():
                    idx = list(part_idx)
                    gqty = base.loc[idx, "Group_ΔQty"].iloc[0]
                    target = int(round(float(gqty)))
                    cur_sum = int(_np.nansum(base.loc[idx, "Allocated_ΔQty_Rounded"].astype(float)))
                    delta = target - cur_sum
                    if delta == 0:
                        continue
                    # Priority by fractional part of raw allocation
                    frac = (base.loc[idx, "Allocated_ΔQty"].astype(float) - _np.floor(base.loc[idx, "Allocated_ΔQty"].astype(float))).fillna(0.0)
                    order = frac.sort_values(ascending=False).index.tolist() if delta > 0 else frac.sort_values(ascending=True).index.tolist()
                    take = order[:abs(delta)]
                    if delta > 0:
                        base.loc[take, "Allocated_ΔQty_Rounded"] = base.loc[take, "Allocated_ΔQty_Rounded"].astype(int) + 1
                    else:
                        base.loc[take, "Allocated_ΔQty_Rounded"] = base.loc[take, "Allocated_ΔQty_Rounded"].astype(int) - 1
        except Exception:
            pass
    else:
        base["Allocated_ΔQty_Rounded"] = base.get("Allocated_ΔQty", pd.Series(dtype=float)).round().astype(int)

    # Priority score (normalized component sum when fields present)
    for col in [
        "Expected_Benefit",
        "Confidence_Score",
        "Sell_Through_Improvement",
        "Capacity_Utilization",
    ]:
        if col not in base.columns:
            base[col] = pd.NA

    def _norm(s: pd.Series) -> pd.Series:
        s = pd.to_numeric(s, errors="coerce")
        if s.notna().sum() == 0:
            return pd.Series([pd.NA] * len(s))
        mn, mx = s.min(), s.max()
        if pd.isna(mn) or pd.isna(mx) or mx == mn:
            return pd.Series([0.5] * len(s))
        return (s - mn) / (mx - mn)

    eb = _norm(base["Expected_Benefit"])
    cs = _norm(base["Confidence_Score"])
    ts = _norm(base["Sell_Through_Improvement"])
    su = 1 - _norm(base["Capacity_Utilization"])  # lower utilization → higher suitability
    base["Priority_Score"] = 0.45 * eb.fillna(0.5) + 0.25 * cs.fillna(0.5) + 0.20 * ts.fillna(0.5) + 0.10 * su.fillna(0.5)

    # Minimal gap highlights when available
    if not gap_df.empty:
        gap_keep = [
            c for c in [
                "cluster_id",
                "category",
                "subcategory",
                "gap_intensity",
                "coverage_index",
                "priority_index",
            ] if c in gap_df.columns
        ]
        g = gap_df[gap_keep].copy()
        g = g.rename(columns={
            "cluster_id": "Cluster_ID",
            "category": "Category",
            "subcategory": "Subcategory",
            "gap_intensity": "Gap_Intensity",
            "coverage_index": "Coverage_Index",
            "priority_index": "Priority_Index",
        })
        on_cols = [c for c in ["Cluster_ID", "Category", "Subcategory"] if c in base.columns and c in g.columns]
        if on_cols:
            base = base.merge(g, on=on_cols, how="left")

    # Coalesce Cluster_ID and Cluster_Name from all sources into a single set and drop dupes
    cluster_sources: List[str] = [
        c for c in base.columns if c.lower() in ("cluster_id", "cluster_id_alloc", "cluster_id_grp") or c.endswith("cluster_id")
    ]
    if cluster_sources:
        # pick first non-null across columns
        def _first_non_null(row):
            for c in cluster_sources:
                v = row.get(c)
                if pd.notna(v):
                    return v
            return pd.NA
        base["Cluster_ID"] = base.apply(_first_non_null, axis=1)
        # try cast to int safely
        try:
            base["Cluster_ID"] = pd.to_numeric(base["Cluster_ID"], errors="coerce").astype("Int64")
        except Exception:
            pass
        drop_cols = [c for c in cluster_sources if c != "Cluster_ID"]
        base = base.drop(columns=[c for c in drop_cols if c in base.columns])

    # If Cluster_Name/Operational_Tag/Temperature_Zone missing, prefer Step 24 labels
    if not labels_df.empty and "Cluster_ID" in base.columns:
        lab_cols_map = {
            "cluster_id": "Cluster_ID",
            "cluster_name": "Cluster_Name",
            "operational_tag": "Operational_Tag_Label",
            "temperature_zone": "Temperature_Zone_Label",
        }
        lab_map = labels_df.rename(columns={k: v for k, v in lab_cols_map.items() if k in labels_df.columns})
        use_cols = [c for c in ["Cluster_ID", "Cluster_Name", "Operational_Tag_Label", "Temperature_Zone_Label"] if c in lab_map.columns]
        lab_map = lab_map[use_cols].drop_duplicates()
        base = base.merge(lab_map, on="Cluster_ID", how="left")
        # Fill fields preferring Step 24 labels when base is missing
        if "Cluster_Name" in base.columns and "Cluster_Name_y" in base.columns:
            base["Cluster_Name"] = base["Cluster_Name_x"].fillna(base["Cluster_Name_y"])
            base = base.drop(columns=[c for c in ["Cluster_Name_x", "Cluster_Name_y"] if c in base.columns])
        if "Operational_Tag" in base.columns and "Operational_Tag_Label" in base.columns:
            base["Operational_Tag"] = base["Operational_Tag"].fillna(base["Operational_Tag_Label"])
        elif "Operational_Tag_Label" in base.columns:
            base["Operational_Tag"] = base["Operational_Tag_Label"]
        if "Temperature_Zone" in base.columns and "Temperature_Zone_Label" in base.columns:
            base["Temperature_Zone"] = base["Temperature_Zone"].fillna(base["Temperature_Zone_Label"])
        elif "Temperature_Zone_Label" in base.columns:
            base["Temperature_Zone"] = base["Temperature_Zone_Label"]
        for c in ["Operational_Tag_Label", "Temperature_Zone_Label"]:
            if c in base.columns:
                base = base.drop(columns=[c])

    # Prefer group-level sell-through columns; keep store-level as separate if present
    if "Sell_Through_Rate" in base.columns and "Current_Sell_Through_Rate" in base.columns:
        base = base.rename(columns={"Sell_Through_Rate": "Store_Sell_Through_Rate"})

    # Fill/fallback sell-through fields when missing
    def _clip01(s: pd.Series) -> pd.Series:
        s = pd.to_numeric(s, errors="coerce")
        return s.clip(lower=0, upper=1)

    # Track ST provenance
    base["Current_ST_source"] = pd.NA
    base["Target_ST_source"] = pd.NA
    base["Improvement_source"] = pd.NA

    if "Current_Sell_Through_Rate" in base.columns:
        cur = pd.to_numeric(base["Current_Sell_Through_Rate"], errors="coerce")
        # mark original (step18) rows
        base.loc[cur.notna(), "Current_ST_source"] = "step18"
        if cur.isna().any():
            if "Store_Sell_Through_Rate" in base.columns:
                base.loc[cur.isna(), "Current_Sell_Through_Rate"] = base.loc[cur.isna(), "Store_Sell_Through_Rate"]
                base.loc[cur.isna(), "Current_ST_source"] = "store_level"
        # default any remaining missing to baseline 0.67
        cur2 = pd.to_numeric(base["Current_Sell_Through_Rate"], errors="coerce")
        if cur2.isna().any():
            base.loc[cur2.isna(), "Current_Sell_Through_Rate"] = 0.67
            base.loc[cur2.isna(), "Current_ST_source"] = "fallback_baseline"
        base["Current_Sell_Through_Rate"] = _clip01(base["Current_Sell_Through_Rate"]) if "Current_Sell_Through_Rate" in base.columns else base.get("Current_Sell_Through_Rate")

    if "Target_Sell_Through_Rate" in base.columns:
        tgt = pd.to_numeric(base["Target_Sell_Through_Rate"], errors="coerce")
        base.loc[tgt.notna(), "Target_ST_source"] = "step18"
        missing_tgt = tgt.isna()
        if missing_tgt.any():
            cur = pd.to_numeric(base.get("Current_Sell_Through_Rate", pd.Series(index=base.index)), errors="coerce").fillna(0.67)
            base.loc[missing_tgt, "Target_Sell_Through_Rate"] = (cur + 0.10).clip(0, 1)
            base.loc[missing_tgt, "Target_ST_source"] = "computed+10pp"
        base["Target_Sell_Through_Rate"] = _clip01(base["Target_Sell_Through_Rate"]) if "Target_Sell_Through_Rate" in base.columns else base.get("Target_Sell_Through_Rate")

        # Cap Target ST by historical percentile when historical data exists
        # Historical candidates: fraction or percent; fallback to store-level ST
        hist_frac = None
        if "Historical_ST_Frac" in base.columns:
            hist_frac = pd.to_numeric(base["Historical_ST_Frac"], errors="coerce")
        elif "Historical_ST_Pct" in base.columns:
            hist_frac = pd.to_numeric(base["Historical_ST_Pct"], errors="coerce") / 100.0
        elif "Historical_Sell_Through_Rate" in base.columns:
            # This field (from Step 14) is percent
            hist_frac = pd.to_numeric(base["Historical_Sell_Through_Rate"], errors="coerce") / 100.0
        elif "Store_Sell_Through_Rate" in base.columns:
            hist_frac = pd.to_numeric(base["Store_Sell_Through_Rate"], errors="coerce")

        if hist_frac is not None:
            # Compute global p95 cap from available historical distribution
            try:
                cap_p = 0.95
                cap_val = float(hist_frac.dropna().quantile(cap_p)) if hist_frac.dropna().size > 0 else 0.95
            except Exception:
                cap_p, cap_val = 0.95, 0.95

            tgt_before = pd.to_numeric(base["Target_Sell_Through_Rate"], errors="coerce")
            over_cap = tgt_before > cap_val
            if over_cap.any():
                base["Target_ST_cap_percentile"] = cap_p
                base["Target_ST_cap_value"] = cap_val
                base["Target_ST_capped_flag"] = False
                base.loc[over_cap, "Target_Sell_Through_Rate"] = cap_val
                base.loc[over_cap, "Target_ST_capped_flag"] = True
                # Preserve original source but annotate capping
                base.loc[over_cap & base["Target_ST_source"].notna(), "Target_ST_source"] = base.loc[over_cap, "Target_ST_source"].astype(str) + "+capped_p95_hist"
                base.loc[over_cap & base["Target_ST_source"].isna(), "Target_ST_source"] = "capped_p95_hist"
            else:
                base["Target_ST_cap_percentile"] = cap_p
                base["Target_ST_cap_value"] = cap_val
                base["Target_ST_capped_flag"] = False

    if "Sell_Through_Improvement" in base.columns:
        imp0 = pd.to_numeric(base["Sell_Through_Improvement"], errors="coerce")
        base.loc[imp0.notna(), "Improvement_source"] = "step18"
        # Ensure series context for robust fill and clipping
        cur3 = pd.to_numeric(base.get("Current_Sell_Through_Rate", pd.Series(index=base.index)), errors="coerce")
        cur3 = cur3.fillna(0.67)
        tgt3 = pd.to_numeric(base.get("Target_Sell_Through_Rate", pd.Series(index=base.index)), errors="coerce")
        tgt3 = tgt3.fillna((cur3 + 0.10).clip(0,1))
        imp = (tgt3 - cur3).clip(-1, 1)
        # replace only where original is na
        base.loc[imp0.isna(), "Sell_Through_Improvement"] = imp.loc[imp0.isna()]
        base.loc[imp0.isna(), "Improvement_source"] = "computed_target_minus_current"

    # Confidence_Score fallback
    if "Confidence_Score" in base.columns:
        cs = pd.to_numeric(base["Confidence_Score"], errors="coerce")
        base["Confidence_Score_source"] = pd.NA
        base.loc[cs.notna(), "Confidence_Score_source"] = "step18"
        need = cs.isna()
        if need.any():
            eb = _norm(base.get("Expected_Benefit", pd.Series(index=base.index)))
            sti = _norm(base.get("Sell_Through_Improvement", pd.Series(index=base.index)).abs())
            cu = _norm(base.get("Capacity_Utilization", pd.Series(index=base.index)))
            fallback = (0.4 * eb.fillna(0.5) + 0.3 * sti.fillna(0.5) + 0.3 * (1 - cu.fillna(0.5))).clip(0, 1)
            base.loc[need, "Confidence_Score"] = fallback.loc[need]
            base.loc[need, "Confidence_Score_source"] = "composite_fallback"

    # Validated views and range flags (do not alter raw fields)
    def _flag_range(series: pd.Series, lo: float, hi: float, name: str) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce")
        flag = pd.Series(index=s.index, dtype=object)
        flag[:] = pd.NA
        flag = flag.where(~s.notna(), other='ok')
        flag = flag.mask((s.notna()) & (s < lo), 'low')
        flag = flag.mask((s.notna()) & (s > hi), 'high')
        return flag

    if "Expected_Benefit" in base.columns:
        eb = pd.to_numeric(base["Expected_Benefit"], errors="coerce")
        base["Expected_Benefit_valid"] = eb.clip(lower=0)
        base["Expected_Benefit_range_flag"] = _flag_range(eb, 0.0, 1e12, "Expected_Benefit")

    if "Current_Sell_Through_Rate" in base.columns:
        cs = pd.to_numeric(base["Current_Sell_Through_Rate"], errors="coerce")
        base["Current_Sell_Through_Rate_valid"] = cs.clip(lower=0, upper=1)
        base["Current_ST_range_flag"] = _flag_range(cs, 0.0, 1.0, "Current_ST")

    if "Target_Sell_Through_Rate" in base.columns:
        ts = pd.to_numeric(base["Target_Sell_Through_Rate"], errors="coerce")
        base["Target_Sell_Through_Rate_valid"] = ts.clip(lower=0, upper=1)
        base["Target_ST_range_flag"] = _flag_range(ts, 0.0, 1.0, "Target_ST")

    if "Sell_Through_Improvement" in base.columns:
        si = pd.to_numeric(base["Sell_Through_Improvement"], errors="coerce")
        base["Sell_Through_Improvement_valid"] = si.clip(lower=-1, upper=1)
        base["ST_Improvement_range_flag"] = _flag_range(si, -1.0, 1.0, "ST_Improvement")

    if "Capacity_Utilization" in base.columns:
        cu = pd.to_numeric(base["Capacity_Utilization"], errors="coerce")
        base["Capacity_Utilization_valid"] = cu.clip(lower=0, upper=1.2)
        base["Capacity_range_flag"] = _flag_range(cu, 0.0, 1.2, "Capacity_Utilization")

    # Recompute sell-through improvement strictly as Target minus Current, then recalibrate Growth_Potential
    if all(c in base.columns for c in ["Current_Sell_Through_Rate","Target_Sell_Through_Rate","Sell_Through_Improvement"]):
        cur = pd.to_numeric(base["Current_Sell_Through_Rate"], errors='coerce').clip(lower=0, upper=1)
        tgt = pd.to_numeric(base["Target_Sell_Through_Rate"], errors='coerce').clip(lower=0, upper=1)
        imp = (tgt - cur).clip(lower=-1, upper=1)
        base["Current_Sell_Through_Rate"] = cur
        base["Target_Sell_Through_Rate"] = tgt
        base["Sell_Through_Improvement"] = imp
        # Add reasons: capping or computed+10pp
        if "Sell_Through_Improvement_source" in base.columns:
            base["Sell_Through_Improvement_source"] = 'recomputed_target_minus_current'
        if "Target_ST_capped_flag" in base.columns:
            capped = base["Target_ST_capped_flag"] == True
            base.loc[capped, "Improvement_source"] = base.loc[capped, "Improvement_source"].astype(str).where(base.loc[capped, "Improvement_source"].notna(), "")
            base.loc[capped, "Improvement_source"] = base.loc[capped, "Improvement_source"].replace({"nan": ""}) + ("+target_capped_p95_hist")
    # Validated/clipped variants
    if "Sell_Through_Improvement" in base.columns:
        si = pd.to_numeric(base["Sell_Through_Improvement"], errors="coerce")
        base["Sell_Through_Improvement_valid"] = si.clip(lower=-1, upper=1)
    # Growth_Potential recalibration via quantile bins and write distribution report
    if "Sell_Through_Improvement" in base.columns and "Capacity_Utilization" in base.columns:
        imp_series = pd.to_numeric(base['Sell_Through_Improvement'], errors='coerce')
        cu_series = pd.to_numeric(base['Capacity_Utilization'], errors='coerce')

        # Compute robust quantile thresholds
        def _q(s: pd.Series, qs):
            s2 = s.dropna()
            if s2.empty:
                return {q: None for q in qs}
            return {q: float(s2.quantile(q)) for q in qs}

        imp_qs = _q(imp_series, [0.2, 0.5, 0.8])
        cu_qs = _q(cu_series, [0.3, 0.5, 0.9])

        def _gpq(row):
            impv = row.get('Sell_Through_Improvement')
            cuv = row.get('Capacity_Utilization')
            try:
                impv = float(impv)
                cuv = float(cuv)
            except Exception:
                return 'Maintain'
            # Quantile-based rules
            if imp_qs[0.8] is not None and cu_qs[0.5] is not None and (impv >= imp_qs[0.8]) and (cuv <= cu_qs[0.5]):
                return 'High-Growth'
            if imp_qs[0.5] is not None and (impv >= imp_qs[0.5]):
                return 'Growth-Ready'
            if cu_qs[0.3] is not None and (cuv <= cu_qs[0.3]):
                return 'Growth-Ready'
            if cu_qs[0.9] is not None and imp_qs[0.2] is not None and (cuv >= cu_qs[0.9]) and (impv < imp_qs[0.2]):
                return 'Constrained'
            return 'Maintain'

        base['Growth_Potential'] = base.apply(_gpq, axis=1)
        base['Growth_Potential_source'] = 'quantile_recalibration'

        # Write distribution report
        try:
            gp_counts = base['Growth_Potential'].value_counts(dropna=False).to_dict()
            out_base = f"output/unified_delivery_{period_label}_{out_ts}"
            gp_report = out_base + "_growth_distribution.md"
            lines = []
            lines.append(f"# Growth Potential Distribution — {period_label}")
            lines.append("")
            lines.append("## Quantile thresholds")
            lines.append(f"- imp_q20={imp_qs[0.2]:.4f} imp_q50={imp_qs[0.5]:.4f} imp_q80={imp_qs[0.8]:.4f}" if imp_qs[0.2] is not None else "- insufficient data for improvement quantiles")
            lines.append(f"- cu_q30={cu_qs[0.3]:.4f} cu_q50={cu_qs[0.5]:.4f} cu_q90={cu_qs[0.9]:.4f}" if cu_qs[0.3] is not None else "- insufficient data for capacity quantiles")
            lines.append("")
            lines.append("## Category counts")
            for k, v in gp_counts.items():
                lines.append(f"- {k}: {v}")
            with open(gp_report, 'w') as f:
                f.write("\n".join(lines))
            log(f"✅ Wrote Growth Potential distribution: {gp_report}")
        except Exception as e:
            log(f"⚠️ Could not write growth distribution report: {e}")

    # Derive Action and simple Instruction for retailer-ready guidance
    try:
        if "Allocated_ΔQty_Rounded" in base.columns:
            def _action(v):
                try:
                    if v > 0:
                        return "Add"
                    if v < 0:
                        return "Reduce"
                    return "No-Change"
                except Exception:
                    return pd.NA
            base["Action"] = base["Allocated_ΔQty_Rounded"].apply(_action)
        if all(c in base.columns for c in ["Action","Allocated_ΔQty_Rounded"]):
            def _instr(row):
                try:
                    act = row.get("Action") or row.get("Allocation_Action") or "Allocate"
                    qty = int(pd.to_numeric(row.get("Target_SPU_Quantity"), errors="coerce").fillna(0)) if isinstance(row.get("Target_SPU_Quantity"), pd.Series) else row.get("Target_SPU_Quantity")
                    cat = row.get("Category") or "Category"
                    sub = row.get("Subcategory") or "Subcategory"
                    loc = row.get("Location") or row.get("Display_Location") or "Front/Back"
                    sn = row.get("Season") or row.get("Planning_Season") or "Season"
                    gd = row.get("Gender") or "Gender"
                    return f"{act} {qty} SPUs in {cat}/{sub} ({sn}, {gd}, {loc})"
                except Exception:
                    return pd.NA
            base["Instruction"] = base.apply(_instr, axis=1)
        # Backfill Product_Season from Step 14 compact map on robust keys
        try:
            st14 = None
            # Try common filenames for Step 14 output
            for p in [
                f"output/enhanced_fast_fish_format_{target_yyyymm}{target_period}_unified.csv",
                f"output/enhanced_fast_fish_format_{target_yyyymm}{target_period}.csv",
            ]:
                try:
                    st14 = pd.read_csv(p, low_memory=False)
                    break
                except Exception:
                    continue
            if st14 is not None:
                # Prepare key columns from Step 14 (prefer raw, then parsed)
                def pick_cols(df, name, parsed_name):
                    if name in df.columns:
                        return df[name]
                    if parsed_name in df.columns:
                        return df[parsed_name]
                    return None
                cols = {}
                for name, parsed in [("Category","Parsed_Category"),("Subcategory","Parsed_Subcategory"),("Gender","Parsed_Gender"),("Location","Parsed_Location"),("Target_Style_Tags","Target_Style_Tags")]:
                    s = pick_cols(st14, name, parsed)
                    if s is not None and name in base.columns:
                        cols[name] = s
                # Derive season from Step 14
                if "Parsed_Season" in st14.columns:
                    s14 = st14["Parsed_Season"].apply(_norm_season_en)
                elif "Season" in st14.columns:
                    s14 = st14["Season"].apply(_norm_season_en)
                elif "Target_Style_Tags" in st14.columns:
                    s14 = st14["Target_Style_Tags"].apply(_derive_season_from_tags_en)
                else:
                    s14 = pd.Series("Unknown", index=st14.index)
                if cols:
                    map_df = pd.DataFrame(cols)
                    map_df["Product_Season_s14map"] = s14
                    map_df = map_df.dropna().drop_duplicates()
                    # Hierarchical key sets to maximize matches even when some attrs (e.g., Location) are null
                    key_options = [
                        ["Target_Style_Tags","Category","Subcategory","Gender","Location"],
                        ["Target_Style_Tags","Category","Subcategory","Gender"],
                        ["Target_Style_Tags","Category","Subcategory"],
                        ["Target_Style_Tags","Category"],
                        ["Target_Style_Tags"],
                    ]
                    if 'Product_Season' not in base.columns:
                        base['Product_Season'] = pd.NA
                    if 'Product_Season_source' not in base.columns:
                        base['Product_Season_source'] = 'Unknown'
                    for keys in key_options:
                        join_keys = [k for k in keys if k in map_df.columns and k in base.columns]
                        if len(join_keys) < len(keys):
                            continue
                        # Only attempt if there are still rows to seed
                        need = base['Product_Season'].isna() | (base['Product_Season']=='Unknown') | (base['Product_Season_source']=='Planning_Season')
                        if not need.any():
                            break
                        # Merge a minimal mapping (dedupe by join_keys)
                        mdedup = map_df[join_keys + ["Product_Season_s14map"]].dropna().drop_duplicates(subset=join_keys)
                        if mdedup.empty:
                            continue
                        tmp = base.loc[need, join_keys].merge(mdedup, on=join_keys, how='left')
                        # Align back by index
                        base.loc[need, 'Product_Season_s14map_tmp'] = tmp.get('Product_Season_s14map')
                        mseed = need & base['Product_Season_s14map_tmp'].notna()
                        if mseed.any():
                            base.loc[mseed, 'Product_Season'] = base.loc[mseed, 'Product_Season_s14map_tmp'].apply(_norm_season_en)
                            base.loc[mseed, 'Product_Season_source'] = 'Step14_map'
                        if 'Product_Season_s14map_tmp' in base.columns:
                            base = base.drop(columns=['Product_Season_s14map_tmp'])
                    # If still many unseeded, try aggregated majority season by (Category,Subcategory,Gender) then (Category,Subcategory)
                    try:
                        need = base['Product_Season'].isna() | (base['Product_Season']=='Unknown') | (base['Product_Season_source']=='Planning_Season')
                        if need.any():
                            # Prepare Step14 aggregation
                            s14_df = pd.DataFrame(cols)
                            s14_df['__ps__'] = s14
                            # Helper to mode (majority) ignoring Unknown
                            def mode_non_unknown(g):
                                vals = g[g!='Unknown']
                                if vals.empty:
                                    return 'Unknown'
                                return vals.value_counts().idxmax()
                            # First with Gender if available
                            keys_g = [k for k in ['Category','Subcategory','Gender'] if k in s14_df.columns and k in base.columns]
                            if keys_g:
                                agg_g = s14_df.groupby(keys_g)['__ps__'].apply(mode_non_unknown).reset_index().rename(columns={'__ps__':'Product_Season_s14agg'})
                                tmp = base.loc[need, keys_g].merge(agg_g, on=keys_g, how='left')
                                base.loc[need, 'Product_Season_s14agg_tmp'] = tmp.get('Product_Season_s14agg')
                                mseed = need & base['Product_Season_s14agg_tmp'].notna()
                                if mseed.any():
                                    base.loc[mseed, 'Product_Season'] = base.loc[mseed, 'Product_Season_s14agg_tmp'].apply(_norm_season_en)
                                    base.loc[mseed, 'Product_Season_source'] = 'Step14_agg_cat_sub_g'
                                if 'Product_Season_s14agg_tmp' in base.columns:
                                    base = base.drop(columns=['Product_Season_s14agg_tmp'])
                            # Then fallback to (Category, Subcategory)
                            keys_cs = [k for k in ['Category','Subcategory'] if k in s14_df.columns and k in base.columns]
                            need = base['Product_Season'].isna() | (base['Product_Season']=='Unknown') | (base['Product_Season_source']=='Planning_Season')
                            if keys_cs and need.any():
                                agg_cs = s14_df.groupby(keys_cs)['__ps__'].apply(mode_non_unknown).reset_index().rename(columns={'__ps__':'Product_Season_s14agg'})
                                tmp = base.loc[need, keys_cs].merge(agg_cs, on=keys_cs, how='left')
                                base.loc[need, 'Product_Season_s14agg_tmp'] = tmp.get('Product_Season_s14agg')
                                mseed = need & base['Product_Season_s14agg_tmp'].notna()
                                if mseed.any():
                                    base.loc[mseed, 'Product_Season'] = base.loc[mseed, 'Product_Season_s14agg_tmp'].apply(_norm_season_en)
                                    base.loc[mseed, 'Product_Season_source'] = 'Step14_agg_cat_sub'
                                if 'Product_Season_s14agg_tmp' in base.columns:
                                    base = base.drop(columns=['Product_Season_s14agg_tmp'])
                    except Exception:
                        pass
        except Exception:
            pass
        # Derive Product_Season and source (does not alter existing Season/Planning_Season)
        try:
            # Start from any existing Product_Season carried from group_view/Step14
            if 'Product_Season' in base.columns:
                ps = base['Product_Season'].copy()
            else:
                ps = pd.Series(pd.NA, index=base.index)
            src = base['Product_Season_source'].copy() if 'Product_Season_source' in base.columns else pd.Series('Unknown', index=base.index)
            # Normalize any pre-existing values
            try:
                mask_exist = ps.notna()
                ps.loc[mask_exist] = ps.loc[mask_exist].apply(_norm_season_en)
            except Exception:
                pass
            # Priority: Season_alloc -> Season_grp -> Target_Style_Tags -> Planning_Season -> Season -> Unknown
            if 'Season_alloc' in base.columns and base['Season_alloc'].notna().any():
                mask = (ps.isna() | (ps == 'Unknown')) & base['Season_alloc'].notna()
                ps.loc[mask] = base.loc[mask, 'Season_alloc'].apply(_norm_season_en)
                src.loc[mask] = 'Season_alloc'
            if 'Season_grp' in base.columns and base['Season_grp'].notna().any():
                mask = (ps.isna() | (ps == 'Unknown')) & base['Season_grp'].notna()
                ps.loc[mask] = base.loc[mask, 'Season_grp'].apply(_norm_season_en)
                src.loc[mask] = 'Season_grp'
            if 'Target_Style_Tags' in base.columns:
                mask = (ps.isna() | (ps == 'Unknown')) & base['Target_Style_Tags'].notna()
                ps.loc[mask] = base.loc[mask, 'Target_Style_Tags'].apply(_derive_season_from_tags_en)
                src.loc[mask] = 'Target_Style_Tags'
            if 'Planning_Season' in base.columns and base['Planning_Season'].notna().any():
                mask = (ps.isna() | (ps == 'Unknown')) & base['Planning_Season'].notna()
                ps.loc[mask] = base.loc[mask, 'Planning_Season'].apply(_norm_season_en)
                src.loc[mask] = 'Planning_Season'
            if 'Season' in base.columns and base['Season'].notna().any():
                mask = (ps.isna() | (ps == 'Unknown')) & base['Season'].notna()
                ps.loc[mask] = base.loc[mask, 'Season'].apply(_norm_season_en)
                src.loc[mask] = 'Season'
            # Fill remaining Unknowns explicitly
            ps = ps.fillna('Unknown')
            base['Product_Season'] = ps
            base['Product_Season_source'] = src
        except Exception:
            pass
        # Consolidated tag bundle for quick filtering
        def _bundle(row):
            parts = []
            for k in ["Season","Planning_Season","Gender","Location","Temperature_Band_Simple","Store_Fashion_Profile"]:
                v = row.get(k)
                if pd.notna(v):
                    parts.append(str(v))
            return ", ".join(dict.fromkeys(parts)) if parts else pd.NA
        base["Tag_Bundle"] = base.apply(_bundle, axis=1)
        # Sorting preference: Action (Add, Reduce, No-Change), then Priority_Score desc, then abs(Δ) desc
        if "Action" in base.columns:
            order_map = {"Add": 0, "Reduce": 1, "No-Change": 2}
            base["Action_Order"] = base["Action"].map(order_map).fillna(3)
        if "Priority_Score" not in base.columns:
            base["Priority_Score"] = pd.NA
        base = base.sort_values(by=[c for c in ["Action_Order","Priority_Score","Allocated_ΔQty_Rounded"] if c in base.columns], ascending=[True, False, False], kind="mergesort")
        # Rank within Action by Priority
        if all(c in base.columns for c in ["Action","Priority_Score"]):
            try:
                base["Action_Priority_Rank"] = base.groupby("Action")["Priority_Score"].rank(ascending=False, method="dense")
            except Exception:
                pass
    except Exception:
        pass

    # Final column ordering
    preferred = [
        "Analysis_Year",
        "Analysis_Month",
        "Analysis_Period",
        "Store_Code",
        "Store_Group_Name",
        "Target_Style_Tags",
        "Category",
        "Subcategory",
        "Target_SPU_Quantity",
        "Allocated_ΔQty_Rounded",
        "Allocated_ΔQty",
        "Group_ΔQty",
        "Action",
        "Instruction",
        "Action_Priority_Rank",
        "Tag_Bundle",
        "Expected_Benefit",
        "Confidence_Score",
        "Current_Sell_Through_Rate",
        "Target_Sell_Through_Rate",
        "Sell_Through_Improvement",
        "Store_Sell_Through_Rate",
        "Constraint_Status",
        "Capacity_Utilization",
        "Store_Temperature_Band",
        "Temperature_Band_Simple",
        "Temperature_Band_Detailed",
        "Temperature_Value_C",
        "Cluster_Temp_C_Mean",
        "Cluster_Temp_Quintile",
        "Temperature_Suitability_Graded",
        "Store_Fashion_Profile",
        "Action_Priority",
        "Performance_Tier",
        "Growth_Potential",
        "Risk_Level",
        "Cluster_ID",
        "Cluster_Name",
        "Operational_Tag",
        "Temperature_Zone",
        "Season",
        "Season_source",
        "Gender",
        "Gender_source",
        "Location",
        "Location_source",
        "Planning_Season",
        "Planning_Year",
        "Planning_Period_Label",
        "Data_Based_Rationale",
        "Priority_Score",
        "Historical_Temp_C_Mean",
        "Historical_Temp_C_P5",
        "Historical_Temp_C_P95",
        "Historical_Temp_Band_Detailed",
        "Historical_Temp_Quintile",
        "Temp_Band_Divergence",
    ]
    cols = [c for c in preferred if c in base.columns] + [c for c in base.columns if c not in preferred]
    final_df = base.loc[:, cols].copy()

    # Enforce Target_Style_Tags bracket format and integer allocation for final output
    if "Target_Style_Tags" in final_df.columns:
        def _ensure_brackets(x):
            if pd.isna(x):
                return "[]"
            s = str(x).strip()
            # remove pre-existing brackets to avoid nesting
            if s.startswith("[") and s.endswith("]"):
                s = s[1:-1].strip()
            return f"[{s}]" if s else "[]"
        final_df["Target_Style_Tags"] = final_df["Target_Style_Tags"].apply(_ensure_brackets)
    if "Allocated_ΔQty_Rounded" in final_df.columns:
        try:
            final_df["Allocated_ΔQty_Rounded"] = pd.to_numeric(final_df["Allocated_ΔQty_Rounded"], errors="coerce").round().astype(int)
            # Provide explicit business-facing alias for target quantity
            final_df["Target_SPU_Quantity"] = final_df["Allocated_ΔQty_Rounded"].astype(int)
        except Exception:
            pass
    # Ensure final ordering honors preferred list (including newly added Target_SPU_Quantity)
    preferred_after = [
        "Analysis_Year","Analysis_Month","Analysis_Period","Store_Code","Store_Group_Name",
        "Target_Style_Tags","Category","Subcategory","Target_SPU_Quantity","Allocated_ΔQty_Rounded",
        "Allocated_ΔQty","Group_ΔQty","Action","Instruction","Action_Priority_Rank","Tag_Bundle",
        "Expected_Benefit","Confidence_Score","Current_Sell_Through_Rate","Target_Sell_Through_Rate",
        "Sell_Through_Improvement","Store_Sell_Through_Rate","Constraint_Status","Capacity_Utilization",
        "Store_Temperature_Band","Temperature_Band_Simple","Temperature_Band_Detailed","Temperature_Value_C",
        "Cluster_Temp_C_Mean","Cluster_Temp_Quintile","Temperature_Suitability_Graded","Store_Fashion_Profile",
        "Action_Priority","Performance_Tier","Growth_Potential","Risk_Level","Cluster_ID","Cluster_Name",
        "Operational_Tag","Temperature_Zone","Season","Product_Season","Product_Season_source","Season_source","Gender","Gender_source","Location",
        "Location_source","Planning_Season","Planning_Year","Planning_Period_Label","Data_Based_Rationale",
        "Priority_Score","Historical_Temp_C_Mean","Historical_Temp_C_P5","Historical_Temp_C_P95",
        "Historical_Temp_Band_Detailed","Historical_Temp_Quintile","Temp_Band_Divergence",
    ]
    cols2 = [c for c in preferred_after if c in final_df.columns] + [c for c in final_df.columns if c not in preferred_after]
    final_df = final_df.loc[:, cols2]

    # Attempt to enrich cluster-level output with fashion and weather profiles (best-effort)
    def _enrich_cluster_level(cluster_df: pd.DataFrame) -> pd.DataFrame:
        try:
            # Merge cluster fashion makeup
            path_fm = _latest_from_manifest('step14', 'cluster_fashion_makeup', period_label)
            if path_fm and os.path.exists(path_fm):
                fm_head = pd.read_csv(path_fm, nrows=0)
                fm = pd.read_csv(path_fm)
                cid = next((c for c in fm.columns if c.lower() in ("cluster_id","cluster","clusterid")), None)
                if cid:
                    fm = fm.rename(columns={cid: "Cluster_ID"})
                    fm_cols = [c for c in fm.columns if c in ("Cluster_ID","fashion_ratio","basic_ratio","balanced_ratio","fashion_share","basic_share")]
                    cluster_df = cluster_df.merge(fm[fm_cols].drop_duplicates(), on="Cluster_ID", how="left")
            # Merge cluster weather profile
            path_wp = _latest_from_manifest('step14', 'cluster_weather_profile', period_label)
            if path_wp and os.path.exists(path_wp):
                wp = pd.read_csv(path_wp)
                cid = next((c for c in wp.columns if c.lower() in ("cluster_id","cluster","clusterid")), None)
                if cid:
                    wp = wp.rename(columns={cid: "Cluster_ID"})
                    keep = [c for c in wp.columns if c in ("Cluster_ID","dominant_band","cold_share","warm_share","moderate_share")]
                    cluster_df = cluster_df.merge(wp[keep].drop_duplicates(), on="Cluster_ID", how="left")
        except Exception:
            pass
        return cluster_df

    # Save outputs (DUAL OUTPUT PATTERN)
    out_base = f"output/unified_delivery_{period_label}_{out_ts}"
    os.makedirs("output", exist_ok=True)
    
    # Define both timestamped and generic versions
    timestamped_csv_path = f"{out_base}.csv"
    timestamped_xlsx_path = f"{out_base}.xlsx"
    generic_csv_path = "output/unified_delivery.csv"
    generic_xlsx_path = "output/unified_delivery.xlsx"
    
    # Use timestamped versions for manifest registration
    csv_path = timestamped_csv_path
    xlsx_path = timestamped_xlsx_path
    # Embed period metadata columns required by downstream consumers
    try:
        final_df["period_label"] = period_label
        final_df["target_yyyymm"] = str(yyyymm)
        final_df["target_period"] = str(period)
    except Exception:
        # Safe guard: if final_df is not a DataFrame yet or columns cannot be set, proceed without raising
        pass
    
    # Save with dual output pattern (timestamped + period symlink + generic symlink)
    base_path = "output/unified_delivery"
    timestamped_file, period_file, generic_file = create_output_with_symlinks(
        df=final_df,
        base_path=base_path,
        period_label=period_label
    )
    csv_path = timestamped_file  # Use timestamped file for manifest registration
    log(f"✅ Wrote CSV with dual output pattern: [{len(final_df):,} rows, {len(final_df.columns)} cols]")
    log(f"   Timestamped: {timestamped_file}")
    log(f"   Period: {period_file}")
    log(f"   Generic: {generic_file}")

    # Optional Excel with data dictionary
    xlsx_written: Optional[str] = None
    try:
        import openpyxl  # noqa: F401
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            final_df.to_excel(writer, index=False, sheet_name="Unified Data")
            # Data dictionary
            dict_rows: List[Tuple[str, str]] = [
                ("Analysis_Year", "4-digit year for analysis window (string)"),
                ("Analysis_Month", "2-digit month for analysis window (string, zero-padded)"),
                ("Analysis_Period", "Period within month: 'A' or 'B'"),
                ("Target_SPU_Quantity", "Integer target SPU quantity per store line (alias of Allocated_ΔQty_Rounded)"),
                ("Allocated_ΔQty_Rounded", "Integer store allocation reconciled to Group_ΔQty"),
                ("Allocated_ΔQty", "Raw fractional store allocation from Step 32"),
                ("Group_ΔQty", "Group-level ΔQty from Step 18/14"),
                ("Priority_Score", "Composite score of benefit, confidence, trend, suitability"),
                ("Constraint_Status", "Store constraint status from Step 33"),
                ("Capacity_Utilization", "Store capacity utilization (0..1) from Step 33"),
            ]
            dd = pd.DataFrame(dict_rows, columns=["Column", "Description"])
            dd.to_excel(writer, index=False, sheet_name="Data Dictionary")
        xlsx_written = xlsx_path
        log(f"✅ Wrote timestamped XLSX: {xlsx_path}")
        
        # Also create generic Excel version (for pipeline flow)
        try:
            with pd.ExcelWriter(generic_xlsx_path, engine="openpyxl") as writer:
                final_df.to_excel(writer, index=False, sheet_name="Unified Data")
                # Data dictionary
                dd.to_excel(writer, index=False, sheet_name="Data Dictionary")
            log(f"✅ Wrote generic XLSX: {generic_xlsx_path}")
        except Exception as e2:
            log(f"⚠️ Generic Excel not written ({e2})")
    except Exception as e:
        log(f"⚠️ Excel not written ({e}); CSV generated only")

    # Produce prioritized Top Adds/Reduces (overall and Autumn-only)
    try:
        if all(c in final_df.columns for c in ["Action","Action_Priority_Rank","Allocated_ΔQty_Rounded"]):
            adds = final_df[final_df["Action"] == "Add"].copy()
            adds = adds.sort_values(["Action_Priority_Rank","Allocated_ΔQty_Rounded"], ascending=[True, False])
            reduces = final_df[final_df["Action"] == "Reduce"].copy()
            reduces = reduces.sort_values(["Action_Priority_Rank","Allocated_ΔQty_Rounded"], ascending=[True, True])
            adds_path = f"{out_base}_top_adds.csv"
            red_path = f"{out_base}_top_reduces.csv"
            adds.to_csv(adds_path, index=False)
            reduces.to_csv(red_path, index=False)
            # Autumn-only filters (use Season or Planning_Season)
            def _is_autumn(df):
                s = df.get("Season")
                ps = df.get("Planning_Season")
                mask = pd.Series(False, index=df.index)
                if s is not None:
                    mask = mask | (s.astype(str).str.contains("Autumn|秋", na=False))
                if ps is not None:
                    mask = mask | (ps.astype(str).str.contains("Autumn|秋", na=False))
                return df[mask]
            adds_aut = _is_autumn(adds)
            red_aut = _is_autumn(reduces)
            adds_aut.to_csv(f"{out_base}_top_adds_autumn.csv", index=False)
            red_aut.to_csv(f"{out_base}_top_reduces_autumn.csv", index=False)
    except Exception:
        pass

    # QA validation (group sums, required columns, integer checks, coverage, buffers)
    qa = {"period_label": period_label, "records": int(len(final_df)), "checks": {}, "warnings": [], "errors": []}
    if "Group_ΔQty" in base.columns and "Allocated_ΔQty_Rounded" in base.columns:
        # Reconcile at the same grain as rounding: Store_Group_Name × Category × Subcategory
        recon_keys = [k for k in ["Store_Group_Name","Category","Subcategory"] if k in base.columns]
        grp = base.groupby(recon_keys, dropna=False)
        comp = grp.agg({"Group_ΔQty": "first", "Allocated_ΔQty_Rounded": "sum"}).reset_index()
        # Name the aggregates explicitly for later calculations
        comp = comp.rename(columns={"Group_ΔQty": "group_sum", "Allocated_ΔQty_Rounded": "alloc_sum"})
        comp["match"] = (comp["group_sum"].round().astype(int) == comp["alloc_sum"].astype(int))
        qa_ok = bool(comp["match"].all()) if not comp.empty else True
        mismatches = comp.loc[~comp["match"], :].head(50).to_dict(orient="records")
        qa["checks"]["group_sum_reconciliation"] = {"ok": qa_ok, "mismatch_samples": mismatches}
        if not qa_ok:
            qa["errors"].append("Group sum reconciliation failed for some groups")
    else:
        qa["checks"]["group_sum_reconciliation"] = {"ok": False, "reason": "Required columns missing"}
        qa["errors"].append("Missing columns for group sum reconciliation")

    # Required columns presence
    required_cols = [
        "Analysis_Year",
        "Analysis_Month",
        "Analysis_Period",
        "Store_Code",
        "Store_Group_Name",
        "Target_Style_Tags",
        "Target_SPU_Quantity",
        "Allocated_ΔQty_Rounded",
        "Group_ΔQty",
    ]
    missing_counts = {}
    for c in required_cols:
        if c not in final_df.columns:
            missing_counts[c] = "column_missing"
        else:
            missing_counts[c] = int(final_df[c].isna().sum())
    qa["checks"]["required_columns_missing_counts"] = missing_counts
    if any(v == "column_missing" or (isinstance(v, int) and v > 0) for v in missing_counts.values()):
        qa["warnings"].append("Some required columns are missing or contain nulls")

    # Integer check for Allocated_ΔQty_Rounded
    if "Allocated_ΔQty_Rounded" in final_df.columns:
        try:
            rounded_numeric = pd.to_numeric(final_df["Allocated_ΔQty_Rounded"], errors="coerce")
            int_ok = bool((rounded_numeric.dropna() == rounded_numeric.dropna().round()).all())
            qa["checks"]["allocated_qty_integer_check"] = {"ok": int_ok, "non_integer_count": int((rounded_numeric != rounded_numeric.round()).sum())}
            if not int_ok:
                qa["errors"].append("Allocated_ΔQty_Rounded contains non-integer values")
        except Exception as e:
            qa["checks"]["allocated_qty_integer_check"] = {"ok": False, "error": str(e)}
            qa["errors"].append("Integer check failed for Allocated_ΔQty_Rounded")

    # Consistency check: Target_SPU_Quantity mirrors Allocated_ΔQty_Rounded
    if all(c in final_df.columns for c in ["Target_SPU_Quantity","Allocated_ΔQty_Rounded"]):
        try:
            same = bool((pd.to_numeric(final_df["Target_SPU_Quantity"], errors="coerce") == pd.to_numeric(final_df["Allocated_ΔQty_Rounded"], errors="coerce")).all())
            qa["checks"]["target_qty_consistency"] = {"ok": same}
            if not same:
                qa["warnings"].append("Target_SPU_Quantity differs from Allocated_ΔQty_Rounded on some rows")
        except Exception as e:
            qa["checks"]["target_qty_consistency"] = {"ok": False, "error": str(e)}

    # Duplicate check on unique grain (Store_Code, Store_Group_Name, Target_Style_Tags)
    dup_key = [c for c in ["Store_Code", "Store_Group_Name", "Target_Style_Tags"] if c in final_df.columns]
    if len(dup_key) == 3:
        dup_mask = final_df.duplicated(subset=dup_key, keep=False)
        dup_count = int(dup_mask.sum())
        qa["checks"]["duplicate_on_store_line_key"] = {"duplicate_rows": dup_count}
        if dup_count > 0:
            qa["warnings"].append("Duplicates detected on (Store_Code, Store_Group_Name, Target_Style_Tags)")

    # Write mismatch report CSV for group reconciliation
    mismatch_path = f"{out_base}_group_reconciliation_mismatches.csv"
    if "Group_ΔQty" in base.columns and "Allocated_ΔQty_Rounded" in base.columns:
        if not comp.empty:
            mismatch_path = f"{out_base}_reconciliation_mismatches.csv"
            comp.loc[~comp["match"], :].to_csv(mismatch_path, index=False)
            log(f"⚠️ Group reconciliation mismatches written: {mismatch_path}")

        # ±20% buffer validation at group level
        try:
            comp2 = comp.copy()
            comp2["abs_diff"] = (comp2["alloc_sum"].fillna(0) - comp2["group_sum"].fillna(0)).abs()
            comp2["allowed"] = (comp2["group_sum"].abs() * 0.20).fillna(0)
            comp2["within_20pct"] = comp2["abs_diff"] <= comp2["allowed"]
            pct_ok = float(comp2["within_20pct"].mean()) if len(comp2) else 1.0
            qa["checks"]["buffer_within_20pct_ratio"] = round(pct_ok, 4)
            if pct_ok < 1.0:
                qa["warnings"].append("Some group allocations deviate beyond ±20% buffer")
        except Exception:
            qa["warnings"].append("Buffer ±20% validation could not be computed")

    # Coverage checks (Temperature_Zone and capacity)
    try:
        if "Temperature_Zone" in final_df.columns:
            tz_cov = float(final_df["Temperature_Zone"].notna().mean())
            qa["checks"]["temperature_zone_coverage"] = round(tz_cov, 4)
            if tz_cov < 0.8:
                qa["warnings"].append("Temperature_Zone coverage below 80%")
    except Exception:
        qa["warnings"].append("Failed to compute Temperature_Zone coverage")
    try:
        cap_cols = [c for c in ["Estimated_Rack_Capacity", "Store_Capacity", "Capacity_Utilization"] if c in final_df.columns]
        for c in cap_cols:
            cov = float(final_df[c].notna().mean())
            qa["checks"][f"coverage_{c}"] = round(cov, 4)
            if cov < 0.8:
                qa["warnings"].append(f"{c} coverage below 80%")
    except Exception:
        qa["warnings"].append("Failed to compute capacity coverage")

    # Season distribution snapshot for validation
    try:
        dist = {}
        if "Season" in final_df.columns:
            vc = final_df["Season"].astype(str).fillna("(NaN)").value_counts().to_dict()
            dist["Season"] = vc
        if "Product_Season" in final_df.columns:
            pvc = final_df["Product_Season"].astype(str).fillna("(NaN)").value_counts().to_dict()
            dist["Product_Season"] = pvc
        if "Planning_Season" in final_df.columns:
            pvc = final_df["Planning_Season"].astype(str).fillna("(NaN)").value_counts().to_dict()
            dist["Planning_Season"] = pvc
        if dist:
            qa["checks"]["season_distribution"] = dist
    except Exception:
        qa["warnings"].append("Failed to compute season distribution")

    # Compact summary (MD and JSON) with pivots: Season, Gender, Location, Temperature_Zone, Category
    try:
        piv = {}
        def _vc(col):
            if col in final_df.columns:
                s = final_df[col].astype(str).fillna("(NaN)")
                return s.value_counts().head(50).to_dict()
            return {}
        for col in ["Planning_Season", "Season", "Product_Season", "Gender", "Location", "Temperature_Zone", "Category", "Subcategory"]:
            piv[col] = _vc(col)
        summary_json_path = f"{out_base}_summary.json"
        with open(summary_json_path, "w", encoding="utf-8") as f:
            json.dump({"period_label": period_label, "records": int(len(final_df)), "pivots": piv}, f, indent=2, ensure_ascii=False)
        # Markdown summary
        summary_md_path = f"{out_base}_summary.md"
        with open(summary_md_path, "w", encoding="utf-8") as f:
            f.write(f"# Unified Delivery Summary for {period_label}\n\n")
            f.write(f"Total Records: {len(final_df):,}\n\n")
            for col, vc in piv.items():
                f.write(f"## {col}\n\n")
                for k, v in vc.items():
                    f.write(f"- {k}: {v}\n")
                f.write("\n")
        log(f"✅ Wrote summary: {summary_md_path}")
    except Exception as e:
        qa["warnings"].append(f"Failed to write summary: {e}")

    qa_path = f"{out_base}_validation.json"
    with open(qa_path, "w", encoding="utf-8") as f:
        json.dump(qa, f, indent=2, ensure_ascii=False)
    log(f"🧪 QA written: {qa_path}")

    # Additionally, produce cluster-level summary output (with tags if available)
    cluster_csv = None
    if "Cluster_ID" in final_df.columns:
        # Group by stable cluster descriptors only to avoid duplicated rows
        cluster_group_cols = [c for c in ["Cluster_ID", "Cluster_Name", "Operational_Tag", "Temperature_Zone"] if c in final_df.columns]
        agg_spec = {
            "Allocated_ΔQty_Rounded": "sum",
            "Allocated_ΔQty": "sum",
            "Group_ΔQty": "sum",
            "Capacity_Utilization": "mean",
            "Expected_Benefit": "sum",
            "Confidence_Score": "mean",
            "Current_Sell_Through_Rate": "mean",
            "Target_Sell_Through_Rate": "mean",
            "Sell_Through_Improvement": "mean",
        }
        exist_agg = {k: v for k, v in agg_spec.items() if k in final_df.columns}
        # Add cluster fashion aggregations if present
        if 'Cluster_Fashion_Ratio' in final_df.columns:
            exist_agg['Cluster_Fashion_Ratio'] = 'mean'
        if 'Cluster_Fashion_Profile' in final_df.columns:
            exist_agg['Cluster_Fashion_Profile'] = (lambda x: x.mode().iloc[0] if len(x.mode())>0 else pd.NA)
        cluster_df = final_df.groupby(cluster_group_cols, dropna=False).agg(exist_agg).reset_index()
        # Derive Cluster_Fashion_Profile from Cluster_Fashion_Ratio if available
        try:
            if 'Cluster_Fashion_Ratio' in cluster_df.columns:
                def _cprof(v: float) -> object:
                    try:
                        v = float(v)
                    except Exception:
                        return pd.NA
                    if v >= 0.65:
                        return 'Fashion-Heavy'
                    if v <= 0.35:
                        return 'Basic-Heavy'
                    return 'Balanced'
                cluster_df['Cluster_Fashion_Profile'] = cluster_df['Cluster_Fashion_Ratio'].apply(_cprof)
        except Exception:
            pass
        cluster_df = _enrich_cluster_level(cluster_df)
        # Consolidate cluster fashion profile into a single column
        try:
            # Always compute from ratio if available (authoritative)
            if 'Cluster_Fashion_Ratio' in cluster_df.columns:
                def _cprof2(v):
                    try:
                        v = float(v)
                    except Exception:
                        return pd.NA
                    if v >= 0.65:
                        return 'Fashion-Heavy'
                    if v <= 0.35:
                        return 'Basic-Heavy'
                    return 'Balanced'
                cluster_df['Cluster_Fashion_Profile'] = cluster_df['Cluster_Fashion_Ratio'].apply(_cprof2)
            # Drop any suffix duplicates (_x/_y)
            drop_list = [c for c in cluster_df.columns if c.startswith('Cluster_Fashion_Profile_')]
            if drop_list:
                cluster_df = cluster_df.drop(columns=drop_list, errors='ignore')
        except Exception:
            pass
        # Merge cluster fashion makeup if available
        try:
            cfm_path = f"output/cluster_fashion_makeup_{period_label}.csv"
            if not os.path.exists(cfm_path):
                cfm_path = "output/cluster_fashion_makeup.csv" if os.path.exists("output/cluster_fashion_makeup.csv") else None
            if cfm_path:
                cfm = pd.read_csv(cfm_path)
                # Normalize to Cluster_ID and derive Cluster_Fashion_Profile by majority share
                if 'Cluster_ID' not in cfm.columns:
                    if 'cluster_id' in cfm.columns:
                        cfm = cfm.rename(columns={'cluster_id':'Cluster_ID'})
                    elif 'Cluster' in cfm.columns:
                        cfm = cfm.rename(columns={'Cluster':'Cluster_ID'})
                # compute profile based on men/women/unisex percentages if present
                if all(col in cfm.columns for col in ['men_percentage','women_percentage','unisex_percentage']):
                    def prof(row):
                        vals = {
                            'Men': row.get('men_percentage', 0),
                            'Women': row.get('women_percentage', 0),
                            'Unisex': row.get('unisex_percentage', 0)
                        }
                        return max(vals, key=vals.get)
                    cfm['Cluster_Fashion_Profile'] = cfm.apply(prof, axis=1)
                # Keep minimal mapping
                cfm = cfm[[c for c in ['Cluster_ID','Cluster_Fashion_Profile'] if c in cfm.columns]].drop_duplicates()
                if 'Cluster_ID' in cfm.columns and 'Cluster_Fashion_Profile' in cfm.columns:
                    cluster_df = cluster_df.merge(cfm, on='Cluster_ID', how='left')
                    # Resolve duplicates: prefer computed from ratio; fillna from mapping; drop suffixes
                    try:
                        # Identify possible columns
                        has_canon = 'Cluster_Fashion_Profile' in cluster_df.columns
                        cfp_x = 'Cluster_Fashion_Profile_x' if 'Cluster_Fashion_Profile_x' in cluster_df.columns else None
                        cfp_y = 'Cluster_Fashion_Profile_y' if 'Cluster_Fashion_Profile_y' in cluster_df.columns else None
                        if not has_canon:
                            # Create canonical by coalescing suffixes
                            if cfp_x and cfp_y:
                                cluster_df['Cluster_Fashion_Profile'] = cluster_df[cfp_x].where(cluster_df[cfp_x].notna(), cluster_df[cfp_y])
                            elif cfp_x:
                                cluster_df['Cluster_Fashion_Profile'] = cluster_df[cfp_x]
                            elif cfp_y:
                                cluster_df['Cluster_Fashion_Profile'] = cluster_df[cfp_y]
                        else:
                            # Fill missing from any suffix
                            if cfp_x and cluster_df['Cluster_Fashion_Profile'].isna().any():
                                cluster_df['Cluster_Fashion_Profile'] = cluster_df['Cluster_Fashion_Profile'].where(cluster_df['Cluster_Fashion_Profile'].notna(), cluster_df[cfp_x])
                            if cfp_y and cluster_df['Cluster_Fashion_Profile'].isna().any():
                                cluster_df['Cluster_Fashion_Profile'] = cluster_df['Cluster_Fashion_Profile'].where(cluster_df['Cluster_Fashion_Profile'].notna(), cluster_df[cfp_y])
                        # Drop suffix columns if present
                        for c in [cfp_x, cfp_y]:
                            if c and c in cluster_df.columns:
                                cluster_df = cluster_df.drop(columns=[c])
                    except Exception:
                        pass
        except Exception:
            pass
        # Save cluster-level outputs with dual output pattern
        base_path_cluster = "output/unified_delivery_cluster_level"
        timestamped_cluster_file, period_cluster_file, generic_cluster_file = create_output_with_symlinks(
            df=cluster_df,
            base_path=base_path_cluster,
            period_label=period_label
        )
        log(f"✅ Wrote Cluster-Level CSV with dual output pattern: [{len(cluster_df):,} rows]")
        log(f"   Timestamped: {timestamped_cluster_file}")
        log(f"   Period: {period_cluster_file}")
        log(f"   Generic: {generic_cluster_file}")

    # Register in manifest
    meta = {
        "target_year": int(yyyymm[:4]),
        "target_month": int(yyyymm[4:]),
        "target_period": period,
        "records": int(len(final_df)),
        "columns": int(len(final_df.columns)),
    }
    try:
        register_step_output("step36", "unified_delivery_csv", csv_path, meta)
        register_step_output("step36", f"unified_delivery_csv_{period_label}", csv_path, meta)
        register_step_output("step36", "unified_delivery_validation", qa_path, meta)
        register_step_output("step36", f"unified_delivery_validation_{period_label}", qa_path, meta)
        if xlsx_written:
            register_step_output("step36", "unified_delivery_xlsx", xlsx_written, meta)
            register_step_output("step36", f"unified_delivery_xlsx_{period_label}", xlsx_written, meta)
        if cluster_csv:
            register_step_output("step36", "unified_delivery_cluster_csv", cluster_csv, meta)
            register_step_output("step36", f"unified_delivery_cluster_csv_{period_label}", cluster_csv, meta)
    except Exception as e:
        log(f"⚠️ Manifest registration failed: {e}")

    return csv_path, xlsx_written, qa_path


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Unified Delivery Builder (Step 36)")
    p.add_argument("--target-yyyymm", required=True, help="Target year-month, e.g., 202509")
    p.add_argument("--target-period", required=True, choices=["A", "B"], help="Target period (A/B)")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    yyyymm = args.target_yyyymm
    period = args.target_period.upper()
    period_label = get_period_label(yyyymm, period)
    out_ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    log(f"🚀 Step 36 Unified Delivery Builder for {period_label}")
    csv_path, xlsx_path, qa_path = _build_unified(yyyymm, period, period_label, out_ts)

    log("\n📁 Generated Files:")
    log(f" • {csv_path}")
    if xlsx_path:
        log(f" • {xlsx_path}")
    log(f" • {qa_path}")
    log("✅ Step 36 completed")


if __name__ == "__main__":
    main()


