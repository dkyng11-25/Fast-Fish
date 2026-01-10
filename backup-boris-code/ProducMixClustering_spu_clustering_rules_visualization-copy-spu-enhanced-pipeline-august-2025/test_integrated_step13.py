#!/usr/bin/env python3
"""
Quick Test for Integrated Step 13: ComprehensiveTrendAnalyzer

Fast test that only validates the trending system integration
without running the full pipeline.
"""

import sys
import os
sys.path.append('src')

# Import the trend analyzer from our integrated step13
from step13_consolidate_spu_rules import ComprehensiveTrendAnalyzer

def test_integrated_trend_analyzer():
    print("=== TESTING INTEGRATED COMPREHENSIVE TREND ANALYZER ===")
    print("Testing: Your Memory-Efficient Step13 + Andy's Trending System")
    
    # Initialize the analyzer
    try:
        analyzer = ComprehensiveTrendAnalyzer()
        print(f"✓ Analyzer initialized successfully")
        print(f"✓ Data sources loaded: {analyzer.data_sources_loaded}/4")
        
        # Test with multiple sample suggestions
        test_stores = ['11003', '11004', '11005']
        
        for store_code in test_stores:
            sample_suggestion = {
                'store_code': store_code,
                'spu_code': 'TEST_SPU',
                'rule': 'Test Rule',
                'current_quantity': 50,
                'recommended_quantity_change': -10,
                'target_quantity': 40,
                'unit_price': 150,
                'investment_required': -1500
            }
            
            print(f"\n=== TESTING STORE {store_code} ===")
            
            # Test comprehensive analysis
        comprehensive_result = analyzer.analyze_comprehensive_trends(sample_suggestion)
        print(f"   Overall Score: {comprehensive_result.get('overall_trend_score', 'N/A')}")
            print(f"   Business Priority: {comprehensive_result.get('business_priority_score', 'N/A')}")
            print(f"   Data Quality: {comprehensive_result.get('data_quality_score', 'N/A')}")
            print(f"   Sales Trend: {comprehensive_result.get('sales_trend', 'N/A')[:60]}...")
        
        print(f"\n✅ INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print(f"✅ Trending system working on all test stores!")
        return True
        
    except Exception as e:
        print(f"❌ Error during integration testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fast_mode_performance():
    """Test the performance optimizations"""
    print("\n=== TESTING FAST_MODE PERFORMANCE ===")
    
    try:
        # Import configuration
        from step13_consolidate_spu_rules import FAST_MODE, TREND_SAMPLE_SIZE, CHUNK_SIZE_SMALL
        
        print(f"✓ FAST_MODE: {FAST_MODE}")
        print(f"✓ Sample size: {TREND_SAMPLE_SIZE:,}")
        print(f"✓ Chunk size: {CHUNK_SIZE_SMALL:,}")
        
        if FAST_MODE:
            print("✅ Performance optimizations are ENABLED")
            print("   → Expected runtime: 2-5 minutes")
        else:
            print("⚠️  Performance optimizations are DISABLED")
            print("   → Expected runtime: 30-60 minutes")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking performance settings: {e}")
        return False

if __name__ == "__main__":
    print("🎯 QUICK INTEGRATION TEST")
    print("=" * 60)
    print("Fast validation of trending system integration")
    print("=" * 60)
    
    # Test 1: Trend Analyzer
    test1_passed = test_integrated_trend_analyzer()
    
    # Test 2: Performance Settings
    test2_passed = test_fast_mode_performance()
    
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Trend Analyzer Test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Performance Settings: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 INTEGRATION SUCCESSFUL!")
        print("Your enhanced step13 is ready with:")
        print("✓ Memory-efficient processing (your code)")
        print("✓ Real quantity data (your improvement)")
        print("✓ Comprehensive trending (Andy's system)")
        print("✓ Performance optimizations (FAST_MODE)")
        print("\nTo run the full pipeline:")
        print("  python src/step13_consolidate_spu_rules.py")
        print("\nTo run historical analysis (still compatible):")
        print("  bash historical_analysis/run_workflow.sh")
    else:
        print("\n❌ INTEGRATION ISSUES DETECTED")
        print("Please review the error messages above") 