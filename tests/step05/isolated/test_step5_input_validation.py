"""
Step 5 Input Validation Test (Isolated Synthetic)
==================================================

Validates that Step 5 correctly reads from weather data files and handles missing inputs.

This test ensures Step 5 follows the input reading pattern:
- Reads from output/weather_data/*.csv files (from Step 4)
- Works with or without altitude data (optional)
- Fails gracefully when weather data is missing
"""

import os
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step5_reads_from_weather_data_files(tmp_path):
    """
    Verify Step 5 reads from weather data files correctly.
    
    Setup:
    - Create synthetic weather data files
    - Run Step 5
    
    Verify:
    - Step 5 succeeds by reading weather files
    - Step 5 creates feels-like temperature output
    """
    # Create isolated sandbox
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    
    # Copy src directory
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Create directories
    output_dir = sandbox / "output"
    output_dir.mkdir()
    weather_dir = output_dir / "weather_data"
    weather_dir.mkdir()
    
    # Create stub pipeline_manifest.py
    stub_manifest = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}
    
    def get_latest_output(self, *args, **kwargs):
        return None

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None

def get_step_input(*_args, **_kwargs):
    return None
""".strip()
    (src_dir / "pipeline_manifest.py").write_text(stub_manifest, encoding="utf-8")
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    
    # Create synthetic weather data files for 3 stores
    stores = ['11001', '11002', '11003']
    
    for store_code in stores:
        # Create hourly weather data for 10 days
        dates = pd.date_range(start='2025-10-01', periods=240, freq='H')  # 10 days hourly
        
        weather_data = pd.DataFrame({
            'time': dates,
            'store_code': store_code,
            'temperature_2m': [20.0 + (i % 24) * 0.5 for i in range(240)],
            'relative_humidity_2m': [60.0 + (i % 24) * 1.0 for i in range(240)],
            'wind_speed_10m': [5.0 + (i % 24) * 0.2 for i in range(240)],
            'pressure_msl': [1013.0 + (i % 24) * 0.1 for i in range(240)],
            'shortwave_radiation': [500.0 + (i % 24) * 20.0 for i in range(240)],
            'direct_radiation': [400.0 + (i % 24) * 15.0 for i in range(240)],
            'diffuse_radiation': [100.0 + (i % 24) * 5.0 for i in range(240)],
            'terrestrial_radiation': [50.0 + (i % 24) * 2.0 for i in range(240)]
        })
        
        weather_file = weather_dir / f"weather_data_{store_code}_202510A.csv"
        weather_data.to_csv(weather_file, index=False)
    
    print(f"\n📁 Created test setup:")
    print(f"   Weather files: {len(stores)} stores")
    print(f"   Weather directory: {weather_dir}")
    
    # Run Step 5
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step5_calculate_feels_like_temperature.py"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(f"\n🔍 Step 5 execution:")
    print(f"   Exit code: {result.returncode}")
    if result.stdout:
        print(f"   STDOUT (last 500 chars):\n{result.stdout[-500:]}")
    if result.stderr and result.returncode != 0:
        print(f"   STDERR:\n{result.stderr}")
    
    # Verify Step 5 succeeded
    assert result.returncode == 0, \
        f"Step 5 should succeed when weather data exists\nSTDERR: {result.stderr}"
    
    # Verify Step 5 created output
    output_files = list(output_dir.glob("stores_with_feels_like_temperature*.csv"))
    assert len(output_files) > 0, "Step 5 should create feels-like temperature output"
    
    # Verify output has data
    output_file = output_files[0]
    output_df = pd.read_csv(output_file)
    assert len(output_df) > 0, "Output should have data"
    assert 'store_code' in output_df.columns or 'str_code' in output_df.columns, \
        "Output should have store code column"
    
    print(f"\n✅ Step 5 successfully read weather data and created output with {len(output_df)} stores")


def test_step5_fails_gracefully_when_weather_data_missing(tmp_path):
    """
    Verify Step 5 fails with clear error when weather data is missing.
    
    Setup:
    - Create sandbox WITHOUT weather data
    - Run Step 5
    
    Verify:
    - Step 5 fails with non-zero exit code
    - Error message mentions missing weather data
    """
    # Create isolated sandbox
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    
    # Copy src directory
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Create directories
    output_dir = sandbox / "output"
    output_dir.mkdir()
    weather_dir = output_dir / "weather_data"
    weather_dir.mkdir()  # Create directory but NO files
    
    # Create stub pipeline_manifest.py
    stub_manifest = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}
    
    def get_latest_output(self, *args, **kwargs):
        return None

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None

def get_step_input(*_args, **_kwargs):
    return None
""".strip()
    (src_dir / "pipeline_manifest.py").write_text(stub_manifest, encoding="utf-8")
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    
    print(f"\n📁 Created test setup WITHOUT weather data files")
    
    # Run Step 5
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step5_calculate_feels_like_temperature.py"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(f"\n🔍 Step 5 execution:")
    print(f"   Exit code: {result.returncode}")
    if result.stderr:
        print(f"   STDERR:\n{result.stderr}")
    if result.stdout:
        print(f"   STDOUT (last 300 chars):\n{result.stdout[-300:]}")
    
    # Verify Step 5 failed
    assert result.returncode != 0, \
        "Step 5 should fail when weather data is missing"
    
    # Verify error message mentions weather or files
    error_output = (result.stderr + result.stdout).lower()
    assert "weather" in error_output or "no files" in error_output or "not found" in error_output or "error" in error_output, \
        f"Error message should mention missing weather data\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}"
    
    print(f"\n✅ Step 5 correctly failed with error when weather data missing")


