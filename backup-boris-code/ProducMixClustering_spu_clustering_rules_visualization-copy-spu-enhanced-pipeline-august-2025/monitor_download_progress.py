#!/usr/bin/env python3
"""
Simple progress monitor for 202506A download
"""

import pandas as pd
import os
import time
from glob import glob
from datetime import datetime

def check_progress():
    """Check current download progress."""
    print(f"📊 Download Progress Check - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    # Find latest partial files
    spu_files = sorted(glob('data/api_data/partial_spu_sales_202506A_*.csv'))
    
    if not spu_files:
        print("❌ No partial files found")
        return
    
    latest_spu = spu_files[-1]
    
    try:
        df = pd.read_csv(latest_spu)
        stores = len(df['str_code'].unique())
        size_mb = os.path.getsize(latest_spu) / (1024*1024)
        
        # Expected total
        expected_stores = 2268
        progress_pct = stores / expected_stores * 100
        
        print(f"📁 Latest file: {os.path.basename(latest_spu)}")
        print(f"📈 Progress: {progress_pct:.1f}% ({stores:,}/{expected_stores:,} stores)")
        print(f"💾 Data: {len(df):,} SPU records ({size_mb:.1f} MB)")
        print(f"⏳ Remaining: {expected_stores - stores:,} stores")
        
        # Check if process is still running
        import subprocess
        try:
            result = subprocess.run(['pgrep', '-f', 'step1_download'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                print("🟢 Download process: RUNNING")
            else:
                print("🔴 Download process: NOT RUNNING")
                
                # Check if we should consolidate
                if stores >= expected_stores * 0.95:  # 95% complete
                    print("✅ Download appears complete - ready for consolidation")
                elif stores > 200:  # Substantial progress
                    print("⚠️  Download stopped with partial data - can consolidate for testing")
                    
        except:
            print("❓ Process status: UNKNOWN")
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
    
    print("=" * 50)

def monitor_continuously(interval_seconds=60):
    """Monitor progress continuously."""
    try:
        while True:
            check_progress()
            print(f"⏱️  Next check in {interval_seconds} seconds... (Ctrl+C to stop)")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        monitor_continuously()
    else:
        check_progress() 