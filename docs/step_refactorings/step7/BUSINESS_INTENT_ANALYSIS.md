# Business Intent Analysis - ROI Filtering in Step 7

**Date:** 2025-11-07  
**Status:** ⚠️ CRITICAL - Business Intent Unclear  
**Impact:** High - We're replicating logic we don't understand

---

## The Fundamental Problem

**We don't actually know what problem the ROI filtering is trying to solve.**

After analyzing the legacy code, we can describe **WHAT** it does mechanically, but we cannot answer:
- **WHY** does it use two different quantities?
- **WHAT business problem** does the $100 margin_uplift threshold solve?
- **WHO decided** these thresholds and based on what criteria?
- **WHAT happens** if we filter too aggressively or too permissively?
- **HOW do stores use** these recommendations in practice?

---

## What We Know (Mechanics)

### The Code Does This:

1. **Identifies missing opportunities** - Stores not selling items their peers sell
2. **Calculates expected sales** - Based on peer performance in the cluster
3. **Recommends quantities** - How many units to order
4. **Filters by ROI** - Removes "low-value" opportunities
5. **Outputs recommendations** - For stores to act on

### The Filtering Logic:

```python
if not (roi_value >= 0.30 and           # 30% ROI minimum
        margin_uplift >= 100.0 and      # $100 margin minimum
        n_comparables >= 10):           # 10 comparable stores minimum
    continue  # Filter out
```

**But we don't know WHY these specific values!**

---

## What We Don't Know (Business Intent)

### Question 1: What is the filtering trying to prevent?

**Possible answers:**
- ❓ Prevent stores from ordering unprofitable items?
- ❓ Avoid overwhelming stores with too many recommendations?
- ❓ Filter out statistically unreliable opportunities?
- ❓ Ensure recommendations are worth the operational effort?
- ❓ Protect against data quality issues?

**We don't know which of these (if any) is the actual intent.**

### Question 2: Why $100 margin_uplift specifically?

**Possible rationales:**
- ❓ Operational cost threshold - recommendations below $100 aren't worth processing?
- ❓ Arbitrary round number chosen without analysis?
- ❓ Historical performance data showed $100 as breakeven?
- ❓ Risk tolerance - only recommend "sure bets" above $100?
- ❓ Store capacity constraint - limit to high-value opportunities?

**We have no documentation explaining this choice.**

### Question 3: Why use two different quantities?

**Possible explanations:**
- ❓ Intentional conservative/aggressive split for different purposes?
- ❓ Bug that became "the way it works"?
- ❓ Evolution of code where someone added ROI later without updating quantity logic?
- ❓ Attempt to balance risk (conservative recommendation) vs filtering (aggressive ROI)?
- ❓ Copy-paste error that was never caught?

**The code provides no comments explaining this design.**

### Question 4: What happens if we get this wrong?

**If we filter too aggressively (fewer opportunities):**
- ❓ Stores miss profitable opportunities?
- ❓ Sales targets not met?
- ❓ Inventory gaps in assortment?
- ❓ Customer dissatisfaction from missing products?

**If we filter too permissively (more opportunities):**
- ❓ Stores overwhelmed with recommendations?
- ❓ Unprofitable inventory accumulation?
- ❓ Operational burden on store managers?
- ❓ Loss of trust in recommendation system?

**We don't know the business impact of either scenario.**

### Question 5: How do stores actually use these recommendations?

**Possible workflows:**
- ❓ Stores automatically order recommended quantities?
- ❓ Store managers review and adjust recommendations?
- ❓ Recommendations feed into automated replenishment system?
- ❓ Recommendations are advisory only, stores can ignore?
- ❓ Different stores have different processes?

**We don't know the downstream usage pattern.**

---

## Evidence of Confusion in the Code

### 1. Optional ROI Filtering

```python
USE_ROI = os.environ.get('RULE7_USE_ROI', '1').strip() in {'1','true','yes','on'}
```

**Why is this optional?**
- If ROI filtering is critical, why can it be disabled?
- If it's not critical, why is it enabled by default?
- Who disables it and under what circumstances?

### 2. Environment Variable Overrides

```python
ROI_MIN_THRESHOLD = float(os.environ.get('ROI_MIN_THRESHOLD', '0.3'))
MIN_MARGIN_UPLIFT = float(os.environ.get('MIN_MARGIN_UPLIFT', '100'))
MIN_COMPARABLES = int(os.environ.get('MIN_COMPARABLES', '10'))
```

**Why are these configurable?**
- Are different values used for different scenarios?
- Is there experimentation happening with these thresholds?
- Do different business units use different values?

### 3. Inconsistent Quantity Calculation

```python
# For recommendation output
expected_quantity_int = int(max(1.0, np.ceil(avg_sales_per_store / unit_price)))

# For ROI filtering
expected_units = int(max(1.0, np.ceil(median_amt / unit_price)))
```

