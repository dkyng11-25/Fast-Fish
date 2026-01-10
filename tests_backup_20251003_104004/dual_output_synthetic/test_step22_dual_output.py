"""
Step 22 Dual Output Pattern Test
==================================================

Tests that Step 22 (Store Attribute Enrichment) follows the dual output pattern.

The dual output pattern ensures:
1. Timestamped files (real files): filename_YYYYMMDD_HHMMSS.csv
2. Period symlinks: filename_202510A.csv → timestamped file
3. Generic symlinks: filename.csv → timestamped file
"""

import os
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest
import re

TARGET_YYYYMM = "202510"
TARGET_PERIOD = "A"
PERIOD_LABEL = f"{TARGET_YYYYMM}{TARGET_PERIOD}"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"


def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox with src/ code"""
    sandbox = tmp_path / "sandbox"
    src_target = sandbox / "src"
    shutil.copytree(SRC_ROOT, src_target)

    stub = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None
""".strip()
    (src_target / "pipeline_manifest.py").write_text(stub, encoding="utf-8")
    (src_target / "__init__.py").write_text("", encoding="utf-8")

    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    return sandbox


def test_step22_creates_output_without_timestamp(tmp_path):
    """Test that Step 22 follows the dual output pattern with timestamped files and symlinks"""
    # For now, just verify the pattern in actual output directory
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist - run pipeline first")
    
    # Look for files matching the base pattern
    matching_files = list(output_dir.glob(f"enriched_store_attributes_*.csv"))
    
    if not matching_files:
        pytest.skip(f"No output files found for step 22 - run pipeline first")
    
    # Dual output pattern requires:
    # 1. Timestamped file (real file)
    # 2. Period symlink (optional but recommended)
    # 3. Generic symlink (required)
    
    timestamp_pattern = r'_\d{8}_\d{6}'
    period_pattern = r'_\d{6}[AB]'
    
    # Find timestamped files (REQUIRED - these are the real files)
    timestamped_files = [f for f in matching_files 
                         if re.search(timestamp_pattern, f.name) and f.is_file()]
    
    # Find period symlinks (files with period but no timestamp)
    period_symlinks = [f for f in matching_files 
                      if re.search(period_pattern, f.name) 
                      and not re.search(timestamp_pattern, f.name)
                      and f.is_symlink()]
    
    # Find generic symlink
    generic_symlink = output_dir / "enriched_store_attributes.csv"
    
    # MUST have at least one timestamped file
    assert len(timestamped_files) > 0, \
        f"❌ No timestamped files found (expected pattern: *_YYYYMMA_YYYYMMDD_HHMMSS.csv)"
    
    # MUST have generic symlink
    assert generic_symlink.exists() and generic_symlink.is_symlink(), \
        f"❌ Generic symlink not found: {generic_symlink}"
    
    print(f"✅ Step 22 follows dual output pattern:")
    print(f"   Timestamped files: {len(timestamped_files)}")
    for f in timestamped_files:
        print(f"      - {f.name}")
    if period_symlinks:
        print(f"   Period symlinks: {len(period_symlinks)}")
        for f in period_symlinks:
            target = f.readlink() if f.is_symlink() else "N/A"
            print(f"      - {f.name} -> {target}")
    if generic_symlink.exists():
        target = generic_symlink.readlink() if generic_symlink.is_symlink() else "N/A"
        print(f"   Generic symlink: {generic_symlink.name} -> {target}")


def test_step22_output_has_period_label(tmp_path):
    """Test that Step 22 output files have period labels"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    matching_files = list(output_dir.glob(f"enriched_store_attributes_*.csv"))
    
    if not matching_files:
        pytest.skip(f"No output files found for step 22")
    
    # Verify files have period label pattern (YYYYMMA or YYYYMMB)
    period_pattern = r'_\d{6}[AB]'
    
    for file in matching_files:
        assert re.search(period_pattern, file.name), \
            f"❌ File should have period label (YYYYMMA/B): {file.name}"
    
    print(f"✅ Step 22 output files have period labels")


def test_step22_output_consumable_by_downstream(tmp_path):
    """Test that Step 22 output can be found by downstream steps"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    # Check that at least one output file exists
    matching_files = list(output_dir.glob(f"enriched_store_attributes_*.csv"))
    
    if not matching_files:
        pytest.skip(f"No output files found for step 22")
    
    # Verify file is readable
    test_file = matching_files[0]
    assert test_file.exists(), f"File should exist: {test_file}"
    assert test_file.stat().st_size > 0, f"File should not be empty: {test_file}"
    
    print(f"✅ Step 22 output is consumable by downstream steps")
    print(f"   File: {test_file.name} ({test_file.stat().st_size} bytes)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
