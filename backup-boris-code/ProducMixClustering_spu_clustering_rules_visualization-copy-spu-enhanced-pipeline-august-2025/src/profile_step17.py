#!/usr/bin/env python3
"""
Profile Step 17 Performance Issues
==================================

Identify exactly where the performance bottleneck is in the trending analysis.
"""

import pandas as pd
import time
import cProfile
import pstats
import io
from datetime import datetime
import os
import sys

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def profile_trending_analysis():
    """Profile the trending analysis to find bottlenecks."""
    
    print("🔍 Profiling Step 17 Trending Analysis Performance...")
    
    # Load a small sample of Fast Fish data for testing
    fast_fish_file = "../output/fast_fish_spu_count_recommendations_20250713_164050.csv"
    if not os.path.exists(fast_fish_file):
        print(f"❌ Fast Fish file not found: {fast_fish_file}")
        return
    
    print(f"📊 Loading Fast Fish data from: {fast_fish_file}")
    fast_fish_df = pd.read_csv(fast_fish_file)
    print(f"   Loaded {len(fast_fish_df):,} recommendations")
    
    # Take a small sample for profiling
    sample_size = 10  # Just 10 recommendations for profiling
    sample_df = fast_fish_df.head(sample_size).copy()
    print(f"   Using sample of {len(sample_df)} recommendations for profiling")
    
    # Profile the trending analysis
    print("\n🚀 Starting profiling...")
    
    # Create a profiler
    profiler = cProfile.Profile()
    
    # Start profiling
    profiler.enable()
    
    # Time the overall process
    start_time = time.time()
    
    try:
        # Import and initialize trending analyzer
        from step13_consolidate_spu_rules import ComprehensiveTrendAnalyzer
        print("✅ Imported ComprehensiveTrendAnalyzer")
        
        # Time the initialization
        init_start = time.time()
        trend_analyzer = ComprehensiveTrendAnalyzer()
        init_time = time.time() - init_start
        print(f"   Initialization took: {init_time:.2f} seconds")
        
        # Test a single trending analysis call
        print("\n🧪 Testing single trending analysis call...")
        single_start = time.time()
        
        # Create a sample recommendation
        sample_recommendation = {
            'store_code': '001',
            'spu_code': 'TEST_SPU',
            'action': 'TREND_ANALYSIS',
            'recommended_quantity_change': 1,
            'investment_required': 100
        }
        
        # Call the trending analysis
        result = trend_analyzer.analyze_comprehensive_trends(sample_recommendation)
        single_time = time.time() - single_start
        
        print(f"   Single trending analysis took: {single_time:.2f} seconds")
        print(f"   Result type: {type(result)}")
        print(f"   Result preview: {str(result)[:200]}...")
        
        # Test multiple calls
        print(f"\n🔄 Testing {sample_size} trending analysis calls...")
        multi_start = time.time()
        
        for i, (idx, row) in enumerate(sample_df.iterrows()):
            call_start = time.time()
            
            # Create recommendation for this row
            recommendation = {
                'store_code': row.get('Store_Code', '001'),
                'spu_code': f'SPU_{i}',
                'action': 'TREND_ANALYSIS',
                'recommended_quantity_change': 1,
                'investment_required': 100
            }
            
            # Call trending analysis
            result = trend_analyzer.analyze_comprehensive_trends(recommendation)
            call_time = time.time() - call_start
            
            print(f"   Call {i+1}: {call_time:.2f} seconds")
            
            # Break if taking too long
            if call_time > 30:
                print(f"   ⚠️ Call {i+1} took over 30 seconds, stopping profiling")
                break
        
        multi_time = time.time() - multi_start
        print(f"   Total time for {sample_size} calls: {multi_time:.2f} seconds")
        print(f"   Average time per call: {multi_time/sample_size:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Error during profiling: {e}")
        import traceback
        traceback.print_exc()
    
    # Stop profiling
    profiler.disable()
    
    total_time = time.time() - start_time
    print(f"\n⏱️ Total profiling time: {total_time:.2f} seconds")
    
    # Generate profiling report
    print("\n📊 Profiling Report:")
    print("="*80)
    
    # Create string buffer for profiling output
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    # Print the profiling results
    profiling_output = s.getvalue()
    print(profiling_output)
    
    # Save profiling report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    profile_file = f"../output/step17_profiling_report_{timestamp}.txt"
    
    with open(profile_file, 'w') as f:
        f.write("Step 17 Trending Analysis Performance Profile\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Sample size: {sample_size} recommendations\n")
        f.write(f"Total time: {total_time:.2f} seconds\n")
        f.write(f"Average per call: {total_time/sample_size:.2f} seconds\n\n")
        f.write("Detailed Profiling Results:\n")
        f.write("-" * 30 + "\n")
        f.write(profiling_output)
    
    print(f"\n💾 Profiling report saved to: {profile_file}")

def compare_with_old_approach():
    """Compare current approach with what worked before."""
    
    print("\n🔍 Analyzing differences from old working approach...")
    
    # Check what the old approach was doing
    print("\n📋 Old Working Approach Analysis:")
    print("   1. ✅ Used simple historical lookup (fast)")
    print("   2. ✅ Applied basic trending without expensive API calls")
    print("   3. ✅ Processed all recommendations in vectorized operations")
    print("   4. ✅ Avoided row-by-row expensive function calls")
    
    print("\n📋 Current Slow Approach Issues:")
    print("   1. ❌ Calls ComprehensiveTrendAnalyzer for EVERY recommendation")
    print("   2. ❌ Each call takes 30+ seconds (based on previous logs)")
    print("   3. ❌ 3,862 recommendations × 30 seconds = 32+ hours!")
    print("   4. ❌ No caching or optimization")
    
    print("\n🎯 Recommended Fix:")
    print("   1. ✅ Cache trending results by store group (46 groups vs 3,862 calls)")
    print("   2. ✅ Use vectorized operations for historical data")
    print("   3. ✅ Simplify trending analysis or use pre-computed results")
    print("   4. ✅ Apply trending at store group level, not per recommendation")

if __name__ == "__main__":
    profile_trending_analysis()
    compare_with_old_approach() 