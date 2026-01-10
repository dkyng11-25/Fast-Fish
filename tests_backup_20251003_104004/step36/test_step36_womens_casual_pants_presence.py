import glob
import os
import pandas as pd
import pytest


def _latest_unified_csv():
    candidates = sorted(glob.glob(os.path.join('output', 'unified_delivery_*_*.csv')))
    assert candidates, 'No unified_delivery_*.csv files found under output/. Run Step 36 export first.'
    # Exclude cluster-level rollups
    base = [
        p for p in candidates
        if all(excl not in os.path.basename(p).lower() for excl in [
            'cluster_level', 'top_', 'growth_distribution', 'summary', 'validation'
        ])
    ]
    candidates = base or candidates
    candidates.sort(key=lambda p: os.path.getmtime(p))
    return candidates[-1]


def _load_df(path):
    df = pd.read_csv(path, low_memory=False)
    assert len(df) > 0, f"Unified delivery output is empty: {path}"
    return df


@pytest.mark.timeout(60)
def test_step36_presence_womens_casual_pants():
    """FAILS if women's casual pants are absent in the final unified export.

    Uses zh-only Gender and subcategory/category naming to detect presence.
    """
    path = _latest_unified_csv()
    df = _load_df(path)

    # Hardcoded aliases for women's casual pants family per observed taxonomy
    pants_aliases = [
        "直筒裤", "锥形裤", "阔腿裤", "工装裤", "喇叭裤", "烟管裤", "弯刀裤", "中裤", "短裤", "束脚裤"
    ]

    # Subcategory/category columns in unified export can vary; try typical names
    text_cols = [c for c in ["Subcategory", "subcategory", "二级分类", "sub_cate_name", "Category", "cate_name"] if c in df.columns]
    assert text_cols, f"No subcategory/category text columns found to evaluate pants presence in {path}"

    # If Gender exists, enforce women's-specific presence. Otherwise, enforce general presence (non-gendered)
    if "Gender" in df.columns:
        womens = df[df["Gender"].astype(str).str.strip() == '女']
        assert len(womens) > 0, "No women's rows found in unified export; cannot validate women's casual pants presence"
        present = False
        for col in text_cols:
            s = womens[col].astype(str).str.lower()
            if any(any(alias.lower() in name for alias in pants_aliases) for name in s):
                present = True
                break
        assert present, (
            f"ABSENCE: Women's casual pants not found in unified export. Aliases tried={pants_aliases}. "
            f"Check upstream coverage (Step 13) and attribute enrichment (Step 14). File={path}"
        )
    else:
        # Fallback: enforce general casual pants presence and instruct to enable Gender in export
        present = False
        for col in text_cols:
            s = df[col].astype(str).str.lower()
            if any(any(alias.lower() in name for alias in pants_aliases) for name in s):
                present = True
                break
        assert present, (
            f"ABSENCE: Casual pants not found in unified export (no Gender column available). Aliases tried={pants_aliases}. "
            f"Add Gender to unified export or run Step 14 tests for women's-specific validation. File={path}"
        )
