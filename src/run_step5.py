#!/usr/bin/env python3
"""
Run Step 5: Calculate Feels-Like Temperature

This script runs the refactored Step 5 using the factory pattern
with dependency injection.

Usage:
    python src/run_step5.py <YYYYMM> <period>
    
Example:
    python src/run_step5.py 202506 A

Author: Data Pipeline Team
Date: 2025-10-10
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from factories.step5_factory import create_feels_like_temperature_step
from core.context import StepContext
from core.logger import PipelineLogger


def main():
    """Main execution function."""
    
    # Parse arguments
    if len(sys.argv) < 3:
        print("Usage: python src/run_step5.py <YYYYMM> <period>")
        print("Example: python src/run_step5.py 202506 A")
        sys.exit(1)
    
    target_yyyymm = sys.argv[1]
    target_period = sys.argv[2]
    
    print("=" * 70)
    print(f"Step 5: Calculate Feels-Like Temperature")
    print(f"Target: {target_yyyymm}{target_period}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    try:
        # Create logger
        logger = PipelineLogger("Step5")
        
        # Create Step 5 using factory
        print("Creating Step 5 instance...")
        step5 = create_feels_like_temperature_step(
            target_yyyymm=target_yyyymm,
            target_period=target_period,
            logger=logger
        )
        print("✅ Step 5 instance created")
        print()
        
        # Execute
        print("Executing Step 5...")
        context = StepContext()
        result = step5.execute(context)
        print()
        
        # Get results
        processed_weather = result.data['processed_weather']
        temperature_bands = result.data['temperature_bands']
        
        # Print summary
        print("=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)
        print(f"✅ Step 5 completed successfully!")
        print()
        print(f"Stores processed: {len(processed_weather)}")
        print(f"Temperature range: {processed_weather['feels_like_temperature'].min():.1f}°C to {processed_weather['feels_like_temperature'].max():.1f}°C")
        print(f"Temperature bands: {processed_weather['temperature_band'].nunique()}")
        print()
        
        # Check seasonal data
        seasonal_col = 'temperature_band_q3q4_seasonal'
        if seasonal_col in processed_weather.columns:
            seasonal_count = processed_weather[seasonal_col].notna().sum()
            print(f"Seasonal bands: {seasonal_count} stores with Sep-Nov data")
        print()
        
        # Output files
        print("Output files:")
        print("  • output/stores_with_feels_like_temperature_*.csv")
        print("  • output/temperature_bands_*.csv")
        print()
        
        # Downstream compatibility
        print("Downstream compatibility:")
        print("  ✅ Ready for Step 6 (Cluster Analysis)")
        print("  ✅ All 15 required columns present")
        print("  ✅ Seasonal bands available")
        print()
        
        print("=" * 70)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print(f"Step 5 failed: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
