#!/usr/bin/env python3
"""
Step IO Contract Test (Steps 1–36) — Period-Aware

Validates, for a target period, that each step:
- Has period-matching outputs registered in manifest and present on disk ("out").
- Has required inputs (where dependencies are defined) resolvable to period-matching source outputs ("in").

Notes:
- Target period derived from env: PIPELINE_TARGET_YYYYMM (default '202509'), PIPELINE_TARGET_PERIOD (default 'B').
- Uses manifest as source of truth. Steps with no outputs for the target period are SKIPPED, not failed.
- Dependencies mirrored from src/pipeline_manifest.get_input mapping.

Run:
  python test_step_io_contracts.py
  PIPELINE_TARGET_YYYYMM=202509 PIPELINE_TARGET_PERIOD=A python test_step_io_contracts.py
"""
import os
import sys
import json
from typing import Dict, List

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.append(os.path.join(project_root, "src"))

from src.pipeline_manifest import get_manifest  # type: ignore
from src.config import get_period_label  # type: ignore

# Mirror the dependency mapping used by PipelineManifest.get_input()
DEPENDENCY_MAP: Dict[str, Dict[str, str]] = {
    "step14": {"consolidated_rules": "step13:consolidated_rules"},
    "step15": {"fast_fish_format": "step14:enhanced_fast_fish_format"},
    "step17": {"fast_fish_format": "step14:enhanced_fast_fish_format"},
    "step18": {"augmented_recommendations": "step17:augmented_recommendations"},
    "step19": {"detailed_recommendations": "step13:detailed_spu_recommendations"},
    "step20": {
        "detailed_spu_recommendations": "step19:detailed_spu_breakdown",
        "store_level_aggregation": "step19:store_level_aggregation",
        "cluster_subcategory_aggregation": "step19:cluster_subcategory_aggregation",
    },
    "step21": {"spu_recommendations": "step19:detailed_spu_breakdown"},
}

TARGET_STEPS: List[str] = [f"step{i}" for i in range(1, 37)]


def load_manifest_json() -> Dict:
    man = get_manifest()
    # Access internal JSON representation safely by reading the file directly
    # This avoids relying on private attributes.
    manifest_path = getattr(man, "manifest_path", os.path.join("output", "pipeline_manifest.json"))
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_target_period_label() -> str:
    yyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM", "202509")
    period = os.environ.get("PIPELINE_TARGET_PERIOD", "B")
    return get_period_label(yyyymm, period)


def _matches_period(key: str, meta: Dict, period_label: str) -> bool:
    # Match by explicit metadata, key suffix, or filepath pattern
    md = meta.get("metadata", {}) if isinstance(meta, dict) else {}
    md_pl = str(md.get("period_label", ""))
    if md_pl.endswith(period_label):
        return True
    if key.endswith(period_label):
        return True
    fp = str(meta.get("file_path", ""))
    if f"_{period_label}_" in fp or fp.endswith(f"_{period_label}.csv") or fp.endswith(f"_{period_label}.xlsx") or fp.endswith(f"_{period_label}.json"):
        return True
    return False


def _latest_by_created(items: List[tuple]) -> List[tuple]:
    """Given list of (key, meta) where meta has 'created', return the newest per key.
    Here we just sort by created and keep all (since keys are unique per output)."""
    # Sort descending by created timestamp to let caller pick first
    return sorted(items, key=lambda kv: (kv[1].get("created") or ""), reverse=True)


