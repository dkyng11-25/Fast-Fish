# Rule 10: Smart Overcapacity Spu-Level Multi-Profile Analysis Summary

**Date**: 2025-06-17 18:06:47
**Analysis Level**: Spu

## Rule Definition
Identifies stores with underperforming allocations that could be reallocated to better-performing clusters.
Now supports multiple performance threshold profiles for business scenario testing.

## Performance Profiles
### Strict (Conservative)
- **Gap Threshold**: ≥20%
- **Local Performance**: ≤50000%
- **Target Performance**: >90000%
- **Description**: Conservative SPU-level profile focusing on high-performance reallocations

### Standard (Balanced)
- **Gap Threshold**: ≥15%
- **Local Performance**: ≤40000%
- **Target Performance**: >80000%
- **Description**: Balanced SPU-level approach with moderate reallocation sensitivity

### Lenient (Aggressive)
- **Gap Threshold**: ≥10%
- **Local Performance**: ≤35000%
- **Target Performance**: >70000%
- **Description**: Aggressive SPU-level profile for growth-focused reallocation strategies

## Results Summary
- **Total stores analyzed**: 2,263

### Strict (Conservative) Results
- Stores flagged: 2,157
- Total opportunities: 11,952
- Total suggested reallocation: 5246.8 styles
- Potential performance improvement: 529.4%


## Top Subcategories for Reallocation
- 针织防晒衣: 1529.7 styles
- 锥形裤: 419.8 styles
- 中裤: 396.7 styles
- 直筒裤: 394.8 styles
- 短裤: 380.1 styles
- 阔腿裤: 358.7 styles
- 工装裤: 197.3 styles
- 休闲圆领T恤: 190.7 styles
- 束脚裤: 181.1 styles
- 裙类套装: 178.5 styles
### Standard (Balanced) Results
- Stores flagged: 2,001
- Total opportunities: 8,977
- Total suggested reallocation: 3515.0 styles
- Potential performance improvement: 594.2%


## Top Subcategories for Reallocation
- 针织防晒衣: 993.6 styles
- 短裤: 311.5 styles
- 直筒裤: 301.2 styles
- 阔腿裤: 258.7 styles
- 中裤: 174.4 styles
- 束脚裤: 151.9 styles
- 修身圆领T恤: 144.4 styles
- 锥形裤: 121.8 styles
- 微宽松圆领T恤: 116.8 styles
- 休闲衬衣: 99.6 styles
### Lenient (Aggressive) Results
- Stores flagged: 1,983
- Total opportunities: 9,578
- Total suggested reallocation: 3249.1 styles
- Potential performance improvement: 586.6%


## Top Subcategories for Reallocation
- 针织防晒衣: 827.2 styles
- 短裤: 368.8 styles
- 微宽松圆领T恤: 257.6 styles
- 直筒裤: 185.4 styles
- 束脚裤: 167.6 styles
- 修身圆领T恤: 149.9 styles
- 阔腿裤: 143.6 styles
- 休闲POLO: 126.4 styles
- 中裤: 97.4 styles
- 锥形裤: 90.0 styles
