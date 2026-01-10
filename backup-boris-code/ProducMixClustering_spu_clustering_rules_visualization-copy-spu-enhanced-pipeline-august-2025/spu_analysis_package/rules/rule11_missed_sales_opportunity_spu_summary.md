# Rule 11: Missed Sales Opportunity Spu-Level Analysis Summary

**Date**: 2025-06-17 20:53:08
**Analysis Level**: Spu

## Rule Definition
Identifies stores missing SPU sales opportunities where the store has low SPU sales (<$50) but 60%+ of cluster peers have high SPU sales (≥$200).
**Inverse of overcapacity rule**: Instead of reallocating away, boost the underperformer.

### Supplementary Measures
1. **Cluster Relative Underperformance**: Store performs significantly below cluster average
2. **Cluster Misjudgment**: Cluster may be poorly formed (high variability or poor performance vs global average)

## Parameters
- Store underperformance threshold: <$50 sales
- High sales target: $200
- Cluster success threshold: ≥60% of peers exceeding target
- Minimum cluster peers: 3 stores
- Minimum sales volume: 1 units
- Cluster underperformance margin: 10000%
- Cluster misjudgment threshold: 30%
- Cluster variability threshold: 60%

## Results
- Total stores analyzed: 2,263
- Stores with missed opportunities: 1,326
- Total missed opportunities: 2,219
- Stores with cluster relative underperformance: 2,256
- Stores affected by cluster misjudgment: 2,259
- Total potential sales increase: 1008790.9 units
- Average opportunity gap: 45461.5%
- Facing count recommendations: 2,219
- Promotion recommendations: 72

## Top Subcategories for Opportunity
- 休闲圆领T恤: 300603.9 units potential increase
- 微宽松圆领T恤: 93820.0 units potential increase
- 束脚裤: 91200.2 units potential increase
- 合体圆领T恤: 77726.0 units potential increase
- 休闲POLO: 77488.9 units potential increase
- 中裤: 65172.3 units potential increase
- 短裤: 58516.7 units potential increase
- 锥形裤: 34570.5 units potential increase
- 凉感圆领T恤: 30757.0 units potential increase
- 套头POLO: 26917.5 units potential increase

## Recommendation Distribution
- Increase facing count: 2,147 cases
- Increase facing count + Local promotion: 72 cases
