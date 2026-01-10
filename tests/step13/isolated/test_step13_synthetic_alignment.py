import contextlib
import importlib.util
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@contextlib.contextmanager
def _chdir(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


@contextlib.contextmanager
def _patched_environ(values: dict[str, str | None]):
    saved = {k: os.environ.get(k) for k in values}
    try:
        for key, val in values.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        yield
    finally:
        for key, val in saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val


@contextlib.contextmanager
def _sandbox_import(sandbox: Path):
    step13_path = sandbox / "src" / "step13_consolidate_spu_rules.py"
    module_name = f"sandbox_step13_{sandbox.name}"

    removed = {}
    for name in list(sys.modules):
        if name == "src" or name.startswith("src."):
            removed[name] = sys.modules.pop(name)

    sys.path.insert(0, str(sandbox))
    try:
        spec = importlib.util.spec_from_file_location(module_name, step13_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        loader = spec.loader
        assert loader is not None
        loader.exec_module(module)  # type: ignore[arg-type]
        yield module
    finally:
        sys.path.pop(0)
        sys.modules.pop(module_name, None)
        # Remove sandbox versions of src.*
        for name in list(sys.modules):
            if name == "src" or name.startswith("src."):
                sys.modules.pop(name)
        # Restore originals
        sys.modules.update(removed)


def _prepare_sandbox(tmp_path: Path) -> Path:
    sandbox = tmp_path / "sandbox"
    src_target = sandbox / "src"
    shutil.copytree(Path(__file__).resolve().parents[3] / "src", src_target)

    stub = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}


def get_manifest():
    return _DummyManifest()


def register_step_output(*_args, **_kwargs):
    return None
""".strip()
    (src_target / "pipeline_manifest.py").write_text(stub, encoding="utf-8")
    (src_target / "__init__.py").write_text("", encoding="utf-8")

    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    return sandbox


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def _alloc_shares(df: pd.DataFrame) -> pd.DataFrame:
    pants = ["直筒裤", "工装裤", "锥形裤"]
    d = df.copy()
    d["add_qty"] = d["recommended_quantity_change"].clip(lower=0)
    fam = d[d["sub_cate_name"].isin(pants)].groupby(["str_code", "sub_cate_name"], as_index=False)["add_qty"].sum()
    tot = fam.groupby("str_code", as_index=False)["add_qty"].sum().rename(columns={"add_qty": "alloc_tot"})
    fam = fam.merge(tot, on="str_code", how="left")
    fam["alloc_share"] = np.where(fam["alloc_tot"] > 0, fam["add_qty"] / fam["alloc_tot"], np.nan)
    return fam


def test_alignment_non_zero_mix_isolated(tmp_path):
    sandbox = _prepare_sandbox(tmp_path)
    period_label = "209901A"
    env = {
        "PIPELINE_TARGET_YYYYMM": "209901",
        "PIPELINE_TARGET_PERIOD": "A",
        "STEP13_EXPLORATION_CAP_ZERO_HISTORY": None,
    }

    sales_rows = [
        {"str_code": "S1", "sub_cate_name": "直筒裤", "spu_sales_amt": 600.0, "quantity": 60.0, "unit_price": 10.0},
        {"str_code": "S1", "sub_cate_name": "工装裤", "spu_sales_amt": 400.0, "quantity": 40.0, "unit_price": 10.0},
    ]
    _write_csv(sandbox / "data" / "api_data" / f"complete_spu_sales_{period_label}.csv", sales_rows)
    cluster_rows = [
        {"str_code": "S1", "Cluster": 1, "cluster_id": 1},
    ]
    _write_csv(sandbox / "output" / f"clustering_results_spu_{period_label}.csv", cluster_rows)
    _write_csv(sandbox / "output" / "clustering_results_spu.csv", cluster_rows)

    consolidated = pd.DataFrame(
        [
            {"str_code": "S1", "spu_code": "A1", "sub_cate_name": "直筒裤", "recommended_quantity_change": 9.0},
            {"str_code": "S1", "spu_code": "B1", "sub_cate_name": "工装裤", "recommended_quantity_change": 1.0},
        ]
    )

    with _chdir(sandbox), _patched_environ(env), _sandbox_import(sandbox) as step13:
        corrected, _, _ = step13.apply_data_quality_corrections(consolidated)

    fam = _alloc_shares(corrected)
    alloc = fam.set_index("sub_cate_name")["alloc_share"].to_dict()
    assert alloc["直筒裤"] == pytest.approx(0.6, abs=0.15)
    assert alloc["工装裤"] == pytest.approx(0.4, abs=0.15)


def test_alignment_zero_history_cap_isolated(tmp_path):
    sandbox = _prepare_sandbox(tmp_path)
    period_label = "209902A"
    env = {
        "PIPELINE_TARGET_YYYYMM": "209902",
        "PIPELINE_TARGET_PERIOD": "A",
        "STEP13_EXPLORATION_CAP_ZERO_HISTORY": "0.15",
    }

    sales_rows = [
        {"str_code": "S2", "sub_cate_name": "工装裤", "spu_sales_amt": 1000.0, "quantity": 100.0, "unit_price": 10.0},
        {"str_code": "S2", "sub_cate_name": "直筒裤", "spu_sales_amt": 1.0, "quantity": 0.1, "unit_price": 10.0},
    ]
    _write_csv(sandbox / "data" / "api_data" / f"complete_spu_sales_{period_label}.csv", sales_rows)
    cluster_rows = [
        {"str_code": "S2", "Cluster": 2, "cluster_id": 2},
    ]
    _write_csv(sandbox / "output" / f"clustering_results_spu_{period_label}.csv", cluster_rows)
    _write_csv(sandbox / "output" / "clustering_results_spu.csv", cluster_rows)

    consolidated = pd.DataFrame(
        [
            {"str_code": "S2", "spu_code": "C1", "sub_cate_name": "直筒裤", "recommended_quantity_change": 1.0},
            {"str_code": "S2", "spu_code": "D1", "sub_cate_name": "工装裤", "recommended_quantity_change": 9.0},
        ]
    )

    with _chdir(sandbox), _patched_environ(env), _sandbox_import(sandbox) as step13:
        corrected, _, _ = step13.apply_data_quality_corrections(consolidated)

    fam = _alloc_shares(corrected)
    share_new = fam.loc[(fam["str_code"] == "S2") & (fam["sub_cate_name"] == "直筒裤"), "alloc_share"].max()
    assert pd.notna(share_new)
    assert share_new <= 0.15 + 1e-9
