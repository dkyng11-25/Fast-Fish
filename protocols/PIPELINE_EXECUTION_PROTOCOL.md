# Pipeline Execution Protocol

**Depth Level:** 2 (Problem-solving)  
**Last Updated:** 2025-01-05  
**References:** FAST_FISH_THINKING_STRATEGY.md, PERSPECTIVES_NEEDED.md

---

## Purpose

Define the structured approach for executing and improving the Fast Fish 36-step pipeline. This protocol guides implementation, testing, and validation of pipeline steps.

---

## Pipeline Overview

### 5 Main Phases

| Phase | Steps | Purpose | Typical Time |
|-------|-------|---------|--------------|
| **1. Data Collection** | 1-3 | API download → Coordinates → Matrix preparation | 16 min |
| **2. Weather Integration** | 4-5 | Weather data → Temperature analysis | 15 min |
| **3. Clustering** | 6 | Temperature-aware store clustering | <1 min |
| **4. Business Rules** | 7-12 | 6 optimization rules analysis | 35 min |
| **5. Visualization** | 13-15 | Consolidation → Dashboards | <1 min |

### Extended Steps (16-36)

| Step Range | Purpose |
|------------|---------|
| 15-18 | Historical baseline and comparison |
| 19-24 | Detailed breakdown and enrichment |
| 25-29 | Product role and gap analysis |
| 30-33 | Optimization engine and allocation |
| 34-37 | Strategy deployment and delivery |

---

## Step Execution Pattern

### The 4-Phase Step Pattern

Every pipeline step follows this structure:

```python
class MyStep(Step):
    def setup(self, context: StepContext) -> StepContext:
        """Phase 1: Load data from repositories"""
        # Load input data
        # Prepare for processing
        return context
    
    def apply(self, context: StepContext) -> StepContext:
        """Phase 2: Transform and process data"""
        # Core business logic here
        # Transform data
        return context
    
    def validate(self, context: StepContext) -> None:
        """Phase 3: Validate results - raise exception if invalid"""
        # Check data quality
        # Raise DataValidationError if problems found
        # Return None if valid
    
    def persist(self, context: StepContext) -> StepContext:
        """Phase 4: Save results via repositories"""
        # Save to files/database
        return context
```

### Phase Details

#### Phase 1: Setup
- **Purpose:** Load all required input data
- **Pattern:** Use repositories for all I/O
- **Validation:** Check input data exists and is valid
- **Output:** Context populated with input data

#### Phase 2: Apply
- **Purpose:** Execute core business logic
- **Pattern:** Pure transformation, no I/O
- **Validation:** Intermediate checks as needed
- **Output:** Context with transformed data

#### Phase 3: Validate
- **Purpose:** Ensure output meets quality standards
- **Pattern:** Raise exception on failure
- **Validation:** Schema, completeness, business rules
- **Output:** None (or exception)

#### Phase 4: Persist
- **Purpose:** Save results to storage
- **Pattern:** Use repositories for all I/O
- **Validation:** Confirm write success
- **Output:** Context with persistence confirmation

---

## Step Implementation Checklist

### Before Implementation

- [ ] Read original legacy script
- [ ] Identify input/output data
- [ ] List business logic requirements
- [ ] Define validation criteria
- [ ] Create feature file (BDD scenarios)

### During Implementation

- [ ] Create step class following 4-phase pattern
- [ ] Implement setup() with repository calls
- [ ] Implement apply() with pure transformations
- [ ] Implement validate() with quality checks
- [ ] Implement persist() with repository calls
- [ ] Add type hints throughout
- [ ] Keep file under 500 LOC

### After Implementation

- [ ] Run BDD tests
- [ ] Compare output with legacy script
- [ ] Document any differences
- [ ] Update feature file if needed
- [ ] Create/update documentation

---

## Business Rules Execution (Steps 7-12)

### Rule 7: Missing Category Rule

**Purpose:** Identify stores missing high-performing categories

**Input:**
- Store sales data
- Category performance metrics
- Cluster assignments

**Output:**
- Missing category opportunities
- Recommended additions per store

**Validation:**
- All stores analyzed
- Valid category recommendations
- Performance thresholds met

---

### Rule 8: Imbalanced Allocation Rule

**Purpose:** Detect over/under-allocated products

**Input:**
- Current allocation data
- Sales performance
- Cluster benchmarks

**Output:**
- Imbalanced allocation cases
- Rebalancing recommendations

