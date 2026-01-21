# Step 7-13 Quality Evaluation & Improvement Opportunities

> **Document Type:** Technical Quality Assessment & Enhancement Roadmap  
> **Audience:** Data Scientists, Developers, Project Owners  
> **Purpose:** Evaluate module quality and identify improvement opportunities  
> **Last Updated:** January 2026

---

## Executive Summary

This document provides a comprehensive quality evaluation of Steps 7-13, identifying strengths, weaknesses, and actionable improvement opportunities. The goal is to help you understand where to focus efforts for maximum impact.

### Overall Quality Score Card

| Step | Functionality | Code Quality | Documentation | Maintainability | Overall |
|------|--------------|--------------|---------------|-----------------|---------|
| Step 7 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | **B** |
| Step 8 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | **B-** |
| Step 9 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | **B** |
| Step 10 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | **B** |
| Step 11 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | **B** |
| Step 12 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | **B** |
| Step 13 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | **B+** |

**Legend:** ⭐ = Poor, ⭐⭐ = Below Average, ⭐⭐⭐ = Average, ⭐⭐⭐⭐ = Good, ⭐⭐⭐⭐⭐ = Excellent

---

## Critical Issue: Code Size Violations

### The Problem

All Step 7-13 modules **significantly exceed** the 500 LOC (Lines of Code) limit:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CODE SIZE ANALYSIS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  File                                    Lines    Status                    │
│  ────                                    ─────    ──────                    │
│  step7_missing_category_rule.py          1,625   ❌ VIOLATION (+1,125)      │
│  step7_missing_category_rule_DEBUG.py      924   ❌ VIOLATION (+424)        │
│  step7_missing_category_rule_refactored.py  82   ✅ OK                      │
│  step7_missing_category_rule_subcategory.py 873  ❌ VIOLATION (+373)        │
│  step8_imbalanced_rule.py                1,653   ❌ VIOLATION (+1,153)      │
│  step9_below_minimum_rule.py             1,286   ❌ VIOLATION (+786)        │
│  step10_spu_assortment_optimization.py   1,452   ❌ VIOLATION (+952)        │
│  step11_missed_sales_opportunity.py      1,288   ❌ VIOLATION (+788)        │
│  step12_sales_performance_rule.py        1,808   ❌ VIOLATION (+1,308)      │
│  step13_consolidate_spu_rules.py         2,905   ❌ VIOLATION (+2,405)      │
│                                                                             │
│  TOTAL VIOLATIONS: 9 out of 10 files                                        │
│  AVERAGE EXCESS: +1,035 lines per file                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why This Matters

1. **Cognitive Overload**: Developers cannot hold 1,600+ lines in working memory
2. **Debugging Difficulty**: Finding bugs in large files is exponentially harder
3. **Testing Challenges**: Monolithic files are difficult to unit test
4. **Merge Conflicts**: Multiple developers editing the same large file causes conflicts
5. **Code Reuse**: Shared logic is duplicated instead of extracted

### Recommended Fix: CUPID-Based Modularization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROPOSED MODULAR ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CURRENT (Monolithic):                                                      │
│  └── step7_missing_category_rule.py (1,625 lines)                           │
│                                                                             │
│  PROPOSED (Modular):                                                        │
│  └── src/steps/step7/                                                       │
│      ├── __init__.py                    (~20 lines)                         │
│      ├── config.py                      (~80 lines)  - Configuration        │
│      ├── data_loader.py                 (~150 lines) - Load data            │
│      ├── well_selling_detector.py       (~120 lines) - Find well-selling    │
│      ├── opportunity_identifier.py      (~200 lines) - Find missing         │
│      ├── quantity_calculator.py         (~150 lines) - Calculate quantities │
│      ├── sellthrough_validator.py       (~100 lines) - Validate profitability│
│      ├── report_generator.py            (~100 lines) - Generate outputs     │
│      └── main.py                        (~80 lines)  - Orchestration        │
│                                                                             │
│  BENEFITS:                                                                  │
│  • Each file < 200 lines (well under 500 limit)                             │
│  • Single responsibility per file                                           │
│  • Easy to test individual components                                       │
│  • Reusable across steps (e.g., data_loader, sellthrough_validator)         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Quality Analysis

### Step 7: Missing Category/SPU Rule

#### Strengths ✅
- **Comprehensive sell-through validation**: Only recommends products that will actually sell
- **Real quantity data**: Uses actual unit prices, not synthetic estimates
- **Cluster-aware analysis**: Compares stores to their true peers
- **Configurable thresholds**: Easy to adjust sensitivity
- **Detailed documentation**: Excellent docstrings explaining business logic

