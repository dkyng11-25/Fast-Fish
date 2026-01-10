# Step 12 Change Proposal and Rationale

## Executive Summary

Update `src/step12_sales_performance_rule.py` to eliminate synthetic quantity/price derivations, ensure period-accurate unit targets, cap recommendation volume, and remove duplicated/legacy code paths. The aim is to prevent Step 14–style issues (seasonality gaps, incorrect gender defaults, synthetic data, unrealistic volumes, location bias) while keeping the strengths already present (selectivity filters, seasonal blending, labeled outputs).

## Keep
- Period-labeled outputs and manifest registration
- August seasonal blending with explicit sources and fallbacks
- Left-join + diagnostics (preserve unmatched rows; log missingness)
- Selectivity and per-store cap logic already present

## Fixes Needed (and why)
- Use real per‑SPU quantities: join `quantity = base_sal_qty + fashion_sal_qty` (fallback `sal_qty`) on `['str_code','spu_code']` from API period files, not `spu_sales / avg_unit_price`. Reason: avoid synthetic units; stabilize ratios and targets.
- Defensible unit prices: compute `unit_price = spu_sales_amt / quantity` at (store×SPU) with ordered fallbacks (store×subcategory → store overall → cluster×subcategory) and preserve NA. Reason: realistic investment calculations.
- Period scaling: ensure `current_quantity`, `target_period_qty`, and `recommended_quantity_change` are scaled by `SCALING_FACTOR` and that text reflects the same period. Reason: period correctness.
- Remove sales→units synthesis: where per‑SPU quantity is unavailable, skip/flag the case (keep sales metrics separate if needed) instead of converting sales to units. Reason: prevent synthetic data.
- Enforce total per-store unit cap: apply `MAX_TOTAL_QUANTITY_PER_STORE` after filtering/validation in addition to `MAX_RECOMMENDATIONS_PER_STORE`. Reason: avoid unrealistic total volumes per store.
- Validator semantics: confirm contract. If counts required, pass SKU counts (e.g., 1 per SPU change); if units allowed, clamp integerized units (0–100) and skip NA. Reason: meaningful Fast Fish validation.
- Seasonal discipline and logging: require blending for August/autumn flows; log recent/seasonal file paths and weights; log explicit fallbacks. Reason: prevent summer-biased outputs and improve auditability.
- Gender/location handling: avoid synthetic defaults; use presence checks with NA; exclude missing dims from grouping and log missingness. Reason: avoid incorrect “unisex” or location biases.
- Remove duplicate/legacy code paths: the file contains overlapping implementations (older variants). Consolidate to a single coherent implementation. Reason: prevent drift and inconsistent behavior.

## Acceptance Criteria
- Per‑SPU quantities sourced from API; fail-fast with clear message if required fields are missing
- Unit prices computed at most granular defensible grain; NA preserved where not defensible
- All unit targets and changes are scaled to `TARGET_PERIOD_DAYS` and reflected in text
- No unit synthesis from amounts; sales-only metrics not converted to units
- Both per-store item cap and per-store total units cap enforced post-validation
- Validator inputs aligned and clamped; NA cases skipped with logged reasons
- Seasonal blending required for autumn; file paths and weights logged; fallbacks logged
- No synthetic gender/location defaults; missingness logged
- Single, unified code path (duplicates removed)

## Test Plan
- Quantity sourcing: present (sum base+fashion), fallback (`sal_qty`), absent (fail-fast with period+file list)
- Unit price: computed at (store×SPU) with NA-preserving fallbacks; investment totals remain NA if all prices unknown
- Period scaling: verify unit recommendations align with `TARGET_PERIOD_DAYS`
- Caps: verify per-store SPU count cap and per-store total unit cap hold; logs include trimming details
- Validator: confirm counts vs units path; clamping and NA-skip behavior verified
- Seasonality: August run with and without seasonal files; logs show sources, weights, and fallbacks; outputs stable
- No duplicate code: static inspection confirms one set of function definitions and one `__main__` entry point

## Rollout
- Implement behind existing CLI/config; no interface breaks
- Stage on summer and August periods; monitor NA rates (quantity/price), seasonal source logs, validator summaries, cap trimming
- Deploy; monitor first production run for realism of quantities and volume per store

## Backward Compatibility
- Inputs: requires per‑SPU quantity fields in period files; fail-fast otherwise (intentional to prevent synthetic data)
- Outputs: schema unchanged; values grounded in real units and period scaling; volume constrained by caps; manifests unchanged
