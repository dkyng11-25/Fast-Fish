#!/usr/bin/env python3
"""
Step 7 EDA Analyzer

Generates simple, non-interactive EDA summaries for Step 7 (Missing Rule) outputs.
Writes markdown reports to tests/test_output/eda/ without launching servers.

Author: Data Pipeline
Date: 2025-09-17
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def analyze_step7_outputs(period_label: str, analysis_level: str = "spu", data_dir: str = "output") -> Dict[str, Any]:
    data_path = Path(data_dir)
    results_file = data_path / f"rule7_missing_{analysis_level}_sellthrough_results_{period_label}.csv"
    opp_file = data_path / f"rule7_missing_{analysis_level}_sellthrough_opportunities_{period_label}.csv"

    out_dir = Path("tests/test_output/eda")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"step7_eda_{analysis_level}_{period_label}.md"

    report_lines = []
    report_lines.append(f"# Step 7 EDA Report ({analysis_level.upper()} - {period_label})\n")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    summary: Dict[str, Any] = {"exists": {}, "rows": {}}

    if results_file.exists():
        df = pd.read_csv(results_file)
        summary["exists"]["results"] = True
        summary["rows"]["results"] = int(len(df))
        report_lines.append("## Results Summary\n")
        report_lines.append(f"- Rows: {len(df)}\n")
        report_lines.append(f"- Columns: {list(df.columns)}\n")
        for col in ["missing_spus_count", "total_opportunity_value", "total_quantity_needed"]:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                desc = df[col].describe()
                report_lines.append(f"- {col}: min={desc['min']:.3f}, max={desc['max']:.3f}, mean={desc['mean']:.3f}, std={desc['std']:.3f}\n")
        report_lines.append("\n")
    else:
        summary["exists"]["results"] = False

    if opp_file.exists():
        df = pd.read_csv(opp_file)
        summary["exists"]["opportunities"] = True
        summary["rows"]["opportunities"] = int(len(df))
        report_lines.append("## Opportunities Summary\n")
        report_lines.append(f"- Rows: {len(df)}\n")
        report_lines.append(f"- Columns: {list(df.columns)}\n")
        if "opportunity_type" in df.columns:
            vc = df["opportunity_type"].value_counts()
            report_lines.append("- Opportunity Type Distribution:\n")
            for k, v in vc.items():
                report_lines.append(f"  - {k}: {v}\n")
        report_lines.append("\n")
    else:
        summary["exists"]["opportunities"] = False

    with open(report_path, 'w') as f:
        f.write("\n".join(report_lines))

    return {"report_path": str(report_path), "summary": summary}


__all__ = [
    'analyze_step7_outputs'
]


