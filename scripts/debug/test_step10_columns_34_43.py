#!/usr/bin/env python3
import os
import sys
import json
import math
import pandas as pd

# Ensure we can import from src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.step10_spu_assortment_optimization import fast_expand_spu_data


def approx_equal(a, b, tol=1e-6):
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return False


def run_test():
    print("Testing STEP10 columns #34–#43 with deterministic in-memory data...")

    # Use deterministic default margin rate
    os.environ['MARGIN_RATE_DEFAULT'] = '0.45'

    # Build minimal input config DataFrame with 1 overcapacity category and 1 SPU
    # Current SPU count = 10, target = 5 -> excess 5, overcapacity% = 100%
    # JSON sales has SPU1 with 200 sales value; sufficient volume (>20)
    df = pd.DataFrame([
        {
            'str_code': '001',
            'ext_sty_cnt_avg': 10,
            'target_sty_cnt_avg': 5,
            'sty_sal_amt': json.dumps({'SPU1': 200.0}),
        }
    ])

    # Quantity/join DF: quantity_real = base + fashion = 10 + 30 = 40
    # Amount for unit_price comes from 'spu_sales_amt' (preferred): 200
    quantity_df = pd.DataFrame([
        {
            'str_code': '001',
            'spu_code': 'SPU1',
            'base_sal_qty': 10,
            'fashion_sal_qty': 30,
            'spu_sales_amt': 200.0,
        }
    ])

    out = fast_expand_spu_data(df, quantity_df)
    assert len(out) >= 1, "No expanded rows returned"

    row = out.iloc[0]

    # Expected values
    qty_real = 40.0
    unit_price = 200.0 / qty_real  # 5.0
    current_qty = qty_real * 1.0  # SCALING_FACTOR = 1.0
    frac_excess = 5.0 / 10.0  # 0.5
    potential_reduction = frac_excess * current_qty  # 20.0
    max_reduction = current_qty * 0.4  # 16.0
    constrained_reduction = min(potential_reduction, max_reduction)  # 16.0

    margin_rate = float(os.environ.get('MARGIN_RATE_DEFAULT', '0.45'))  # 0.45
    unit_cost = unit_price * (1 - margin_rate)  # 5 * 0.55 = 2.75
    investment_required = -(constrained_reduction * unit_cost)  # -44.0
    estimated_cost_savings = constrained_reduction * unit_cost  # 44.0
    margin_per_unit = unit_price - unit_cost  # 2.25
    expected_margin_uplift = constrained_reduction * margin_per_unit  # 36.0
    roi_percentage = (expected_margin_uplift / -investment_required) * 100  # ~81.818...

    # Assertions for columns #34–#43
    # 34 recommend_reduction (bool)
    assert bool(row['recommend_reduction']) is True, f"recommend_reduction expected True, got {row['recommend_reduction']}"

    # 35 recommended_quantity_change (negative of constrained_reduction)
    assert approx_equal(row['recommended_quantity_change'], -constrained_reduction), (
        f"recommended_quantity_change expected {-constrained_reduction}, got {row['recommended_quantity_change']}"
    )

    # 36 margin_rate (filled from default and clipped)
    assert approx_equal(row['margin_rate'], margin_rate), f"margin_rate expected {margin_rate}, got {row['margin_rate']}"

    # 37 retail_value (alias of unit_price)
    assert approx_equal(row['retail_value'], unit_price), f"retail_value expected {unit_price}, got {row['retail_value']}"

    # 38 investment_required (negative cost-based investment)
    assert approx_equal(row['investment_required'], investment_required), (
        f"investment_required expected {investment_required}, got {row['investment_required']}"
    )

    # 39 estimated_cost_savings (positive)
    assert approx_equal(row['estimated_cost_savings'], estimated_cost_savings), (
        f"estimated_cost_savings expected {estimated_cost_savings}, got {row['estimated_cost_savings']}"
    )

    # 40 margin_per_unit
    assert approx_equal(row['margin_per_unit'], margin_per_unit), (
        f"margin_per_unit expected {margin_per_unit}, got {row['margin_per_unit']}"
    )

    # 41 expected_margin_uplift
    assert approx_equal(row['expected_margin_uplift'], expected_margin_uplift), (
        f"expected_margin_uplift expected {expected_margin_uplift}, got {row['expected_margin_uplift']}"
    )

    # 42 roi_percentage (allow small tolerance)
    assert approx_equal(row['roi_percentage'], roi_percentage, tol=1e-4), (
        f"roi_percentage expected ~{roi_percentage}, got {row['roi_percentage']}"
    )

    # 43 recommendation_text content
    text = str(row.get('recommendation_text', ''))
    assert 'REDUCE 16.0 units/15-days' in text, f"recommendation_text missing reduction phrase: {text}"
    assert 'SPU SPU1' in text, f"recommendation_text missing SPU code: {text}"
    assert '(overcapacity: 100.0%)' in text, f"recommendation_text missing overcapacity value: {text}"

    print("\n✅ STEP10 columns #34–#43 validations passed.")


if __name__ == '__main__':
    try:
        run_test()
    except AssertionError as e:
        print(f"❌ Test assertion failed: {e}")
        raise
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        raise
