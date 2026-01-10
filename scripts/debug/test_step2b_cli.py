import pytest
import os
import sys
import glob
import json
import time
import subprocess
from pathlib import Path


def _ensure_output_dir(repo_root: Path) -> Path:
    out = repo_root / 'output'
    out.mkdir(exist_ok=True)
    return out


def _write_csv(path: Path, header: str, rows: str) -> None:
    path.write_text(header + "\n" + rows + "\n", encoding='utf-8')


def test_step2b_cli_dynamic_period_generation_single_lookback(tmp_path):
    # Skip test gracefully if pandas is not available in this interpreter
    pytest.importorskip('pandas')

    repo_root = Path(__file__).resolve().parent
    output_dir = _ensure_output_dir(repo_root)

    # Anchor period
    yyyymm = '202509'
    period = 'A'
    period_label = f"{yyyymm}{period}"

    # Minimal dummy inputs for the anchor period
    cat_path = output_dir / f"complete_category_sales_{period_label}.csv"
    spu_path = output_dir / f"complete_spu_sales_{period_label}.csv"
    cfg_path = output_dir / f"store_config_{period_label}.csv"

    _write_csv(
        cat_path,
        header="str_code,sub_cate_name,sal_amt",
        rows="S0001,CatX,10",
    )
    _write_csv(
        spu_path,
        header="str_code,spu_code",
        rows="S0001,X1",
    )
    _write_csv(
        cfg_path,
        header="str_code,store_name",
        rows="S0001,Demo Store",
    )

    # Snapshot existing metadata files
    before = set(glob.glob(str(output_dir / 'seasonal_clustering_metadata_*.json')))

    # Run Step 2B with a single look-back (should only include the anchor period)
    t0 = time.time()
    cmd = [
        sys.executable,
        str(repo_root / 'src' / 'step2b_consolidate_seasonal_data.py'),
        '--seasonal-look-back', '1',
        '--target-yyyymm', yyyymm,
        '--target-period', period,
    ]
    res = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
    assert res.returncode == 0, f"Step 2B failed: {res.stderr}\nSTDOUT:\n{res.stdout}"

    # Find the latest metadata produced by this invocation
    after = set(glob.glob(str(output_dir / 'seasonal_clustering_metadata_*.json')))
    new_files = sorted(after - before, key=os.path.getmtime)
    if new_files:
        latest_meta = new_files[-1]
    else:
        # Fallback: pick the most recent file by mtime
        all_meta = sorted(after, key=os.path.getmtime)
        assert all_meta, 'No seasonal metadata files found after running Step 2B'
        latest_meta = all_meta[-1]
        # Sanity: ensure it's fresh (within 2 minutes)
        assert os.path.getmtime(latest_meta) >= t0 - 120

    with open(latest_meta, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    # Validate dynamic window and anchor period
    assert meta.get('seasonal_look_back') == 1
    assert meta.get('input_periods') == [period_label]

    # Consolidated features file should exist and include our store code
    consolidated = output_dir / 'consolidated_seasonal_features.csv'
    assert consolidated.exists(), 'consolidated_seasonal_features.csv not found'
    content = consolidated.read_text(encoding='utf-8')
    assert 'S0001' in content, 'Expected store code S0001 in consolidated features'