**Why the difference?**
- No comments explain this
- Variable names don't clarify intent
- No documentation of the design decision

### 4. Comment Says "Optional ROI gating"

```python
# Optional ROI gating
roi_value = None
margin_uplift = None
```

**"Gating" implies:**
- This is a quality gate / approval step
- But what quality is being gated?
- What's the approval criteria based on?

---

## What the Documentation Says (or Doesn't)

### From the File Header:

```python
"""
Step 7: Missing Category/SPU Rule with QUANTITY RECOMMENDATIONS + FAST FISH SELL-THROUGH VALIDATION

Key Features:
- 🎯 UNIT QUANTITY RECOMMENDATIONS (e.g., "Stock 5 units/15-days")
- 📈 FAST FISH SELL-THROUGH VALIDATION (only profitable recommendations)
- Real sales data integration for accurate quantity calculations
"""
```

**Notice:**
- ✅ Mentions "profitable recommendations"
- ❌ Doesn't explain what "profitable" means
- ❌ Doesn't mention ROI filtering at all
- ❌ Doesn't explain the $100 threshold
- ❌ Doesn't explain dual-quantity calculation

### No Business Requirements Document

We have:
- ❌ No PRD (Product Requirements Document)
- ❌ No business logic specification
- ❌ No stakeholder interviews documented
- ❌ No A/B test results justifying thresholds
- ❌ No performance metrics tied to filtering

---

## Hypotheses About Original Intent

### Hypothesis 1: Risk Management Filter

**Theory:** The ROI filter prevents recommending risky opportunities.

**Evidence for:**
- 30% ROI is a reasonable risk-adjusted return threshold
- $100 margin ensures recommendations are "worth it"
- 10 comparables ensures statistical reliability

**Evidence against:**
- If this were true, why use inflated `expected_units` for ROI?
- Inflating ROI makes filtering LESS conservative, not more
- The dual-quantity approach undermines risk management

**Verdict:** 🤷 Partially plausible but inconsistent implementation

### Hypothesis 2: Operational Capacity Filter

**Theory:** The filter limits recommendations to what stores can handle.

**Evidence for:**
- Stores may have limited capacity to process recommendations
- $100 threshold could represent minimum effort-to-value ratio
- Filtering reduces cognitive load on store managers

**Evidence against:**
- No evidence of store capacity constraints in code
- No per-store limits or quotas
- No prioritization logic beyond binary pass/fail

**Verdict:** 🤷 Possible but no supporting evidence

### Hypothesis 3: Data Quality Filter

**Theory:** The filter removes unreliable opportunities with poor data.

**Evidence for:**
- `n_comparables >= 10` ensures sufficient sample size
- ROI calculation could catch pricing/margin data issues
- Filtering protects against garbage-in-garbage-out

**Evidence against:**
- No explicit data quality checks beyond comparables
- Margin_uplift threshold doesn't correlate with data quality
- No validation of unit_price or margin_rate reliability

**Verdict:** 🤷 Partially plausible for comparables check only

### Hypothesis 4: Historical Accident

**Theory:** The filtering evolved organically without clear design.

**Evidence for:**
- Dual-quantity calculation suggests code evolution/refactoring
- Optional ROI flag suggests it was added later
- Environment variables suggest ongoing experimentation
- No documentation of original design intent
- Inconsistent implementation patterns

**Evidence against:**
- The thresholds are suspiciously round numbers (30%, $100, 10)
- Someone made deliberate choices at some point

**Verdict:** 🎯 **Most likely** - This feels like accumulated technical debt

---

## Critical Questions for Stakeholders

Before we can properly re-engineer this, we need answers to:

### Business Strategy Questions

1. **What is the primary goal of Step 7?**
   - Maximize sales opportunities?
   - Optimize inventory efficiency?
   - Improve store assortment?
   - Reduce stockouts?

2. **What is the cost of a false positive?**
   - Store orders unprofitable item → How bad is this?
   - Quantify the downside risk

3. **What is the cost of a false negative?**
   - Store misses profitable opportunity → How bad is this?
   - Quantify the opportunity cost

4. **How do stores use these recommendations?**
   - Automatic ordering?
   - Manual review?
   - Advisory only?
   - Different by store type?

### Operational Questions

5. **What is the operational cost of processing a recommendation?**
   - Store manager time to review?
   - System processing overhead?
   - Inventory management burden?

6. **Is there a limit to how many recommendations stores can handle?**
   - Per store per period?
   - Based on store size/capacity?
   - Based on category?

7. **How are recommendations currently performing?**
   - Acceptance rate by stores?
   - Actual ROI vs predicted ROI?
   - Sell-through rates of recommended items?

### Technical Questions

