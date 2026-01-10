import numpy as np
import pandas as pd
import pytest

from tests.step13_synthetic.test_step13_synthetic_regression import (
    _prepare_sandbox,
    _seed_synthetic_inputs,
    _run_step13,
    _load_outputs,
)


def test_no_sales_new_classes_blocked_isolated(tmp_path):
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_inputs(sandbox)
    _run_step13(sandbox)
    outputs = _load_outputs(sandbox)
    detailed = outputs["detailed"].copy()
    detailed["str_code"] = detailed["str_code"].astype(str)

    stores = set(detailed["str_code"].unique())
    assert "1004" not in stores, "Store with zero historical peer sales should be removed"
    assert stores == {"1001", "1002"}
