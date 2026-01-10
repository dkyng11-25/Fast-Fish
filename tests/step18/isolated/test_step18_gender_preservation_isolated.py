#!/usr/bin/env python3
"""
Standalone Isolated Test: Step 18 Gender Preservation
=====================================================

Tests that Step 18 preserves gender distribution from Step 14 output,
specifically ensuring neutral gender (中性) is not lost or transformed.

This test validates:
1. Gender mapping preserves Chinese values (男, 女, 中性)
2. Neutral gender is not treated as ambiguous
3. Gender distribution is maintained through enrichment
"""

import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def test_gender_preservation():
    """Test that Step 18 preserves gender distribution including neutral gender."""
    
    print("="*80)
    print("🧪 STEP 18 GENDER PRESERVATION TEST")
    print("="*80)
    print()
    
    # Create test data with known gender distribution
    test_data = pd.DataFrame({
        'Store_Group_Name': ['Store Group 1'] * 100,
        'Category': ['T恤'] * 100,
        'Subcategory': ['圆领T恤'] * 100,
        'Gender': ['女'] * 75 + ['男'] * 19 + ['中性'] * 6,  # 75% female, 19% male, 6% neutral
        'Season': ['夏'] * 100,
        'Location': ['前台'] * 100,
        'Group_ΔQty': [10] * 100,
        'Store_Codes_In_Group': ['11001,11002,11003'] * 100,
    })
    
    print("📊 Input Data:")
    print(f"   Total records: {len(test_data)}")
    gender_dist_before = test_data['Gender'].value_counts()
    for gender, count in gender_dist_before.items():
        pct = (count / len(test_data)) * 100
        print(f"   {gender}: {count} ({pct:.1f}%)")
    print()
    
    # Test the gender mapping logic directly
    print("🔍 Testing Gender Mapping Logic:")
    print("-"*80)
    
    # Current (buggy) mapping
    buggy_gender_map = {'男': 'Men', '女': 'Women', '中': 'Unisex'}
    buggy_amb_gender = {'Unisex', '中性', 'Unknown'}
    
    # Fixed mapping
    fixed_gender_map = {
        '男': '男',
        '女': '女',
        '中': '中性',
        '中性': '中性'
    }
    fixed_amb_gender = {'Unknown', ''}
    
    # Test buggy mapping
    print("\n1. Testing BUGGY mapping:")
    print(f"   gender_map = {buggy_gender_map}")
    print(f"   amb_gender = {buggy_amb_gender}")
    
    buggy_results = test_data.copy()
    
    # Simulate the buggy logic
    def is_ambiguous_buggy(val):
        if pd.isna(val):
            return True
        v = str(val).strip()
        return v == '' or v in buggy_amb_gender
    
    ambiguous_count = buggy_results['Gender'].apply(is_ambiguous_buggy).sum()
    print(f"   ❌ Records marked as ambiguous: {ambiguous_count}")
    print(f"   ❌ This includes ALL '中性' values!")
    
    # Count neutral gender that would be lost
    neutral_before = (test_data['Gender'] == '中性').sum()
    print(f"   ❌ Neutral gender records at risk: {neutral_before}")
    print()
    
    # Test fixed mapping
    print("2. Testing FIXED mapping:")
    print(f"   gender_map = {fixed_gender_map}")
    print(f"   amb_gender = {fixed_amb_gender}")
    
    fixed_results = test_data.copy()
    
    # Simulate the fixed logic
    def is_ambiguous_fixed(val):
        if pd.isna(val):
            return True
        v = str(val).strip()
        return v == '' or v in fixed_amb_gender
    
    ambiguous_count = fixed_results['Gender'].apply(is_ambiguous_fixed).sum()
    print(f"   ✅ Records marked as ambiguous: {ambiguous_count}")
    print(f"   ✅ '中性' is NOT ambiguous!")
    
    # Apply the fixed mapping
    fixed_results['Gender'] = fixed_results['Gender'].map(
        lambda x: fixed_gender_map.get(x, x) if pd.notna(x) else x
    )
    
    neutral_after = (fixed_results['Gender'] == '中性').sum()
    print(f"   ✅ Neutral gender preserved: {neutral_after}")
    print()
    
    # Validate distribution preservation
    print("="*80)
    print("📊 VALIDATION RESULTS")
    print("="*80)
    print()
    
    gender_dist_after = fixed_results['Gender'].value_counts()
    
    print("Gender Distribution Comparison:")
    print(f"{'Gender':<10} {'Before':<15} {'After':<15} {'Status'}")
    print("-"*60)
    
    all_passed = True
    
    for gender in ['女', '男', '中性']:
        count_before = (test_data['Gender'] == gender).sum()
        count_after = (fixed_results['Gender'] == gender).sum()
        pct_before = (count_before / len(test_data)) * 100
        pct_after = (count_after / len(fixed_results)) * 100
        
        if count_before == count_after:
            status = "✅ PRESERVED"
        else:
            status = f"❌ CHANGED ({count_before} → {count_after})"
            all_passed = False
        
        print(f"{gender:<10} {count_before:>3} ({pct_before:>5.1f}%) {count_after:>3} ({pct_after:>5.1f}%)  {status}")
    
    print()
    print("="*80)
    
    if all_passed:
        print("✅ TEST PASSED: Gender distribution preserved with fixed mapping!")
        print()
        print("The fixed mapping correctly:")
        print("  • Preserves Chinese gender values (男, 女, 中性)")
        print("  • Does not treat neutral (中性) as ambiguous")
        print("  • Maintains exact gender distribution")
        return True
    else:
        print("❌ TEST FAILED: Gender distribution not preserved")
        return False


