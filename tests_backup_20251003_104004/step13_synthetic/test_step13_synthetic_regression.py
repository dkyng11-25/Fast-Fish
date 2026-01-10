import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

TARGET_YYYYMM = "202501"
TARGET_PERIOD = "A"
PERIOD_LABEL = f"{TARGET_YYYYMM}{TARGET_PERIOD}"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"


def _prepare_sandbox(tmp_path: Path) -> Path:
    sandbox = tmp_path / "sandbox"
    src_target = sandbox / "src"
    shutil.copytree(SRC_ROOT, src_target)

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


def _seed_synthetic_inputs(sandbox: Path) -> None:
    output_dir = sandbox / "output"
    api_dir = sandbox / "data" / "api_data"

    rule_rows = pd.DataFrame(
        [
            {
                "str_code": "1001",
                "spu_code": "SPU101",
                "sub_cate_name": "束脚裤",
                "recommended_quantity_change": 6.0,
                "unit_price": 100.0,
                "rule_source": "rule10",
            },
            {
                "str_code": "1001",
                "spu_code": "SPU102",
                "sub_cate_name": "直筒裤",
                "recommended_quantity_change": 2.0,
                "unit_price": 90.0,
                "rule_source": "rule10",
            },
            {
                "str_code": "1001",
                "spu_code": "SPU103",
                "sub_cate_name": "外套",
                "recommended_quantity_change": 3.0,
                "unit_price": 120.0,
                "rule_source": "rule10",
            },
            {
                "str_code": "1002",
                "spu_code": "SPU201",
                "sub_cate_name": "束脚裤",
                "recommended_quantity_change": 0.0,
                "unit_price": 110.0,
                "rule_source": "rule10",
            },
            {
                "str_code": "1002",
                "spu_code": "SPU202",
                "sub_cate_name": "直筒裤",
                "recommended_quantity_change": 0.0,
                "unit_price": 130.0,
                "rule_source": "rule10",
            },
            {
                "str_code": "1002",
                "spu_code": "SPU203",
                "sub_cate_name": "短裤",
                "recommended_quantity_change": 0.0,
                "unit_price": 80.0,
                "rule_source": "rule10",
            },
            {
                "str_code": "1004",
                "spu_code": "SPU401",
                "sub_cate_name": "束脚裤",
                "recommended_quantity_change": 4.0,
                "unit_price": 95.0,
                "rule_source": "rule10",
            },
        ]
    )
    rule_path = output_dir / f"rule10_spu_overcapacity_opportunities_{PERIOD_LABEL}.csv"
    rule_rows.to_csv(rule_path, index=False)

    cluster_rows = pd.DataFrame(
        [
            {"str_code": "1001", "Cluster": 1, "cluster_id": 1},
            {"str_code": "1002", "Cluster": 2, "cluster_id": 2},
            {"str_code": "1004", "Cluster": 4, "cluster_id": 4},
        ]
    )
    for name in [f"clustering_results_spu_{PERIOD_LABEL}.csv", "clustering_results_spu.csv"]:
        cluster_rows.to_csv(output_dir / name, index=False)

    sales_rows = pd.DataFrame(
        [
            {"str_code": "1001", "sub_cate_name": "束脚裤", "spu_code": "SPU101", "spu_sales_amt": 600.0, "quantity": 60.0, "unit_price": 10.0},
            {"str_code": "1001", "sub_cate_name": "直筒裤", "spu_code": "SPU102", "spu_sales_amt": 400.0, "quantity": 40.0, "unit_price": 10.0},
            {"str_code": "1001", "sub_cate_name": "外套", "spu_code": "SPU103", "spu_sales_amt": 800.0, "quantity": 20.0, "unit_price": 40.0},
            {"str_code": "1002", "sub_cate_name": "束脚裤", "spu_code": "SPU201", "spu_sales_amt": 250.0, "quantity": 25.0, "unit_price": 10.0},
            {"str_code": "1002", "sub_cate_name": "直筒裤", "spu_code": "SPU202", "spu_sales_amt": 350.0, "quantity": 17.5, "unit_price": 20.0},
            {"str_code": "1002", "sub_cate_name": "短裤", "spu_code": "SPU203", "spu_sales_amt": 150.0, "quantity": 15.0, "unit_price": 10.0},
            {"str_code": "1002", "sub_cate_name": "锥形裤", "spu_code": "SPU204", "spu_sales_amt": 250.0, "quantity": 25.0, "unit_price": 10.0},
        ]
    )
    sales_path = api_dir / f"complete_spu_sales_{PERIOD_LABEL}.csv"
    sales_rows.to_csv(sales_path, index=False)

    store_config = pd.DataFrame(
        [
            {"str_code": "1001", "cluster_id": 1},
            {"str_code": "1002", "cluster_id": 2},
            {"str_code": "1004", "cluster_id": 4},
        ]
    )
    store_config.to_csv(api_dir / f"store_config_{PERIOD_LABEL}.csv", index=False)


