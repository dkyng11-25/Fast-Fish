## End-to-End Technical Findings and Architecture Overview

### Executive context
- **Client**: Fashion retailer in China.
- **Goal**: Improve store-level product mix decisions by clustering stores and applying rules to generate Fast Fish–compliant recommendations, packaged into client-ready outputs and dashboards.
- **Granularity & cadence**: Month-level with optional half-month periods (A/B). All recommendations are tied to explicit periods and intended for short-horizon execution (15 days when using A/B).

### Core objectives (what the system delivers)
- **Descriptive analytics**: Multi-phase pipeline that ingests API data, builds feature matrices, clusters stores, and applies 6 business rules to surface opportunities.
- **Consolidation + client output**: Unifies rule results and formats output to a client-compliant Fast Fish file with additional fields and guardrails.
- **Validation**: Adds sell-through calculations and comprehensive data QA.
- **Advanced analysis**: Historical augmentation, SPU-level breakdown, comparison tables, and scenario tooling; an optimization engine is planned.

### System map (where things live)
- Pipeline orchestration and CLI: `pipeline.py`
- Config, periods, paths, compatibility: `src/config.py`
- Step registry and execution (scripts): `src/step*.py`
- Manifest for explicit file dependencies: `src/pipeline_manifest.py`
- Fast Fish sell-through validator (corrected): `src/sell_through_validator.py`
- Tests and step docs (golden expectations): `output/tests/**`
- Guides and reference docs: `docs/**`, `documentation/**`

### Data sourcing and periodization
- API files for a given period are standardized via `get_api_data_files(...)` in `src/config.py`:
  - `data/api_data/store_config_<YYYYMM[A|B]>.csv`
  - `data/api_data/store_sales_<YYYYMM[A|B]>.csv`
  - `data/api_data/complete_category_sales_<YYYYMM[A|B]>.csv`
  - `data/api_data/complete_spu_sales_<YYYYMM[A|B]>.csv`
- Defaults: `DEFAULT_YYYYMM = "202506"`, `DEFAULT_PERIOD = "B"` (can be overridden by env or CLI).
- Backward-compat: `ensure_backward_compatibility()` and `update_legacy_file_references()` create copies like `complete_category_sales_202505.csv` and `clustering_results.csv` for older steps that expect legacy names.
- A separate set of combined-quarter placeholders (e.g., `*_2025Q2_combined.csv`) exist in `src/config.py` for flexibility, but the live pipeline primarily consumes periodized files returned by `get_api_data_files`.

### Pipeline execution and controls
- Entry point: `pipeline.py` provides CLI to run full or partial ranges with step validation, strict/continue behaviors, and environment setup.
- Critical vs optional steps: Steps 1, 2, 3, 6 are critical; others continue-on-failure unless `--strict` is set.
- Flags: `--skip-api`, `--skip-weather`, `--start-step`, `--end-step`, `--validate-data`, `--clear-all`, `--clear-period`, `--list-steps`, `--list-periods`.
- Sample data provisioning: If API is skipped and required source files are missing, the runner synthesizes plausible demo data for end-to-end dry-runs.

### File manifest (explicit step I/O contracts)
- `src/pipeline_manifest.py` records exact outputs per step and resolves downstream inputs by dependency aliases.
- Current dependency map includes inputs for steps 14, 17–21, enabling deterministic file chaining across runs with validation (existence/size).

### Phase & step overview (as implemented)
- Phases: Data collection (1–3), Weather (4–5), Clustering (6), Rules (7–12), Consolidation/Advanced (13–19), Validation (20). Additional analysis modules extend to 33 in `src/`.
- Representative outputs (periodized names may be used by some steps; legacy names are maintained for compatibility):
  - Clustering: `output/clustering_results.csv` (plus periodized variants in some docs)
  - Consolidated rules: `output/consolidated_rule_results.csv`
  - Individual rule files: `output/rule7_missing_category_results.csv`, `output/rule8_imbalanced_results.csv`, `output/rule9_below_minimum_results.csv`, `output/rule10_smart_overcapacity_results.csv`, `output/rule11_missed_sales_opportunity_results.csv`, `output/rule12_sales_performance_results.csv`
  - Dashboards: `output/global_overview_spu_dashboard.html`, `output/interactive_map_spu_dashboard.html`

### Business rules (6 core guards)
Based on `docs/COMPLETE_PIPELINE_DOCUMENTATION.md`, `docs/PIPELINE_STEPS_REFERENCE.md`, and step modules under `src/`:
- Rule 7 – Missing Categories (`src/step7_missing_category_rule.py`)
  - Level: Subcategory. Thresholds: ≥70% adoption within cluster and ≥100 sales.
  - Flags stores missing subcategories adopted by peers with proven demand.
- Rule 8 – Imbalanced Allocation (`src/step8_imbalanced_rule.py`)
  - Level: SPU. Threshold: absolute Z-score > 2.0 vs cluster norm.
  - Detects over/under-allocated SPUs.
- Rule 9 – Below Minimum (`src/step9_below_minimum_rule.py`)
  - Level: Subcategory. Threshold: < 2 styles.
  - Identifies subcategories below minimum viable assortment.