def test_gender_mapping_edge_cases():
    """Test edge cases in gender mapping."""
    
    print("="*80)
    print("🧪 GENDER MAPPING EDGE CASES TEST")
    print("="*80)
    print()
    
    # Test various gender values
    test_cases = [
        ('男', '男', 'Standard male'),
        ('女', '女', 'Standard female'),
        ('中性', '中性', 'Full neutral form'),
        ('中', '中性', 'Short neutral form'),
        ('', '', 'Empty string'),
        (None, None, 'None value'),
        ('Unknown', 'Unknown', 'Unknown value'),
    ]
    
    fixed_gender_map = {
        '男': '男',
        '女': '女',
        '中': '中性',
        '中性': '中性'
    }
    
    print("Testing gender mapping edge cases:")
    print(f"{'Input':<15} {'Expected':<15} {'Description':<30} {'Status'}")
    print("-"*80)
    
    all_passed = True
    
    for input_val, expected, description in test_cases:
        if pd.isna(input_val):
            result = None
        else:
            result = fixed_gender_map.get(input_val, input_val)
        
        if result == expected or (pd.isna(result) and pd.isna(expected)):
            status = "✅ PASS"
        else:
            status = f"❌ FAIL (got {result})"
            all_passed = False
        
        input_str = str(input_val) if input_val is not None else 'None'
        expected_str = str(expected) if expected is not None else 'None'
        print(f"{input_str:<15} {expected_str:<15} {description:<30} {status}")
    
    print()
    print("="*80)
    
    if all_passed:
        print("✅ ALL EDGE CASES PASSED")
        return True
    else:
        print("❌ SOME EDGE CASES FAILED")
        return False


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "STEP 18 GENDER PRESERVATION TEST SUITE" + " "*20 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    # Run tests
    test1_passed = test_gender_preservation()
    print()
    test2_passed = test_gender_mapping_edge_cases()
    
    # Summary
    print()
    print("="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    print()
    
    if test1_passed and test2_passed:
        print("✅ ALL TESTS PASSED")
        print()
        print("The fixed gender mapping logic correctly:")
        print("  1. Preserves neutral gender (中性)")
        print("  2. Maintains gender distribution")
        print("  3. Handles edge cases properly")
        print()
        print("Ready to apply fix to src/step18_validate_results.py")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Issues found:")
        if not test1_passed:
            print("  • Gender distribution not preserved")
        if not test2_passed:
            print("  • Edge cases not handled correctly")
        sys.exit(1)
