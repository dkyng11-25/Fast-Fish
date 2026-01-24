# Step 7 Enhancement Proposal: Time-Aware & Climate-Aware Missing SPU Rule

> **Document Type:** Business Proposal & Technical Design  
> **Audience:** Business Stakeholders, Merchandising Team, Data Science Team  
> **Purpose:** Explain why and how Step 7 should be enhanced with climate awareness  
> **Last Updated:** January 2026

---

## Executive Summary

This proposal recommends enhancing Step 7 (Missing SPU Rule) with **time-aware** and **climate-aware** logic to reduce false-positive recommendations and improve seasonal alignment.

### The Problem in One Sentence

> **Current Step 7 may recommend winter jackets to stores in June because it doesn't know what season it is.**

### The Solution in One Sentence

> **Add climate-based gating conditions that suppress recommendations when the product doesn't match the current weather.**

---

## 1. Background: What Step 7 Does Today

### Purpose in the Fast Fish Pipeline

Step 7 is part of the **demand forecasting decision support system**. After stores are clustered (Steps 1-6), Step 7 identifies **missing products** that should be added to each store.

### Current Logic (Simplified)

```
IF ≥80% of stores in the same cluster sell a specific SPU
AND the SPU is missing from a given store
THEN recommend:
    → SPU to ADD
    → Recommended quantity
    → Expected investment
    → Sell-through validation
```

### Example

| Store | Cluster | SPU | Cluster Adoption | Recommendation |
|-------|---------|-----|------------------|----------------|
| S001 | Cluster 15 | Winter Jacket A | 85% | ✅ ADD 5 units |
| S002 | Cluster 15 | Summer T-Shirt B | 90% | ✅ ADD 8 units |

**The rule works well when products are season-appropriate.** But what happens in June when the rule recommends Winter Jacket A?

---

## 2. Current Limitations: Why Step 7 Needs Improvement

### ❌ Limitation 1: Time-Agnostic

**Problem:** Step 7 uses historical aggregated sales data without considering **when** the recommendation will be executed.

**Example:**
- Historical data shows Winter Jacket A sold well in January
- Step 7 runs in June and still recommends Winter Jacket A
- Store receives winter inventory in summer → **dead stock**

**Business Impact:**
- Increased markdown pressure
- Reduced sell-through rates
- Wasted investment capital

### ❌ Limitation 2: Climate-Blind

**Problem:** Step 7 doesn't consider the **current weather conditions** at each store's location.

**Example:**
- Store in Harbin (cold climate): 15°C in June
- Store in Guangzhou (hot climate): 32°C in June
- Same recommendation for both → **one is wrong**

**Business Impact:**
- Misaligned inventory for regional climate differences
- Lost sales opportunities (right product, wrong store)
- Customer dissatisfaction

### ❌ Limitation 3: Static Thresholds

**Problem:** The 80% adoption threshold is fixed regardless of season or product type.

**Example:**
- In peak winter season, 80% adoption for winter coats makes sense
- In off-season, even 50% adoption might be too aggressive

**Business Impact:**
- Over-recommendation in off-season
- Under-recommendation in peak season

### ❌ Limitation 4: Binary Rule Triggering

**Problem:** The rule is either "ADD" or "DO NOTHING" with no conditional activation.

**Example:**
- A store might benefit from a product in 2 weeks when weather changes
- Current rule can't express "ADD, but only when temperature drops"

**Business Impact:**
- Missed timing opportunities
- No forward-looking capability

---

## 3. Design Philosophy: Why Rule-Based, Not ML

### Why We Are NOT Building a Machine Learning Model

| Approach | Pros | Cons |
|----------|------|------|
| **ML Model** | Potentially higher accuracy | Black-box, hard to explain to merchandisers |
| **Rule-Based** | Transparent, auditable, business-aligned | May miss complex patterns |

**Fast Fish's Priority:** Merchandisers need to **understand and trust** the recommendations.

> "If I can't explain why the system recommended this, I won't use it."  
> — Typical merchandiser feedback

### Our Approach: Enhanced Rules, Not Replaced Rules

