import glob
import os
import pandas as pd
import pytest


def _latest_step14_csv():
    """Find the most recent Step 14 formatted CSV with Season (and ideally Gender/Location), non-empty.

    Excludes diagnostic and reconciliation files that may be empty.
    """
    # Prefer enhanced Fast Fish format which contains Season/Gender/Location
    enhanced_candidates = sorted(glob.glob(os.path.join('output', 'enhanced_fast_fish_format_*.csv')))
    for path in reversed(enhanced_candidates):
        try:
            df_head = pd.read_csv(path, nrows=50, low_memory=False)
            if len(df_head) == 0:
                continue
            cols = set(df_head.columns)
            if {'Season','Gender','Location'}.issubset(cols):
                return path
        except Exception:
            continue

    # Fallback: store-level breakdown, but only if it already provides Season/Gender/Location
    s14_candidates = sorted(glob.glob(os.path.join('output', 'store_level_recommendation_breakdown_*.csv')))
    for path in reversed(s14_candidates):
        try:
            df_head = pd.read_csv(path, nrows=100, low_memory=False)
            if len(df_head) == 0:
                continue
            cols = set(df_head.columns)
            if {'Season','Gender','Location'}.issubset(cols):
                return path
        except Exception:
            continue

    candidates = sorted(glob.glob(os.path.join('output', '*_*.csv')))
    exclude_terms = [
        'cluster_level', 'top_', 'growth_distribution', 'summary', 'validation',
        'reconciliation', 'mismatch', 'mismatches', 'top_reduces'
    ]
    candidates = [
        p for p in candidates
        if all(excl not in os.path.basename(p).lower() for excl in exclude_terms)
    ]
    best = None
    for path in reversed(candidates):
        try:
            df_head = pd.read_csv(path, nrows=200, low_memory=False)
            if len(df_head) == 0:
                continue
            cols = set(df_head.columns)
            if 'Season' in cols:
                if {'Season', 'Gender', 'Location'}.issubset(cols):
                    return path
                best = best or path
        except Exception:
            continue
    return best


def _ensure_step14_run():
    env = os.environ.copy()
    env.setdefault('PYTHONPATH', '.')
    path = _latest_step14_csv()
    if path:
        return
    import subprocess
    subprocess.run(['python3', 'src/step14_create_fast_fish_format.py'], check=True, env=env)


def _load_formatted():
    path = _latest_step14_csv()
    assert path and os.path.exists(path), 'No Step 14 formatted CSV with Season found under output/. '
    df = pd.read_csv(path, low_memory=False)
    assert len(df) > 0, f'Step 14 formatted output is empty: {path}'
    return path, df


def _pick_qty_col(df: pd.DataFrame):
    """Try to pick a quantity column for share calculations; returns None if not found."""
    candidates = [
        'Allocated_ΔQty', 'Allocated_ΔQty_Rounded', 'Target_SPU_Quantity',
        'recommended_quantity_change', 'quantity', 'ΔQty', 'delta_qty'
    ]
    for c in candidates:
        if c in df.columns:
            try:
                s = pd.to_numeric(df[c], errors='coerce')
                if s.notna().any():
                    return c
            except Exception:
                continue
    return None


