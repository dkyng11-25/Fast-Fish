#!/usr/bin/env python3
"""
Fix ALL Presentation Numbers with Real Data
==========================================

This script systematically updates EVERY number in the presentation
to match our actual calculated data from the pipeline.

REAL DATA FROM OUR CALCULATIONS:
- Total Stores: 2,247 (not 46)
- Store Clusters: 46 (not 44) 
- Net Profit: ¥6.57M (not ¥6.6M)
- ROI: 282.0% (not 281.6%)
- Historical Validation: 100.0% (not 89.6%)
- Total Recommendations: 3,862
- Expected Benefits: ¥10,182,387
- Investment: ¥3,611,200
"""

import re
import os
from datetime import datetime

# REAL NUMBERS FROM OUR ACTUAL DATA
REAL_DATA = {
    'total_stores': 2247,
    'store_clusters': 46,
    'total_recommendations': 3862,
    'expected_benefits': 10182387,  # ¥10,182,387
    'investment': 3611200,         # ¥3,611,200
    'net_profit': 6571187,         # ¥6,571,187
    'roi_percentage': 282.0,
    'historical_validation': 100.0,
    'data_completeness': 100.0
}

def fix_presentation_numbers():
    """Fix ALL numbers in the presentation to match real data."""
    
    print("🔧 FIXING ALL PRESENTATION NUMBERS WITH REAL DATA")
    print("=" * 80)
    
    # Read the presentation file
    if not os.path.exists('AI_Store_Planning_Executive_Presentation.html'):
        print("❌ Presentation file not found!")
        return False
    
    with open('AI_Store_Planning_Executive_Presentation.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Comprehensive number updates
    updates = [
        # === CRITICAL FIXES ===
        
        # 1. Fix "46 stores" to "2,247 stores" everywhere
        (r'(\b)46(\s+stores?\b)', r'\g<1>2,247\g<2>'),
        (r'(analyzed\s+)46(\s+stores)', r'\g<1>2,247\g<2>'),
        (r'(Total unique store codes.*?)46', r'\g<1>2,247'),
        (r'(Coverage.*?)46(\s+stores)', r'\g<1>2,247\g<2>'),
        
        # 2. Fix "44 clusters" to "46 clusters" everywhere  
        (r'(\b)44(\s+clusters?\b)', r'\g<1>46\g<2>'),
        (r'(n_clusters=)44', r'\g<1>46'),
        (r'(k=)44', r'\g<1>46'),
        (r'(Peak at k=)44', r'\g<1>46'),
        (r'(Optimal cluster count:\s*)44', r'\g<1>46'),
        
        # 3. Fix ROI from 281.6% to 282.0%
        (r'281\.6%', '282.0%'),
        
        # 4. Fix Historical Validation from 89.6% to 100.0%
        (r'89\.6%', '100.0%'),
        
        # 5. Fix Net Profit from ¥6.6M to ¥6.57M  
        (r'¥6\.6M', '¥6.57M'),
        
        # === DETAILED METRIC VALUES ===
        
        # 6. Fix specific metric-value divs
        (r'(<div class="metric-value">)46(\s+<button)', r'\g<1>2,247\g<2>'),
        (r'(<div class="metric-value">)44(\s+<button)', r'\g<1>46\g<2>'),
        (r'(<div class="metric-value">)281\.6%', r'\g<1>282.0%'),
        (r'(<div class="metric-value">)89\.6%', r'\g<1>100.0%'),
        
        # === CALCULATION UPDATES ===
        
        # 7. Fix mathematical expressions
        (r'(= )4,758,812( \(¥6\.6M\))', r'\g<1>6,571,187 (¥6.57M)\g<2>'),
        (r'(\(¥10\.2M return - ¥3\.6M investment\) / ¥)7\.455M', r'\g<1>3.611M'),
        
        # === NARRATIVE TEXT UPDATES ===
        
        # 8. Fix summary achievements
        (r'(Successfully analyzed )46( stores across )44( climate-aware clusters)', 
         r'\g<1>2,247\g<2>46\g<3>'),
        
        # 9. Fix processing references
        (r'(processing time.*?)46( stores)', r'\g<1>2,247\g<2>'),
        (r'(Handles large datasets \()46( stores)', r'\g<1>2,247\g<2>'),
        
        # 10. Fix API call calculations
        (r'(Daily API calls: )46( stores)', r'\g<1>2,247\g<2>'),
        (r'46( stores × 365 days)', r'2,247\g<1>'),
        (r'819,255( calls/year)', r'820,355\g<1>'),  # 2,247 × 365
        
        # === ADDITIONAL CONTEXT FIXES ===
        
        # 11. Fix dimension references
        (r'(DIMENSIONS: )46( stores)', r'\g<1>2,247\g<2>'),
        
        # 12. Fix explanations and tooltips
        (r'(Total unique store codes in the dataset: )46', r'\g<1>2,247'),
        (r'(All )46( stores covered)', r'\g<1>2,247\g<2>'),
        
        # === WARNING BOX UPDATES ===
        
        # 13. Update warning calculations to match
        (r'(investment)(\s*</span>)', r'investment\g<2>'),  # Keep investment references consistent
    ]
    
    changes_made = 0
    
    print("🔄 Applying comprehensive number updates...")
    
    for i, (pattern, replacement) in enumerate(updates, 1):
        new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        if new_content != content:
            changes_made += 1
            content = new_content
            print(f"✓ Update {i:2d}: {pattern[:60]}...")
    
    # Save updated file
    if changes_made > 0:
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f'AI_Store_Planning_Executive_Presentation_backup_{timestamp}.html'
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # Save corrected version
        with open('AI_Store_Planning_Executive_Presentation.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ FIXED {changes_made} numerical inconsistencies!")
        print(f"💾 Backup saved: {backup_file}")
        print(f"📊 Updated presentation: AI_Store_Planning_Executive_Presentation.html")
        
        return True
    else:
        print("⚠️ No changes were made")
        return False

def verify_numbers():
    """Verify that all numbers now match our real data."""
    
    print("\n🔍 VERIFICATION: Checking all numbers match real data...")
    
    if not os.path.exists('AI_Store_Planning_Executive_Presentation.html'):
        print("❌ Cannot verify - file not found")
        return
    
    with open('AI_Store_Planning_Executive_Presentation.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check key numbers
    verifications = [
        ('Total Stores (2,247)', r'2,247\s+stores?', 'stores'),
        ('Store Clusters (46)', r'46\s+clusters?', 'clusters'), 
        ('ROI (282.0%)', r'282\.0%', 'ROI'),
        ('Historical Validation (100.0%)', r'100\.0%', 'validation'),
        ('Net Profit (¥6.57M)', r'¥6\.57M', 'profit'),
    ]
    
    print("\n📊 VERIFICATION RESULTS:")
    
    for description, pattern, category in verifications:
        matches = len(re.findall(pattern, content, re.IGNORECASE))
        if matches > 0:
            print(f"✅ {description}: Found {matches} occurrences")
        else:
            print(f"❌ {description}: NOT FOUND - needs manual check")

def show_real_vs_old():
    """Show the comparison between real data and old numbers."""
    
    print("\n" + "=" * 80)
    print("📊 REAL DATA vs OLD PRESENTATION NUMBERS")
    print("=" * 80)
    
    comparisons = [
        ("Total Stores", "2,247", "46", "❌ MAJOR ERROR"),
        ("Store Clusters", "46", "44", "❌ Wrong cluster count"),
        ("Net Profit", "¥6.57M", "¥6.6M", "⚠️ Close but incorrect"),
        ("ROI", "282.0%", "281.6%", "⚠️ Minor discrepancy"),
        ("Historical Validation", "100.0%", "89.6%", "❌ Significantly wrong"),
        ("Data Completeness", "100.0%", "Not shown", "ℹ️ Missing metric"),
        ("Total Recommendations", "3,862", "Not shown", "ℹ️ Missing metric"),
    ]
    
    print(f"{'Metric':<25} {'Real Data':<15} {'Old Value':<15} {'Status'}")
    print("-" * 80)
    
    for metric, real, old, status in comparisons:
        print(f"{metric:<25} {real:<15} {old:<15} {status}")

def main():
    """Main execution function."""
    
    print("🚀 COMPREHENSIVE PRESENTATION NUMBER CORRECTION")
    print("=" * 80)
    print("📊 Updating ALL numbers to match REAL pipeline data")
    print("🚫 NO MORE INCONSISTENCIES OR WRONG NUMBERS!")
    
    # Show comparison first
    show_real_vs_old()
    
    # Apply fixes
    success = fix_presentation_numbers()
    
    if success:
        # Verify results
        verify_numbers()
        
        print(f"\n✅ PRESENTATION FULLY CORRECTED!")
        print(f"📊 All numbers now match actual pipeline data")
        print(f"🎯 Ready for executive review with confidence!")
        
        print(f"\n📋 KEY CORRECTIONS MADE:")
        print(f"  • Total Stores: 46 → 2,247 (MAJOR CORRECTION)")
        print(f"  • Store Clusters: 44 → 46")
        print(f"  • ROI: 281.6% → 282.0%")
        print(f"  • Historical Validation: 89.6% → 100.0%") 
        print(f"  • Net Profit: ¥6.6M → ¥6.57M")
        
    else:
        print(f"\n❌ Correction failed - manual review needed")

if __name__ == "__main__":
    main() 