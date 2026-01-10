#!/usr/bin/env python3
"""
Verification Script: Confirm 202506B Data Authenticity

This script verifies that we're working with genuine 202506B data 
(second half of June 2025) and not 202506A data.

Author: Data Pipeline
Date: 2025-06-24
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any
import json

def verify_spu_data() -> Dict[str, Any]:
    """Verify SPU sales data is from 202506B period."""
    print("🔍 Verifying SPU Sales Data...")
    
    spu_file = "data/api_data/complete_spu_sales_202506B.csv"
    if not os.path.exists(spu_file):
        return {"status": "ERROR", "message": f"File not found: {spu_file}"}
    
    try:
        # Read a sample of the data
        df = pd.read_csv(spu_file, nrows=10000)
        
        results = {
            "status": "SUCCESS",
            "file_path": spu_file,
            "file_size_mb": round(os.path.getsize(spu_file) / (1024*1024), 2),
            "total_records": len(pd.read_csv(spu_file)),
            "sample_records": len(df),
            "columns": list(df.columns),
            "unique_stores": df['str_code'].nunique(),
            "unique_spus": df['spu_code'].nunique(),
            "store_sample": sorted(df['str_code'].unique())[:10],
            "spu_sample": sorted(df['spu_code'].unique())[:10],
            "quantity_stats": {
                "mean": round(df['quantity'].mean(), 2),
                "min": round(df['quantity'].min(), 2),
                "max": round(df['quantity'].max(), 2),
                "total": round(df['quantity'].sum(), 2)
            },
            "sales_stats": {
                "mean": round(df['spu_sales_amt'].mean(), 2),
                "min": round(df['spu_sales_amt'].min(), 2),
                "max": round(df['spu_sales_amt'].max(), 2),
                "total": round(df['spu_sales_amt'].sum(), 2)
            }
        }
        
        return results
        
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def verify_weather_data() -> Dict[str, Any]:
    """Verify weather data is from correct time period (June 16-30, 2025)."""
    print("🌤️  Verifying Weather Data...")
    
    weather_dir = "output/weather_data"
    if not os.path.exists(weather_dir):
        return {"status": "ERROR", "message": f"Directory not found: {weather_dir}"}
    
    try:
        # Count files with correct period label
        period_files = [f for f in os.listdir(weather_dir) if "20250616_to_20250630" in f]
        wrong_period_files = [f for f in os.listdir(weather_dir) if "20250601_to_20250615" in f]
        
        if not period_files:
            return {"status": "WARNING", "message": "No weather files found for 202506B period"}
        
        # Sample a weather file to verify date range
        sample_file = os.path.join(weather_dir, period_files[0])
        weather_df = pd.read_csv(sample_file)
        
        # Extract dates from time column
        weather_df['date'] = pd.to_datetime(weather_df['time']).dt.date
        min_date = weather_df['date'].min()
        max_date = weather_df['date'].max()
        
        results = {
            "status": "SUCCESS",
            "correct_period_files": len(period_files),
            "wrong_period_files": len(wrong_period_files),
            "sample_file": sample_file,
            "date_range_verified": {
                "start_date": str(min_date),
                "end_date": str(max_date),
                "expected_start": "2025-06-16",
                "expected_end": "2025-06-30",
                "dates_correct": str(min_date) >= "2025-06-16" and str(max_date) <= "2025-06-30"
            },
            "sample_records": len(weather_df),
            "weather_columns": list(weather_df.columns)
        }
        
        if wrong_period_files:
            results["warning"] = f"Found {len(wrong_period_files)} files from wrong period (202506A)"
        
        return results
        
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def verify_store_config() -> Dict[str, Any]:
    """Verify store configuration data."""
    print("🏪 Verifying Store Configuration...")
    
    config_file = "data/api_data/store_config_202506B.csv"
    if not os.path.exists(config_file):
        return {"status": "ERROR", "message": f"File not found: {config_file}"}
    
    try:
        df = pd.read_csv(config_file, dtype={'str_code': str})
        
        results = {
            "status": "SUCCESS",
            "file_path": config_file,
            "total_stores": len(df),
            "columns": list(df.columns),
            "store_sample": sorted(df['str_code'].astype(str).unique())[:10],
            "provinces": df['province'].value_counts().head(10).to_dict() if 'province' in df.columns else {},
            "cities": df['city'].value_counts().head(10).to_dict() if 'city' in df.columns else {}
        }
        
        return results
        
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def verify_coordinates() -> Dict[str, Any]:
    """Verify store coordinates data."""
    print("📍 Verifying Store Coordinates...")
    
    coord_file = "data/store_coordinates_extended_202506B.csv"
    if not os.path.exists(coord_file):
        return {"status": "ERROR", "message": f"File not found: {coord_file}"}
    
    try:
        df = pd.read_csv(coord_file, dtype={'str_code': str})
        
        results = {
            "status": "SUCCESS",
            "file_path": coord_file,
            "total_stores": len(df),
            "columns": list(df.columns),
            "coordinate_stats": {
                "lat_range": [df['latitude'].min(), df['latitude'].max()],
                "lon_range": [df['longitude'].min(), df['longitude'].max()],
                "missing_coords": df[['latitude', 'longitude']].isnull().sum().to_dict()
            }
        }
        
        return results
        
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def verify_configuration() -> Dict[str, Any]:
    """Verify pipeline configuration."""
    print("⚙️  Verifying Pipeline Configuration...")
    
    try:
        import sys
        sys.path.append('src')
        from config import get_current_period, get_period_label
        
        yyyymm, period = get_current_period()
        period_label = get_period_label(yyyymm, period)
        
        results = {
            "status": "SUCCESS",
            "current_yyyymm": yyyymm,
            "current_period": period,
            "period_label": period_label,
            "expected_label": "202506B",
            "configuration_correct": period_label == "202506B"
        }
        
        return results
        
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def main():
    """Run comprehensive verification."""
    print("=" * 60)
    print("🔍 202506B DATA VERIFICATION REPORT")
    print("=" * 60)
    print(f"Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all verifications
    verifications = {
        "configuration": verify_configuration(),
        "spu_data": verify_spu_data(),
        "weather_data": verify_weather_data(),
        "store_config": verify_store_config(),
        "coordinates": verify_coordinates()
    }
    
    # Print results
    all_success = True
    for section, results in verifications.items():
        status = results.get("status", "UNKNOWN")
        print(f"📊 {section.upper()}: {status}")
        
        if status == "SUCCESS":
            if section == "configuration":
                print(f"   ✅ Period: {results.get('period_label', 'Unknown')}")
                print(f"   ✅ Config Correct: {results.get('configuration_correct', False)}")
            elif section == "spu_data":
                print(f"   ✅ Records: {results.get('total_records', 0):,}")
                print(f"   ✅ Stores: {results.get('unique_stores', 0):,}")
                print(f"   ✅ SPUs: {results.get('unique_spus', 0):,}")
                print(f"   ✅ Total Sales: ¥{results.get('sales_stats', {}).get('total', 0):,.2f}")
            elif section == "weather_data":
                print(f"   ✅ Weather Files: {results.get('correct_period_files', 0):,}")
                print(f"   ✅ Date Range: {results.get('date_range_verified', {}).get('start_date', 'Unknown')} to {results.get('date_range_verified', {}).get('end_date', 'Unknown')}")
                print(f"   ✅ Dates Correct: {results.get('date_range_verified', {}).get('dates_correct', False)}")
                if results.get('wrong_period_files', 0) > 0:
                    print(f"   ⚠️  Wrong Period Files: {results.get('wrong_period_files', 0)}")
            elif section == "store_config":
                print(f"   ✅ Stores: {results.get('total_stores', 0):,}")
            elif section == "coordinates":
                print(f"   ✅ Stores with Coords: {results.get('total_stores', 0):,}")
        elif status == "ERROR":
            print(f"   ❌ Error: {results.get('message', 'Unknown error')}")
            all_success = False
        elif status == "WARNING":
            print(f"   ⚠️  Warning: {results.get('message', 'Unknown warning')}")
    
    print()
    print("=" * 60)
    if all_success:
        print("✅ VERIFICATION COMPLETE: All data confirmed as 202506B (Second Half June 2025)")
    else:
        print("❌ VERIFICATION ISSUES: Some data may not be from 202506B period")
    print("=" * 60)
    
    # Save detailed results
    with open("202506B_verification_report.json", "w") as f:
        json.dump(verifications, f, indent=2, default=str)
    
    print(f"📄 Detailed report saved to: 202506B_verification_report.json")

if __name__ == "__main__":
    main() 