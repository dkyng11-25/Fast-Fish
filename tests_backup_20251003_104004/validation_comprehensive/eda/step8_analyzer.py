#!/usr/bin/env python3
"""
Step 8 EDA Analyzer

Generates simple, non-interactive EDA summaries for Step 8 (Imbalanced Rule) outputs.
Writes markdown reports to tests/test_output/eda/ without launching servers.

Author: Data Pipeline
Date: 2025-09-17
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def analyze_step8_outputs(period_label: str, analysis_level: str = "spu", data_dir: str = "output") -> Dict[str, Any]:
    """
    Analyze Step 8 outputs and write a markdown report.
    """
    data_path = Path(data_dir)
    results_file = data_path / f"rule8_imbalanced_{analysis_level}_results_{period_label}.csv"
    imbalances_file = data_path / f"rule8_imbalanced_{analysis_level}_imbalances_{period_label}.csv"

    out_dir = Path("tests/test_output/eda")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"step8_eda_{analysis_level}_{period_label}.md"

    report_lines = []
    report_lines.append(f"# Step 8 EDA Report ({analysis_level.upper()} - {period_label})\n")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    summary: Dict[str, Any] = {
        "exists": {
            "results": results_file.exists(),
            "imbalances": imbalances_file.exists()
        },
        "rows": {
            "results": 0,
            "imbalances": 0
        }
    }

    if results_file.exists():
        df_res = pd.read_csv(results_file)
        summary["rows"]["results"] = int(len(df_res))
        report_lines.append("## Results Summary\n")
        report_lines.append(f"- Rows: {len(df_res)}\n")
        report_lines.append(f"- Columns: {list(df_res.columns)}\n")
        for col in [
            "imbalanced_categories_count", "total_imbalance_value", "total_quantity_adjustment"
        ]:
            if col in df_res.columns and pd.api.types.is_numeric_dtype(df_res[col]):
                desc = df_res[col].describe()
                report_lines.append(f"- {col}: min={desc['min']:.3f}, max={desc['max']:.3f}, mean={desc['mean']:.3f}, std={desc['std']:.3f}\n")
        report_lines.append("\n")

    if imbalances_file.exists():
        df_imb = pd.read_csv(imbalances_file)
        summary["rows"]["imbalances"] = int(len(df_imb))
        report_lines.append("## Imbalances Summary\n")
        report_lines.append(f"- Rows: {len(df_imb)}\n")
        report_lines.append(f"- Columns: {list(df_imb.columns)}\n")
        if "imbalance_type" in df_imb.columns:
            vc = df_imb["imbalance_type"].value_counts()
            report_lines.append("- Imbalance Type Distribution:\n")
            for k, v in vc.items():
                report_lines.append(f"  - {k}: {v}\n")
        if "category" in df_imb.columns:
            top_cats = df_imb["category"].value_counts().head(10)
            report_lines.append("- Top Categories (Top 10):\n")
            for k, v in top_cats.items():
                report_lines.append(f"  - {k}: {v}\n")
        report_lines.append("\n")

    with open(report_path, 'w') as f:
        f.write("\n".join(report_lines))

    return {
        "report_path": str(report_path),
        "summary": summary
    }


__all__ = [
    'analyze_step8_outputs'
]