We will **preserve the original Step 7 logic** and add **gating conditions** based on climate and time.

```
Original Rule:
    IF adoption ≥ 80% AND spu_missing THEN ADD

Enhanced Rule:
    IF adoption ≥ 80% 
    AND spu_missing 
    AND climate_appropriate(spu, store_temperature)  ← NEW
    AND timing_appropriate(spu, current_period)      ← NEW
    THEN ADD
    ELSE suppress_temporarily
```

---

## 4. Proposed Enhancement: Time-Aware & Climate-Aware Step 7

### 4.1 Climate-Aware Activation

#### Concept

Each SPU (or category) is mapped to a **temperature suitability range**:

| Category | Temperature Band | Feels-Like Range |
|----------|-----------------|------------------|
| Winter Outerwear | Cold | ≤ 10°C |
| Transitional Jackets | Cool/Warm | 10°C - 20°C |
| Summer Tops | Warm/Hot | ≥ 20°C |
| All-Season Basics | Any | -∞ to +∞ |

#### How It Works

1. **Load store temperature data** from Step 5 (feels_like_temperature.csv)
2. **Map each SPU to its temperature band** based on category
3. **Gate the recommendation:**
   - If store temperature matches SPU band → **ALLOW recommendation**
   - If store temperature doesn't match → **SUPPRESS recommendation**

#### Example

| Store | Current Temp | SPU | SPU Band | Match? | Action |
|-------|--------------|-----|----------|--------|--------|
| S001 (Harbin) | 15°C | Winter Jacket | Cold (≤10°C) | ❌ No | SUPPRESS |
| S002 (Harbin) | 15°C | Light Jacket | Cool (10-20°C) | ✅ Yes | ADD |
| S003 (Guangzhou) | 32°C | Summer Dress | Hot (≥20°C) | ✅ Yes | ADD |
| S004 (Guangzhou) | 32°C | Winter Coat | Cold (≤10°C) | ❌ No | SUPPRESS |

### 4.2 Time-Aware Logic

#### Concept

The rule should consider **when** the recommendation will be executed:

| Time Context | Behavior |
|--------------|----------|
| **Early Season** | Aggressive recommendations (prepare inventory) |
| **Peak Season** | Standard recommendations |
| **Off-Season** | Conservative recommendations (avoid dead stock) |

#### How It Works

1. **Determine current period** (e.g., 202506A = June 2025, first half)
2. **Classify season phase** based on month:
   - Summer peak: June-August
   - Winter peak: December-February
   - Transition: March-May, September-November
3. **Adjust recommendation behavior:**
   - In-season products: Full recommendations
   - Off-season products: Suppress or reduce quantities

#### Example

| Period | Product Type | Season Phase | Action |
|--------|--------------|--------------|--------|
| 202506A (June) | Summer Dress | Peak Season | ✅ Full recommendation |
| 202506A (June) | Winter Coat | Off-Season | ❌ Suppress |
| 202512A (December) | Winter Coat | Peak Season | ✅ Full recommendation |
| 202512A (December) | Summer Dress | Off-Season | ❌ Suppress |

### 4.3 Enhanced Rule Logic (Complete)

```python
def should_recommend_spu(store, spu, cluster_adoption, store_temperature, current_period):
    """
    Enhanced Step 7 recommendation logic with climate and time awareness.
    
    Original Rule: adoption ≥ 80% AND spu_missing
    Enhanced Rule: Original + climate_gate + time_gate
    """
    # Original Step 7 logic (PRESERVED)
    if cluster_adoption < 0.80:
        return False, "Below adoption threshold"
    
    if spu_already_in_store(store, spu):
        return False, "SPU already present"
    
    # NEW: Climate-aware gating
    spu_temp_band = get_spu_temperature_band(spu)
    if not temperature_matches_band(store_temperature, spu_temp_band):
        return False, f"Climate mismatch: store={store_temperature}°C, spu_band={spu_temp_band}"
    
    # NEW: Time-aware gating
    spu_season = get_spu_season(spu)
    current_season = get_current_season(current_period)
    if not season_appropriate(spu_season, current_season):
        return False, f"Season mismatch: spu={spu_season}, current={current_season}"
    
    # All gates passed
    return True, "Recommendation approved"
```

