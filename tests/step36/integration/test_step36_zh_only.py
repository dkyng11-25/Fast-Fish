import glob
import os
import pandas as pd
import pytest


def _latest_unified_csv():
    candidates = sorted(glob.glob(os.path.join('output', 'unified_delivery_*_*.csv')))
    assert candidates, 'No unified_delivery_*.csv files found under output/'
    # Exclude cluster-level rollups
    base = [
        p for p in candidates
        if all(excl not in os.path.basename(p).lower() for excl in [
            'cluster_level', 'top_', 'growth_distribution', 'summary', 'validation'
        ])
    ]
    candidates = base or candidates
    assert candidates, 'Only cluster-level unified files found; expected row-level unified delivery CSV.'
    # Prefer the most recent by mtime
    candidates.sort(key=lambda p: os.path.getmtime(p))
    # If multiple, choose the one that actually has Season column
    for p in reversed(candidates):
        try:
            import pandas as pd
            # quick sample to verify structure and non-empty
            df_head = pd.read_csv(p, nrows=50)
            if len(df_head) > 0 and {'Season','Gender','Location'}.issubset(set(df_head.columns)):
                return p
        except Exception:
            continue
    return candidates[-1]


def _load_df(path):
    df = pd.read_csv(path, low_memory=False)
    assert len(df) > 0, f"Unified delivery output is empty: {path}"
    return df


def _unique_non_zh(series, allowed):
    s = series.copy()
    valid = (~s.isna()) & (s.astype(str).str.strip() != '')
    s_valid = s[valid].astype(str)
    mask = ~s_valid.isin(allowed)
    return sorted(s_valid[mask].unique().tolist())


@pytest.mark.parametrize(
    'col,allowed',
    [
        ('Season',  ['春','夏','秋','冬','四季']),
        ('Gender',  ['男','女','中性']),
        ('Location',['前台','后台','鞋配']),
    ],
)
def test_step36_unified_dimensional_fields_are_zh_only(col, allowed):
    path = _latest_unified_csv()
    df = _load_df(path)
    assert col in df.columns, f"Column '{col}' not found in unified delivery output: {path}"
    non_zh = _unique_non_zh(df[col], allowed)
    assert not non_zh, (
        f"Found non-zh values in {col}: {non_zh[:10]} (total unique non-zh={len(non_zh)}) in file {path}"
    )