def _run_step13(sandbox: Path) -> None:
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    env.setdefault("PYTHONPATH", str(sandbox))
    subprocess.run(
        [
            "python3",
            "src/step13_consolidate_spu_rules.py",
            "--target-yyyymm",
            TARGET_YYYYMM,
            "--target-period",
            TARGET_PERIOD,
        ],
        cwd=sandbox,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _load_outputs(sandbox: Path) -> dict:
    detailed_path = sandbox / "output" / f"consolidated_spu_rule_results_detailed_{PERIOD_LABEL}.csv"
    store_path = sandbox / "output" / "consolidated_spu_rule_results.csv"
    cluster_path = sandbox / "output" / "consolidated_cluster_subcategory_results.csv"

    return {
        "detailed": pd.read_csv(detailed_path),
        "store": pd.read_csv(store_path),
        "cluster": pd.read_csv(cluster_path),
    }


def test_step13_synthetic_end_to_end(tmp_path):
    sandbox = _prepare_sandbox(tmp_path)
    _seed_synthetic_inputs(sandbox)
    _run_step13(sandbox)
    outputs = _load_outputs(sandbox)

    detailed = outputs["detailed"].copy()
    detailed["str_code"] = detailed["str_code"].astype(str)
    detailed["add_qty"] = detailed["recommended_quantity_change"].clip(lower=0)

    # No-sales guard should drop store 1004 entirely
    assert set(detailed["str_code"].unique()) == {"1001", "1002"}

    # Volume floor enforcement: every store meets floor >= 10
    store_adds = detailed.groupby("str_code", as_index=False)["add_qty"].sum()
    assert (store_adds["add_qty"] >= 10 - 1e-6).all()

    # Share alignment: pants-family adds versus historical shares
    pants_aliases = {"束脚裤", "直筒裤", "短裤", "锥形裤"}
    pants_det = detailed[detailed["sub_cate_name"].isin(pants_aliases)].copy()
    pants_det_tot = pants_det.groupby(["str_code"], as_index=False)["add_qty"].sum().rename(columns={"add_qty": "tot"})
    pants_det = pants_det.merge(pants_det_tot, on="str_code", how="left")
    pants_det["alloc_share"] = np.where(pants_det["tot"] > 0, pants_det["add_qty"] / pants_det["tot"], np.nan)

    sales_rows = _seeded_sales_shares()
    for str_code, fam_shares in sales_rows.items():
        det_store = pants_det[pants_det["str_code"] == str_code]
        if det_store.empty:
            continue
        for fam, expected_share in fam_shares.items():
            row = det_store[det_store["sub_cate_name"] == fam]
            if row.empty:
                continue
            observed = float(row["alloc_share"].iloc[0])
            assert abs(observed - expected_share) <= 0.15

    # Ensure zero-add store 1002 receives positive recommended quantities after alignment
    add_1002 = store_adds.loc[store_adds["str_code"] == "1002", "add_qty"].iloc[0]
    assert add_1002 > 0

    # Store summary must match adds-only totals
    store = outputs["store"].copy()
    store["str_code"] = store["str_code"].astype(str)
    total_col = next(
        (c for c in ["total_quantity_change", "recommended_quantity_change", "total_quantity_needed"] if c in store.columns),
        None,
    )
    assert total_col is not None
    store["store_add_qty"] = pd.to_numeric(store[total_col], errors="coerce").fillna(0).clip(lower=0)
    store_totals = store.groupby("str_code", as_index=False)["store_add_qty"].sum()
    merged = store_adds.merge(store_totals, on="str_code", how="left")
    assert np.allclose(merged["add_qty"], merged["store_add_qty"], atol=1e-6)

    # Cluster aggregation must align with detailed totals
    cluster = outputs["cluster"].copy()
    cluster_col = "cluster_id" if "cluster_id" in detailed.columns else "Cluster_ID"
    cluster_det = detailed.groupby([cluster_col, "sub_cate_name"], as_index=False)["recommended_quantity_change"].sum()
    cluster_det[cluster_col] = cluster_det[cluster_col].astype(str)
    cluster = cluster.rename(columns={"cluster": cluster_col, "subcategory": "sub_cate_name"})
    cluster[cluster_col] = cluster[cluster_col].astype(str)
    merged_cluster = cluster_det.merge(
        cluster[[cluster_col, "sub_cate_name", "total_quantity_change"]],
        on=[cluster_col, "sub_cate_name"],
        how="left",
    )
    assert np.allclose(
        merged_cluster["recommended_quantity_change"],
        merged_cluster["total_quantity_change"],
        atol=1e-6,
    )


def _seeded_sales_shares() -> dict:
    return {
        "1001": {"束脚裤": 0.6, "直筒裤": 0.4},
        "1002": {"束脚裤": 0.25, "直筒裤": 0.35, "短裤": 0.15, "锥形裤": 0.25},
    }