8. **Why are there two different quantity calculations?**
   - Is this intentional or a bug?
   - What was the original design intent?

9. **Why $100 specifically for margin_uplift?**
   - Based on analysis or arbitrary?
   - Has this been validated?
   - Should it vary by category/store?

10. **Why is ROI filtering optional?**
    - When is it disabled?
    - What changes when it's off?
    - Who makes this decision?

---

## Recommended Immediate Actions

### 1. Stakeholder Interview (URGENT)

**Schedule meetings with:**
- Product owner who defined Step 7 requirements
- Business analysts who use the output
- Store operations team who receive recommendations
- Data science team who may have analyzed performance

**Questions to ask:**
- "What problem is the ROI filter solving?"
- "How were the thresholds (30%, $100, 10) determined?"
- "What happens if we change these values?"
- "How do stores use these recommendations?"

### 2. Data Analysis (HIGH PRIORITY)

**Analyze historical performance:**
```sql
-- Compare recommended vs actual outcomes
SELECT 
    margin_uplift_bucket,
    COUNT(*) as recommendations,
    AVG(actual_roi) as avg_actual_roi,
    AVG(acceptance_rate) as avg_acceptance
FROM historical_recommendations
GROUP BY margin_uplift_bucket
```

**Questions to answer:**
- Do opportunities with margin_uplift > $100 actually perform better?
- What's the acceptance rate at different threshold levels?
- Is there a natural breakpoint in the data?

### 3. A/B Test Proposal (MEDIUM PRIORITY)

**Test different filtering approaches:**
- **Group A:** Legacy logic (baseline)
- **Group B:** Consistent quantity, $100 threshold
- **Group C:** Consistent quantity, $50 threshold
- **Group D:** No margin_uplift filter, ROI only

**Measure:**
- Recommendation acceptance rate
- Actual ROI achieved
- Store feedback/satisfaction
- Sales impact

### 4. Document Current State (IMMEDIATE)

**Create honest documentation:**
- ✅ What the code does mechanically
- ❌ What we don't know about business intent
- ❓ Open questions requiring stakeholder input
- 🚨 Risks of proceeding without clarity

---

## Decision Framework

Until we have stakeholder input, we have three options:

### Option A: Replicate Legacy Exactly (Current Approach)

**Pros:**
- ✅ Matches current output
- ✅ No risk of changing business behavior
- ✅ Can deploy immediately

**Cons:**
- ❌ Perpetuates broken logic
- ❌ Doesn't solve underlying problems
- ❌ Technical debt continues to accumulate
- ❌ We still don't understand what we're doing

**Recommendation:** ⚠️ **Only if stakeholders unavailable and deadline is critical**

### Option B: Fix Logic, Keep Threshold (Recommended Short-term)

**Pros:**
- ✅ Eliminates dual-quantity inconsistency
- ✅ Makes ROI calculations accurate
- ✅ Reduces rounding sensitivity
- ⚠️ May change opportunity count (need to adjust threshold)

**Cons:**
- ⚠️ Changes output without understanding business impact
- ⚠️ Requires threshold tuning to match legacy count
- ❌ Still doesn't address root question of "why filter?"

**Recommendation:** ✅ **If we must ship soon but can get threshold approval**

### Option C: Pause and Understand (Recommended Long-term)

**Pros:**
- ✅ Ensures we solve the right problem
- ✅ Enables proper re-engineering
- ✅ Builds institutional knowledge
- ✅ Prevents future confusion

**Cons:**
- ❌ Delays delivery
- ❌ Requires stakeholder availability
- ❌ May reveal larger systemic issues

**Recommendation:** 🎯 **STRONGLY RECOMMENDED - This is the right thing to do**

---

## Conclusion

**We are currently replicating logic we don't understand.**

The ROI filtering in Step 7 appears to be:
- ❌ Poorly documented
- ❌ Inconsistently implemented
- ❌ Lacking clear business rationale
- ❌ Possibly the result of historical accidents

**Before we can properly fix this, we need to answer:**
1. What business problem is this solving?
2. How do we measure success?
3. What are the actual requirements?

**Recommendation:**
- **Pause the replication effort**
- **Schedule stakeholder interviews**
- **Analyze historical performance data**
- **Document actual business requirements**
- **Then** re-engineer with confidence

**Otherwise, we're just copying broken code without understanding why it's broken or what it should do instead.**

---

## Appendix: Questions This Document Raises

1. Who originally wrote this code?
2. Is there a git history showing when ROI filtering was added?
3. Are there any Jira tickets or design docs for Step 7?
4. Has anyone ever questioned these thresholds before?
5. What happens if we just remove the ROI filter entirely?
6. Are there other steps with similar unexplained logic?
7. Is this a systemic problem across the pipeline?

**These questions suggest we may have a larger documentation and knowledge management problem beyond just Step 7.**
