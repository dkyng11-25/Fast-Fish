#!/usr/bin/env python3
"""
Step 4: Weather Data Download (Refactored)

This script uses the refactored WeatherDataDownloadStep implementation.
It downloads weather data for store locations using the Open-Meteo Archive API.

Usage:
    # Download for default period (from environment variables)
    python src/step4_weather_data_download_refactored.py
    
    # Download for specific period
    python src/step4_weather_data_download_refactored.py --target-yyyymm 202506 --target-period A
    
    # Download with custom configuration
    python src/step4_weather_data_download_refactored.py --months-back 6 --max-retries 5
    
Environment Variables:
    PIPELINE_TARGET_YYYYMM: Target year-month (default: 202506)
    PIPELINE_TARGET_PERIOD: Target period A or B (default: A)
"""

import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from steps.weather_data_factory import create_weather_data_download_step
from core.context import StepContext
from core.exceptions import DataValidationError


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Step 4: Download weather data for store locations (Refactored)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Period configuration
    parser.add_argument(
        '--target-yyyymm',
        type=str,
        default=os.environ.get('PIPELINE_TARGET_YYYYMM', '202506'),
        help='Target year-month (e.g., 202506). Default: from PIPELINE_TARGET_YYYYMM env var or 202506'
    )
    
    parser.add_argument(
        '--target-period',
        type=str,
        choices=['A', 'B'],
        default=os.environ.get('PIPELINE_TARGET_PERIOD', 'A'),
        help='Target period (A or B). Default: from PIPELINE_TARGET_PERIOD env var or A'
    )
    
    # File paths
    parser.add_argument(
        '--coordinates-path',
        type=str,
        default='data/store_coordinates.csv',
        help='Path to store coordinates CSV file'
    )
    
    parser.add_argument(
        '--weather-output-dir',
        type=str,
        default='data/weather',
        help='Directory for weather data output'
    )
    
    parser.add_argument(
        '--altitude-output-path',
        type=str,
        default='data/altitude.csv',
        help='Path for altitude data CSV'
    )
    
    parser.add_argument(
        '--progress-file-path',
        type=str,
        default='data/weather_progress.json',
        help='Path for progress tracking JSON'
    )
    
    # Configuration
    parser.add_argument(
        '--months-back',
        type=int,
        default=3,
        help='Number of months to look back for year-over-year analysis (default: 3)'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts for failed requests (default: 3)'
    )
    
    parser.add_argument(
        '--min-delay',
        type=float,
        default=0.5,
        help='Minimum delay between API requests in seconds (default: 0.5)'
    )
    
    parser.add_argument(
        '--max-delay',
        type=float,
        default=1.5,
        help='Maximum delay between API requests in seconds (default: 1.5)'
    )
    
    parser.add_argument(
        '--disable-vpn-switching',
        action='store_true',
        help='Disable VPN switching support'
    )
    
    parser.add_argument(
        '--vpn-switch-threshold',
        type=int,
        default=5,
        help='Consecutive failures before VPN switch prompt (default: 5)'
    )
    
    return parser.parse_args()


def main():
    """Main execution function."""
    # Parse arguments
    args = parse_arguments()
    
    print("=" * 70)
    print("Step 4: Weather Data Download (Refactored)")
    print("=" * 70)
    print(f"Target Period: {args.target_yyyymm}{args.target_period}")
    print(f"Months Back: {args.months_back}")
    print(f"Coordinates: {args.coordinates_path}")
    print(f"Output Directory: {args.weather_output_dir}")
    print(f"VPN Switching: {'Disabled' if args.disable_vpn_switching else 'Enabled'}")
    print("=" * 70)
    print()
    
    try:
        # Create step with dependencies (composition root)
        print("🔧 Creating Step 4 with dependencies...")
        step = create_weather_data_download_step(
            coordinates_path=args.coordinates_path,
            weather_output_dir=args.weather_output_dir,
            altitude_output_path=args.altitude_output_path,
            progress_file_path=args.progress_file_path,
            target_yyyymm=args.target_yyyymm,
            target_period=args.target_period,
            months_back=args.months_back,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            max_retries=args.max_retries,
            vpn_switch_threshold=args.vpn_switch_threshold,
            enable_vpn_switching=not args.disable_vpn_switching
        )
        print("✅ Step created successfully")
        print()
        
        # Create initial context
        context = StepContext()
        
        # Execute step (runs all 4 phases: setup → apply → validate → persist)
        print("🚀 Executing Step 4...")
        print()
        final_context = step.execute(context)
        
        # Show summary
        print()
        print("=" * 70)
        print("✅ Step 4 completed successfully!")
        print("=" * 70)
        
        # Extract results from context
        periods = final_context.get_state('periods', [])
        altitude_df = final_context.get_state('altitude_data')
        progress = final_context.get_state('progress', {})
        
        print(f"📊 Generated {len(periods)} periods for download")
        if altitude_df is not None:
            print(f"📊 Collected altitude data for {len(altitude_df)} stores")
        print(f"📊 VPN switches: {progress.get('vpn_switches', 0)}")
        print(f"📊 Completed stores: {len(progress.get('completed_stores', []))}")
        print(f"📊 Failed stores: {len(progress.get('failed_stores', []))}")
        print()
        
        print("📁 Output files:")
        print(f"   - Weather data: {args.weather_output_dir}/")
        print(f"   - Altitude data: {args.altitude_output_path}")
        print(f"   - Progress tracking: {args.progress_file_path}")
        print()
        
        return 0
        
    except DataValidationError as e:
        print()
        print("=" * 70)
        print("❌ Step 4 validation failed!")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        print("This means the downloaded data did not meet quality requirements.")
        print("Check the error message above for details.")
        return 1
        
    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("⚠️  Step 4 interrupted by user")
        print("=" * 70)
        print()
        print("Progress has been saved. You can resume by running the script again.")
        return 130
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ Step 4 execution failed!")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