#### Weaknesses ❌
- **4 duplicate files**: step7 has 4 variations (main, DEBUG, refactored, subcategory)
- **1,625 lines**: Far exceeds 500 LOC limit
- **Mixed concerns**: Data loading, business logic, and reporting in one file
- **Hardcoded paths**: Some file paths are hardcoded instead of using config
- **Complex nested loops**: Opportunity identification uses nested iteration

#### Improvement Opportunities 🔧

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| HIGH | Consolidate 4 files into 1 modular implementation | Medium | High |
| HIGH | Extract data loading into shared component | Low | High |
| MEDIUM | Replace nested loops with vectorized pandas operations | Medium | Medium |
| MEDIUM | Add input validation schemas (pandera) | Low | Medium |
| LOW | Add unit tests for each function | Medium | High |

#### Visualization: Step 7 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STEP 7 DATA FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ Clustering   │    │ SPU Sales    │    │ Quantity     │                   │
│  │ Results      │    │ Data         │    │ Data         │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                   │                           │
│         └─────────────┬─────┴───────────────────┘                           │
│                       ▼                                                     │
│              ┌────────────────┐                                             │
│              │ load_data()    │                                             │
│              └────────┬───────┘                                             │
│                       ▼                                                     │
│         ┌─────────────────────────┐                                         │
│         │ identify_well_selling   │  ← Find products selling in 80%+ stores │
│         │ _features()             │                                         │
│         └───────────┬─────────────┘                                         │
│                     ▼                                                       │
│    ┌────────────────────────────────┐                                       │
│    │ identify_missing_opportunities │  ← Find stores missing these products │
│    │ _with_sellthrough()            │                                       │
│    └───────────────┬────────────────┘                                       │
│                    ▼                                                        │
│           ┌────────────────┐                                                │
│           │ Sell-through   │  ← Validate profitability                      │
│           │ Validation     │                                                │
│           └───────┬────────┘                                                │
│                   ▼                                                         │
│    ┌──────────────────────────┐                                             │
│    │ OUTPUT:                  │                                             │
│    │ • Missing SPU results    │                                             │
│    │ • Opportunities CSV      │                                             │
│    │ • Summary report         │                                             │
│    └──────────────────────────┘                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Step 8: Imbalanced Allocation Rule

#### Strengths ✅
- **Statistical rigor**: Uses Z-Score for objective imbalance detection
- **Investment-neutral**: Rebalancing doesn't require additional budget
- **Configurable thresholds**: Z-Score threshold adjustable (default 3.0)
- **Seasonal blending**: Handles August seasonal transitions

#### Weaknesses ❌
- **1,653 lines**: Exceeds limit significantly
- **Complex seasonal logic**: Blending logic is hard to follow
- **Limited validation**: No sell-through check for rebalancing recommendations
- **Memory inefficient**: Loads full datasets into memory

#### Improvement Opportunities 🔧

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| HIGH | Add sell-through validation for rebalancing | Medium | High |
| HIGH | Modularize into smaller components | Medium | High |
| MEDIUM | Optimize memory usage with chunked processing | Medium | Medium |
| MEDIUM | Simplify seasonal blending logic | Medium | Medium |
| LOW | Add visualization of Z-Score distribution | Low | Low |

---

### Step 9: Below Minimum Rule

#### Strengths ✅
- **Clear business logic**: "Below minimum should INCREASE" is well-documented
- **Reasonable size**: 1,286 lines (still over limit but better than others)
- **Defensive coding**: Handles missing data gracefully
- **Unit-based thresholds**: Uses real quantities, not percentages

#### Weaknesses ❌
- **Exceeds 500 LOC**: Still needs modularization
- **Duplicate logic**: Shares code with Step 8 that could be extracted
- **Limited testing**: No visible unit tests

#### Improvement Opportunities 🔧

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| HIGH | Extract shared logic with Step 8 into common module | Medium | High |
| MEDIUM | Add unit tests for boost calculations | Low | Medium |
| LOW | Add configurable minimum thresholds via CLI | Low | Low |

---

### Step 10: Overcapacity Rule

#### Strengths ✅
- **Excellent documentation**: Detailed HOW TO RUN section
- **Prioritization logic**: Reduces lowest-performing SPUs first
- **Per-store caps**: Limits recommendations per store to avoid overwhelming
- **Sell-through integration**: Validates reductions won't hurt profitable items

#### Weaknesses ❌
- **1,452 lines**: Exceeds limit
- **Complex JSON parsing**: `sty_sal_amt` JSON column handling is fragile
- **Performance concerns**: Bulk processing could be optimized

#### Improvement Opportunities 🔧

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| HIGH | Robust JSON parsing with error handling | Low | High |
| HIGH | Modularize into components | Medium | High |
| MEDIUM | Add caching for repeated calculations | Medium | Medium |
| LOW | Parallel processing for large datasets | High | Medium |

---

