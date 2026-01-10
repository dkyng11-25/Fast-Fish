#!/usr/bin/env python3
"""
Detailed Sanity Check for August 2025 Predictions
Analyzes every column in the output file for data integrity and business logic validation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import json

def load_sample_data() -> pd.DataFrame:
    """Load sample rows for detailed analysis."""
    try:
        df = pd.read_csv("output/fast_fish_with_sell_through_analysis_20250711_112025.csv")
        print(f"✅ Loaded {len(df):,} total records")
        
        # Take first 3 rows for detailed analysis
        sample_df = df.head(3).copy()
        print(f"📊 Analyzing first 3 rows in detail")
        return sample_df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return pd.DataFrame()

def analyze_basic_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze basic prediction columns (Year, Month, Period, etc.)."""
    
    print("\n" + "="*60)
    print("🔍 BASIC PREDICTION COLUMNS ANALYSIS")
    print("="*60)
    
    analysis = {}
    
    for idx, row in df.iterrows():
        print(f"\n📋 ROW {idx + 1} ANALYSIS:")
        print(f"   Year: {row['Year']} (Expected: 2025) ✅" if row['Year'] == 2025 else f"   Year: {row['Year']} ❌")
        print(f"   Month: {row['Month']} (Expected: 8 for August) ✅" if row['Month'] == 8 else f"   Month: {row['Month']} ❌")
        print(f"   Period: {row['Period']} (Expected: A for first half) ✅" if row['Period'] == 'A' else f"   Period: {row['Period']} ❌")
        print(f"   Store Group: {row['Store_Group_Name']}")
        print(f"   Target Style: {row['Target_Style_Tags']}")
        
        # Validate quantities
        current_qty = row['Current_SPU_Quantity']
        target_qty = row['Target_SPU_Quantity']
        print(f"   Current SPU Qty: {current_qty}")
        print(f"   Target SPU Qty: {target_qty}")
        print(f"   Change: {target_qty - current_qty:+.0f} SPUs")
        
        # Store analysis
        stores_count = row['Stores_In_Group_Selling_This_Category']
        print(f"   Stores in Group: {stores_count}")
        
        analysis[f'row_{idx+1}'] = {
            'year_valid': row['Year'] == 2025,
            'month_valid': row['Month'] == 8,
            'period_valid': row['Period'] == 'A',
            'qty_change': target_qty - current_qty,
            'stores_count': stores_count
        }
    
    return analysis

