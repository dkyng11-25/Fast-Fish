import pytest
import os
import sys
import json
import subprocess
from pathlib import Path


def _ensure_output_dir(repo_root: Path) -> Path:
    out = repo_root / 'output'
    out.mkdir(exist_ok=True)
    return out


def _write_csv(path: Path, header: str, rows: str) -> None:
    path.write_text(header + "\n" + rows + "\n", encoding='utf-8')


def test_step28_cli_minimal_auto_scenario(tmp_path):
    # Skip test gracefully if critical deps are missing
    pytest.importorskip('pandas')
    pytest.importorskip('numpy')

    repo_root = Path(__file__).resolve().parent
    output_dir = _ensure_output_dir(repo_root)

    # Target period (period-aware execution)
    yyyymm = '202509'
    period = 'A'
    period_label = f"{yyyymm}{period}"

    # Minimal dummy inputs
    # 1) Sales CSV (override) with required columns to avoid loader fallback
    sales_path = output_dir / 'dummy_sales_step28.csv'
    _write_csv(
        sales_path,
        header="spu_code,fashion_sal_amt,basic_sal_amt",
        rows="X1,100,50",
    )

    # 2) Product roles CSV at default resolved path
    roles_path = output_dir / 'product_role_classifications.csv'
    _write_csv(
        roles_path,
        header="spu_code,product_role,category,subcategory",
        rows="X1,CORE,Cat,Sub",
    )

    # 3) Price bands CSV at default resolved path
    price_path = output_dir / 'price_band_analysis.csv'
    _write_csv(
        price_path,
        header="spu_code,price_band,avg_unit_price",
        rows="X1,VALUE,100",
    )

    # 4) Gap analysis CSV at default resolved path
    gap_analysis_path = output_dir / 'gap_analysis_detailed.csv'
    _write_csv(
        gap_analysis_path,
        header="cluster_id,total_products,total_stores",
        rows="1,1,1",
    )

    # 5) Gap summary JSON with at least one CRITICAL gap to produce scenarios
    gap_summary_path = output_dir / 'gap_matrix_summary.json'
    gap_summary = {
        "gap_severity_counts": {"CRITICAL": 1, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
        "cluster_summary": {
            "Cluster_1": {
                "significant_gaps": 1,
                "gaps_detail": [
                    {"role": "CORE", "gap": 10, "severity": "CRITICAL"}
                ],
            }
        },
    }
    gap_summary_path.write_text(json.dumps(gap_summary), encoding='utf-8')

    # Run Step 28 (AUTO scenario by default) with period-aware args and sales override
    cmd = [
        sys.executable,
        str(repo_root / 'src' / 'step28_scenario_analyzer.py'),
        '--target-yyyymm', yyyymm,
        '--target-period', period,
        '--sales-file', str(sales_path),
        '--scenario', 'AUTO',
    ]
    res = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
    assert res.returncode == 0, f"Step 28 failed: {res.stderr}\nSTDOUT:\n{res.stdout}"

    # Expected output file names (period-aware naming)
    base_name = f'scenario_analysis_results_{period_label}'
    results_file = output_dir / f'{base_name}.json'
    report_file = output_dir / f'{base_name}_report.md'
    recs_file = output_dir / f'{base_name}_recommendations.csv'

    assert results_file.exists(), f"Missing results JSON: {results_file}"
    assert report_file.exists(), f"Missing report MD: {report_file}"
    assert recs_file.exists(), f"Missing recommendations CSV: {recs_file}"

    # Basic content checks
    with open(results_file, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    assert 'analysis_metadata' in summary
    assert isinstance(summary.get('scenario_results'), list)
    assert len(summary['scenario_results']) >= 1  # At least one scenario from CRITICAL gap

    # Report headline present
    report_text = report_file.read_text(encoding='utf-8')
    assert '# What-If Scenario Analysis Report' in report_text

    # Recommendations CSV sanity
    recs_text = recs_file.read_text(encoding='utf-8')
    assert 'scenario_type' in recs_text
    assert 'GAP_FILLING' in recs_text or 'PRICE_STRATEGY' in recs_text
