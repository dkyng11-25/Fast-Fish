#!/usr/bin/env python3
import os
import sys
import json
import glob
import argparse
from typing import List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def _scan_forbidden(paths: List[str]) -> List[str]:
    forbidden_suffixes = [
        "complete_spu_sales_2025Q2_combined.csv",
        "complete_category_sales_2025Q2_combined.csv",
        "store_config_2025Q2_combined.csv",
        "_combined.csv",
    ]
    hits: List[str] = []
    for base in paths:
        for dirpath, _, filenames in os.walk(base):
            # Skip quarantine directories explicitly
            if "_forbidden_quarantine" in dirpath:
                continue
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                if any(fp.endswith(suf) for suf in forbidden_suffixes):
                    hits.append(fp)
    return hits


def _reset_manifest(path: str = os.path.join("output", "pipeline_manifest.json")) -> None:
    try:
        from src.pipeline_manifest import reset_manifest
    except Exception:
        from pipeline_manifest import reset_manifest  # type: ignore
    reset_manifest(delete_file=True, manifest_path=path)


def _clean_step28_outputs() -> None:
    patterns = [
        os.path.join("output", "scenario_analysis_results*.json"),
        os.path.join("output", "scenario_analysis*_report.md"),
        os.path.join("output", "scenario*_recommendations.csv"),
        os.path.join("output", "scenario_analysis_results.json"),
        os.path.join("output", "scenario_analysis_report.md"),
        os.path.join("output", "scenario_recommendations.csv"),
    ]
    removed = 0
    for pat in patterns:
        for fp in glob.glob(pat):
            try:
                os.remove(fp)
                removed += 1
            except Exception:
                pass
    print(f"[PREFLIGHT] Cleaned Step 28/generic outputs: removed={removed}")


def _assert_required_api_inputs(yyyymm: str, period: str) -> None:
    required = [
        os.path.join("data", "api_data", f"complete_spu_sales_{yyyymm}{period}.csv"),
        os.path.join("data", "api_data", f"store_config_{yyyymm}{period}.csv"),
        # store_sales is not strictly required if SPU includes splits, but check presence for ratios where needed
        # os.path.join("data", "api_data", f"store_sales_{yyyymm}{period}.csv"),
    ]
    missing = [p for p in required if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(f"Missing required raw API inputs for {yyyymm}{period}: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Preflight for raw-only fresh runs (Step 28 and downstream)")
    parser.add_argument("--periods", nargs="+", required=True, help="Period labels like 202509A 202509B 202510A 202510B")
    args = parser.parse_args()

    # 1) Scan for forbidden combined files
    hits = _scan_forbidden(["data", "output"])
    if hits:
        print("[PREFLIGHT] Forbidden combined files present:")
        for h in hits:
            print(f"  - {h}")
        sys.exit(2)
    print("[PREFLIGHT] No forbidden combined files detected")

    # 2) Reset pipeline manifest
    _reset_manifest()
    print("[PREFLIGHT] Manifest reset: output/pipeline_manifest.json")

    # 3) Clean Step 28 and generic outputs
    _clean_step28_outputs()

    # 4) Assert required inputs for each target period
    for pl in args.periods:
        if not isinstance(pl, str) or len(pl) not in (6, 7):
            raise SystemExit(f"Invalid period label: {pl}")
        yyyymm = pl[:6]
        p = pl[6:] if len(pl) == 7 else None
        if p not in ("A", "B"):
            raise SystemExit(f"Invalid half period for {pl}; expected A or B")
        _assert_required_api_inputs(yyyymm, p)
        print(f"[PREFLIGHT] Inputs OK for {pl}")

    print("[PREFLIGHT] All checks passed")


if __name__ == "__main__":
    main()


