#!/usr/bin/env python3
"""
SPU Rule System Visualization
Creates comprehensive charts showing the business distribution and performance
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load the consolidated results
print("Loading SPU rule analysis results...")
df = pd.read_csv('output/consolidated_spu_rule_results.csv', dtype={'str_code': str})

# Set up the plotting style
plt.style.use('default')
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
fig.suptitle('SPU Rule System - Business Intelligence Dashboard', fontsize=16, fontweight='bold')

# 1. Total Violations Distribution (Bar Chart)
violation_counts = df['total_spu_rule_violations'].value_counts().sort_index()
colors = ['#2E8B57', '#FFD700', '#FFA500', '#FF6347', '#DC143C', '#8B0000']
ax1.bar(violation_counts.index, violation_counts.values, color=colors[:len(violation_counts)])
ax1.set_title('Total Violations Distribution', fontweight='bold')
ax1.set_xlabel('Number of Violations')
ax1.set_ylabel('Number of Stores')
for i, v in enumerate(violation_counts.values):
    ax1.text(violation_counts.index[i], v + 10, f'{v}\n({v/len(df)*100:.1f}%)', 
             ha='center', va='bottom', fontweight='bold')

# 2. Individual Rule Performance (Horizontal Bar)
rules = ['rule7_missing_spu', 'rule8_imbalanced_spu', 'rule10_smart_overcapacity_standard', 
         'rule11_missed_sales_opportunity', 'rule12_sales_performance']
rule_names = ['Rule 7: Missing SPUs', 'Rule 8: Imbalanced', 'Rule 10: Overcapacity', 
              'Rule 11: Missed Sales', 'Rule 12: Performance']
flagged_counts = [df[rule].sum() for rule in rules if rule in df.columns]
rule_names = rule_names[:len(flagged_counts)]

ax2.barh(rule_names, flagged_counts, color=['#4CAF50', '#2196F3', '#FF9800', '#E91E63', '#9C27B0'])
ax2.set_title('Individual Rule Flagging Rates', fontweight='bold')
ax2.set_xlabel('Stores Flagged')
for i, v in enumerate(flagged_counts):
    ax2.text(v + 20, i, f'{v:,} ({v/len(df)*100:.1f}%)', va='center', fontweight='bold')

# 3. Cluster Violation Analysis (Top 10)
cluster_analysis = df.groupby('Cluster').agg({
    'total_spu_rule_violations': 'sum',
    'str_code': 'count'
}).reset_index()
cluster_analysis['violation_rate'] = cluster_analysis['total_spu_rule_violations'] / cluster_analysis['str_code']
top_clusters = cluster_analysis.nlargest(10, 'violation_rate')

ax3.bar(range(len(top_clusters)), top_clusters['violation_rate'], 
        color='#FF5722', alpha=0.7)
ax3.set_title('Top 10 Clusters by Violation Rate', fontweight='bold')
ax3.set_xlabel('Cluster Rank')
ax3.set_ylabel('Avg Violations per Store')
ax3.set_xticks(range(len(top_clusters)))
ax3.set_xticklabels([f'C{c}' for c in top_clusters['Cluster']], rotation=45)

# 4. Business Impact Summary (Pie Chart)
impact_levels = {
    'Excellent (0-1)': len(df[df['total_spu_rule_violations'] <= 1]),
    'Moderate (2-3)': len(df[df['total_spu_rule_violations'].between(2, 3)]),
    'High (4-5)': len(df[df['total_spu_rule_violations'] >= 4])
}

ax4.pie(impact_levels.values(), labels=impact_levels.keys(), autopct='%1.1f%%',
        colors=['#4CAF50', '#FFC107', '#F44336'], startangle=90)
ax4.set_title('Business Impact Distribution', fontweight='bold')

plt.tight_layout()
plt.savefig('output/spu_rule_summary_visualization.png', dpi=300, bbox_inches='tight')
plt.show()

print('\n=== SPU Rule System Summary ===')
print(f'Total Stores: {len(df):,}')
print(f'Stores with Violations: {(df["total_spu_rule_violations"] > 0).sum():,} ({(df["total_spu_rule_violations"] > 0).mean()*100:.1f}%)')
print(f'Average Violations per Store: {df["total_spu_rule_violations"].mean():.2f}')
print(f'Total Business Opportunities: {df["total_spu_rule_violations"].sum():,}')
print('\nVisualization saved to: output/spu_rule_summary_visualization.png') 