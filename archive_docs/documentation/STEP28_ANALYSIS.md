# Step 28 Analysis: Scenario Analyzer

## Hardcoded Values Identified

### Configuration Values
1. **Input File Paths**: 
   - Sales data file: `complete_spu_sales_2025Q2_combined.csv`
   - Product roles file from step 25
   - Price bands file from step 26
   - Gap analysis file from step 27
   - Gap summary file from step 27

2. **Output File Paths**:
   - Scenario analysis results JSON: `scenario_analysis_results.json`
   - Scenario analysis report: `scenario_analysis_report.md`
   - Scenario recommendations CSV: `scenario_recommendations.csv`

3. **Scenario Parameters**: Hardcoded parameters for different scenario types

### Directory Structure
1. **Data Directory**: Hardcoded to `data/` directory
2. **Output Directory**: Hardcoded to `output/` directory

## Synthetic Data Usage Assessment

### ✅ Real Data Usage
- **Scenario Analysis**: Uses actual sales data for scenario impact calculations
- **Product Role Data**: Uses real product role classifications from step 25
- **Price Band Data**: Uses actual price band analysis from step 26
- **Gap Analysis Data**: Uses real gap analysis results from step 27
- **What-If Analysis**: Performs real scenario analysis on actual business data

### ⚠️ Potential Synthetic Data Issues
- **Fixed File Paths**: Hardcoded input/output file locations
- **Static Parameters**: Fixed scenario analysis parameters
- **Fixed Directory Structure**: Hardcoded directory paths

## Data Treatment Assessment

### ✅ Proper Data Handling
- **Real API Data Integration**: Processes actual sales and product data
- **Scenario Engine**: Implements real what-if scenario analysis engine
- **Impact Calculations**: Calculates real impact on sell-through, revenue, and inventory
- **Recommendation Generation**: Creates actionable recommendations based on real data

### ⚠️ Areas for Improvement
1. **Configurable Paths**: Should support custom input/output locations
2. **Dynamic Parameters**: Should allow customization of scenario parameters
3. **Flexible Directory Structure**: Should support different directory configurations

## Business Logic Alignment

### ✅ Aligned with Business Requirements
- **Scenario Analysis**: Correctly implements what-if scenario analysis capabilities
- **Real Data Processing**: Uses actual business data for all scenario calculations
- **No Placeholder Data**: No synthetic or placeholder data detected in core processing
- **Actionable Insights**: Generates business-ready scenario recommendations

## Recommendations and Remediation Plan
- Externalize all file paths and parameters via central `config` and CLI overrides.
- Support YAML/ENV config loading with precedence: CLI > ENV > YAML > defaults.
- Parameterize scenario types and their knobs (e.g., price elasticity, inventory caps).
- Standardize output naming with period and scenario labels.
- Keep directories flexible; resolve via config keys (no hardcoded `data/` or `output/`).

### Proposed Configuration Keys
- data_dir, output_dir
- sales_file, product_roles_file, price_bands_file
- gap_analysis_file, gap_summary_file
- scenario.type, scenario.params (dict of key/value)
- run.period_label (e.g., 202508A), run.timestamp_suffix (bool)

### Proposed CLI Flags
- --data-dir, --output-dir
- --sales-file, --product-roles-file, --price-bands-file
- --gap-analysis-file, --gap-summary-file
- --scenario TYPE
- --param key=value (repeatable)
- --period-label 202508A
- --config path/to/config.yaml

### Output Naming Standard
- scenario_analysis_results_{scenario}_{period}.json
- scenario_analysis_report_{scenario}_{period}.md
- scenario_recommendations_{scenario}_{period}.csv
- Optional timestamp suffix when `--timestamp` or `config.run.timestamp_suffix=true`

### Validation & QA Checklist
- Validate inputs exist and schemas match expectations.
- Row counts > 0; joins by `SPU_CODE`/`STORE_CODE` preserve expected cardinality.
- Scenario math sanity: price up -> units down given elasticity; inventory caps respected.
- Deterministic runs (set random seeds if any stochastic elements).

### Backward Compatibility
- Provide defaults matching prior hardcoded values.
- Auto-detect legacy filenames when explicit inputs are not provided.
- Emit deprecation warnings for legacy paths; do not break existing pipelines.

### Risks & Mitigations
- Misconfigured paths: strict validation and helpful error messages.
- Parameter misuse: schema for `scenario.params` with type checking and bounds.
- Oversized outputs: support gzip for large JSON/CSV via `--compress`.

### Action Items
1) Remove hardcoded paths/dirs and wire to config/CLI.
2) Implement output naming helper using period/scenario.
3)  - Integrate input validation and join integrity checks.
  - Add unit tests; update CI to run them.
  - Publish updated docs and sample config.

### Configuration Limitations
- **Fixed Analysis Parameters**: Hardcoded scenario parameters may not suit all business scenarios
- **Static File Names**: Fixed output file names may not be optimal for all deployments

