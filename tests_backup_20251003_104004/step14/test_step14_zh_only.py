import glob
import os
import re
import pandas as pd
import pytest


def _latest_step14_csv():
    candidates = sorted(glob.glob(os.path.join('output', 'enhanced_fast_fish_format_*.csv')))
    assert candidates, 'No Step 14 enhanced_fast_fish_format_*.csv files found under output/'
    # Exclude unified/auxiliary variants from step34b or others
    base = [
        p for p in candidates
        if all(excl not in os.path.basename(p).lower() for excl in [
            'unified', 'mismatches', 'validation'
        ])
    ]
    candidates = base or candidates
    # Prefer the most recent by mtime
    candidates.sort(key=lambda p: os.path.getmtime(p))
    # If multiple, choose one that actually has the dimensional columns
    for p in reversed(candidates):
        try:
            import pandas as pd
            df_head = pd.read_csv(p, nrows=50)
            if len(df_head) > 0 and {'Season','Gender','Location'}.issubset(set(df_head.columns)):
                return p
        except Exception:
            continue
    return candidates[-1]


def _load_df(path):
    df = pd.read_csv(path, low_memory=False)
    assert len(df) > 0, f"Step 14 output is empty: {path}"
    return df


def _unique_non_zh(series, allowed):
    # Treat NaN/empty as acceptable missing values; only flag concrete non-zh strings
    s = series.copy()
    # Build a mask of valid (non-null, non-empty) entries
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
def test_step14_dimensional_fields_are_zh_only(col, allowed):
    path = _latest_step14_csv()
    df = _load_df(path)
    assert col in df.columns, f"Column '{col}' not found in Step 14 output: {path}"
    non_zh = _unique_non_zh(df[col], allowed)
    assert not non_zh, (
        f"Found non-zh values in {col}: {non_zh[:10]} (total unique non-zh={len(non_zh)}) in file {path}"
    )


def test_target_style_tags_present_and_contains_zh_tokens():
    path = _latest_step14_csv()
    df = _load_df(path)
    assert 'Target_Style_Tags' in df.columns, 'Target_Style_Tags column missing from Step 14 output'
    sample = df['Target_Style_Tags'].astype(str).head(200).tolist()
    # Expect at least one Chinese character in these tags (粗略检测)
    zh_char = re.compile(r'[\u4e00-\u9fff]')
    has_zh = any(bool(zh_char.search(x)) for x in sample)
    assert has_zh, 'Target_Style_Tags do not appear to contain Chinese tokens in sample rows'
