# ❌ D-C: Cluster Stability Report - NOT DONE

**Requirement ID:** D-C  
**Status:** ❌ NOT DONE  
**Source:** July 15 Deliverables  
**Priority:** 🔴 CRITICAL  
**Score:** 2/10

---

## 📋 Requirement Description

Create a Cluster Stability Report that tracks how cluster membership changes across periods using **Jaccard similarity**.

**Client Expectation:**
- Compare clustering results between consecutive periods
- Calculate Jaccard similarity for each cluster
- Identify stable vs unstable clusters
- Track store migration between clusters

---

## ❌ Current State

### What Exists
- Clustering results are saved per period (`clustering_results_spu_YYYYMMP.csv`)
- Multiple periods of data exist
- No comparison logic between periods

### What's Missing
1. **Jaccard Similarity Calculation** - No function to compare cluster membership
2. **Period Comparison Logic** - No code to load and compare multiple periods
3. **Stability Report Generation** - No output file for stability metrics

---

## 🔧 What is Needed to Get it Done

### 1. Python Code Required ✅

**Location:** New file `src/step6b_cluster_stability.py` or extension of Step 6

**Implementation:**

```python
import pandas as pd
from typing import Dict, List, Tuple, Set

def calculate_jaccard_similarity(set_a: Set, set_b: Set) -> float:
    """
    Calculate Jaccard similarity between two sets.
    
    Jaccard = |A ∩ B| / |A ∪ B|
    
    Returns:
        float: Jaccard similarity (0.0 to 1.0)
    """
    if len(set_a) == 0 and len(set_b) == 0:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def find_best_matching_cluster(
    current_stores: Set[str],
    previous_results: pd.DataFrame
) -> Tuple[int, float]:
    """
    Find the cluster in previous period that best matches current cluster.
    
    Returns:
        Tuple of (best_matching_cluster_id, jaccard_similarity)
    """
    best_cluster = -1
    best_jaccard = 0.0
    
    for prev_cluster_id in previous_results['cluster_id'].unique():
        prev_stores = set(
            previous_results[previous_results['cluster_id'] == prev_cluster_id]['str_code'].astype(str)
        )
        jaccard = calculate_jaccard_similarity(current_stores, prev_stores)
        if jaccard > best_jaccard:
            best_jaccard = jaccard
            best_cluster = prev_cluster_id
    
    return best_cluster, best_jaccard


def generate_cluster_stability_report(
    current_period: str,
    previous_period: str,
    current_results_path: str,
    previous_results_path: str,
    output_path: str = "output/cluster_stability_report.csv"
) -> pd.DataFrame:
    """
    Generate cluster stability report comparing two periods.
    
    Args:
        current_period: Current period label (e.g., "202509A")
        previous_period: Previous period label (e.g., "202508B")
        current_results_path: Path to current clustering results
        previous_results_path: Path to previous clustering results
        output_path: Path to save stability report
    
    Returns:
        DataFrame with stability metrics per cluster
    """
    # Load clustering results
    current_df = pd.read_csv(current_results_path)
    previous_df = pd.read_csv(previous_results_path)
    
    # Ensure str_code is string
    current_df['str_code'] = current_df['str_code'].astype(str)
    previous_df['str_code'] = previous_df['str_code'].astype(str)
    
    stability_records = []
    
    for cluster_id in current_df['cluster_id'].unique():
        current_stores = set(
            current_df[current_df['cluster_id'] == cluster_id]['str_code']
        )
        
        # Find best matching cluster in previous period
        best_prev_cluster, jaccard = find_best_matching_cluster(
            current_stores, previous_df
        )
        
        # Get previous cluster stores for comparison
        if best_prev_cluster >= 0:
            prev_stores = set(
                previous_df[previous_df['cluster_id'] == best_prev_cluster]['str_code']
            )
            stores_added = current_stores - prev_stores
            stores_removed = prev_stores - current_stores
            stores_retained = current_stores & prev_stores
        else:
            stores_added = current_stores
            stores_removed = set()
            stores_retained = set()
        
        stability_records.append({
            'current_period': current_period,
            'previous_period': previous_period,
            'cluster_id': cluster_id,
            'cluster_size': len(current_stores),
            'best_matching_prev_cluster': best_prev_cluster,
            'jaccard_similarity': round(jaccard, 4),
            'is_stable': jaccard >= 0.7,
            'stores_retained': len(stores_retained),
            'stores_added': len(stores_added),
            'stores_removed': len(stores_removed),
            'retention_rate': round(len(stores_retained) / len(current_stores), 4) if len(current_stores) > 0 else 0
        })
    
    stability_df = pd.DataFrame(stability_records)
    
    # Add summary statistics
    summary = {
        'total_clusters': len(stability_df),
        'stable_clusters': stability_df['is_stable'].sum(),
        'unstable_clusters': (~stability_df['is_stable']).sum(),
        'avg_jaccard': stability_df['jaccard_similarity'].mean(),
        'min_jaccard': stability_df['jaccard_similarity'].min(),
        'max_jaccard': stability_df['jaccard_similarity'].max(),
        'avg_retention_rate': stability_df['retention_rate'].mean()
    }
    
    print(f"Cluster Stability Summary:")
    print(f"  Total clusters: {summary['total_clusters']}")
    print(f"  Stable clusters (Jaccard ≥ 0.7): {summary['stable_clusters']}")
    print(f"  Unstable clusters: {summary['unstable_clusters']}")
    print(f"  Average Jaccard: {summary['avg_jaccard']:.4f}")
    print(f"  Average retention rate: {summary['avg_retention_rate']:.4f}")
    
    # Save report
    stability_df.to_csv(output_path, index=False)
    print(f"Stability report saved to: {output_path}")
    
    return stability_df


if __name__ == "__main__":
    # Example usage
    generate_cluster_stability_report(
        current_period="202509A",
        previous_period="202508B",
        current_results_path="output/clustering_results_spu_202509A.csv",
        previous_results_path="output/clustering_results_spu_202508B.csv"
    )
```