**Validation:**
- Allocation totals verified
- Recommendations within capacity

---

### Rule 9: Below Minimum Rule

**Purpose:** Find categories below threshold levels

**Input:**
- Category inventory levels
- Minimum thresholds
- Sales velocity

**Output:**
- Below-minimum cases
- Replenishment recommendations

**Validation:**
- Thresholds correctly applied
- Recommendations feasible

---

### Rule 10: Smart Overcapacity Rule

**Purpose:** Identify overcapacity opportunities

**Input:**
- Current capacity utilization
- Sales performance
- Expansion potential

**Output:**
- Overcapacity opportunities
- Expansion recommendations

**Validation:**
- Capacity calculations correct
- Opportunities prioritized

---

### Rule 11: Missed Sales Opportunity Rule

**Purpose:** Detect missed sales opportunities

**Input:**
- Sales data
- Demand signals
- Inventory availability

**Output:**
- Missed opportunity cases
- Prevention recommendations

**Validation:**
- Opportunity calculations correct
- Root causes identified

---

### Rule 12: Sales Performance Rule

**Purpose:** Analyze performance gaps

**Input:**
- Sales performance data
- Benchmarks by cluster
- Historical trends

**Output:**
- Performance gap analysis
- Improvement recommendations

**Validation:**
- Benchmarks correctly applied
- Gaps accurately measured

---

## Quality Gates

### Gate 1: Data Quality
**When:** After Step 1-3 (Data Collection)
**Criteria:**
- [ ] All API data downloaded
- [ ] Coordinates extracted correctly
- [ ] Matrix prepared with valid schema

### Gate 2: Clustering Quality
**When:** After Step 6 (Clustering)
**Criteria:**
- [ ] All stores assigned to clusters
- [ ] Cluster sizes reasonable
- [ ] Temperature bands correctly applied

### Gate 3: Business Rules Quality
**When:** After Steps 7-12
**Criteria:**
- [ ] All rules executed successfully
- [ ] Recommendations generated
- [ ] Validation passed for each rule

### Gate 4: Output Quality
**When:** After Steps 13-15 (Visualization)
**Criteria:**
- [ ] Consolidated results complete
- [ ] Dashboards generated
- [ ] All visualizations accessible

### Gate 5: Delivery Quality
**When:** After Steps 34-37 (Delivery)
**Criteria:**
- [ ] Customer format correct
- [ ] All deliverables complete
- [ ] Documentation included

---

## Error Handling

### Error Categories

1. **Data Errors:** Missing or invalid input data
2. **Processing Errors:** Logic failures during transformation
3. **Validation Errors:** Output doesn't meet quality standards
4. **Persistence Errors:** Failed to save results

### Error Response Protocol

```
1. Log error with full context
2. Determine error category
3. If recoverable: retry with backoff
4. If not recoverable: fail step with clear message
5. Update pipeline status
6. Notify if critical
```

### Retry Strategy

- **API calls:** 3 retries with exponential backoff
- **File operations:** 2 retries with 1-second delay
- **Validation failures:** No retry (fix data first)

---

## Performance Monitoring

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Step execution time | < 5 min per step | > 10 min |
| Memory usage | < 16 GB | > 24 GB |
| Success rate | 100% | < 95% |
| Data completeness | 100% | < 99% |

### Monitoring Points

- **Before step:** Log start time, input data size
- **During step:** Log progress milestones
- **After step:** Log end time, output data size, success/failure

---

## Loop Prevention

### Execution Limits

- **Max step retries:** 3
- **Max pipeline restarts:** 2
- **Max validation iterations:** 3

### Progress Indicators

Every step execution must produce:
- [ ] Input data loaded
- [ ] Transformation completed
- [ ] Validation passed
- [ ] Output persisted

**If no progress after 3 attempts, escalate to manual review.**

---

## Documentation Requirements

### Per-Step Documentation

1. **Feature file:** BDD scenarios in Gherkin format
2. **Code comments:** Inline documentation for complex logic
3. **README section:** Step purpose and usage
4. **Test coverage:** Unit and integration tests

### Pipeline Documentation

1. **Architecture diagram:** Step dependencies and data flow
2. **Configuration guide:** Parameters and settings
3. **Troubleshooting guide:** Common issues and solutions
4. **Performance guide:** Optimization tips

---

**Version:** 1.0  
**Status:** Active  
**Next Review:** After pipeline milestone
