#!/usr/bin/env python3
"""
Top 10 Offenders Study - Detailed Analysis with Postulates vs Evidence Matrix
Investigates the root causes behind the most extreme outlier cases.
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Tuple, Any
from collections import defaultdict

def analyze_top_10_offenders() -> None:
    """Analyze top 10 outlier cases with postulates and evidence validation."""
    
    print("🔍 TOP 10 OFFENDERS DETAILED STUDY")
    print("=" * 80)
    
    # Load datasets
    main_df = pd.read_csv('output/all_rule_suggestions.csv')
    rule10_df = pd.read_csv('output/rule10_spu_overcapacity_opportunities.csv')
    
    # Load source data files
    source_files = []
    api_data_dir = 'data/api_data'
    if os.path.exists(api_data_dir):
        for file in os.listdir(api_data_dir):
            if file.endswith('.csv'):
                source_files.append(os.path.join(api_data_dir, file))
    
    # Get top 10 massive outliers
    top_10 = main_df[main_df['current_quantity'] > 1000].nlargest(10, 'current_quantity')
    
    print(f"✅ Loaded {len(main_df):,} total suggestions")
    print(f"✅ Loaded {len(rule10_df):,} Rule 10 detailed records")
    print(f"✅ Found {len(source_files)} source data files")
    print(f"✅ Analyzing top 10 offenders")
    
    # Define postulates for investigation
    postulates = {
        'P1_AGGREGATION_EFFECT': {
            'description': 'High quantities result from aggregating multiple gender/location variants',
            'indicators': ['Multiple gender records', 'Multiple location records', 'Sum matches total'],
            'test_method': 'count_variants_and_sum'
        },
        'P2_HIGH_SALES_VOLUME': {
            'description': 'Store genuinely has very high sales requiring large inventory',
            'indicators': ['High sales amounts in source', 'Consistent across periods', 'Regional leader'],
            'test_method': 'analyze_sales_patterns'
        },
        'P3_DATA_QUALITY_ISSUE': {
            'description': 'Source data contains erroneous sales amounts or quantities',
            'indicators': ['Unrealistic sales amounts', 'Inconsistent with store size', 'Outlier in region'],
            'test_method': 'validate_data_quality'
        },
        'P4_STORE_CHARACTERISTICS': {
            'description': 'Store has unique characteristics (flagship, warehouse, etc.)',
            'indicators': ['Large store format', 'Regional hub', 'Special designation'],
            'test_method': 'analyze_store_profile'
        },
        'P5_SEASONAL_ACCUMULATION': {
            'description': 'Quantities represent seasonal accumulation or clearance needs',
            'indicators': ['Seasonal item patterns', 'End-of-season timing', 'Clearance indicators'],
            'test_method': 'check_seasonal_patterns'
        },
        'P6_CALCULATION_ERROR': {
            'description': 'Unit price calculation or quantity conversion error in pipeline',
            'indicators': ['Unrealistic unit prices', 'Conversion artifacts', 'Mathematical inconsistencies'],
            'test_method': 'validate_calculations'
        }
    }
    
    # Analysis results storage
    case_analysis = []
    postulate_matrix = defaultdict(list)
    
    print(f"\n📊 ANALYZING EACH OFFENDER")
    print("-" * 80)
    
    for idx, (_, case) in enumerate(top_10.iterrows()):
        store_code = case['store_code']
        spu_code = case['spu_code']
        quantity = case['current_quantity']
        unit_price = case['unit_price']
        
        print(f"\n🔍 CASE {idx+1}: Store {store_code} - {quantity:.1f} units")
        print(f"   SPU: {spu_code}")
        print(f"   Unit Price: ${unit_price:.2f}")
        print(f"   Total Value: ${quantity * unit_price:,.0f}")
        
        # Initialize case analysis
        case_data = {
            'case_id': f"Case_{idx+1}",
            'store_code': store_code,
            'spu_code': spu_code,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_value': quantity * unit_price,
            'postulate_results': {},
            'evidence_summary': {},
            'conclusion': ''
        }
        
        # Test each postulate
        for postulate_id, postulate_info in postulates.items():
            print(f"   Testing {postulate_id}: {postulate_info['description']}")
            
            # Execute test based on method
            test_method = postulate_info['test_method']
            evidence = execute_postulate_test(
                test_method, case, rule10_df, source_files, postulate_info
            )
            
            case_data['postulate_results'][postulate_id] = evidence
            postulate_matrix[postulate_id].append({
                'case_id': case_data['case_id'],
                'store_code': store_code,
                'evidence_score': evidence['score'],
                'key_findings': evidence['key_findings']
            })
            
            print(f"     Score: {evidence['score']}/10 - {evidence['conclusion']}")
        
        # Determine most likely cause
        best_postulate = max(
            case_data['postulate_results'].items(),
            key=lambda x: x[1]['score']
        )
        
        case_data['conclusion'] = f"Most likely: {best_postulate[0]} (Score: {best_postulate[1]['score']}/10)"
        case_analysis.append(case_data)
        
        print(f"   🎯 CONCLUSION: {case_data['conclusion']}")
    
    # Generate comprehensive report
    generate_postulate_matrix_report(case_analysis, postulate_matrix, postulates)
    
    # Save detailed results
    save_case_analysis_results(case_analysis, postulate_matrix)

def execute_postulate_test(test_method: str, case: pd.Series, rule10_df: pd.DataFrame, 
                          source_files: List[str], postulate_info: Dict) -> Dict:
    """Execute specific test for a postulate."""
    
    store_code = case['store_code']
    spu_pattern = case['spu_code'].split('_')[1] if '_' in case['spu_code'] else 'Unknown'
    quantity = case['current_quantity']
    
    if test_method == 'count_variants_and_sum':
        return test_aggregation_effect(store_code, spu_pattern, quantity, rule10_df)
    elif test_method == 'analyze_sales_patterns':
        return test_high_sales_volume(store_code, spu_pattern, source_files)
    elif test_method == 'validate_data_quality':
        return test_data_quality_issues(store_code, spu_pattern, quantity, source_files)
    elif test_method == 'analyze_store_profile':
        return test_store_characteristics(store_code, rule10_df)
    elif test_method == 'check_seasonal_patterns':
        return test_seasonal_accumulation(store_code, spu_pattern, source_files)
    elif test_method == 'validate_calculations':
        return test_calculation_errors(case, rule10_df)
    else:
        return {'score': 0, 'conclusion': 'Test not implemented', 'key_findings': [], 'evidence': {}}

def test_aggregation_effect(store_code: str, spu_pattern: str, total_quantity: float, 
                           rule10_df: pd.DataFrame) -> Dict:
    """Test if high quantity results from aggregating multiple variants."""
    
    # Find all Rule 10 records for this store-SPU
    records = rule10_df[
        (rule10_df['str_code'].astype(str) == str(store_code)) & 
        (rule10_df['sub_cate_name'] == spu_pattern)
    ]
    
    if len(records) == 0:
        return {'score': 0, 'conclusion': 'No detailed records found', 'key_findings': [], 'evidence': {}}
    
    # Analyze variants
    gender_variants = records['sex_name'].nunique()
    location_variants = records['display_location_name'].nunique()
    total_variants = len(records)
    
    # Calculate sum of individual quantities
    quantity_sum = records['current_quantity'].sum()
    quantity_match = abs(quantity_sum - total_quantity) < 1.0
    
    # Score based on evidence
    score = 0
    key_findings = []
    
    if total_variants > 1:
        score += 3
        key_findings.append(f"Multiple variants: {total_variants} records")
    
    if gender_variants > 1:
        score += 2
        key_findings.append(f"Multiple genders: {list(records['sex_name'].unique())}")
    
    if location_variants > 1:
        score += 2
        key_findings.append(f"Multiple locations: {list(records['display_location_name'].unique())}")
    
    if quantity_match:
        score += 3
        key_findings.append(f"Quantities sum correctly: {quantity_sum:.1f} ≈ {total_quantity:.1f}")
    else:
        key_findings.append(f"Quantity mismatch: {quantity_sum:.1f} vs {total_quantity:.1f}")
    
    conclusion = "Strong evidence" if score >= 7 else "Moderate evidence" if score >= 4 else "Weak evidence"
    
    return {
        'score': score,
        'conclusion': conclusion,
        'key_findings': key_findings,
        'evidence': {
            'total_variants': total_variants,
            'gender_variants': gender_variants,
            'location_variants': location_variants,
            'quantity_sum': quantity_sum,
            'quantity_match': quantity_match
        }
    }

def test_high_sales_volume(store_code: str, spu_pattern: str, source_files: List[str]) -> Dict:
    """Test if store has genuinely high sales volume."""
    
    key_findings = []
    evidence = {}
    score = 0
    
    # Look for sales data in source files
    total_sales_found = 0
    sales_records = 0
    
    for source_file in source_files:
        try:
            if os.path.exists(source_file):
                df = pd.read_csv(source_file)
                
                # Look for this store's records
                store_records = df[df['str_code'].astype(str) == str(store_code)]
                
                if len(store_records) > 0:
                    sales_records += len(store_records)
                    
                    # Check for high sales amounts
                    if 'spu_sales_amt' in df.columns:
                        store_sales = store_records['spu_sales_amt'].sum()
                        total_sales_found += store_sales
                        
                        # Check if this SPU pattern has high sales
                        spu_records = store_records[
                            store_records['sub_cate_name'] == spu_pattern
                        ] if 'sub_cate_name' in store_records.columns else pd.DataFrame()
                        
                        if len(spu_records) > 0:
                            spu_sales = spu_records['spu_sales_amt'].sum()
                            if spu_sales > 10000:
                                score += 3
                                key_findings.append(f"High SPU sales: ${spu_sales:,.0f}")
        
        except Exception as e:
            continue
    
    # Score based on sales evidence
    if total_sales_found > 50000:
        score += 2
        key_findings.append(f"Very high total sales: ${total_sales_found:,.0f}")
    elif total_sales_found > 20000:
        score += 1
        key_findings.append(f"High total sales: ${total_sales_found:,.0f}")
    
    if sales_records > 10:
        score += 1
        key_findings.append(f"Many sales records: {sales_records}")
    
    if not key_findings:
        key_findings.append("No significant sales data found")
    
    conclusion = "Strong evidence" if score >= 6 else "Moderate evidence" if score >= 3 else "Weak evidence"
    
    evidence = {
        'total_sales_found': total_sales_found,
        'sales_records_count': sales_records,
        'files_checked': len(source_files)
    }
    
    return {
        'score': score,
        'conclusion': conclusion,
        'key_findings': key_findings,
        'evidence': evidence
    }

def test_data_quality_issues(store_code: str, spu_pattern: str, quantity: float, 
                            source_files: List[str]) -> Dict:
    """Test for data quality issues in source data."""
    
    key_findings = []
    evidence = {}
    score = 0
    
    # Look for suspicious patterns in source data
    suspicious_amounts = []
    
    for source_file in source_files:
        try:
            if os.path.exists(source_file):
                df = pd.read_csv(source_file)
                
                # Look for this store's records
                store_records = df[df['str_code'].astype(str) == str(store_code)]
                
                if len(store_records) > 0 and 'spu_sales_amt' in df.columns:
                    sales_amounts = store_records['spu_sales_amt'].values
                    
                    for amount in sales_amounts:
                        # Check if sales amount suspiciously close to our quantity
                        if abs(amount - quantity) < 10:
                            score += 4
                            key_findings.append(f"Sales amount {amount} ≈ quantity {quantity}")
                            suspicious_amounts.append(amount)
                        
                        # Check for decimal patterns
                        if amount > 1000 and str(amount).count('.') == 1:
                            decimal_part = str(amount).split('.')[1]
                            if len(decimal_part) == 1:
                                score += 2
                                key_findings.append(f"Suspicious decimal: {amount}")
        
        except Exception as e:
            continue
    
    # Check for unrealistic quantity for item type
    if spu_pattern == '休闲圆领T恤' and quantity > 1500:
        score += 2
        key_findings.append(f"Unrealistic T-shirt quantity: {quantity}")
    
    if not key_findings:
        key_findings.append("No obvious data quality issues")
    
    conclusion = "Strong evidence" if score >= 6 else "Moderate evidence" if score >= 3 else "Weak evidence"
    
    evidence = {
        'suspicious_amounts': suspicious_amounts,
        'files_checked': len(source_files)
    }
    
    return {
        'score': score,
        'conclusion': conclusion,
        'key_findings': key_findings,
        'evidence': evidence
    }

def test_store_characteristics(store_code: str, rule10_df: pd.DataFrame) -> Dict:
    """Test if store has special characteristics."""
    
    store_records = rule10_df[rule10_df['str_code'].astype(str) == str(store_code)]
    
    key_findings = []
    evidence = {}
    score = 0
    
    if len(store_records) > 0:
        unique_spus = store_records['sub_cate_name'].nunique()
        total_records = len(store_records)
        avg_quantity = store_records['current_quantity'].mean()
        
        if unique_spus > 20:
            score += 2
            key_findings.append(f"High SPU diversity: {unique_spus} types")
        
        if total_records > 50:
            score += 2
            key_findings.append(f"High activity: {total_records} records")
        
        if avg_quantity > 300:
            score += 1
            key_findings.append(f"High avg quantity: {avg_quantity:.1f}")
        
        evidence = {
            'unique_spus': unique_spus,
            'total_records': total_records,
            'avg_quantity': avg_quantity
        }
    else:
        key_findings.append("No store records found")
    
    conclusion = "Strong evidence" if score >= 5 else "Moderate evidence" if score >= 3 else "Weak evidence"
    
    return {
        'score': score,
        'conclusion': conclusion,
        'key_findings': key_findings,
        'evidence': evidence
    }

def test_seasonal_accumulation(store_code: str, spu_pattern: str, source_files: List[str]) -> Dict:
    """Test for seasonal patterns."""
    
    key_findings = []
    score = 0
    
    if spu_pattern == '休闲圆领T恤':
        score += 2
        key_findings.append("T-shirts are seasonal items")
    
    for source_file in source_files:
        if 'A.csv' in source_file:
            score += 1
            key_findings.append("Data from period A (seasonal)")
            break
    
    if not key_findings:
        key_findings.append("No seasonal indicators")
    
    conclusion = "Moderate evidence" if score >= 2 else "Weak evidence"
    
    return {
        'score': score,
        'conclusion': conclusion,
        'key_findings': key_findings,
        'evidence': {'item_type': spu_pattern}
    }

def test_calculation_errors(case: pd.Series, rule10_df: pd.DataFrame) -> Dict:
    """Test for calculation errors."""
    
    unit_price = case['unit_price']
    quantity = case['current_quantity']
    
    key_findings = []
    score = 0
    
    if unit_price == 20.00:
        score += 2
        key_findings.append("Unit price exactly $20.00 (calculated?)")
    
    if 1000 < quantity < 3000 and quantity % 100 < 10:
        score += 3
        key_findings.append(f"Quantity resembles currency: {quantity}")
    
    if not key_findings:
        key_findings.append("No calculation errors detected")
    
    conclusion = "Strong evidence" if score >= 5 else "Moderate evidence" if score >= 3 else "Weak evidence"
    
    return {
        'score': score,
        'conclusion': conclusion,
        'key_findings': key_findings,
        'evidence': {'unit_price': unit_price, 'quantity': quantity}
    }

def generate_postulate_matrix_report(case_analysis: List[Dict], postulate_matrix: Dict, 
                                   postulates: Dict) -> None:
    """Generate postulate vs case matrix report."""
    
    print(f"\n" + "=" * 100)
    print(f"📊 POSTULATE VS CASE MATRIX ANALYSIS")
    print("=" * 100)
    
    # Create matrix table
    print(f"\n{'Case':<8} {'Store':<8} {'P1':<4} {'P2':<4} {'P3':<4} {'P4':<4} {'P5':<4} {'P6':<4} {'Top Postulate':<25}")
    print("-" * 95)
    
    for case in case_analysis:
        case_id = case['case_id']
        store_code = case['store_code']
        
        scores = []
        for p_id in ['P1_AGGREGATION_EFFECT', 'P2_HIGH_SALES_VOLUME', 'P3_DATA_QUALITY_ISSUE', 
                    'P4_STORE_CHARACTERISTICS', 'P5_SEASONAL_ACCUMULATION', 'P6_CALCULATION_ERROR']:
            score = case['postulate_results'][p_id]['score']
            scores.append(f"{score:2d}")
        
        best_postulate = max(case['postulate_results'].items(), key=lambda x: x[1]['score'])
        top_p = best_postulate[0].split('_')[0] + f"({best_postulate[1]['score']})"
        
        print(f"{case_id:<8} {store_code:<8} {' '.join(scores)} {top_p:<25}")

def save_case_analysis_results(case_analysis: List[Dict], postulate_matrix: Dict) -> None:
    """Save analysis results."""
    
    print(f"\n💾 Saving results...")
    
    # Save case analysis
    case_df_data = []
    for case in case_analysis:
        row = {
            'case_id': case['case_id'],
            'store_code': case['store_code'],
            'spu_code': case['spu_code'],
            'quantity': case['quantity'],
            'unit_price': case['unit_price'],
            'total_value': case['total_value'],
            'conclusion': case['conclusion']
        }
        
        for p_id, result in case['postulate_results'].items():
            row[f"{p_id}_score"] = result['score']
            row[f"{p_id}_conclusion"] = result['conclusion']
        
        case_df_data.append(row)
    
    case_df = pd.DataFrame(case_df_data)
    case_df.to_csv('output/top_10_offenders_analysis.csv', index=False)
    print(f"   ✅ Case analysis saved")

def main():
    """Run the study."""
    analyze_top_10_offenders()
    print("\n✅ Study complete!")

if __name__ == "__main__":
    main() 