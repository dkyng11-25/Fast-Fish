### Objective
Implement per-store ΔQty allocation from group-level recommendations with clear, deterministic logic that:
- Preserves group totals exactly
- Respects per-store capacity/constraints
- Reflects store-specific demand and suitability
- Produces integer quantities with rationale fields
- Integrates cleanly into the pipeline (no post-process needed)

### Data contracts (inputs)
- Group-level recs (prefer enriched)
  - File: Step 18 A/B “with_trends_business_enriched.csv” or Step 14 adds-only
  - Required: `Store_Group_Name`, `Target_Style_Tags` (or `lookup_key`), `Category`, `Subcategory`, `Season`, `Gender`, `Location`, `ΔQty` (group), `Store_Codes_In_Group`, `Store_Count_In_Group`, `Expected_Benefit`, `Confidence_Score`, `trend_cluster_performance`, `cluster_trend_score`, `cluster_trend_confidence`
- Store-level meta (A/B)
  - File: `store_level_plugin_output.csv` (Step 33)
  - Required: `Store_Code`, `Store_Type`, `Capacity_Utilization` (0–1), optionally `Estimated_Rack_Capacity`
- Store-level tags (A/B)
  - File: `store_tags_202509A.csv`, `store_tags_202509B.csv` (Step 24)
  - Required: `str_code` (string), `climate_label_refined`, seasonal fields
- Store-level sales (for weights)
  - Category- or subcategory-level sales
  - Preferred: `data/api_data/complete_category_sales_202409A.csv` / `_B.csv`
  - Fallback: `data/api_data/complete_category_sales_2025Q2_combined.csv`
  - Required: `str_code`, `cate_name`, `sub_cate_name`, `sal_amt` (and/or `estimated_quantity`)

### Allocation logic (per recommendation row r)
- Definitions
  - Group G, stores S(G), category C, subcategory SC, group ΔQty(R)
  - Season `Season_r`, store codes from `Store_Codes_In_Group`
- Compute store weights
  - Sales share (recent history):
    - For each store s in S(G): `sales_s = sal_amt(str_code=s, sub_cate_name=SC)`; if SC absent, fallback to category-level; if all zero, use uniform epsilon
    - `w_sales_s = sales_s / sum_sales`
  - Capacity headroom:
    - `headroom_s = max(0, 1 - Capacity_Utilization_s)`; if missing, 1.0
    - Optionally scale by `Estimated_Rack_Capacity_s` if present: `w_cap_s = headroom_s * min(1, (cap_s / cap_norm))`
  - Suitability (season vs climate, and store-type alignment):
    - Temperature:
      - Hot/Moderate with 夏 or 四季 → 1.0; 秋/春 with Moderate/Cool → 0.8; 冬 with Cool/Moderate → 1.0; else 0.7
    - Store type:
      - Aligned → 1.0; Mixed → 0.9; Unknown → 0.7
    - `w_fit_s = w_temp_s * w_type_s`
  - Composite weight (normalized):
    - `w_s ∝ w_sales_s^α * w_cap_s^β * w_fit_s^γ`
    - Defaults: α=0.6, β=0.3, γ=0.1
    - Normalize across S(G): `w_s = w_s / sum(w_t)`
- Caps and constraints
  - Per-store cap:
    - If `Estimated_Rack_Capacity_s` and a per-category shelf share exist, compute a headroom unit cap; else:
    - `cap_s = min(ALLOC_MAX_PER_STORE, round(headroom_s * ALLOC_HEADROOM_UNIT_SCALE))`
    - Defaults: `ALLOC_MAX_PER_STORE=10`, `ALLOC_HEADROOM_UNIT_SCALE=10` (env)
  - Minimum coverage (optional):
    - If `ALLOC_MIN_STORES > 0`, assign 1 unit to top `ALLOC_MIN_STORES` stores by `w_s` if `ΔQty` allows
  - Exclusions:
    - If `Capacity_Utilization_s > CAPACITY_MAX_UTIL` (e.g., 0.90), set `cap_s = 0` or reduce `w_cap_s`
- Integer allocation preserving group total
  - Continuous allocation: `a_s = ΔQty(R) * w_s`
  - Floor: `f_s = min(cap_s, floor(a_s))`
  - Remainder: `R = ΔQty(R) - sum(f_s)`
  - Distribute R by descending `a_s - f_s` among stores with `f_s < cap_s`, 1 unit each pass until R=0
  - If still R>0 (all at caps), log `unallocatable_units` and optionally relax caps slightly (by 1) for top-weight stores; else leave residual flagged
- Business prioritization (optional but recommended)
  - Multiply `w_s` by a group-level prioritization factor based on `Expected_Benefit` and `Confidence_Score` to bias distributions toward higher-ROI and higher-confidence recs without changing totals