def check_outputs(step_name: str, man_json: Dict, period_label: str) -> List[str]:
    errors: List[str] = []
    step = man_json.get("steps", {}).get(step_name)
    if not step:
        return errors  # step not present -> skip quietly
    outputs = step.get("outputs", {}) or {}
    # Filter to period-matching outputs
    period_items = [(k, v) for k, v in outputs.items() if _matches_period(k, v, period_label)]
    if not period_items:
        # No outputs for this period -> skip rather than fail
        return errors
    # Prefer items whose key/file_path explicitly include the period label; if present, ignore
    # metadata-only matches (e.g., alias outputs) to avoid false negatives.
    primary: List[tuple] = []
    fallback: List[tuple] = []
    for out_key, meta in period_items:
        fp = str(meta.get("file_path", ""))
        has_key_period = out_key.endswith(period_label)
        has_fp_period = (
            f"_{period_label}_" in fp
            or fp.endswith(f"_{period_label}.csv")
            or fp.endswith(f"_{period_label}.xlsx")
            or fp.endswith(f"_{period_label}.json")
        )
        if has_key_period or has_fp_period:
            primary.append((out_key, meta))
        else:
            fallback.append((out_key, meta))

    items_to_check = primary if primary else fallback

    # Validate existence for latest items
    for out_key, meta in _latest_by_created(items_to_check):
        path = meta.get("file_path")
        if not path:
            errors.append(f"{step_name}:{out_key} missing file_path in manifest")
            continue
        if not os.path.exists(path):
            errors.append(f"{step_name}:{out_key} path does not exist -> {path}")
            continue
        # Optional consistency check
        meta_exists = meta.get("exists")
        if meta_exists is False:
            # Do not fail for stale 'exists' flag; just warn
            pass
    return errors


def check_inputs(step_name: str, man_json: Dict, period_label: str) -> List[str]:
    errors: List[str] = []
    deps = DEPENDENCY_MAP.get(step_name)
    if not deps:
        return errors  # no declared deps -> skip
    steps = man_json.get("steps", {})
    for input_type, dep in deps.items():
        try:
            src_step, src_output = dep.split(":")
        except ValueError:
            errors.append(f"{step_name}:{input_type} has invalid dependency spec '{dep}'")
            continue
        src = steps.get(src_step, {})
        outputs = src.get("outputs", {}) or {}
        # Find candidates that both match the expected output key and period
        candidates = []
        for out_key, meta in outputs.items():
            if out_key == src_output or out_key.startswith(src_output):
                if _matches_period(out_key, meta, period_label):
                    candidates.append((out_key, meta))
        if not candidates:
            errors.append(f"{step_name}:{input_type} requires {src_step}:{src_output} for {period_label} but none found")
            continue
        # Ensure at least one candidate file exists
        ok = False
        for out_key, meta in _latest_by_created(candidates):
            path = meta.get("file_path")
            if path and os.path.exists(path):
                ok = True
                break
        if not ok:
            errors.append(f"{step_name}:{input_type} depends on missing file(s) for {period_label} -> {src_step}:{src_output}")
    return errors


def main() -> int:
    man_json = load_manifest_json()
    total_errors: List[str] = []
    checked_steps = 0
    skipped_steps = 0
    period_label = _get_target_period_label()

    for step in TARGET_STEPS:
        out_errs = check_outputs(step, man_json, period_label)
        in_errs = check_inputs(step, man_json, period_label)
        if not (step in man_json.get("steps", {}) and out_errs == [] and any(True for _ in man_json.get("steps", {}).get(step, {}).get("outputs", {}) )):
            # Determine skip when no period-matching outputs
            step_data = man_json.get("steps", {}).get(step, {})
            outs = step_data.get("outputs", {}) or {}
            has_period_out = any(_matches_period(k, v, period_label) for k, v in outs.items())
            if not has_period_out:
                skipped_steps += 1
                print(f"[IO-SKIP] {step} (no outputs for {period_label})")
                continue
        if out_errs or in_errs:
            total_errors.extend(out_errs)
            total_errors.extend(in_errs)
        else:
            checked_steps += 1
            print(f"[IO-OK] {step}")

    if total_errors:
        print("\n[IO-ERRORS]")
        for e in total_errors:
            print(" - ", e)
        print(f"\nChecked steps: {checked_steps} | Skipped (no period outputs): {skipped_steps} | Failures: {len(total_errors)}")
        return 2

    print(f"\nAll IO checks passed. Checked steps: {checked_steps} | Skipped: {skipped_steps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