### Environment Variable Mapping (examples)
- **DATA_DIR** → `data_dir`
- **OUTPUT_DIR** → `output_dir`
- **SALES_FILE** → `sales_file`
- **RUN_PERIOD_LABEL** → `run.period_label`
- **RUN_TIMESTAMP_SUFFIX** → `run.timestamp_suffix`
- **SCENARIO_TYPE** → `scenario.type`
- **SCENARIO_PARAMS__ELASTICITY** → `scenario.params.elasticity`
- Note: nested keys use double underscore `__` to denote hierarchy (e.g., `SCENARIO_PARAMS__PRICE_DELTA_PCT`).

### Implementation Outline (code sketch)
```python
import os
import argparse
from pathlib import Path
import yaml

DEFAULTS = {
    "data_dir": "data",
    "output_dir": "output",
    "sales_file": "complete_spu_sales_2025Q2_combined.csv",
    "product_roles_file": "step25_product_roles.csv",
    "price_bands_file": "step26_price_bands.csv",
    "gap_analysis_file": "step27_gap_analysis.csv",
    "gap_summary_file": "step27_gap_summary.csv",
    "run": {"period_label": "2025Q2A", "timestamp_suffix": False},
    "scenario": {"type": "price_increase", "params": {}}
}

def deep_update(base, upd):
    for k, v in (upd or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_update(base[k], v)
        else:
            base[k] = v
    return base

def load_yaml(path):
    p = Path(path)
    if p.exists():
        with p.open("r") as f:
            return yaml.safe_load(f) or {}
    return {}

def load_env():
    out = {}
    for key, val in os.environ.items():
        # Map ENV like RUN_PERIOD_LABEL → {run: {period_label: val}}
        parts = key.lower().split("__")
        parts = [p.replace("_", ".") for p in parts]
        # flatten underscores: RUN_PERIOD_LABEL → ["run.period.label"] then split again
        path = []
        for token in parts:
            path.extend(token.split("."))
        # Only consider known prefixes
        if path[0] in {"data", "output", "sales", "product", "price", "gap", "run", "scenario"}:
            cursor = out
            for p in path[:-1]:
                cursor = cursor.setdefault(p, {})
            cursor[path[-1]] = val
    return out

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--data-dir")
    ap.add_argument("--output-dir")
    ap.add_argument("--sales-file")
    ap.add_argument("--product-roles-file")
    ap.add_argument("--price-bands-file")
    ap.add_argument("--gap-analysis-file")
    ap.add_argument("--gap-summary-file")
    ap.add_argument("--scenario")
    ap.add_argument("--param", action="append", help="key=value; repeatable")
    ap.add_argument("--period-label")
    ap.add_argument("--timestamp", action="store_true")
    ap.add_argument("--compress", action="store_true")
    return ap.parse_args()

def cli_to_cfg(args):
    cfg = {}
    if args.data_dir: cfg["data_dir"] = args.data_dir
    if args.output_dir: cfg["output_dir"] = args.output_dir
    if args.sales_file: cfg["sales_file"] = args.sales_file
    if args.product_roles_file: cfg["product_roles_file"] = args.product_roles_file
    if args.price_bands_file: cfg["price_bands_file"] = args.price_bands_file
    if args.gap_analysis_file: cfg["gap_analysis_file"] = args.gap_analysis_file
    if args.gap_summary_file: cfg["gap_summary_file"] = args.gap_summary_file
    if args.period_label: deep_update(cfg, {"run": {"period_label": args.period_label}})
    if args.timestamp: deep_update(cfg, {"run": {"timestamp_suffix": True}})
    if args.scenario: deep_update(cfg, {"scenario": {"type": args.scenario}})
    if args.param:
        params = {}
        for item in args.param:
            if "=" in item:
                k, v = item.split("=", 1)
                # basic type coercion
                if v.lower() in {"true", "false"}: v = v.lower() == "true"
                else:
                    try:
                        v = int(v)
                    except ValueError:
                        try:
                            v = float(v)
                        except ValueError:
                            pass
                params[k] = v
        deep_update(cfg, {"scenario": {"params": params}})
    return cfg

def validate(cfg):
    # Add schema checks (paths exist, required columns, bounds for params, etc.)
    pass

def load_config():
    args = parse_args()
    cfg = deep_update({}, DEFAULTS.copy())
    if args.config:
        cfg = deep_update(cfg, load_yaml(args.config))
    cfg = deep_update(cfg, load_env())
    cfg = deep_update(cfg, cli_to_cfg(args))
    validate(cfg)
    return cfg, args

### Definition of Done
- **Config precedence works**: CLI > ENV > YAML > Defaults verified by unit tests.
- **Paths configurable**: No hardcoded `data/` or `output/`; all inputs/outputs overridable.
- **Standard output names**: Files include `{scenario}` and `{period}` (and timestamp when enabled).
- **Validation & errors**: Clear, actionable messages on misconfig or schema/join issues.
- **Backward-compatible**: Defaults mirror legacy behavior; deprecations logged not fatal.
- **Docs & examples**: README and sample YAML updated; CLI help covers parameters.

### Open Questions
- Should we support multi-scenario batch runs in one invocation (e.g., `--scenario price_increase,price_decrease`)?
- How strict should param type coercion be (schema-driven vs best-effort)?
- Should unknown `--param` keys be rejected (fail-fast) or passed through to engine with a warning?