@pytest.mark.timeout(90)
def test_step14_future_season_coverage_present():
    """Enforce that coverage exists for the future-target season at Step 14.
    The expected season depends on the target month (future-facing):
      - 3-5: 春, 6-8: 夏, 9-11: 秋, else: 冬
    四季 (all-season) also counts as valid coverage.
    Optionally enforce a minimum share via env STEP14_FUTURE_SEASON_MIN_SHARE (0..1).
    """
    _ensure_step14_run()
    path, df = _load_formatted()
    assert 'Season' in df.columns, f"Season column missing in Step 14 output: {path}"

    # Determine target yyyymm from env or infer from filename suffix
    target_yyyymm = os.getenv('PIPELINE_TARGET_YYYYMM')
    if not target_yyyymm:
        # Try parse from file name ..._YYYYMMP.csv
        base = os.path.basename(path)
        # Find last 7 chars before extension like 202510A
        stem = os.path.splitext(base)[0]
        # Split by underscores and look for a 6-digit + A/B token
        parts = stem.split('_')
        cand = next((p for p in reversed(parts) if len(p) == 7 and p[:6].isdigit()), None)
        if cand:
            target_yyyymm = cand[:6]
    assert target_yyyymm and len(target_yyyymm) == 6 and target_yyyymm.isdigit(), (
        f"Cannot determine target yyyymm for future-season assertion from env or filename: {path}"
    )

    # Determine expected season with a NEXT-season mapping (forward-looking):
    #   3-5 -> 夏, 6-8 -> 秋, 9-11 -> 冬, else (12,1,2) -> 春
    # This ensures October is evaluated against Winter coverage (future oriented).
    mm = int(target_yyyymm[4:6])
    override_season = os.getenv('STEP14_EXPECTED_SEASON')
    if override_season:
        expected_season = override_season.strip()
    else:
        if 3 <= mm <= 5:
            expected_season = '夏'
        elif 6 <= mm <= 8:
            expected_season = '秋'
        elif 9 <= mm <= 11:
            expected_season = '冬'
        else:
            expected_season = '春'

    season_mask = df['Season'].astype(str).str.strip().isin([expected_season, '四季'])
    assert season_mask.any(), (
        f"ABSENCE: No future-season coverage found. Expected Season='{expected_season}' (or '四季') in file: {path}"
    )

    # Enforce minimum share for the computed future season (default 30%)
    # Prefer quantity-based share if a numeric quantity column is available; otherwise, use row counts.
    min_share = 0.30
    try:
        env_min = os.getenv('STEP14_FUTURE_SEASON_MIN_SHARE')
        if env_min is not None:
            min_share = float(env_min)
    except Exception:
        pass
    assert 0.0 <= min_share <= 1.0, "STEP14_FUTURE_SEASON_MIN_SHARE must be within [0,1] if set"

    qty_col = _pick_qty_col(df)
    if qty_col:
        q = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
        total = float(q.sum())
        season_share = float(q[season_mask].sum()) / total if total > 0 else 0.0
        basis = f"quantity column '{qty_col}'"
    else:
        total = float(len(df))
        season_share = float(season_mask.sum()) / total if total > 0 else 0.0
        basis = "row count"
    assert season_share >= min_share, (
        f"Future-season share {season_share:.3f} < required {min_share:.3f} using {basis}. "
        f"Expected Season='{expected_season}'. File={path}"
    )


@pytest.mark.timeout(90)
def test_step14_frontcourt_coverage_present():
    """Enforce that frontcourt (前台) coverage is present at Step 14.
    If a quantity column is available, optionally enforce a minimum share via env STEP14_FRONTCOURT_MIN_SHARE (0..1).
    """
    _ensure_step14_run()
    path, df = _load_formatted()
    assert 'Location' in df.columns, f"Location column missing in Step 14 output: {path}"

    front_mask = df['Location'].astype(str).str.strip() == '前台'
    assert front_mask.any(), f"ABSENCE: No frontcourt (前台) coverage found in Step 14 output: {path}"

    qty_col = _pick_qty_col(df)
    min_share_raw = os.getenv('STEP14_FRONTCOURT_MIN_SHARE')
    if qty_col and min_share_raw is not None:
        try:
            min_share = float(min_share_raw)
        except Exception:
            min_share = None
        if min_share is not None and 0 <= min_share <= 1:
            q = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
            total = q.sum()
            front_share = q[front_mask].sum() / total if total > 0 else 0.0
            assert front_share >= min_share, (
                f"Frontcourt share {front_share:.3f} < required {min_share:.3f} using {qty_col}. File={path}"
            )


@pytest.mark.timeout(60)
def test_step14_dimensional_fields_are_zh_only():
    """Assert zh-only values for Season/Gender/Location at Step 14 (early enforcement)."""
    _ensure_step14_run()
    path, df = _load_formatted()
    for col, allowed in [
        ('Season',  ['春','夏','秋','冬','四季']),
        ('Gender',  ['男','女','中性']),
        ('Location',['前台','后台','鞋配']),
    ]:
        assert col in df.columns, f"Column '{col}' not found in Step 14 output: {path}"
        s = df[col].astype(str).str.strip()
        mask = (~s.isna()) & (s != '')
        bad = sorted(s[mask & (~s.isin(allowed))].unique().tolist())
        assert not bad, (
            f"Found non-zh values in {col}: {bad[:10]} (total unique non-zh={len(bad)}) in file {path}"
        )