def analyze_financial_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze financial and sales columns."""
    
    print("\n" + "="*60)
    print("💰 FINANCIAL COLUMNS ANALYSIS")
    print("="*60)
    
    analysis = {}
    
    for idx, row in df.iterrows():
        print(f"\n💵 ROW {idx + 1} FINANCIAL METRICS:")
        
        total_sales = row['Total_Current_Sales']
        avg_sales_per_spu = row['Avg_Sales_Per_SPU']
        current_qty = row['Current_SPU_Quantity']
        
        print(f"   Total Current Sales: ¥{total_sales:,.2f}")
        print(f"   Avg Sales per SPU: ¥{avg_sales_per_spu:,.2f}")
        print(f"   Current SPU Quantity: {current_qty}")
        
        # Validation: Total Sales ≈ Avg Sales per SPU × Current Quantity
        calculated_total = avg_sales_per_spu * current_qty
        difference = abs(total_sales - calculated_total)
        tolerance = total_sales * 0.01  # 1% tolerance
        
        if difference <= tolerance:
            print(f"   ✅ Sales calculation valid: {total_sales:,.2f} ≈ {calculated_total:,.2f}")
        else:
            print(f"   ❌ Sales calculation error: {total_sales:,.2f} vs {calculated_total:,.2f} (diff: {difference:,.2f})")
        
        # Expected benefit analysis
        expected_benefit = row['Expected_Benefit']
        print(f"   Expected Benefit: {expected_benefit}")
        
        analysis[f'row_{idx+1}'] = {
            'total_sales': total_sales,
            'avg_sales_per_spu': avg_sales_per_spu,
            'sales_calculation_valid': difference <= tolerance,
            'sales_difference': difference
        }
    
    return analysis

def analyze_historical_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze historical comparison columns."""
    
    print("\n" + "="*60)
    print("📈 HISTORICAL ANALYSIS COLUMNS")
    print("="*60)
    
    analysis = {}
    
    for idx, row in df.iterrows():
        print(f"\n📊 ROW {idx + 1} HISTORICAL COMPARISON:")
        
        # Historical data
        historical_qty = row['Historical_SPU_Quantity_202407A']  # Note: Column name says 202407A but contains 202408A data
        spu_change = row['SPU_Change_vs_Historical']
        spu_change_pct = row['SPU_Change_vs_Historical_Pct']
        historical_stores = row['Historical_Store_Count_202407A']
        historical_sales = row['Historical_Total_Sales_202407A']
        
        print(f"   Historical SPU Qty: {historical_qty}")
        print(f"   SPU Change: {spu_change:+.1f}")
        print(f"   SPU Change %: {spu_change_pct:+.1f}%")
        print(f"   Historical Store Count: {historical_stores}")
        print(f"   Historical Total Sales: ¥{historical_sales:,.2f}")
        
        # Validation: SPU Change calculation
        target_qty = row['Target_SPU_Quantity']
        calculated_change = target_qty - historical_qty
        calculated_pct = (calculated_change / historical_qty * 100) if historical_qty > 0 else 0
        
        change_valid = abs(spu_change - calculated_change) < 0.1
        pct_valid = abs(spu_change_pct - calculated_pct) < 0.1
        
        print(f"   ✅ Change calculation: {spu_change} vs {calculated_change:.1f}" if change_valid else f"   ❌ Change calculation: {spu_change} vs {calculated_change:.1f}")
        print(f"   ✅ Percentage calculation: {spu_change_pct:.1f}% vs {calculated_pct:.1f}%" if pct_valid else f"   ❌ Percentage calculation: {spu_change_pct:.1f}% vs {calculated_pct:.1f}%")
        
        analysis[f'row_{idx+1}'] = {
            'historical_qty': historical_qty,
            'change_calculation_valid': change_valid,
            'percentage_calculation_valid': pct_valid,
            'historical_stores': historical_stores,
            'historical_sales': historical_sales
        }
    
    return analysis

