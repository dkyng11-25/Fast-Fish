# Step 14 Change Proposal and Rationale

## Executive Summary

Update `src/step14_create_fast_fish_format.py` to strictly avoid synthetic data, separate unit quantities from SPU counts, require real autumn context where applicable, and cap volumes to keep outputs realistic. Align gender and display location handling with source data (NA when missing). Remove or gate heuristics (e.g., default sales amounts, modulo clusters, price-based benefits) to prevent reintroduction of Step 14 issues: seasonality bias, incorrect gender defaults, synthetic data, unrealistic volumes, and front/back-only bias.

## What’s Good (keep)
- Loads detailed SPU-level consolidated file from Step 13 when present
- Uses cluster mapping for group creation (when available)
- Dimensional attributes are merged from real store_config; missing dims preserved as NA
- Customer mix and season percentages are computed from actual data (no forced 100% men/women only)
- Historical sell-through calculation uses quantities (not revenues) when data exists
- Registers output in manifest; clear logging

## Gaps and Risks (linked to prior failures)
1) Unit quantities vs SPU counts are conflated
- `integrate_rule_adjustments` sums `recommended_quantity_change` (unit deltas) and adds to `Target_SPU_Quantity` (a count of distinct SPUs). This converts units into counts and leads to unrealistic SPU type changes (prior issue #4).

2) Synthetic fallbacks and defaults
- `spu_sales_amt` set to 1000 when not derivable; weather defaults to 25°C; historical sell-through defaults to 85%. These produce fabricated metrics (prior issue #3). Prefer NA and skip dependent metrics.

3) Synthetic store-grouping when clusters missing
- Fallback modulo-based grouping invents clusters (prior issue #3) and can bias seasonality/temperature aggregation (#1).

4) Target SPU count heuristics
- If rule fields absent, uses avg sales per SPU with ±10% to set `Target_SPU_Quantity` → synthetic and can drift high (prior issue #4).

5) Seasonality discipline
- Dims come from store_config; good. But ensure autumn context is used deliberately: Step relies on historical September data for ST% but not for dims. Risk of summer dominance (#1) if config is stale or biased.

6) Gender and display location handling
- Mode selection is good; but any fallback must be NA (not forced to front/back or unisex). Presently mapping function returns '未知' string; prefer keeping NA as data value and render user-facing string downstream (prior issue #2 and #5).

7) “Expected_Benefit” as 5% of sales
- Synthetic scalar unrelated to validated sell-through improvements. Encourages over-interpretation of benefit (#3, #4).

8) Periodization
- Hard-coded `TARGET_YEAR/TARGET_MONTH` and env-only period; should be tied to pipeline period to avoid drift.

## Required Changes

- Separate unit quantities from SPU counts
  - Do not add unit `recommended_quantity_change` into `Target_SPU_Quantity`.
  - Define `Target_SPU_Quantity` changes from counts of distinct SPUs recommended for add/remove (from upstream rules), not unit deltas. If unavailable, leave target equal to current or NA; never synthesize from unit math.

- Remove synthetic defaults
  - When `spu_sales_amt` cannot be derived from quantity×unit_price or provided amounts, set to NA and skip dependent metrics (`Avg_Sales_Per_SPU`, `Expected_Benefit`).
  - Weather and historical ST%: when inputs missing, set NA rather than default 25.0/85.0.

- Require real clustering for grouping
  - If clustering results are missing, skip grouping-dependent outputs or fail with a clear message. Do not use modulo-based grouping.

- Eliminate heuristic target count logic
  - Remove ±10% sales-based target heuristic. Only use rule-derived counts or keep target equal to current.

- Seasonality
  - Document and require autumn context for September runs: use September YOY sales for context (already done for historical ST%).
  - Do not invent season labels. Leave NA when not present. Do not remap missing to summer.

- Gender and display location
  - Keep NA in data columns when missing; avoid returning placeholder literals like '未知' in data fields. Handle presentation-layer mapping at export time if needed.
  - For location percentages, include an "other/unknown" share rather than forcing front/back to sum to 100%.

- Volume realism caps
  - Cap net ΔQty per group to a reasonable bound (e.g., ±20% of `Current_SPU_Quantity`, min 1) after aggregating rule-based SPU count changes (not units).
  - Optionally cap the number of distinct subcategories adjusted per group.

- Expected benefit
  - Remove the blanket 5% multiplier. Either compute from validated sell-through improvements (if available) or set NA.

- Periodization and outputs
  - Source target period from pipeline config (period-label aware) and write a period-labeled copy of the output alongside the timestamped file.

## Acceptance Criteria
- No unit→count conversions: unit deltas never modify SPU counts. Target counts only from SPU-level add/remove flags or remain equal to current.
- No synthetic defaults: where inputs are missing, values are NA; dependent metrics are omitted or clearly flagged.
- No modulo grouping: cluster-based grouping only; if clusters missing, step logs and skips grouping outputs.
- No heuristic ±10% target logic; target counts are grounded.
- Seasonality/gender/location fields are never defaulted to summer/unisex/front; NA preserved when not present.
- ΔQty and total target SPUs per group are capped to realistic bounds.
- "Expected_Benefit" is NA or computed from validated inputs.
- Output includes a period-labeled artifact and manifest registration uses the pipeline period.

## Test Plan
- Unit tests
  - Unit vs count separation: feed rules with unit `recommended_quantity_change` only → target SPU count remains equal to current.
  - Missing data behavior: remove weather/historical files → fields are NA; no defaults appear.
  - Grouping: remove clustering file → step logs error and skips grouping outputs (or fails clearly); no modulo clusters.
  - Caps: construct a group with current 50 SPUs and 100 SPU-add recommendations → final target SPU count change capped (e.g., ≤ +10).
  - Location percentages: include a third location → front/back do not falsely absorb unknown; other share reported or remains unallocated.

- Integration tests
  - September run with available 202409A/B historical data: verify seasonality fields present when available and not defaulted.
  - Pipeline period passthrough: output has correct period label and manifest entries reference the same.
  - Benefit calculation: when validator-derived uplift is available, benefit computed from that; otherwise NA.

## Rollout
- Implement changes behind flags for target count and benefit computation to avoid breaking downstream expectations.
- Validate on summer and September periods. Compare ΔQty distributions and group volumes to current production; ensure reductions in synthetic artifacts and improved realism.
- Monitor logs for NA rates, missing clustering, and capped adjustments. Coordinate with consumers of Step 14 for any schema notes (e.g., NA benefit).

## Backward Compatibility
- Schema preserved for key columns; values become NA where previously defaulted.
- Target SPU counts may change (more conservative), but columns remain. ΔQty semantics clarified (counts only, not units).
- Timestamped file still produced; add period-labeled companion file to align with other steps.

## References
- Production: `src/step14_create_fast_fish_format.py`
- Reference: `backup-boris-code/step14_create_fast_fish_format.py`
- Upstream dependencies: Step 13 detailed SPU-level file; clustering results; store_config dims; weather and historical sales