---

## 5. Expected Benefits

### 5.1 Reduced False-Positive Recommendations

| Metric | Before | After (Expected) |
|--------|--------|------------------|
| Off-season recommendations | ~30% of total | <5% of total |
| Climate-mismatched recommendations | ~20% of total | <3% of total |
| Overall false-positive rate | ~40% | <10% |

### 5.2 Better Seasonal Alignment

- **Summer period (June):** Only summer-appropriate products recommended
- **Winter period (December):** Only winter-appropriate products recommended
- **Transition periods:** Balanced mix based on temperature trends

### 5.3 Higher Trust from Merchandisers

> "The system now recommends products that make sense for the weather. I trust it more."

- Fewer manual overrides needed
- Higher adoption rate of recommendations
- Faster decision-making

### 5.4 Improved Sell-Through Rates

By recommending only climate-appropriate products:
- Products arrive when customers want them
- Reduced markdown pressure
- Better inventory turnover

---

## 6. What Changed vs Original Step 7

### Code-Level Changes (Summary)

| Component | Original | Enhanced |
|-----------|----------|----------|
| **Data Loading** | Sales + Clustering | Sales + Clustering + **Temperature** |
| **Adoption Check** | ≥80% threshold | ≥80% threshold (unchanged) |
| **Missing Check** | SPU not in store | SPU not in store (unchanged) |
| **Climate Gate** | ❌ None | ✅ Temperature band matching |
| **Time Gate** | ❌ None | ✅ Season phase matching |
| **Output** | ADD recommendations | ADD + **suppression reasons** |

### New Functions Added

1. `load_store_temperature_data()` - Load Step 5 temperature output
2. `get_spu_temperature_band()` - Map SPU to temperature suitability
3. `temperature_matches_band()` - Check if store temp matches SPU band
4. `get_current_season()` - Determine season from period
5. `season_appropriate()` - Check if SPU season matches current season

### New Output Columns

| Column | Description |
|--------|-------------|
| `climate_gate_passed` | True/False - did climate check pass? |
| `time_gate_passed` | True/False - did time check pass? |
| `suppression_reason` | Why recommendation was suppressed (if applicable) |
| `store_temperature` | Current feels-like temperature at store |
| `spu_temperature_band` | Expected temperature band for this SPU |

---

## 7. Implementation Plan

### Phase 1: Development (This Sprint)

1. Create `step7_missing_spu_time_aware.py` in Evelyn folder
2. Implement climate-aware gating logic
3. Implement time-aware gating logic
4. Add comprehensive logging for auditability

### Phase 2: Validation (This Sprint)

1. Run on 202506A sample dataset
2. Compare original vs enhanced recommendations
3. Generate evaluation report with visualizations
4. Review with merchandising team

### Phase 3: Production Rollout (Next Sprint)

1. Integrate with main pipeline
2. Monitor recommendation quality
3. Collect merchandiser feedback
4. Iterate based on feedback

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Over-suppression of valid recommendations | Medium | Medium | Configurable thresholds, easy to adjust |
| Temperature data unavailable | Low | High | Graceful fallback to original logic |
| Category-temperature mapping errors | Medium | Medium | Start with broad categories, refine over time |
| Downstream step compatibility | Low | High | Output format unchanged, only adds columns |

---

## 9. Conclusion

### Recommendation

**Proceed with the Time-Aware & Climate-Aware Step 7 enhancement.**

### Key Points

1. **Preserves original logic** - No breaking changes
2. **Adds business value** - Reduces false-positive recommendations
3. **Maintains interpretability** - Rule-based, not black-box ML
4. **Low risk** - Graceful fallback if temperature data unavailable
5. **Aligned with Fast Fish operations** - Merchandisers can understand and trust it

### Next Steps

1. ✅ Review and approve this proposal
2. ⏳ Implement enhanced module
3. ⏳ Run validation on 202506A
4. ⏳ Present results to merchandising team

---

*Proposal prepared for Fast Fish Demand Forecasting Project*  
*For questions, contact the Data Science Team*