- Rule 10 – Smart Overcapacity (`src/step10_spu_assortment_optimization.py`)
  - Level: Subcategory. Multi-profile reallocation (Strict/Standard/Lenient) driven by performance gaps.
- Rule 11 – Missed Sales Opportunity (`src/step11_missed_sales_opportunity.py`)
  - Level: SPU. Threshold: < 15% sell-through (peer-comparison supplemental metrics included).
- Rule 12 – Sales Performance (`src/step12_sales_performance_rule.py`)
  - Level: SPU. Benchmarks performance vs cluster top performers; classifies opportunity tiers.

### Fast Fish sell‑through compliance (corrected)
- Module: `src/sell_through_validator.py` implements the official definition: SPUs Sold ÷ SPUs In Stock, not days-based proxies.
- Key thresholds and behaviors:
  - `MIN_SELL_THROUGH_THRESHOLD = 25%`, `OPTIMAL_SELL_THROUGH_TARGET = 70%`.
  - For DECREASE actions: require non-negative improvement.
  - For INCREASE actions: allow reasonable degradation provided final ST% ≥ minimum; at very small counts, up to −50pp allowed; standard max degradation −10pp.
  - Batch validation returns a merged frame with compliance flags and rationales per recommendation.

### Client output and validation
- Step 13 consolidates rule outputs. Step 14 exports Fast Fish format with standardized fields; enhanced validation is exercised by `test_enhanced_pipeline.py`:
  - Required fields checked: `Year`, `Month`, `Period`, `Store_Group_Name`, `Target_Style_Tags`, `Current_SPU_Quantity`, `Target_SPU_Quantity`, `ΔQty`, `Data_Based_Rationale`, `Expected_Benefit`, `men_percentage`, `women_percentage`, `front_store_percentage`, `back_store_percentage`, `Display_Location`, `Temp_14d_Avg`, `Historical_ST%`.
  - Validates ΔQty arithmetic, dimensional tag format, percentage ranges, and null safety.

### Data quality and runtime characteristics
- `pipeline.py` enforces post-step checks (existence, size thresholds, basic content integrity) for critical steps when `--validate-data` is set.
- Typical runtime (from docs): ~60–90 minutes full run on 32GB+ RAM, Python 3.12+.
- Requirements: see `requirements.txt` (pandas, numpy, scikit-learn, plotly, folium, tqdm, requests, openpyxl).

### Extended modules (beyond step 20)
- Present in `src/`: comparison tables, historical augmentation, label/tagging, store attribute enrichment, feature updates, comprehensive cluster labeling, product role classification, price band & elasticity, gap matrix generator, scenario analyzer, supply-demand gap analysis, sell-through optimization engine (`src/step30_sellthrough_optimization_engine.py`), enhanced clustering, and store-level plugin output.
- These provide scaffolding for a fully prescriptive solution; core pipeline uses the 1–20 sequence and selectively calls into the later steps for deliverables and R&D.

### Known gaps and program direction (from `COMPREHENSIVE_PROJECT_STATUS_OVERVIEW.md`)
- KPI alignment: A mathematical optimization engine (MILP/LP) is not yet wired end-to-end.
  - Objective: maximize Σ sell_through_rate × allocation subject to capacity, style, and merchandising constraints.
  - Needs: formal objective, constraints, solver integration, and before/after simulation.
- Clustering completeness: Current clusters underweight merchandising realities (style/capacity) and should integrate these as explicit features and constraints.
- Business interpretability: Translate technical cluster labels into stakeholder-friendly profiles and operational tags to drive trust and adoption.

### Operational risks and mitigations
- Naming divergence between legacy and periodized files: mitigated by compatibility copies in `src/config.py` and encouraged adoption of `src/pipeline_manifest.py` for explicit I/O.
- API availability: the runner can synthesize demo inputs when `--skip-api` is used; for production, ensure connectivity and credentials (see `docs/README.md`).
- Memory and performance: large matrices and weather integration require 32GB+ RAM; matrix filtering and normalization mitigate sparsity and size.

### How to run
```bash
python pipeline.py --month 202506 --period A --validate-data
# or run selected ranges
python pipeline.py --month 202506 --period A --start-step 7 --end-step 12
```

### Primary references
- Orchestration: [`pipeline.py`](../pipeline.py)
- Config and periods: [`src/config.py`](../src/config.py)
- File manifest: [`src/pipeline_manifest.py`](../src/pipeline_manifest.py)
- Rules and steps: `src/step*.py` (e.g., [`src/step7_missing_category_rule.py`](../src/step7_missing_category_rule.py))
- Fast Fish validator: [`src/sell_through_validator.py`](../src/sell_through_validator.py)
- Full pipeline docs: [`docs/COMPLETE_PIPELINE_DOCUMENTATION.md`](../docs/COMPLETE_PIPELINE_DOCUMENTATION.md), [`docs/PIPELINE_STEPS_REFERENCE.md`](../docs/PIPELINE_STEPS_REFERENCE.md)
- Project status & roadmap: [`COMPREHENSIVE_PROJECT_STATUS_OVERVIEW.md`](../COMPREHENSIVE_PROJECT_STATUS_OVERVIEW.md)


