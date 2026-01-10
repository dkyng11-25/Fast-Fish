import os, sys
import types
import pandas as pd
import pytest

# Ensure project root and src/ are importable
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# Import the module under test
import importlib

step32 = importlib.import_module('src.step32_store_allocation')


def test_advance_half_periods_sequence():
    adv = step32._advance_half_periods
    # A -> B same month
    yyyymm, half = adv('202508', 'A', 1)
    assert (yyyymm, half) == ('202508', 'B')
    # B -> next month A
    yyyymm, half = adv('202508', 'B', 1)
    assert (yyyymm, half) == ('202509', 'A')
    # Advance 3 steps from 202512B -> 202602 A
    yyyymm, half = adv('202512', 'B', 3)
    assert (yyyymm, half) == ('202602', 'A')


def test_is_future_oriented_with_anchor_map_subcategory():
    # Anchor map with Subcategory
    anchor_df = pd.DataFrame([
        {'Subcategory': '羽绒服', 'Future_Oriented_Flag': 1, 'Anchor_Source': '202410A'}
    ])
    rec = pd.Series({'Subcategory': '羽绒服', 'Season': 'Summer'})
    assert step32._is_future_oriented(rec, anchor_df, True) is True


def test_is_future_oriented_fallback_season_tokens():
    # No anchor available -> rely on Season tokens
    anchor_df = pd.DataFrame()
    rec_aw = pd.Series({'Season': 'Autumn'})
    rec_su = pd.Series({'Season': 'Summer'})
    assert step32._is_future_oriented(rec_aw, anchor_df, False) is True
    assert step32._is_future_oriented(rec_su, anchor_df, False) is False


def test_derive_future_anchor_map_uses_yoy(monkeypatch):
    # Force FUTURE_FORWARD_HALVES and FUTURE_USE_YOY
    monkeypatch.setenv('FUTURE_FORWARD_HALVES', '2')
    monkeypatch.setenv('FUTURE_ANCHOR_SOURCE', 'step14')
    monkeypatch.setenv('FUTURE_USE_YOY', '1')

    # Monkeypatch loader to return a dummy df regardless of period label
    def fake_loader(period_label: str):
        # simulate presence of Subcategory and spu_code in forward (YoY-shifted) periods
        return pd.DataFrame({'Subcategory': ['羽绒服'], 'spu_code': ['SPU123']})

    monkeypatch.setattr(step32, '_try_load_period_file_for_anchor', fake_loader)

    anchor_df, ok = step32._derive_future_anchor_map(target_yyyymm='202508', period='A')
    assert ok is True
    # Should capture both keys from the fake loader
    assert {'Subcategory', 'spu_code'}.issubset(set(anchor_df.columns))
    # Ensure flags are set to 1
    assert anchor_df['Future_Oriented_Flag'].eq(1).all()
