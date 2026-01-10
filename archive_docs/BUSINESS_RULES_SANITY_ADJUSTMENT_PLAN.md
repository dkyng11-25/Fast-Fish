# Business Rules Sanity Adjustment Plan
**Date**: January 2025  
**Purpose**: Adjust business rule thresholds to generate realistic, actionable recommendations  
**Target**: 10-30% flagged stores (down from current 80-90%)

## 🚨 **CURRENT PROBLEMS IDENTIFIED**

### **Unrealistic Flagging Rates**:
- **Rule 7**: 86.4% of stores flagged (should be ~15-20%)
- **Rule 8**: 37.1% of stores flagged (should be ~10-15%) 
- **Rule 12**: 93.7% of stores flagged (should be ~20-25%)

### **Excessive Recommendations**:
- **Average quantity increases**: 215 units/store (should be 5-50)
- **Max missing SPUs**: 64 per store (should be 1-5)
- **Max quantity increase**: 1,032 units (should be 50 max)

## 🔧 **THRESHOLD ADJUSTMENTS BY RULE**

### **Rule 7: Missing SPUs - CONSERVATIVE ADJUSTMENTS**

**Current Parameters**:
```python
CLUSTER_ADOPTION_THRESHOLD = 0.90  # 90%
MIN_SALES_THRESHOLD = 500         # ¥500
MAX_MISSING_SPUS = None           # No limit
```

**Proposed Parameters**:
```python
CLUSTER_ADOPTION_THRESHOLD = 0.98   # 98% (much more selective)
MIN_SALES_THRESHOLD = 3000          # ¥3,000 (proven performers)
MAX_MISSING_SPUS_PER_STORE = 3      # Max 3 SPUs per store
MIN_CLUSTER_SIZE = 5                # At least 5 stores in cluster
MIN_TOTAL_OPPORTUNITY = 2000        # ¥2,000 minimum opportunity
```

**Expected Impact**: Reduce from 86.4% → ~15% flagged stores

### **Rule 8: Imbalanced - STRICTER CRITERIA**

**Current Parameters**:
```python
Z_SCORE_THRESHOLD = 4.0           # |Z-Score| > 4.0
MIN_ADJUSTMENT = None             # No minimum
```

**Proposed Parameters**:
```python
Z_SCORE_THRESHOLD = 6.0             # |Z-Score| > 6.0 (extreme cases only)
MIN_ADJUSTMENT_QUANTITY = 15        # Minimum 15 units impact
MIN_ADJUSTMENT_VALUE = 1000         # Minimum ¥1,000 impact
MAX_ADJUSTMENTS_PER_STORE = 5       # Max 5 rebalancing actions per store
```

**Expected Impact**: Reduce from 37.1% → ~10% flagged stores

### **Rule 12: Performance - REALISTIC BENCHMARKS**

**Current Parameters**:
```python
BENCHMARK_PERCENTILE = 90         # Top 90th percentile
MAX_QUANTITY_INCREASE = None      # No limit
```

**Proposed Parameters**:
```python
BENCHMARK_PERCENTILE = 75           # 75th percentile (more achievable)
MAX_QUANTITY_INCREASE_PER_STORE = 40  # Max 40 units per store
MAX_CATEGORIES_PER_STORE = 3        # Focus on top 3 opportunities
MIN_ROI_THRESHOLD = 0.25            # 25% ROI minimum
MIN_OPPORTUNITY_GAP = 2.0           # 2.0 Z-score minimum gap
```

**Expected Impact**: Reduce from 93.7% → ~20% flagged stores

## 🎯 **ADDITIONAL SANITY CONSTRAINTS**

### **Universal Store Constraints**:
```python
# Store capacity limits
MAX_TOTAL_SPU_CHANGES_PER_STORE = 5      # Max 5 SPU changes per store
MAX_TOTAL_QUANTITY_CHANGES_PER_STORE = 50 # Max 50 units per store
MAX_INVESTMENT_PER_STORE = 8000          # Max ¥8,000 per store

# Business logic constraints  
MIN_CLUSTER_SIMILARITY = 0.7             # Only recommend within similar stores
SEASONAL_ALIGNMENT_REQUIRED = True       # Must match current season
FAST_FISH_VALIDATION_REQUIRED = True     # Must pass sell-through validation
```

### **Fast Fish Integration**:
```python
# Sell-through validation thresholds
MIN_PREDICTED_SELLTHROUGH = 50.0         # 50% minimum sell-through
MIN_SELLTHROUGH_IMPROVEMENT = 5.0        # 5% improvement required
MAX_SELLTHROUGH_RISK = 80.0              # Don't exceed 80% (inventory risk)
```

## 📊 **EXPECTED OUTCOMES AFTER ADJUSTMENTS**

### **Realistic Flagging Rates**:
- **Rule 7**: ~300 stores flagged (vs 1,919 current)
- **Rule 8**: ~220 stores flagged (vs 824 current) 
- **Rule 12**: ~440 stores flagged (vs 2,081 current)
- **Total**: ~960 flagged stores (vs 4,824 current)

### **Quality Improvements**:
- **Average SPU changes**: 1-3 per recommendation
- **Average quantity changes**: 10-30 units per store
- **Average investment**: ¥2,000-¥6,000 per store
- **Fast Fish pass rate**: 60-80% (vs current unknown)

### **Business Benefits**:
- **Actionable recommendations**: Store managers can actually implement
- **Realistic targets**: Achievable within 15-day periods
- **Higher confidence**: Sell-through validated recommendations
- **Better ROI**: Focus on proven opportunities only

## 🔧 **IMPLEMENTATION PRIORITY**

### **Phase 1: Critical Fixes (Immediate)**
1. **Rule 12**: Cap quantity increases at 40 units
2. **Rule 7**: Increase adoption threshold to 98%
3. **All Rules**: Add Fast Fish sell-through validation

### **Phase 2: Refinements (Next)**
1. **Rule 8**: Increase Z-score threshold to 6.0
2. **All Rules**: Add store capacity constraints
3. **Rule 12**: Change benchmark to 75th percentile

### **Phase 3: Optimization (Future)**
1. **Clustering**: Review cluster quality and similarity
2. **Seasonality**: Add seasonal appropriateness filters
3. **ROI**: Implement ROI-based prioritization

## ✅ **SUCCESS CRITERIA**

**Target Metrics After Adjustments**:
- **Flagged Store Rate**: 10-30% (vs current 80-90%)
- **Average Recommendations per Store**: 2-5 (vs current 10+)
- **Fast Fish Pass Rate**: 60-80%
- **Store Manager Adoption Rate**: 70%+ (actionable recommendations)
- **Actual Implementation Rate**: 50%+ (realistic targets)

**Quality Gates**:
- No store should have >5 SPU changes recommended
- No store should have >50 quantity units recommended  
- All recommendations must pass Fast Fish sell-through validation
- All recommendations must have positive ROI projection 