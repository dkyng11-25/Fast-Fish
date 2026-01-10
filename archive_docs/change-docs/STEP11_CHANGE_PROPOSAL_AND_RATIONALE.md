# Step 11 Change Proposal and Rationale

## Executive Summary

Update `src/step11_missed_sales_opportunity.py` to fully ground opportunity sizing in real unit quantities, ensure period accuracy, constrain volume, and avoid synthetic data. Keep existing selectivity and seasonal blending; replace per‑SPU unit estimation via store‑average price with per‑SPU quantities from API; compute defensible unit prices; enforce guardrails to prevent Step 14–style issues (seasonality bias, incorrect gender defaults, synthetic data, unrealistic volumes, display location bias).

## Keep
- Period-labeled outputs and manifest registration
- Seasonal blending for August with explicit sources and fallbacks
- Left-join + diagnostics; NA-preserving calculations
- Strong selectivity filters and per-store cap

## Fixes Needed (and why)
- Real per‑SPU quantities: join `quantity = base_sal_qty + fashion_sal_qty` (fallback `sal_qty`) on `['str_code','spu_code']` instead of estimating `spu_sales / avg_unit_price`. Avoid synthetic backfills. Reason: eliminate synthetic data; produce realistic unit targets.
- Defensible unit prices: compute `unit_price = spu_sales_amt / quantity` at (store×SPU), with ordered fallbacks (store×subcategory → store → cluster×subcategory). Preserve NA. Reason: accurate investment and safer unit math.
- Period scaling: ensure current/target quantities are scaled by `SCALING_FACTOR`; align `recommendation_text` with math. Reason: period correctness.
- No unit synthesis from amounts: when per‑SPU quantity missing, skip/flag; do not convert sales to units. Reason: avoid reintroducing synthetic quantities.
- Validator semantics: confirm contract. If counts required, use SKU counts (e.g., 0→1 for ADD_NEW); if units permitted, clamp integerized units (0–100); skip NA. Reason: meaningful sell-through validation.
- Seasonality policy: require blending for August/autumn; log exact recent/seasonal paths and weights; log fallbacks. Reason: prevent summer dominance; improve auditability.
- Gender/location handling: avoid synthetic defaults; use presence checks and NA; exclude missing dims from grouping; log missingness. Reason: avoid “mostly unisex” and location bias.

## Acceptance Criteria
- Per‑SPU quantities sourced from API; fail-fast if required fields absent
- Unit prices computed from amount/quantity at the finest available grain; NA preserved
- Unit targets/changes correctly scaled to `TARGET_PERIOD_DAYS` and reflected in text
- No synthetic unit fallbacks; sales-to-unit conversions removed
- Validator inputs aligned and clamped; NA cases skipped with logs
- Seasonal blending enforced for autumn; sources and weights logged
- No synthetic gender/location defaults; missingness logged

## Test Plan
- Quantity sourcing: present (sum equals base+fashion), fallback (`sal_qty`), absent (fail-fast with period+file list)
- Ratio/targets: verify based on real quantities and scaling
- Validator: exercise counts vs units path; clamping and NA-skip behavior
- Selectivity/cap: per-store limit holds post-validation; trimming logs show stores/rows removed
- Seasonality: August with/without seasonal files; logs reflect sources/fallbacks; outputs stable

## Rollout
- Implement behind current CLI/config; no interface breaks
- Stage on summer and August periods; monitor quantity/price NA rates, seasonal logs, validator summaries, capping stats

## Backward Compatibility
- Inputs: requires per‑SPU quantity fields; fail-fast otherwise
- Outputs: schema unchanged; values now grounded in real units and period scaling; volume constrained by cap
