# Rule 9: Below Minimum Spus Analysis Summary

**Date**: 2025-06-17 16:25:00
**Analysis Level**: Spu

## Rule Definition
Identifies store-spu combinations with positive but below minimum viable style counts.

## Parameters
- Analysis Level: spu
- Minimum style threshold: 0.035
- Logic: 0 < style_count < threshold

## Results
- Total stores analyzed: 2,263
- Stores with below minimum issues: 2,257
- Total below minimum cases: 62,932
- Total store-spu combinations: 526,846
- Average cases per flagged store: 27.9
- Total style increase needed: 865.4
- Average current count: 0.02

## Severity Breakdown
- HIGH: 62,932 cases

## Most Affected SPUs
- 15S5020: 1,144 cases
- 15S1016: 1,015 cases
- 15S5025: 988 cases
- 15S5016: 980 cases
- 15S5024: 978 cases
- 15S1024: 973 cases
- 15S1022: 942 cases
- 15S5013: 937 cases
- 15S1012: 928 cases
- 15S1017: 899 cases

## Cluster-Level Insights
Top 5 clusters by lowest average style count:
- Cluster 38: 50.0 stores, avg count 0.02
- Cluster 30: 49.0 stores, avg count 0.02
- Cluster 36: 50.0 stores, avg count 0.02
- Cluster 25: 73.0 stores, avg count 0.02
- Cluster 20: 50.0 stores, avg count 0.02