### Outputs (per store allocation)
- Columns per allocated row:
  - Identity: `store_code`, `store_name` (if available), `store_group`, `cluster_id`
  - Dimensions: `Category`, `Subcategory`, `Season`, `Gender`, `Location`
  - Quantities: `Delta_Qty_Store` (int), `Delta_Qty_Group`
  - Weights: `weight_sales`, `weight_capacity`, `weight_suitability`, `weight_composite`
  - Constraints: `cap_store`, `capacity_utilization`, `estimated_rack_capacity` (if any)
  - Suitability: `dominant_climate_in_group`, `temperature_suitability`, `store_type_alignment`
  - Rationale: short text combining trend/performance, confidence, suitability, cap note
- Files:
  - `output/store_level_recommendations_allocated_202509A.csv`
  - `output/store_level_recommendations_allocated_202509B.csv`
  - Reconciliation report: `output/allocation_reconciliation_202509A.json` (and B)

### Validation and quality checks
- Reconciliation:
  - For each group-rec row: `sum(Delta_Qty_Store) == Delta_Qty_Group`
- Caps:
  - Count of stores hitting cap; if high, surface in report (indicates tight capacity)
- Coverage:
  - N stores with allocation vs `Store_Count_In_Group`
- Integer and positivity:
  - All `Delta_Qty_Store` are integers ≥ 0
- Edge handling:
  - Zero/NaN capacity → use defaults (1.0 headroom), but cap per-store to avoid concentration
  - All-zero sales → uniform weights; still respect caps and suitability
  - Very small `ΔQty` < coverage minima → allocate to top-weight stores without forcing negative or fractional
- Spot-check reports:
  - Top 10 groups by `Expected_Benefit` with store-level distributions and reason codes
  - Heatmap by cluster → store count receiving >0 units

### Integration into pipeline
- New step: `src/step32_allocate_store_quantities.py`
  - CLI:
    - `--target-yyyymm 202509 --target-period A|B`
    - `--group-recs-file` (default to latest Step 18 enriched A/B)
    - `--store-sales-file` (default to latest 202409 A/B; fallback to Q2)
  - Env (in `src/config.py`):
    - `ALLOC_ALPHA_SALES=0.6`, `ALLOC_BETA_CAP=0.3`, `ALLOC_GAMMA_FIT=0.1`
    - `ALLOC_MAX_PER_STORE=10`, `ALLOC_HEADROOM_UNIT_SCALE=10`, `ALLOC_MIN_STORES=0`
    - `CAPACITY_MAX_UTIL=0.9`
    - `SUITABILITY_HIGH=1.0`, `SUITABILITY_MED=0.8`, `SUITABILITY_LOW=0.7`
    - `USE_EXPECTED_BENEFIT_WEIGHTING=1`
  - Implementation shape:
    - Load A/B group recs; explode `Store_Codes_In_Group` to long store list; join store-level sales/tags/capacity; compute weights and caps; allocate; write outputs; write reconciliation JSON
- Step 33 enhancement
  - Option A: Merge Step 32 per-store ΔQty into `store_level_plugin_output` as additional columns per category/subcategory (wider file)
  - Option B: Leave `store_level_recommendations_allocated_*.csv` as the execution pick-list file and link it from Step 33 README

### Optional optimization (if pulp/scipy available)
- Upgrade integer allocation to an ILP per group row with:
  - Objective: maximize `sum(weight_composite_s * x_s)`
  - Constraints: `sum x_s = ΔQty(R)`, `0 ≤ x_s ≤ cap_s`, `x_s ∈ ℕ`
- Fallback: use the LRM (largest remainder method) described above when ILP is not available or times out

### Deliverables added
- Files:
  - `store_level_recommendations_allocated_202509A.csv`, `_B.csv`
  - `allocation_reconciliation_202509A.json`, `_B.json`
  - Allocation logic doc (one-pager for business): purpose, rules, examples
- README updates:
  - Add “How to use the store-level pick list” with operational notes (e.g., caps, capacity, rationale interpretation)

### Execution plan
1. Implement `step32_allocate_store_quantities.py` with env-configurable weights, caps, and rationale fields.
2. Update `pipeline_manifest.py` to register Step 32 outputs.
3. Add Step 32 to run script after Step 18 and before/alongside Step 33.
4. Run A/B for 202509; inspect reconciliation JSON; spot-check 3–5 groups.
5. Copy Step 32 outputs and updated README into delivery folder.

### Acceptance criteria
- For every group row, allocated per-store quantities reconcile exactly to group ΔQty; residuals = 0
- No negative or non-integer per-store quantities
- Allocation respects capacity caps; number of cap hits reported
- Rationale fields present and readable; Temperature_Suitability/Store_Type_Alignment populated
- Client-ready per-store pick list produced for A and B periods

If you want, I’ll implement Step 32 now and wire it into the pipeline with the parameters above.