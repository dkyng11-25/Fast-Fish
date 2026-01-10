#!/usr/bin/env python3
"""
Manual verification report generator for Step 36 unified outputs (per column).

For each column, produces:
- Expected provenance (step/source)
- Expected type and validation rules
- Actual dtype, nulls, uniques, min/max (numeric), sample values
- Issues found (type mismatch, range violations, unexpected enums, whitespace)

Outputs a markdown file next to the CSV: *_manual_verification.md
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
	from src.pipeline_manifest import get_manifest
	from src.config import get_period_label
except Exception:
	from pipeline_manifest import get_manifest
	from config import get_period_label


PROVENANCE: Dict[str, Dict] = {
	# Keys: column name; Values: expected provenance and validation rules
	"Store_Code": {"source": "Step 32 allocation / Step 33 meta", "type": "int|str", "nullable": False},
	"Store_Group_Name": {"source": "Step 18/14 group recs", "type": "str", "nullable": False},
	"Target_Style_Tags": {"source": "Step 18/14 group recs", "type": "str", "nullable": False},
	"Category": {"source": "Step 18/14 group recs", "type": "str", "nullable": True},
	"Subcategory": {"source": "Step 18/14 group recs", "type": "str", "nullable": True},
	"Allocated_ΔQty_Rounded": {"source": "Step 36 rounding of Step 32", "type": "int", "nullable": False, "range": [ -10**9, 10**9 ]},
	"Allocated_ΔQty": {"source": "Step 32 allocation", "type": "float", "nullable": False},
	"Group_ΔQty": {"source": "Step 18/14 group recs", "type": "float|int", "nullable": False},
	"Expected_Benefit": {"source": "Step 18 enriched", "type": "float", "nullable": True, "range": [0.0, 1e12]},
	"Confidence_Score": {"source": "Step 18 enriched", "type": "float", "nullable": True, "range": [0.0, 1.0]},
	"Current_Sell_Through_Rate": {"source": "Step 18 enriched", "type": "float", "nullable": True, "range": [0.0, 1.0]},
	"Target_Sell_Through_Rate": {"source": "Step 18 enriched", "type": "float", "nullable": True, "range": [0.0, 1.0]},
	"Sell_Through_Improvement": {"source": "Step 18 enriched", "type": "float", "nullable": True, "range": [-1.0, 1.0]},
	"Constraint_Status": {"source": "Step 33 meta", "type": "str", "nullable": True, "enum": ["Normal","Minor-Constraint","Critical-Constraint","Under-Utilized"]},
	"Capacity_Utilization": {"source": "Step 33 meta", "type": "float", "nullable": True, "range": [0.0, 1.5]},
	"Action_Priority": {"source": "Step 33 meta", "type": "str", "nullable": True, "enum": ["Immediate","High-Priority","Medium-Priority","Monitor"]},
	"Performance_Tier": {"source": "Step 33 meta", "type": "str", "nullable": True},
	"Growth_Potential": {"source": "Step 33 meta", "type": "str", "nullable": True},
	"Risk_Level": {"source": "Step 33 meta", "type": "str", "nullable": True},
	"Cluster_ID": {"source": "Step 33/24", "type": "int|str", "nullable": True},
	"Cluster_Name": {"source": "Step 33/24", "type": "str", "nullable": True},
	"Operational_Tag": {"source": "Step 33", "type": "str", "nullable": True},
	"Temperature_Zone": {"source": "Step 33", "type": "str", "nullable": True},
	"Season": {"source": "Step 18/14", "type": "str", "nullable": True, "enum_soft": ["spring","summer","autumn","winter","Spring","Summer","Autumn","Winter"]},
	"Gender": {"source": "Step 18/14", "type": "str", "nullable": True, "enum_soft": ["men","women","unisex","Men","Women","Unisex"]},
	"Location": {"source": "Step 18/14", "type": "str", "nullable": True, "enum_soft": ["front","back","Front","Back"]},
	"Data_Based_Rationale": {"source": "Step 18/14", "type": "str", "nullable": True},
	"Priority_Score": {"source": "Step 36 composite", "type": "float", "nullable": True, "range": [0.0, 1.0]},
	"Gap_Intensity": {"source": "Step 27/29 (optional)", "type": "str", "nullable": True},
	"Coverage_Index": {"source": "Step 27/29 (optional)", "type": "float", "nullable": True},
	"Priority_Index": {"source": "Step 27/29 (optional)", "type": "float", "nullable": True},
}


def _resolve_unified_csv(period_label: str) -> Optional[str]:
	man = get_manifest()
	try:
		path = man.get_latest_output("step36", key_prefix="unified_delivery_csv", period_label=period_label)
		if path and os.path.exists(path):
			return path
	except Exception:
		pass
	candidates = sorted(glob.glob(f"output/unified_delivery_{period_label}_*.csv"))
	return candidates[-1] if candidates else None


def _sample_values(s: pd.Series, k: int = 8) -> str:
	try:
		vals = s.dropna().astype(str).unique()[:k]
		return ", ".join(map(str, vals))
	except Exception:
		return ""


def _is_numeric_dtype(dtype_str: str) -> bool:
	return dtype_str.startswith("int") or dtype_str.startswith("float")


def build_report(df: pd.DataFrame) -> List[str]:
	lines: List[str] = []
	lines.append(f"# Step 36 Manual Column Verification\n")
	for col in df.columns:
		prov = PROVENANCE.get(col, {"source": "(derived/unknown)", "type": "(unspecified)", "nullable": True})
		dtype = str(df[col].dtype)
		n = len(df)
		nn = int(df[col].notna().sum())
		na = int(n - nn)
		uniq = int(df[col].nunique(dropna=True))
		minv = maxv = None
		if _is_numeric_dtype(dtype):
			vals = pd.to_numeric(df[col], errors="coerce")
			minv = float(vals.min()) if vals.notna().any() else None
			maxv = float(vals.max()) if vals.notna().any() else None
		issues: List[str] = []
		# Nullability
		if prov.get("nullable") is False and na > 0:
			issues.append(f"Nulls present ({na}) but column marked non-nullable")
		# Range
		if prov.get("range") and _is_numeric_dtype(dtype):
			lo, hi = prov["range"]
			vals = pd.to_numeric(df[col], errors="coerce")
			too_low = int((vals < lo).sum()) if vals.notna().any() else 0
			too_high = int((vals > hi).sum()) if vals.notna().any() else 0
			if too_low or too_high:
				issues.append(f"Range violations (low={too_low}, high={too_high}) expected [{lo}, {hi}]")
		# Enum strict
		if prov.get("enum"):
			vals = df[col].dropna().astype(str).unique().tolist()
			unexpected = [v for v in vals if v not in prov["enum"]]
			if unexpected:
				issues.append(f"Unexpected enum values (first {min(len(unexpected),10)}): {unexpected[:10]}")
		# Enum soft
		if prov.get("enum_soft"):
			vals = df[col].dropna().astype(str).unique().tolist()
			unexpected = [v for v in vals if v not in prov["enum_soft"]]
			if unexpected:
				issues.append(f"Unexpected values (soft enum) e.g., {unexpected[:10]}")
		# Whitespace
		if dtype == "object":
			s = df[col].dropna().astype(str)
			lead = int(s.str.match(r"^\s+").sum())
			trail = int(s.str.match(r".*\s+$").sum())
			if lead or trail:
				issues.append(f"Whitespace anomalies (leading={lead}, trailing={trail})")
		# Prepare section
		lines.append(f"## {col}")
		lines.append("")
		lines.append(f"- Source: {prov.get('source')}")
		lines.append(f"- Expected Type: {prov.get('type')}  |  Actual Dtype: {dtype}")
		lines.append(f"- Nulls: {na}/{n} ({na/n:.4%})  |  Unique: {uniq}")
		if minv is not None or maxv is not None:
			lines.append(f"- Numeric Min/Max: {minv} / {maxv}")
		samples = _sample_values(df[col])
		if samples:
			lines.append(f"- Sample Values: {samples}")
		if issues:
			lines.append(f"- Issues: {'; '.join(issues)}")
		else:
			lines.append(f"- Issues: None detected")
		lines.append("")
	return lines


def _parse_args() -> argparse.Namespace:
	p = argparse.ArgumentParser(description="Manual verification of Step 36 columns")
	p.add_argument("--target-yyyymm", required=True)
	p.add_argument("--periods", default="A,B")
	return p.parse_args()


def main() -> int:
	args = _parse_args()
	periods = [p.strip().upper() for p in args.periods.split(",") if p.strip()]
	for p in periods:
		pl = get_period_label(args.target_yyyymm, p)
		csv_path = _resolve_unified_csv(pl)
		if not csv_path:
			print(json.dumps({"period": pl, "error": "Unified CSV not found"}))
			continue
		df = pd.read_csv(csv_path)
		lines = build_report(df)
		out_md = csv_path.replace(".csv", "_manual_verification.md")
		with open(out_md, "w", encoding="utf-8") as f:
			f.write("\n".join(lines))
		print(f"Manual verification written: {out_md}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