### Step 11: Missed Sales Opportunity

#### Strengths ✅
- **Clear business value**: Directly quantifies missed revenue
- **Top performer comparison**: Uses 95th percentile (top 5%)
- **Multiple filters**: Adoption rate, minimum gap, investment threshold
- **Opportunity scoring**: Prioritizes recommendations

#### Weaknesses ❌
- **1,288 lines**: Exceeds limit
- **Strict thresholds**: May miss smaller but valid opportunities
- **Similar to Step 12**: Significant overlap in logic

#### Improvement Opportunities 🔧

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| HIGH | Merge common logic with Step 12 | Medium | High |
| MEDIUM | Make thresholds configurable via CLI | Low | Medium |
| MEDIUM | Add confidence intervals to opportunity scores | Medium | Medium |
| LOW | Visualization of opportunity distribution | Low | Low |

---

### Step 12: Sales Performance Rule

#### Strengths ✅
- **5-tier classification**: Provides nuanced performance view
- **Comprehensive documentation**: Excellent HOW TO RUN section
- **Flexible analysis levels**: Supports both subcategory and SPU
- **Seasonal blending**: Handles seasonal transitions

#### Weaknesses ❌
- **1,808 lines**: Largest violation after Step 13
- **Overlap with Step 11**: Similar logic, different thresholds
- **Complex configuration**: Many environment variables

#### Improvement Opportunities 🔧

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| HIGH | Consolidate with Step 11 into unified performance module | High | High |
| MEDIUM | Simplify configuration with config file | Medium | Medium |
| LOW | Add performance trend analysis over time | High | Medium |

---

### Step 13: Consolidate All Rules

#### Strengths ✅
- **Critical aggregation role**: Essential for final output
- **Data quality correction**: Fixes duplicates, missing clusters
- **Conflict resolution**: Handles contradictory recommendations
- **Production-ready output**: Clean, validated data

#### Weaknesses ❌
- **2,905 lines**: Largest file, nearly 6x the limit
- **Monolithic design**: Does too many things in one file
- **Complex dependencies**: Relies on all previous steps
- **Slow execution**: Full trending analysis is slow

