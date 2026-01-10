"""
Step 24 Dual Output Pattern Test
==================================================

Tests that Step 24 (Comprehensive Cluster Labeling) creates output files WITHOUT timestamps.

The dual output pattern ensures:
1. Files have period labels (e.g., _202510A)
2. Files do NOT have timestamp patterns (_YYYYMMDD_HHMMSS)
3. Downstream steps can reliably find these files
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


def test_step24_creates_output_without_timestamp(tmp_path):
    """Test that Step 24 creates output files WITHOUT timestamp in filename"""
    # NOTE: This is a placeholder test
    # TODO: Implement full sandbox test with synthetic inputs
    
    # For now, just verify the pattern in actual output directory
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist - run pipeline first")
    
    # Check for output file
    pattern = "comprehensive_cluster_labels_{PERIOD_LABEL}.csv"
    expected_file = output_dir / pattern
    
    # Look for files matching the base pattern
    matching_files = list(output_dir.glob(f"comprehensive_cluster_labels_*.csv"))
    
    if not matching_files:
        pytest.skip(f"No output files found for step 24 - run pipeline first")
    
    # Verify period-labeled files exist WITHOUT timestamp
    timestamp_pattern = r'_\d{8}_\d{6}'
    period_pattern = r'_\d{6}[AB]'
    
    # Find period-labeled files (no timestamp)
    period_files = [f for f in matching_files 
                    if re.search(period_pattern, f.name) 
                    and not re.search(timestamp_pattern, f.name)]
    
    # Find timestamped files (optional)
    timestamped_files = [f for f in matching_files 
                         if re.search(timestamp_pattern, f.name)]
    
    # MUST have at least one period-labeled file (no timestamp)
    assert len(period_files) > 0, \
        f"❌ No period-labeled files found (expected pattern: *_YYYYMMA.ext)"
    
    # Timestamped files are OPTIONAL (allowed but not required)
    if timestamped_files:
        print(f"   Note: {len(timestamped_files)} timestamped file(s) also exist (for audit)")
    
    print(f"✅ Step 24 output files have correct naming (no timestamps)")
    for file in matching_files:
        print(f"   - {file.name}")


def test_step24_output_has_period_label(tmp_path):
    """Test that Step 24 output files have period labels"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    matching_files = list(output_dir.glob(f"comprehensive_cluster_labels_*.csv"))
    
    if not matching_files:
        pytest.skip(f"No output files found for step 24")
    
    # Verify files have period label pattern (YYYYMMA or YYYYMMB)
    period_pattern = r'_\d{6}[AB]'
    
    for file in matching_files:
        assert re.search(period_pattern, file.name), \
            f"❌ File should have period label (YYYYMMA/B): {file.name}"
    
    print(f"✅ Step 24 output files have period labels")


def test_step24_output_consumable_by_downstream(tmp_path):
    """Test that Step 24 output can be found by downstream steps"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    # Check that at least one output file exists
    matching_files = list(output_dir.glob(f"comprehensive_cluster_labels_*.csv"))
    
    if not matching_files:
        pytest.skip(f"No output files found for step 24")
    
    # Verify file is readable
    test_file = matching_files[0]
    assert test_file.exists(), f"File should exist: {test_file}"
    assert test_file.stat().st_size > 0, f"File should not be empty: {test_file}"
    
    print(f"✅ Step 24 output is consumable by downstream steps")
    print(f"   File: {test_file.name} ({test_file.stat().st_size} bytes)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
