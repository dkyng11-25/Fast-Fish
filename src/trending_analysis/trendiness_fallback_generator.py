import os
import json
import re
from datetime import datetime
from glob import glob
from typing import Dict, Optional

import pandas as pd


def _find_latest_store_makeup_csv(diagnostics_dir: str) -> Optional[str]:
    pattern = os.path.join(diagnostics_dir, 'store_fashion_basic_makeup_*.csv')
    candidates = glob(pattern)
    if not candidates:
        return None
    # Prefer by filename period code if present, fallback to mtime
    def _period_key(path: str):
        m = re.search(r'(\d{6})([AB])', os.path.basename(path))
        if not m:
            return ('000000', 'A', 0)
        yyyymm, half = m.group(1), m.group(2)
        return (yyyymm, half, os.path.getmtime(path))

    candidates.sort(key=_period_key)
    return candidates[-1]


def _parse_analysis_date_from_filename(path: str) -> str:
    base = os.path.basename(path)
    m = re.search(r'(\d{4})(\d{2})([AB])', base)
    if not m:
        return datetime.now().strftime('%Y-%m-%d')
    yyyy, mm, half = m.group(1), m.group(2), m.group(3)
    # e.g., 2025-09 A
    return f"{yyyy}-{mm} {half}"


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _mix_balance_status(fashion_ratio: float) -> str:
    if fashion_ratio >= 0.70:
        return 'FASHION_HEAVY'
    if fashion_ratio >= 0.60:
        return 'FASHION_LEAN'
    if fashion_ratio > 0.40:
        return 'BALANCED'
    if fashion_ratio > 0.30:
        return 'BASIC_LEAN'
    return 'BASIC_HEAVY'


def _recommendations(fashion_ratio: float, trendy_ratio: float) -> list:
    recs = []
    if fashion_ratio >= 0.70 and trendy_ratio < 0.40:
        recs.append('Increase trendy assortment within fashion to improve novelty mix')
    if fashion_ratio < 0.40:
        recs.append('Introduce more fashion-forward items to lift style appeal')
    if 0.40 <= fashion_ratio <= 0.60 and trendy_ratio < 0.30:
        recs.append('Add select trend capsules to balanced stores to test demand')
    if not recs:
        recs.append('Maintain current mix and monitor performance')
    return recs


def generate_fallback_production_trendiness(
    output_dir: str = 'output',
    diagnostics_dir: Optional[str] = None,
    analysis_date: Optional[str] = None,
    base_total_items: int = 100,
) -> str:
    """
    Generate a fallback production_trendiness_analysis.json using diagnostics store makeup CSV.

    Returns the path to the generated JSON file.
    """
    diagnostics_dir = diagnostics_dir or os.path.join(output_dir, 'diagnostics')
    os.makedirs(output_dir, exist_ok=True)

    src_csv = _find_latest_store_makeup_csv(diagnostics_dir)
    if not src_csv or not os.path.exists(src_csv):
        raise FileNotFoundError(f"No store makeup CSV found in {diagnostics_dir}")

    df = pd.read_csv(src_csv)
    required_cols = {'str_code', 'fashion_ratio', 'basic_ratio'}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {src_csv}: {sorted(missing)}")

    # Ensure numeric
    for col in ['fashion_ratio', 'basic_ratio']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['str_code', 'fashion_ratio', 'basic_ratio'])

    # Convert from percentage to 0-1 ratio if values look like 0-100
    # Heuristic: if median > 1, assume percentages
    if df['fashion_ratio'].median() > 1.0:
        df['fashion_ratio'] = df['fashion_ratio'] / 100.0
    if df['basic_ratio'].median() > 1.0:
        df['basic_ratio'] = df['basic_ratio'] / 100.0

    if analysis_date is None:
        analysis_date = _parse_analysis_date_from_filename(src_csv)

    result: Dict[str, Dict] = {}

    for _, row in df.iterrows():
        try:
            store_id = str(int(row['str_code'])) if pd.notna(row['str_code']) else None
        except Exception:
            store_id = str(row['str_code'])
        if not store_id:
            continue

        fashion_ratio = float(row['fashion_ratio']) if pd.notna(row['fashion_ratio']) else 0.0
        basic_ratio = float(row['basic_ratio']) if pd.notna(row['basic_ratio']) else max(0.0, 1.0 - fashion_ratio)

        # Guard rails
        fashion_ratio = _clamp(fashion_ratio, 0.0, 1.0)
        basic_ratio = _clamp(basic_ratio, 0.0, 1.0)
        if fashion_ratio + basic_ratio == 0:
            # Default to balanced if both missing
            fashion_ratio, basic_ratio = 0.5, 0.5

        # Trendy vs Core synthetic ratios informed by fashion share
        trendy_ratio = _clamp(0.2 + 0.6 * (fashion_ratio - 0.5), 0.05, 0.80)
        core_ratio = _clamp(1.0 - trendy_ratio, 0.2, 0.95)

        # Counts synthesized from base_total_items
        fashion_items_count = int(round(fashion_ratio * base_total_items))
        basic_items_count = int(base_total_items - fashion_items_count)
        trendy_items_count = int(round(trendy_ratio * base_total_items))
        core_items_count = int(base_total_items - trendy_items_count)

        # Classifications and recommendations to satisfy dashboard expectations
        if basic_ratio > 0.6:
            store_type = 'Basic'
        elif fashion_ratio > 0.6:
            store_type = 'Fashion'
        else:
            store_type = 'Hybrid'

        balance_status = _mix_balance_status(fashion_ratio)
        recs = _recommendations(fashion_ratio, trendy_ratio)

        store_payload = {
            'analysis_date': analysis_date,
            'basic_items_count': basic_items_count,
            'fashion_items_count': fashion_items_count,
            'basic_ratio': round(basic_ratio, 4),
            'fashion_ratio': round(fashion_ratio, 4),
            'basic_sales_ratio': round(basic_ratio, 4),
            'fashion_sales_ratio': round(fashion_ratio, 4),
            'trendy_items_count': trendy_items_count,
            'core_items_count': core_items_count,
            'trendy_ratio': round(trendy_ratio, 4),
            'core_ratio': round(core_ratio, 4),
            'mix_balance_status': balance_status,
            'recommendations': recs,
            # Additional fields consumed by dashboard's load_real_trendiness_data()
            'store_type': store_type,
            'balance_status': balance_status,
            'recommendations_count': len(recs),
        }

        result[store_id] = store_payload

    out_path = os.path.join(output_dir, 'production_trendiness_analysis.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return out_path