def test_step5_works_without_altitude_data(tmp_path):
    """
    Verify Step 5 works without altitude data (optional input).
    
    Setup:
    - Create weather data files
    - Do NOT create altitude file
    - Run Step 5
    
    Verify:
    - Step 5 succeeds without altitude data
    - Output is created successfully
    """
    # Create isolated sandbox
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    
    # Copy src directory
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Create directories
    output_dir = sandbox / "output"
    output_dir.mkdir()
    weather_dir = output_dir / "weather_data"
    weather_dir.mkdir()
    
    # Create stub pipeline_manifest.py
    stub_manifest = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}
    
    def get_latest_output(self, *args, **kwargs):
        return None

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None

def get_step_input(*_args, **_kwargs):
    return None
""".strip()
    (src_dir / "pipeline_manifest.py").write_text(stub_manifest, encoding="utf-8")
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    
    # Create synthetic weather data (but NO altitude file)
    stores = ['11001', '11002']
    
    for store_code in stores:
        dates = pd.date_range(start='2025-10-01', periods=240, freq='H')
        
        weather_data = pd.DataFrame({
            'time': dates,
            'store_code': store_code,
            'temperature_2m': [20.0 + (i % 24) * 0.5 for i in range(240)],
            'relative_humidity_2m': [60.0 + (i % 24) * 1.0 for i in range(240)],
            'wind_speed_10m': [5.0 + (i % 24) * 0.2 for i in range(240)],
            'pressure_msl': [1013.0 + (i % 24) * 0.1 for i in range(240)],
            'shortwave_radiation': [500.0 + (i % 24) * 20.0 for i in range(240)],
            'direct_radiation': [400.0 + (i % 24) * 15.0 for i in range(240)],
            'diffuse_radiation': [100.0 + (i % 24) * 5.0 for i in range(240)],
            'terrestrial_radiation': [50.0 + (i % 24) * 2.0 for i in range(240)]
        })
        
        weather_file = weather_dir / f"weather_data_{store_code}_202510A.csv"
        weather_data.to_csv(weather_file, index=False)
    
    print(f"\n📁 Created test setup:")
    print(f"   Weather files: {len(stores)} stores")
    print(f"   Altitude file: NOT created (testing optional input)")
    
    # Run Step 5
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step5_calculate_feels_like_temperature.py"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(f"\n🔍 Step 5 execution:")
    print(f"   Exit code: {result.returncode}")
    if result.returncode != 0 and result.stderr:
        print(f"   STDERR:\n{result.stderr}")
    
    # Verify Step 5 succeeded without altitude data
    assert result.returncode == 0, \
        f"Step 5 should succeed without altitude data (optional input)\nSTDERR: {result.stderr}"
    
    # Verify output was created
    output_files = list(output_dir.glob("stores_with_feels_like_temperature*.csv"))
    assert len(output_files) > 0, "Step 5 should create output even without altitude data"
    
    print(f"\n✅ Step 5 successfully worked without altitude data (optional input)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
