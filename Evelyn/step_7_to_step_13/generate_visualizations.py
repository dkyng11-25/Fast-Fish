#!/usr/bin/env python3
"""
Visualization Generator for Step 7-13 Enhancement Reports

This script generates professional visualizations with clear axis labels
for the Step 7 and Step 8 enhancement evaluation reports.

Author: Data Pipeline Team
Date: January 2026
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
from pathlib import Path

# Set style for professional charts
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 150


def create_step7_recommendation_comparison():
    """Create Step 7 recommendation count comparison chart."""
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Data
    categories = ['Original Step 7', 'Enhanced Step 7']
    approved = [520, 214]
    time_suppressed = [0, 282]
    climate_suppressed = [0, 24]
    
    x = np.arange(len(categories))
    width = 0.5
    
    # Stacked bar chart
    bars1 = ax.bar(x, approved, width, label='Approved (ADD)', color='#2ecc71', edgecolor='white')
    bars2 = ax.bar(x, time_suppressed, width, bottom=approved, label='Suppressed (Time Gate)', color='#e74c3c', edgecolor='white')
    bars3 = ax.bar(x, climate_suppressed, width, bottom=[a+t for a,t in zip(approved, time_suppressed)], 
                   label='Suppressed (Climate Gate)', color='#f39c12', edgecolor='white')
    
    # Labels and title
    ax.set_xlabel('Step 7 Version', fontweight='bold')
    ax.set_ylabel('Number of Recommendations', fontweight='bold')
    ax.set_title('Step 7 Enhancement: Recommendation Count Comparison\n(Period: 202506A - June 2025)', 
                 fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend(loc='upper right')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height / 2),
                    ha='center', va='center', fontweight='bold', color='white', fontsize=12)
    
    for i, bar in enumerate(bars2):
        if time_suppressed[i] > 0:
            ax.annotate(f'{int(time_suppressed[i])}',
                        xy=(bar.get_x() + bar.get_width() / 2, approved[i] + time_suppressed[i] / 2),
                        ha='center', va='center', fontweight='bold', color='white', fontsize=12)
    
    # Add percentage annotation
    ax.annotate('58.8% Reduction\nin False Positives', 
                xy=(1, 350), fontsize=11, ha='center',
                bbox=dict(boxstyle='round', facecolor='#3498db', alpha=0.8),
                color='white', fontweight='bold')
    
    # Add grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    return fig


def create_step7_category_breakdown():
    """Create Step 7 category-wise eligibility breakdown chart."""
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Data
    categories = [
        'Summer Items\n(T恤, 短裤, 短袖)',
        'All-Season Items\n(内衣, 配饰)',
        'Core Subcategories\n(直筒裤, 束脚裤, 锥形裤)',
        'Transitional Items\n(夹克, 针织衫, 风衣)',
        'Winter Items\n(羽绒服, 棉服, 毛呢大衣)'
    ]
    
    approved = [123, 91, 45, 0, 0]  # Approved counts
    suppressed = [24, 0, 0, 144, 138]  # Suppressed counts
    
    y = np.arange(len(categories))
    height = 0.35
    
    # Horizontal bar chart
    bars1 = ax.barh(y - height/2, approved, height, label='ELIGIBLE (Approved)', color='#2ecc71')
    bars2 = ax.barh(y + height/2, suppressed, height, label='INELIGIBLE (Suppressed)', color='#e74c3c')
    
    # Labels and title
    ax.set_xlabel('Number of SPU × Store Combinations', fontweight='bold')
    ax.set_ylabel('Product Category', fontweight='bold')
    ax.set_title('Step 7 Enhancement: Eligibility by Product Category\n(Period: 202506A - June 2025)', 
                 fontweight='bold', fontsize=14)
    ax.set_yticks(y)
    ax.set_yticklabels(categories)
    ax.legend(loc='lower right')
    
    # Add value labels
    for bar in bars1:
        width = bar.get_width()
        if width > 0:
            ax.annotate(f'{int(width)}',
                        xy=(width + 3, bar.get_y() + bar.get_height() / 2),
                        ha='left', va='center', fontsize=10)
    
    for bar in bars2:
        width = bar.get_width()
        if width > 0:
            ax.annotate(f'{int(width)}',
                        xy=(width + 3, bar.get_y() + bar.get_height() / 2),
                        ha='left', va='center', fontsize=10)
    
    # Add annotation for core subcategories
    ax.annotate('Core subcategories\nALWAYS eligible\n(per client requirement)', 
                xy=(50, 2), fontsize=10, ha='center',
                bbox=dict(boxstyle='round', facecolor='#3498db', alpha=0.8),
                color='white', fontweight='bold')
    
    ax.xaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    return fig


def create_step8_filtering_comparison():
    """Create Step 8 eligibility filtering comparison chart."""
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Left chart: Original vs Enhanced
    ax1 = axes[0]
    categories = ['Original Step 8', 'Enhanced Step 8']
    analyzed = [1000, 499]
    filtered = [0, 501]
    
    x = np.arange(len(categories))
    width = 0.5
    
    bars1 = ax1.bar(x, analyzed, width, label='Analyzed for Imbalance', color='#3498db', edgecolor='white')
    bars2 = ax1.bar(x, filtered, width, bottom=analyzed, label='Filtered (Ineligible)', color='#95a5a6', edgecolor='white')
    
    ax1.set_xlabel('Step 8 Version', fontweight='bold')
    ax1.set_ylabel('Number of SPU × Store Combinations', fontweight='bold')
    ax1.set_title('Step 8: Records Analyzed vs Filtered', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.legend(loc='upper right')
    
    for bar in bars1:
        height = bar.get_height()
        ax1.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height / 2),
                    ha='center', va='center', fontweight='bold', color='white', fontsize=12)
    
    for i, bar in enumerate(bars2):
        if filtered[i] > 0:
            ax1.annotate(f'{int(filtered[i])}',
                        xy=(bar.get_x() + bar.get_width() / 2, analyzed[i] + filtered[i] / 2),
                        ha='center', va='center', fontweight='bold', color='white', fontsize=12)
    
    ax1.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax1.set_axisbelow(True)
    
    # Right chart: Eligibility distribution pie
    ax2 = axes[1]
    sizes = [499, 501]
    labels = ['ELIGIBLE\n(Summer/All-Season)\n499 (49.9%)', 'INELIGIBLE\n(Winter/Transition)\n501 (50.1%)']
    colors = ['#2ecc71', '#e74c3c']
    explode = (0.05, 0)
    
    ax2.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='',
            shadow=True, startangle=90)
    ax2.set_title('Eligibility Distribution in June 2025', fontweight='bold')
    
    plt.suptitle('Step 8 Enhancement: Eligibility-Aware Imbalance Detection\n(Period: 202506A)', 
                 fontweight='bold', fontsize=14, y=1.02)
    
    plt.tight_layout()
    return fig


def create_step8_false_positive_analysis():
    """Create Step 8 false positive analysis chart."""
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Data: Categories and their false positive potential
    categories = [
        'Down Jackets\n(羽绒服)',
        'Padded Jackets\n(棉服)',
        'Wool Coats\n(毛呢大衣)',
        'Jackets\n(夹克)',
        'Knitwear\n(针织衫)',
        'T-Shirts\n(T恤)',
        'Shorts\n(短裤)',
        'Underwear\n(内衣)'
    ]
    
    original_false_positives = [61, 38, 39, 51, 49, 0, 0, 0]  # Would be flagged incorrectly
    enhanced_false_positives = [0, 0, 0, 0, 0, 0, 0, 0]  # Correctly filtered
    
    y = np.arange(len(categories))
    height = 0.35
    
    bars1 = ax.barh(y - height/2, original_false_positives, height, 
                    label='Original Step 8 (False Positives)', color='#e74c3c')
    bars2 = ax.barh(y + height/2, enhanced_false_positives, height, 
                    label='Enhanced Step 8 (Correctly Filtered)', color='#2ecc71')
    
    ax.set_xlabel('Number of False Positive Imbalance Signals', fontweight='bold')
    ax.set_ylabel('Product Category', fontweight='bold')
    ax.set_title('Step 8 Enhancement: False Positive Elimination\n(Winter/Transition items in June would trigger false imbalance signals)', 
                 fontweight='bold', fontsize=13)
    ax.set_yticks(y)
    ax.set_yticklabels(categories)
    ax.legend(loc='lower right')
    
    # Add value labels
    for bar in bars1:
        width = bar.get_width()
        if width > 0:
            ax.annotate(f'{int(width)}',
                        xy=(width + 1, bar.get_y() + bar.get_height() / 2),
                        ha='left', va='center', fontsize=10, color='#e74c3c', fontweight='bold')
    
    # Add annotation
    ax.annotate('238 false positive\nsignals eliminated', 
                xy=(40, 6), fontsize=11, ha='center',
                bbox=dict(boxstyle='round', facecolor='#2ecc71', alpha=0.9),
                color='white', fontweight='bold')
    
    ax.xaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_xlim(0, 70)
    
    plt.tight_layout()
    return fig


def create_investment_savings_chart():
    """Create investment savings visualization."""
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    categories = ['Original\nRecommendations', 'Enhanced\nRecommendations', 'Savings']
    values = [547832, 225641, 322191]
    colors = ['#e74c3c', '#2ecc71', '#3498db']
    
    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=2)
    
    ax.set_xlabel('Category', fontweight='bold')
    ax.set_ylabel('Investment Amount (¥)', fontweight='bold')
    ax.set_title('Step 7 Enhancement: Investment Impact\n(Potential Dead Stock Investment Avoided)', 
                 fontweight='bold', fontsize=14)
    
    # Add value labels
    for bar, val in zip(bars, values):
        ax.annotate(f'¥{val:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10000),
                    ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    # Add percentage annotation
    ax.annotate('58.8% Savings', 
                xy=(2, 250000), fontsize=14, ha='center',
                bbox=dict(boxstyle='round', facecolor='white', edgecolor='#3498db', linewidth=2),
                color='#3498db', fontweight='bold')
    
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_ylim(0, 650000)
    
    # Format y-axis with thousands separator
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
    
    plt.tight_layout()
    return fig


def main():
    """Generate all visualizations."""
    
    # Create output directories
    step7_figures = Path(__file__).parent / 'step7' / 'figures'
    step8_figures = Path(__file__).parent / 'step8' / 'figures'
    step7_figures.mkdir(parents=True, exist_ok=True)
    step8_figures.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("GENERATING VISUALIZATIONS FOR STEP 7-13 ENHANCEMENT REPORTS")
    print("=" * 60)
    
    # Step 7 visualizations
    print("\n📊 Generating Step 7 visualizations...")
    
    fig1 = create_step7_recommendation_comparison()
    fig1.savefig(step7_figures / 'recommendation_comparison.png', bbox_inches='tight', dpi=150)
    print("   ✅ recommendation_comparison.png")
    
    fig2 = create_step7_category_breakdown()
    fig2.savefig(step7_figures / 'category_eligibility_breakdown.png', bbox_inches='tight', dpi=150)
    print("   ✅ category_eligibility_breakdown.png")
    
    fig5 = create_investment_savings_chart()
    fig5.savefig(step7_figures / 'investment_savings.png', bbox_inches='tight', dpi=150)
    print("   ✅ investment_savings.png")
    
    # Step 8 visualizations
    print("\n📊 Generating Step 8 visualizations...")
    
    fig3 = create_step8_filtering_comparison()
    fig3.savefig(step8_figures / 'eligibility_filtering_comparison.png', bbox_inches='tight', dpi=150)
    print("   ✅ eligibility_filtering_comparison.png")
    
    fig4 = create_step8_false_positive_analysis()
    fig4.savefig(step8_figures / 'false_positive_elimination.png', bbox_inches='tight', dpi=150)
    print("   ✅ false_positive_elimination.png")
    
    plt.close('all')
    
    print("\n" + "=" * 60)
    print("VISUALIZATION GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nStep 7 figures saved to: {step7_figures}")
    print(f"Step 8 figures saved to: {step8_figures}")


if __name__ == "__main__":
    main()
