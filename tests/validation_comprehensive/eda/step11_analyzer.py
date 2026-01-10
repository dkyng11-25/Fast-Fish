#!/usr/bin/env python3
"""
Step 11 EDA Analyzer

Generates simple EDA summaries for Step 11 (Missed Sales Opportunity).
Outputs markdown reports to tests/test_output/eda/.

Author: Data Pipeline
Date: 2025-09-17
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def analyze_step11_outputs(period_label: str, analysis_level: str = "spu", data_dir: str = "output") -> Dict[str, Any]:
    path = Path(data_dir)
    results_file = path / f"rule11_missed_sales_opportunity_{analysis_level}_results_{period_label}.csv"

    out_dir = Path("tests/test_output/eda")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"step11_eda_{analysis_level}_{period_label}.md"

    report = []
    report.append(f"# Step 11 EDA Report ({analysis_level.upper()} - {period_label})\n")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    summary: Dict[str, Any] = {"exists": False, "rows": 0}

    if results_file.exists():
        df = pd.read_csv(results_file)
        summary["exists"] = True
        summary["rows"] = int(len(df))
        report.append("## Results Summary\n")
        report.append(f"- Rows: {len(df)}\n")
        report.append(f"- Columns: {list(df.columns)}\n")
        for col in ["missed_opportunity_value", "missed_quantity"]:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                desc = df[col].describe()
                report.append(f"- {col}: min={desc['min']:.3f}, max={desc['max']:.3f}, mean={desc['mean']:.3f}, std={desc['std']:.3f}\n")
        report.append("\n")
    else:
        report.append("- Results file not found.\n")

    with open(report_path, 'w') as f:
        f.write("\n".join(report))

    return {"report_path": str(report_path), "summary": summary}


__all__ = [
    'analyze_step11_outputs'
]


