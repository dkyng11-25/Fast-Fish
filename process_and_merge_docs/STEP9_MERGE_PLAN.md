### Scope

- **Targets**: `src/step9_below_minimum_rule.py` (root vs reference) and `src/config.py` (read-only for period/path resolution).
- **Non-goals**: Enabling unrelated features; changing Steps 7/8/10+; altering downstream consumers beyond compatible outputs.

### High-level comparison (Root vs Reference)

- **Focus and data model**
  - Root: SPU-focused “fixed” implementation; counts measured in units per 15 days (`unit_rate`) strictly from SPU sales quantities; ensures positive-only increases; optional seasonal blending; Fast Fish validation; period-labeled outputs and manifest registration.
  - Reference: Supports subcategory and SPU; allocation proxy (`style_count`) derived from planning/sales; can recommend DISCONTINUE or BOOST; quantity estimates if missing; simple outputs, no validation.

- **Quantity sourcing**
  - Root: Hard requirement for real quantities from SPU sales (`quantity` or error). No proxy by default.
  - Reference: Derives from `sal_qty` or estimates from `spu_sales_amt/300` if needed.

- **Joins and cluster columns**
  - Root: Left joins with diagnostics; uses `Cluster` for grouping; standardizes `cluster_id` in store results (Step 9 uses that in create_store_summary).
  - Reference: Primarily inner joins; relies on `Cluster`.

- **Business rules**
  - Root: Below-minimum is “increase only,” with integer-ceiled quantities; per-store cap; Fast Fish gate; optional seasonal blending of store config (SPU expansion still primary); period-aware inputs; manifest integration.
  - Reference: Below-minimum can lead to DISCONTINUE when extremely low; both BOOST and DISCONTINUE text; no sell-through validation, no per-store cap, more permissive quantity estimation.

- **Outputs**
  - Root: Period-labeled results/opportunities/summary (sell-through naming), plus backward-compatible unlabeled copies; manifest metadata persisted.
  - Reference: Single unlabeled files (results/cases/summary), no manifest.

### Risks and mitigations

- **Absence of quantity column in SPU sales**
  - Risk: Root fails fast; reference would estimate. 
  - Mitigation: Document strict behavior. If business needs fallback, add opt-in flag later (e.g., `RULE9_ALLOW_QUANTITY_PROXY=1`) with clear provenance; default remains strict.

- **Cluster column inconsistency**
  - Risk: Inputs might only have `cluster_id` (no `Cluster`) or vice versa.
  - Mitigation: Mirror columns after cluster load (ensure both exist); keep `Cluster` for grouping and `cluster_id` for standardized results.

- **Seasonal blending expectations**
  - Risk: Blending config used without required seasonal inputs.
  - Mitigation: Keep blending optional; log and fall back to recent-only; no silent synthesis.

- **Validator unavailability**
  - Risk: Without Fast Fish, all recommendations would be saved but lack validation context.
  - Mitigation: Maintain current root behavior: run without gating if validator unavailable, but preserve sell-through fields with NA and log explicitly. Do not introduce fallback approvals.

### Plan of record (documentation-first; minimal code changes later if required)

1) Keep root Step 9 as canonical implementation (positive-only increases, strict quantities, period-aware IO, optional seasonal blending, Fast Fish validation, manifest).
2) Add/verify cluster mirroring (ensure both `Cluster` and `cluster_id`) if missing, analogous to Step 8 approach (small, safe change only if needed).
3) No enablement of DISCONTINUE logic from reference at this time; defer to business decision (would conflict with positive-only constraint).
4) Preserve outputs: period-labeled + backward-compatible; maintain column names used by downstream consolidation.

### Diagnostics and tests (post-change checklist)

- Run with explicit period and SPU level; confirm:
  - SPU sales file resolved and contains `quantity`.
  - `unit_rate` populated; NA counts logged and recorded in manifest.
  - All `recommended_quantity_change` > 0 (no negatives) when cases exist.
  - Fast Fish metrics present when validator available; absent (NA) otherwise.
  - Period-labeled files created, plus unlabeled backward-compatible copies.

### Acceptance criteria

- End-to-end success for SPU mode with period-labeled outputs and manifest entries.
- No negative quantity recommendations; no proxy quantities unless an explicit future flag is enabled.
- Downstream Steps 13/14 continue to consume standard columns (`recommended_quantity_change`, `investment_required`, rule flags).

### Operational notes

- Run with explicit period: 
  - `python src/step9_below_minimum_rule.py --yyyymm 202509 --period A --analysis-level spu --target-yyyymm 202509 --target-period A`


