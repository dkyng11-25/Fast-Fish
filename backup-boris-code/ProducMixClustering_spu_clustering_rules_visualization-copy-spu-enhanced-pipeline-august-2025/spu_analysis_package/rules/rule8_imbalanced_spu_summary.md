# Rule 8: Imbalanced Spus Allocation Analysis Summary

**Date**: 2025-06-17 16:22:21
**Analysis Level**: Spu

## Rule Definition
Identifies stores with imbalanced spu allocations using Z-Score analysis within cluster peers.

## Parameters
- Analysis Level: spu
- Z-Score threshold: |Z| > 4.0
- Minimum cluster size: ≥5 stores
- Minimum allocation threshold: ≥0.05 styles

## Results
- Total stores analyzed: 2,263
- Stores with imbalanced allocations: 319
- Total imbalanced SPUs: 530
- Over-allocated cases: 530
- Under-allocated cases: 0
- Average |Z-Score|: 4.47

## Severity Breakdown
- EXTREME: 530 cases

## Top SPUs with Imbalances
- 15P5003: 13 cases
- 15P5004: 11 cases
- 15R1008: 10 cases
- 15S1016: 9 cases
- 15T5098: 8 cases
- 15R1011: 8 cases
- 15T1076: 7 cases
- 15T5033: 7 cases
- 15S5014: 7 cases
- 15S1017: 7 cases

## Cluster-Level Insights
Top 5 clusters by average |Z-Score|:
- Cluster 36: 5.0 stores, avg |Z-Score| 4.80
- Cluster 11: 4.0 stores, avg |Z-Score| 4.73
- Cluster 43: 9.0 stores, avg |Z-Score| 4.70
- Cluster 26: 6.0 stores, avg |Z-Score| 4.68
- Cluster 37: 18.0 stores, avg |Z-Score| 4.67
