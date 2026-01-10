### Scope

- **Targets**: `src/step8_imbalanced_rule.py` (root vs reference) and `src/config.py` (read-only for paths/periods).
- **Non-goals**: Changing unrelated steps or enabling trending engines. No behavioral changes beyond Step 8.

### High-level comparison (Root vs Reference)

- **Period-aware data resolution**
  - Root: Uses `src.config` (`get_current_period`, `get_api_data_files`, `get_output_files`) with layered fallbacks and period-labeled outputs.
  - Reference: Builds dynamic file paths but has more ad-hoc fallbacks; outputs are not period-labeled.

- **Seasonal blending (August enhancement)**
  - Root: Optional seasonal blending for August (weighted recent vs prior-year seasonal) for both planning and quantity.
  - Reference: No seasonal blending.

- **Quantity derivation (critical)**
  - Root: Requires authoritative `quantity` or derives from `base_sal_qty + fashion_sal_qty` or `sal_qty`; fails fast if none present.
  - Reference: If missing, may proxy from `spu_sales_amt / 300.0` (estimation) or fill zeros.

- **Merging strategy and cluster column**
  - Root: Prefers safe left merges with diagnostics; uses `'Cluster'` in groupby but normalizes to `'cluster_id'` in results.
  - Reference: Uses inner merges; only `'Cluster'` is used.

- **Imbalance detection and gating**
  - Root: Z-score thresholds tuned by level, per-store cap (`MAX_TOTAL_ADJUSTMENTS_PER_STORE=8` for SPU), integer quantity rounding, increase-only redistribution strategy by default, Fast Fish validation gate (keeps only compliant), severity tiers tailored by level.
  - Reference: Simpler thresholds; no per-store cap; fractional quantities; no Fast Fish validation.

- **Outputs**
  - Root: Period-labeled results/cases/z-score/summary; backward-compatible files preserved for downstream steps.
  - Reference: Simple outputs without period labels.

- **CLI**
  - Root: CLI for yyyymm/period/analysis-level/target labels and optional z-threshold override.
  - Reference: No CLI.

### Risks and mitigations

- **Missing real quantity fields**
  - Risk: Root fails fast (by design) if `quantity` cannot be derived from authoritative fields.
  - Mitigation: Document strict behavior; if proxy fallback is ever needed, add an opt-in env flag (e.g., `RULE8_ALLOW_QUANTITY_PROXY=1`) in a separate, controlled edit. Default remains strict.

- **Planning schema variance**
  - Risk: Planning files may be missing some grouping columns; reference builds a fallback planning dataset from category sales.
  - Mitigation: Consider porting the fallback builder behind a flag (e.g., `RULE8_ALLOW_PLANNING_FALLBACK=1`) later. Default remains current strict behavior.

- **Cluster column inconsistency**
  - Risk: Downstream consistency issues mixing `'Cluster'` and `'cluster_id'`.
  - Mitigation: After loading clusters, mirror columns so both `Cluster` and `cluster_id` exist if either is present; use `cluster_id` in results and keep `Cluster` for analyses/grouping and backward-compatible outputs.

- **Validator unavailability**
  - Risk: With no Fast Fish validator, root logs and skips validation; cases remain but may not be approved.
  - Mitigation: Keep current behavior. Do not add fallback approvals.

### Plan of record (no code changes yet)

1) Documentation (this file + spec) before edits.
2) Minimal code edits (in next step), preserving defaults:
   - Normalize/mirror cluster columns early so both `Cluster` and `cluster_id` are present; use `cluster_id` in results and `Cluster` in grouping where required.
   - Keep root’s seasonal blending, quantity derivation, left merges, CLI, outputs, integer rounding, per-store cap, and Fast Fish validation.
   - Optionally add guarded planning fallback and quantity proxy in a later commit if required (flags off by default).
3) Diagnostics and testing:
   - Run Step 8 with explicit period and level; confirm period-labeled outputs.
   - Validate counts, quantity rounding, and presence of sell-through metrics when validator is available.
4) Acceptance criteria:
   - End-to-end success on both `subcategory` and `spu` levels with correct outputs and no regressions to downstream steps (Step 13/14).

### Operational notes

- Always pass `--yyyymm` and `--period` when running to avoid default drift.
- Example:
  - `python src/step8_imbalanced_rule.py --yyyymm 202509 --period A --analysis-level spu --target-yyyymm 202509 --target-period A`