def analyze_trend_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze cluster trend analysis columns."""
    
    print("\n" + "="*60)
    print("📊 CLUSTER TREND ANALYSIS COLUMNS")
    print("="*60)
    
    analysis = {}
    
    for idx, row in df.iterrows():
        print(f"\n🎯 ROW {idx + 1} TREND ANALYSIS:")
        
        # Main trend scores
        cluster_trend_score = row['cluster_trend_score']
        cluster_confidence = row['cluster_trend_confidence']
        stores_analyzed = row['stores_analyzed']
        
        print(f"   Cluster Trend Score: {cluster_trend_score}/100")
        print(f"   Cluster Confidence: {cluster_confidence}%")
        print(f"   Stores Analyzed: {stores_analyzed}")
        
        # Individual trend dimensions
        trend_dimensions = [
            'trend_sales_performance', 'trend_weather_impact', 'trend_cluster_performance',
            'trend_price_strategy', 'trend_category_performance', 'trend_regional_analysis',
            'trend_fashion_indicators', 'trend_seasonal_patterns', 'trend_inventory_turnover',
            'trend_customer_behavior'
        ]
        
        print(f"   Trend Dimension Scores:")
        dimension_scores = []
        for dim in trend_dimensions:
            score = row[dim]
            dimension_scores.append(score)
            print(f"     {dim.replace('trend_', '').replace('_', ' ').title()}: {score}/100")
        
        # Product category trends
        product_trend_score = row['product_category_trend_score']
        product_confidence = row['product_category_confidence']
        print(f"   Product Category Score: {product_trend_score}/100")
        print(f"   Product Category Confidence: {product_confidence}%")
        
        # Validate score ranges
        all_scores = dimension_scores + [cluster_trend_score, product_trend_score]
        all_confidences = [cluster_confidence, product_confidence]
        
        scores_valid = all(0 <= score <= 100 for score in all_scores)
        confidence_valid = all(0 <= conf <= 100 for conf in all_confidences)
        
        print(f"   ✅ All scores in valid range (0-100)" if scores_valid else f"   ❌ Some scores out of range")
        print(f"   ✅ All confidences in valid range (0-100)" if confidence_valid else f"   ❌ Some confidences out of range")
        
        analysis[f'row_{idx+1}'] = {
            'cluster_trend_score': cluster_trend_score,
            'scores_valid_range': scores_valid,
            'confidence_valid_range': confidence_valid,
            'avg_dimension_score': np.mean(dimension_scores),
            'stores_analyzed': stores_analyzed
        }
    
    return analysis

def analyze_sellthrough_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze sell-through rate columns."""
    
    print("\n" + "="*60)
    print("🔄 SELL-THROUGH ANALYSIS COLUMNS")
    print("="*60)
    
    analysis = {}
    
    for idx, row in df.iterrows():
        print(f"\n📈 ROW {idx + 1} SELL-THROUGH METRICS:")
        
        # Sell-through data
        spu_store_days_inventory = row['SPU_Store_Days_Inventory']
        spu_store_days_sales = row['SPU_Store_Days_Sales']
        sell_through_rate = row['Sell_Through_Rate']
        historical_daily_sales = row['Historical_Avg_Daily_SPUs_Sold_Per_Store']
        
        print(f"   SPU Store Days Inventory: {spu_store_days_inventory:,.1f}")
        print(f"   SPU Store Days Sales: {spu_store_days_sales:,.1f}")
        print(f"   Sell Through Rate: {sell_through_rate:.2f}%")
        print(f"   Historical Daily Sales per Store: {historical_daily_sales:.2f}")
        
        # Validation calculations
        target_qty = row['Target_SPU_Quantity']
        stores_count = row['Stores_In_Group_Selling_This_Category']
        days_in_period = 15  # First half of month
        
        # Expected inventory = Target SPU Qty × Stores × Days
        expected_inventory = target_qty * stores_count * days_in_period
        inventory_valid = abs(spu_store_days_inventory - expected_inventory) < 1.0
        
        # Expected sales = Historical Daily Sales × Stores × Days
        expected_sales = historical_daily_sales * stores_count * days_in_period
        sales_valid = abs(spu_store_days_sales - expected_sales) < 1.0
        
        # Expected sell-through = (Sales / Inventory) × 100
        expected_sellthrough = (spu_store_days_sales / spu_store_days_inventory * 100) if spu_store_days_inventory > 0 else 0
        sellthrough_valid = abs(sell_through_rate - expected_sellthrough) < 0.1
        
        print(f"   ✅ Inventory calculation: {spu_store_days_inventory:,.1f} vs {expected_inventory:,.1f}" if inventory_valid else f"   ❌ Inventory calculation: {spu_store_days_inventory:,.1f} vs {expected_inventory:,.1f}")
        print(f"   ✅ Sales calculation: {spu_store_days_sales:,.1f} vs {expected_sales:,.1f}" if sales_valid else f"   ❌ Sales calculation: {spu_store_days_sales:,.1f} vs {expected_sales:,.1f}")
        print(f"   ✅ Sell-through calculation: {sell_through_rate:.2f}% vs {expected_sellthrough:.2f}%" if sellthrough_valid else f"   ❌ Sell-through calculation: {sell_through_rate:.2f}% vs {expected_sellthrough:.2f}%")
        
        analysis[f'row_{idx+1}'] = {
            'inventory_calculation_valid': inventory_valid,
            'sales_calculation_valid': sales_valid,
            'sellthrough_calculation_valid': sellthrough_valid,
            'sell_through_rate': sell_through_rate,
            'historical_daily_sales': historical_daily_sales
        }
    
    return analysis

