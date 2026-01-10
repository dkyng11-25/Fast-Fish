# Pipeline Change Summary and Guidelines (Steps 7–18)

## Purpose
Consolidate the findings from our step‑by‑step analysis (Steps 7–18) into one actionable document: what we observed, how we assessed it, and the cross‑cutting guardrails to apply when implementing changes in this delicate pipeline.

## How the observations were derived
- Compared production vs reference implementations for each step (7–18) using direct file reads of `src/` and `backup-boris-code/` counterparts.
- Anchored the review to known Step 14 failure modes (seasonality bias, incorrect gender/location, synthetic data, unrealistic volumes, weak realism checks) and traced those risks upstream and downstream.
- Verified period/manifest alignment, grouping, and data provenance for each step; flagged any heuristic/synthetic paths and count/unit conflation.
- Produced step‑specific change proposals (see `change-docs/STEPxx_CHANGE_PROPOSAL_AND_RATIONALE.md`).

## Cross‑cutting themes (what to enforce everywhere)
- Real unit quantities only: Do not infer units from money (no `sales ÷ price` proxies). Prefer real SPU quantities (e.g., `base_sal_qty + fashion_sal_qty`, or `sal_qty`).
- No synthetic defaults for dimensions: Never inject blanket Season/Gender/Location defaults (e.g., “夏/中/前台”). Carry NA and exclude from grouping when missing.
- Seasonality discipline: Use autumn context for September/October runs. Pull period‑aligned baselines from Step 15; avoid summer‑dominated data.
- Count vs unit semantics: Keep SPU counts (types) separate from unit quantities. Never convert unit deltas into SPU counts.
- Real cluster grouping only: Use actual cluster files (`output/clustering_results_spu.csv`) to derive store groups; remove modulo/hash grouping fallbacks.
- Realism constraints: Apply per‑store caps after validation to prevent hundreds of SPU types or extreme unit changes.
- Manifest alignment and periodization: Resolve inputs by manifest keys with period match; write period‑labeled outputs and register them.
- NA‑preserving math and logging: Use NA instead of fabricated values. Compute percentages only with valid denominators. Log NA/mismatch counts and source file paths.
- Validator semantics/clamping: Ensure the sell‑through validator receives the correct magnitude (counts vs units) and clamp to reasonable ranges; skip NA.
- Investment integrity: Compute `unit_price = amount ÷ quantity` only when both exist; otherwise keep NA. Do not default prices or set investment to 0 to hide unknowns.

## Per‑step focus areas
- `src/step7_missing_category_rule.py`
  - Keep: period‑aware I/O. Ensure merges preserve rows and surface unmatched diagnostics.
  - Focus: no synthetic category backfills; log missingness; maintain real unit usage downstream.

- `src/step8_imbalanced_rule.py`
  - Enforce real unit quantities; derive only from authoritative quantity fields; fail fast if absent.
  - Remove synthetic gender/season/location defaults; use NA. Build grouping keys only from real columns.
  - Add per‑store cap and align recommended quantity with constrained value. NA‑preserving numerics.

- `src/step9_below_minimum_rule.py`
  - Replace money‑derived proxies with unit metrics. Define “below minimum” on units.
  - Compute positive unit increases only from unit math. Cap per‑store after validation.
  - Preserve unknown `unit_price` as NA; require explicit seasonal blending and path logging for autumn.

- `src/step10_spu_assortment_optimization.py`
  - Remove `sales/estimated_price` heuristics; join real quantities and compute real unit prices.
  - Scale metrics to the target period; enforce per‑store cap. Align validator semantics.
  - Avoid synthetic gender/location defaults; require explicit seasonal blending for autumn.

- `src/step11_missed_sales_opportunity.py`
  - Use per‑SPU unit quantities, not store‑average derived units.
  - Compute price at store×SPU where possible; NA if not defensible. No synthetic fallbacks.
  - Period scaling and no unit synthesis from amounts; validator semantics + clamping.

- `src/step12_sales_performance_rule.py`
  - Use SPU units and real prices; NA‑preserving fallbacks only. Enforce item and total‑unit caps post‑validation.
  - Consolidate legacy/duplicate paths; one coherent implementation.

- `src/step13_consolidate_spu_rules.py`
  - Make it consolidation‑only. Disable synthetic trend/fashion generators by default (no randomness, no synthetic clusters, no default dims).
  - Do not fabricate `all_rule_suggestions.csv` from store summaries. Preserve NA investment. Align output paths and period‑labeled files; manifest registration.

