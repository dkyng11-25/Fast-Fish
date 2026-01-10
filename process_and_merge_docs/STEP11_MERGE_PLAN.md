### Scope

- **Targets**: `src/step11_missed_sales_opportunity.py` (root vs reference). Read-only notes for `src/config.py` and `src/pipeline_manifest.py`.
- **Non-goals**: Wiring new trend features; changing Steps 7–10; altering downstream contracts beyond already standardized fields.

### High-level comparison (Root vs Reference)

- **Objective**
  - Both implement Missed Sales Opportunity (Rule 11) via cluster peer analysis and produce SPU-level recommendations to increase units.

- **Data sourcing**
  - Root: Uses period-aware files, optional seasonal blending (Aug), manifests, labeled + unlabeled outputs, Fast Fish validator integration, left join with diagnostics, strict real-unit policy.
  - Reference: Resolves period-specific SPU file; merges cluster inner; can estimate SPU units from store avg price (or hardcoded 300); simpler outputs; no manifest; no validator; no seasonal blending.

- **Unit handling**
  - Root: Real units via `quantity` or `base_sal_qty + fashion_sal_qty` (fallback `sal_qty`); computes `avg_unit_price = sales / units` at store×SPU; strictly avoids synthetic quantity synthesis.
  - Reference: May estimate units as `spu_sales / avg_unit_price` (avg from store) or fallback `spu_sales/300.0` when missing.

- **Detection logic**
  - Both: Identify top performers within cluster×category; compute SPU-to-category ratios; create expected per-store targets; compute gaps; recommend adds/increases with incremental quantities.
  - Root: More selective defaults, explicit NA-preserving math, richer diagnostics; optional Fast Fish gate.

- **Outputs**
  - Root: Results, details, top-performers, and summary (both unlabeled and period-labeled), all registered in manifest with metadata.
  - Reference: Unlabeled CSVs + summary markdown, no manifest.

### Advantages in the reference to leverage (without reintroducing synthetic data)

- **Period-dynamic SPU file resolution** as an additional fallback/override (complementary to root’s config resolution).
- **Inclusive thresholds profile** (wider recall) as an opt-in profile for diagnostics/QA.
- **Inner-join precision mode** for controlled high-precision runs (excludes stores without clusters).
- **Lean fast-path execution** for ad-hoc/debug runs with clear logging.

### Risks and mitigations

- Synthetic unit estimation in reference
  - Risk: Bias from `spu_sales / avg_unit_price` or `/300.0` when units are absent.
  - Mitigation: Keep root’s real-unit only policy; never synthesize units. Skip/flag NA instead of estimating.

- Cluster column inconsistency (`Cluster` vs `cluster_id`)
  - Risk: Downstream joins or contracts may break.
  - Mitigation: Mirror/normalize post-load; standardize pipeline outputs to `cluster_id` while retaining `Cluster` for analysis where needed.

- Seasonal blending availability
  - Risk: Seasonal files missing.
  - Mitigation: Log clearly and fall back to recent-only without synthesis.

- Validator availability/semantics
  - Risk: Inconsistent behavior when validator unavailable.
  - Mitigation: Keep strict, NA-preserving logic; when validator is unavailable or skipped, retain fields and skip gating.

### Plan of record

1) Documentation-first (this plan + spec) before any edits.
2) Keep root as canonical: real-unit quantities, seasonal blending toggle, manifest/labeled outputs, Fast Fish gating, NA-preserving arithmetic, left-join + diagnostics.
3) Surface reference advantages as operational toggles (already used in Step 10):
   - Join precision: `--join-mode {left,inner}`
   - Threshold overrides for exploration vs strict prod.
4) Do not port synthetic unit estimation code.

### Operational toggles to expose/confirm (no behavior change by default)

- `--join-mode {left,inner}` (default `left`).
- Threshold flags (optional overrides): min sales/qty gaps, max per-store recs, adoption/percentile thresholds.
- Seasonal blending toggle (already exists, align messaging/logging with Step 10).

### Diagnostics and tests

- Confirm labeled + legacy outputs and manifest entries.
- Log quantity coverage and NA propagation (no synthetic fills).
- Validate per-store caps if present; confirm gating semantics when validator is active.

### Acceptance criteria

- No synthetic unit estimation; recommendations grounded in real per‑SPU units.
- Parameterized toggles available for precision/recall tradeoff without changing defaults.
- Outputs remain backward compatible and period-labeled; manifest updated.