#### Improvement Opportunities 🔧

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| CRITICAL | Split into multiple modules (loader, validator, aggregator, reporter) | High | Critical |
| HIGH | Add incremental processing (don't reload unchanged data) | Medium | High |
| MEDIUM | Parallel processing for rule loading | Medium | Medium |
| LOW | Add progress dashboard for long runs | Medium | Low |

---

## Cross-Cutting Improvement Opportunities

### 1. Shared Components to Extract

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SHARED COMPONENTS OPPORTUNITY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  COMPONENT                    USED BY                    ESTIMATED SAVINGS  │
│  ─────────                    ───────                    ─────────────────  │
│  DataLoader                   Steps 7-13                 ~800 lines total   │
│  SellThroughValidator         Steps 7, 8, 10, 11, 12     ~300 lines total   │
│  ClusterAnalyzer              Steps 7-12                 ~400 lines total   │
│  QuantityCalculator           Steps 7-12                 ~500 lines total   │
│  ReportGenerator              Steps 7-13                 ~600 lines total   │
│  SeasonalBlender              Steps 8, 10, 11, 12        ~400 lines total   │
│                                                                             │
│  TOTAL POTENTIAL SAVINGS: ~3,000 lines of duplicated code                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Testing Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TESTING RECOMMENDATIONS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TEST TYPE              CURRENT STATE        RECOMMENDED                    │
│  ─────────              ─────────────        ───────────                    │
│  Unit Tests             ❌ None visible      ✅ 80%+ coverage per module    │
│  Integration Tests      ❌ None visible      ✅ End-to-end pipeline tests   │
│  Data Validation        ⚠️ Partial           ✅ Pandera schemas for all I/O │
│  Performance Tests      ❌ None visible      ✅ Benchmark critical paths    │
│  Regression Tests       ❌ None visible      ✅ Golden file comparisons     │
│                                                                             │
│  PRIORITY: Start with unit tests for shared components                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. Performance Optimization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PERFORMANCE OPTIMIZATION ROADMAP                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OPTIMIZATION                          EXPECTED SPEEDUP    EFFORT           │
│  ────────────                          ────────────────    ──────           │
│  Replace pandas with fireducks         2-5x                Low              │
│  Vectorize nested loops                3-10x               Medium           │
│  Add caching for repeated calculations 2-3x                Low              │
│  Parallel processing for independent   2-4x                Medium           │
│  Incremental processing (skip unchanged) 5-10x             High             │
│                                                                             │
│  COMBINED POTENTIAL: 10-50x faster execution                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Visualization: Module Dependency Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MODULE DEPENDENCY MAP                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                      ┌─────────────────┐                                    │
│                      │   CLUSTERING    │                                    │
│                      │   (Steps 1-6)   │                                    │
│                      └────────┬────────┘                                    │
│                               │                                             │
│         ┌─────────────────────┼─────────────────────┐                       │
│         │                     │                     │                       │
│         ▼                     ▼                     ▼                       │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                  │
│  │   Step 7    │      │   Step 8    │      │   Step 9    │                  │
│  │  (Missing)  │      │ (Imbalanced)│      │(Below Min)  │                  │
│  └──────┬──────┘      └──────┬──────┘      └──────┬──────┘                  │
│         │                    │                    │                         │
│         │             ┌──────┴──────┐             │                         │
│         │             │             │             │                         │
│         │             ▼             ▼             │                         │
│         │      ┌─────────────┐ ┌─────────────┐    │                         │
│         │      │   Step 10   │ │   Step 11   │    │                         │
│         │      │(Overcapacity)│ │(Missed Sales)│   │                         │
│         │      └──────┬──────┘ └──────┬──────┘    │                         │
│         │             │              │            │                         │
│         │             │       ┌──────┴──────┐     │                         │
│         │             │       │             │     │                         │
│         │             │       ▼             │     │                         │
│         │             │ ┌─────────────┐     │     │                         │
│         │             │ │   Step 12   │     │     │                         │
│         │             │ │(Performance)│     │     │                         │
│         │             │ └──────┬──────┘     │     │                         │
│         │             │        │            │     │                         │
│         └─────────────┴────────┼────────────┴─────┘                         │
│                                │                                            │
│                                ▼                                            │
│                      ┌─────────────────┐                                    │
│                      │    Step 13      │                                    │
│                      │ (Consolidation) │                                    │
│                      └─────────────────┘                                    │
│                                                                             │
│  LEGEND:                                                                    │
│  ───────                                                                    │
│  → Direct dependency (output feeds input)                                   │
│  Steps 7, 8, 9 can run in parallel                                          │
│  Steps 10, 11 depend on clustering only                                     │
│  Step 12 can run after Steps 10, 11                                         │
│  Step 13 requires ALL previous steps                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Recommended Improvement Roadmap

### Phase 1: Quick Wins (1-2 weeks)

| Task | Impact | Effort |
|------|--------|--------|
| Replace `import pandas as pd` with `import fireducks.pandas as pd` | 2-5x speedup | 1 hour |
| Add input validation with pandera schemas | Fewer runtime errors | 2 days |
| Consolidate Step 7's 4 files into 1 | Reduced confusion | 1 day |
| Add CLI flags for all hardcoded thresholds | Easier tuning | 2 days |

### Phase 2: Modularization (2-4 weeks)

| Task | Impact | Effort |
|------|--------|--------|
| Extract shared DataLoader component | ~800 lines saved | 3 days |
| Extract shared SellThroughValidator | ~300 lines saved | 2 days |
| Extract shared ClusterAnalyzer | ~400 lines saved | 2 days |
| Refactor Step 13 into 4 sub-modules | Maintainability | 5 days |

### Phase 3: Testing & Quality (2-4 weeks)

| Task | Impact | Effort |
|------|--------|--------|
| Add unit tests for shared components | 80%+ coverage | 5 days |
| Add integration tests for full pipeline | Catch regressions | 3 days |
| Add performance benchmarks | Track improvements | 2 days |
| Add golden file tests for outputs | Validate correctness | 2 days |

### Phase 4: Advanced Optimization (4-8 weeks)

| Task | Impact | Effort |
|------|--------|--------|
| Implement incremental processing | 5-10x speedup | 2 weeks |
| Add parallel processing for independent steps | 2-4x speedup | 1 week |
| Merge Steps 11 & 12 into unified performance module | Reduced duplication | 1 week |
| Add real-time progress dashboard | Better UX | 1 week |

---

## Conclusion

### Key Takeaways

1. **Functionality is solid**: All modules accomplish their business goals
2. **Code quality needs work**: Every module exceeds the 500 LOC limit
3. **Significant duplication**: ~3,000 lines could be extracted into shared components
4. **Testing is missing**: No visible unit or integration tests
5. **Performance can improve**: 10-50x speedup possible with optimizations

### Recommended Next Steps

1. **Immediate**: Replace pandas with fireducks for quick performance win
2. **Short-term**: Consolidate Step 7's 4 files and extract shared DataLoader
3. **Medium-term**: Modularize Step 13 (the largest file)
4. **Long-term**: Implement comprehensive testing and incremental processing

### Final Recommendation

> **Start with Step 13 modularization.** It's the largest file (2,905 lines), the most critical (aggregates all rules), and will provide the template for modularizing other steps.

---

*Document prepared for Fast Fish Demand Forecasting Project*  
*For questions, contact the Data Science Team*