def analyze_rationale_column(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze the Enhanced_Rationale column."""
    
    print("\n" + "="*60)
    print("📝 ENHANCED RATIONALE ANALYSIS")
    print("="*60)
    
    analysis = {}
    
    for idx, row in df.iterrows():
        print(f"\n📋 ROW {idx + 1} RATIONALE STRUCTURE:")
        
        rationale = str(row['Enhanced_Rationale'])
        
        # Check for key components
        has_base_rationale = 'High-performing' in rationale or 'sub-category' in rationale
        has_historical = 'HISTORICAL:' in rationale
        has_cluster_trends = 'CLUSTER TRENDS:' in rationale
        has_trend_scores = 'Score:' in rationale and 'Confidence:' in rationale
        
        print(f"   ✅ Base business rationale present" if has_base_rationale else f"   ❌ Missing base rationale")
        print(f"   ✅ Historical analysis present" if has_historical else f"   ❌ Missing historical analysis")
        print(f"   ✅ Cluster trends present" if has_cluster_trends else f"   ❌ Missing cluster trends")
        print(f"   ✅ Trend scores present" if has_trend_scores else f"   ❌ Missing trend scores")
        
        # Check rationale length (should be comprehensive)
        rationale_length = len(rationale)
        length_appropriate = 500 <= rationale_length <= 3000
        
        print(f"   Rationale Length: {rationale_length} characters")
        print(f"   ✅ Appropriate length (500-3000 chars)" if length_appropriate else f"   ❌ Length issue (too short/long)")
        
        # Extract key metrics from rationale
        if 'baseline:' in rationale:
            print(f"   ✅ Historical baseline mentioned")
        if 'SPUs' in rationale and ('+' in rationale or '-' in rationale):
            print(f"   ✅ SPU change quantified")
        
        analysis[f'row_{idx+1}'] = {
            'has_base_rationale': has_base_rationale,
            'has_historical': has_historical,
            'has_cluster_trends': has_cluster_trends,
            'has_trend_scores': has_trend_scores,
            'length_appropriate': length_appropriate,
            'rationale_length': rationale_length
        }
    
    return analysis

def generate_summary_report(analyses: Dict[str, Dict]) -> None:
    """Generate a comprehensive summary report."""
    
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE SANITY CHECK SUMMARY REPORT")
    print("="*80)
    
    # Overall validation status
    total_checks = 0
    passed_checks = 0
    
    for analysis_type, analysis_data in analyses.items():
        print(f"\n🔍 {analysis_type.upper()} VALIDATION:")
        
        for row_key, row_data in analysis_data.items():
            if isinstance(row_data, dict):
                for check_name, check_result in row_data.items():
                    if isinstance(check_result, bool):
                        total_checks += 1
                        if check_result:
                            passed_checks += 1
                        status = "✅" if check_result else "❌"
                        print(f"   {status} {row_key} - {check_name}")
    
    # Calculate overall score
    if total_checks > 0:
        success_rate = (passed_checks / total_checks) * 100
        print(f"\n🎯 OVERALL VALIDATION SCORE: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        
        if success_rate >= 95:
            print("🎉 EXCELLENT: Data quality is outstanding!")
        elif success_rate >= 85:
            print("✅ GOOD: Data quality is acceptable with minor issues")
        elif success_rate >= 70:
            print("⚠️ FAIR: Data quality needs attention")
        else:
            print("❌ POOR: Significant data quality issues detected")
    
    print("\n" + "="*80)

def main():
    """Main execution function."""
    
    print("🔍 AUGUST 2025 PREDICTIONS - DETAILED SANITY CHECK")
    print("="*80)
    
    # Load sample data
    df = load_sample_data()
    if df.empty:
        return
    
    # Run all analyses
    analyses = {}
    analyses['basic_columns'] = analyze_basic_columns(df)
    analyses['financial_columns'] = analyze_financial_columns(df)
    analyses['historical_columns'] = analyze_historical_columns(df)
    analyses['trend_columns'] = analyze_trend_columns(df)
    analyses['sellthrough_columns'] = analyze_sellthrough_columns(df)
    analyses['rationale_column'] = analyze_rationale_column(df)
    
    # Generate summary report
    generate_summary_report(analyses)
    
    # Save detailed analysis to JSON
    with open('detailed_sanity_check_results.json', 'w') as f:
        json.dump(analyses, f, indent=2, default=str)
    
    print(f"\n📁 Detailed analysis saved to: detailed_sanity_check_results.json")
    print("🎯 Sanity check complete!")

if __name__ == "__main__":
    main() 