- `src/step14_create_fast_fish_format.py`
  - Separate SPU counts from unit deltas: do not use unit `recommended_quantity_change` to set `Target_SPU_Quantity`.
  - Remove synthetic defaults; require real cluster mapping; no modulo grouping.
  - Remove blanket 5% “Expected_Benefit”; compute only from validated inputs or leave NA.

- `src/step15_download_historical_baseline.py`
  - Require real clustering and period‑aligned baselines (YOY same month/period). No hash/modulo groups.
  - Align manifest keys with Step 14; period matching required. NA‑safe YoY math; no fabricated amounts/quantities.

- `src/step16_create_comparison_tables.py`
  - Consume Step 15 outputs only; disable synthetic grouping utilities. 
  - NA‑preserving percent math; block‑level schema guards; period‑matching enforcement.

- `src/step17_augment_recommendations.py`
  - Use real clusters/groups from Step 14; no modulo/hash grouping.
  - Gate trending to real‑data provenance; remove heuristic/synthetic trend scores; preserve `Target_Style_Tags`.
  - Keep SPU counts as counts; do not mix units. NA‑preserving trend fields with provenance logs.

- `src/step18_validate_results.py`
  - Compute sell‑through using Step 15 baselines and real clusters; no hard‑coded May baselines.
  - No revenue→unit heuristics; NA where joins fail. 
  - Visibility fields (temperature/confidence/capacity) only when provenance is real; otherwise Unknown/NA.

## Global acceptance criteria
- Inputs resolved via manifest with period alignment; outputs saved with period labels and registered, per file.
- Grouping based on real clusters; any missing clusters result in skip/NA, never fabricated groups.
- Quantities and counts kept separate; all unit‑based math uses real quantities only.
- No synthetic defaults for dims or prices; NA preserved; log counts and paths for audit.
- Per‑store caps enforced post‑validation for both item count and total unit deltas.
- Validator inputs aligned (counts vs units) and clamped; NA cases skipped with logs.

## Test strategy
- Unit tests (step‑scoped)
  - Quantity sourcing (presence, fallback, fail‑fast), NA‑preserving math, percent denominators > 0 only, cap enforcement, validator clamping.
  - Manifest/period alignment; schema guards for each block; parsing robustness for `Target_Style_Tags`.
- Integration tests (pipeline)
  - Summer vs autumn periods; verify seasonal blending/YOY baselines used and logged.
  - Downstream compatibility: period‑labeled outputs present; no synthetic columns/values introduced.

## Rollout plan
- Phase 1 (safe): Remove synthetic defaults/heuristics, enforce manifest alignment, apply NA‑preserving guards, and disable synthetic trend/enhancement code paths by default.
- Phase 2 (strict): Require period‑aligned baselines in Steps 14–18; enforce validator clamping and per‑store caps across steps.
- Phase 3 (polish): Consolidate logs/diagnostics; ensure all steps emit succinct audit lines (source file paths, NA counts, cap trimming, validator summaries).

## Risks and mitigations
- Data gaps cause broader NA propagation
  - Mitigation: Clear logs, acceptance that NA>0 is correct over synthetic fills; targeted backfills only where real sources exist.
- Downstream expectations of synthetic values
  - Mitigation: Communicate schema/value changes; provide compatibility notes and period‑labeled outputs.
- Performance regressions from additional checks/logs
  - Mitigation: Use flags for trending; keep consolidation/trending disabled in production unless needed.

## Traceability (per‑step proposals)
- See `change-docs/STEP7_STEP8_CHANGE_PROPOSAL_AND_RATIONALE.md`
- See `change-docs/STEP9_CHANGE_PROPOSAL_AND_RATIONALE.md`
- See `change-docs/STEP10_CHANGE_PROPOSAL_AND_RATIONALE.md`
- See `change-docs/STEP11_CHANGE_PROPOSAL_AND_RATIONALE.md`
- See `change-docs/STEP12_CHANGE_PROPOSAL_AND_RATIONALE.md`
- See `change-docs/STEP13_CHANGE_PROPOSAL_AND_RATIONALE.md`
- See `change-docs/STEP14_CHANGE_PROPOSAL_AND_RATIONALE.md`
- See `change-docs/STEP15_CHANGE_PROPOSAL_AND_RATIONALE.md`
- See `change-docs/STEP16_CHANGE_PROPOSAL_AND_RATIONALE.md`
- See `change-docs/STEP17_CHANGE_PROPOSAL_AND_RATIONALE.md`
- See `change-docs/STEP18_CHANGE_PROPOSAL_AND_RATIONALE.md`