### 2. Missing Dataset ⚠️

**Required:** Clustering results from at least 2 consecutive periods

**Check if available:**
```bash
ls output/clustering_results_spu_*.csv
```

If only one period exists, need to run Step 6 for additional periods.

### 3. No External Dependencies Required ✅

This can be implemented with existing libraries (pandas, standard Python sets).

---

## 📊 Expected Output

**File:** `output/cluster_stability_report.csv`

| Column | Description |
|--------|-------------|
| current_period | Current period label |
| previous_period | Previous period label |
| cluster_id | Cluster ID in current period |
| cluster_size | Number of stores in cluster |
| best_matching_prev_cluster | Best matching cluster from previous period |
| jaccard_similarity | Jaccard similarity (0.0 to 1.0) |
| is_stable | True if Jaccard ≥ 0.7 |
| stores_retained | Stores that stayed in cluster |
| stores_added | New stores added to cluster |
| stores_removed | Stores that left cluster |
| retention_rate | Proportion of stores retained |

---

## ✅ Action Items

| # | Action | Owner | Status |
|---|--------|-------|--------|
| 1 | Create `step6b_cluster_stability.py` | Data Intern | ⏳ Pending |
| 2 | Verify multiple periods of clustering results exist | Data Intern | ⏳ Pending |
| 3 | Run stability analysis | Data Intern | ⏳ Pending |
| 4 | Generate stability report | Data Intern | ⏳ Pending |

---

## 🔄 Improvement Loop

**Current Iteration:** 1  
**Status:** Ready to implement - Need to verify data availability

**Next Steps:**
1. Check if multiple periods of clustering results exist
2. Implement Python code
3. Generate stability report
4. Re-evaluate requirement status
