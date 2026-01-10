import os
import sys
import glob
import json
import time
import subprocess
from pathlib import Path

import pytest


def _ensure_output_dir(repo_root: Path) -> Path:
    out = repo_root / 'output'
    out.mkdir(exist_ok=True)
    return out


def _write_csv(path: Path, header: str, rows: str) -> None:
    path.write_text(header + "\n" + rows + "\n", encoding='utf-8')


def test_step2b_cli_explicit_periods_single(repo_root: Path = None):
    """
    Validate that Step 2B accepts the --periods CLI override with a single period and
    produces consolidated outputs. This is a fast, single-period smoke test.
    """
    repo_root = Path(__file__).resolve().parent.parent
    output_dir = _ensure_output_dir(repo_root)

    # Use a single tiny period to keep the test fast
    period = '209901A'  # fictitious period label to avoid collisions with real files

    # Create minimal dummy inputs expected by Step 2B under output/
    cat_path = output_dir / f"complete_category_sales_{period}.csv"
    spu_path = output_dir / f"complete_spu_sales_{period}.csv"
    cfg_path = output_dir / f"store_config_{period}.csv"

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

    # Run Step 2B with explicit --periods (single period)
    t0 = time.time()
    cmd = [
        sys.executable,
        str(repo_root / 'src' / 'step2b_consolidate_seasonal_data.py'),
        '--periods', period,
    ]
    res = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
    assert res.returncode == 0, f"Step 2B failed: {res.stderr}\nSTDOUT:\n{res.stdout}"

    # Identify newly created metadata file
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

    # Validate the CLI override was honored
    assert meta.get('input_periods') == [period]
    assert meta.get('total_stores') >= 1

    # Consolidated features file should exist and include our store code
    consolidated = output_dir / 'consolidated_seasonal_features.csv'
    assert consolidated.exists(), 'consolidated_seasonal_features.csv not found'
    content = consolidated.read_text(encoding='utf-8')
    assert 'S0001' in content, 'Expected store code S0001 in consolidated features'
