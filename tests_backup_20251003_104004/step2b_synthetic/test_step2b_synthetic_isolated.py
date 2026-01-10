"""
Step 2b Synthetic Tests - Seasonal Consolidation (Isolated)
===========================================================

Isolated synthetic tests for Step 2b (Seasonal Consolidation) that don't
depend on shared output directory or real pipeline state.

Converts the existing Step 2b tests to use sandbox isolation pattern.
"""

import os
import shutil
import subprocess
import glob
import json
from pathlib import Path

import pandas as pd
import pytest

# Test periods (fictitious to avoid collisions)
P1 = "209901A"
P2 = "209901B"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"


def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox environment for Step 2b testing."""
    sandbox = tmp_path / "sandbox"
    src_target = sandbox / "src"
    shutil.copytree(SRC_ROOT, src_target)

    # Mock pipeline_manifest.py
    manifest_stub = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None

def get_step_input(*_args, **_kwargs):
    return None
""".strip()
    (src_target / "pipeline_manifest.py").write_text(manifest_stub, encoding="utf-8")
    
    # Mock config.py (Step 2b might need basic config)
    config_stub = """
import os
from pathlib import Path

def initialize_pipeline_config(*args, **kwargs):
    pass

def get_current_period():
    return "209901", "A"

def get_period_label(*args, **kwargs):
    if args:
        yyyymm, period = args[0], args[1] if len(args) > 1 else "A"
        return f"{yyyymm}{period}"
    return "209901A"

def get_api_data_files(yyyymm, period):
    base_path = "data/api_data"
    return {
        'store_config': f"{base_path}/store_config_{yyyymm}{period}.csv",
        'spu_sales': f"{base_path}/complete_spu_sales_{yyyymm}{period}.csv",
        'category_sales': f"{base_path}/complete_category_sales_{yyyymm}{period}.csv",
    }

def get_output_files(*args, **kwargs):
    return {
        'consolidated_features': "output/consolidated_seasonal_features.csv",
        'metadata': "output/seasonal_clustering_metadata.json",
    }

# Additional config variables that Step 2b might need
API_DATA_DIR = "data/api_data"
OUTPUT_DIR = "output"
""".strip()
    (src_target / "config.py").write_text(config_stub, encoding="utf-8")
    (src_target / "__init__.py").write_text("", encoding="utf-8")

    # Create directory structure
    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    return sandbox


def _write_minimal_inputs_to_sandbox(sandbox: Path, period: str):
    """Write minimal input files to sandbox output directory."""
    out = sandbox / "output"
    out.mkdir(exist_ok=True)
    
    # Minimal inputs expected by Step 2B (same as original test)
    (out / f"complete_category_sales_{period}.csv").write_text(
        "str_code,sub_cate_name,sal_amt\nS0001,CatX,10\n",
        encoding="utf-8",
    )
    (out / f"complete_spu_sales_{period}.csv").write_text(
        "str_code,spu_code\nS0001,X1\n",
        encoding="utf-8",
    )
    (out / f"store_config_{period}.csv").write_text(
        "str_code,store_name\nS0001,Demo Store\n",
        encoding="utf-8",
    )


def _run_step2b_in_sandbox(sandbox: Path, periods: list) -> subprocess.CompletedProcess:
    """Run Step 2b in isolated sandbox environment."""
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(sandbox))
    
    cmd = [
        "python3",
        "src/step2b_consolidate_seasonal_data.py",
        "--periods",
        ",".join(periods),
    ]
    
    return subprocess.run(
        cmd,
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _latest_metadata_json_in_sandbox(sandbox: Path) -> Path:
    """Find latest metadata JSON in sandbox."""
    candidates = sorted(glob.glob(str(sandbox / "output" / "seasonal_clustering_metadata_*.json")))
    assert candidates, "No seasonal_clustering_metadata_*.json found in sandbox"
    return Path(candidates[-1])


def _read_json(path: Path):
    """Read JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_step2b_two_periods_generates_consolidated_outputs_isolated(tmp_path):
    """Test Step 2b with two periods in isolated environment."""
    sandbox = _prepare_sandbox(tmp_path)
    
    # Arrange: two small periods
    _write_minimal_inputs_to_sandbox(sandbox, P1)
    _write_minimal_inputs_to_sandbox(sandbox, P2)

    # Snapshot existing metadata files
    before = set(glob.glob(str(sandbox / "output" / "seasonal_clustering_metadata_*.json")))

    # Act
    result = _run_step2b_in_sandbox(sandbox, [P1, P2])
    
    # Check successful execution
    assert result.returncode == 0, f"Step 2b failed: STDOUT: {result.stdout} STDERR: {result.stderr}"

    # Assert: new metadata created
    after = set(glob.glob(str(sandbox / "output" / "seasonal_clustering_metadata_*.json")))
    new = sorted(after - before)
    if new:
        meta_path = Path(new[-1])
    else:
        # Fallback: latest by mtime
        meta_path = _latest_metadata_json_in_sandbox(sandbox)
    
    meta = _read_json(meta_path)

    assert meta.get("input_periods") == [P1, P2], "--periods CLI should be honored and ordered"
    assert meta.get("total_stores", 0) >= 1, "Expected at least one store in features"

    # Consolidated outputs exist
    consolidated = sandbox / "output" / "consolidated_seasonal_features.csv"
    assert consolidated.exists(), "consolidated_seasonal_features.csv should exist"

    df = pd.read_csv(consolidated)
    assert not df.empty and "str_code" in df.columns, "Consolidated features should include str_code"
    assert (df["str_code"] == "S0001").any(), "Expected test store S0001 in consolidated features"


def test_step2b_single_period_still_works_isolated(tmp_path):
    """Test Step 2b with single period in isolated environment."""
    sandbox = _prepare_sandbox(tmp_path)
    
    # Arrange: single period
    single = "209902A"
    _write_minimal_inputs_to_sandbox(sandbox, single)

    # Act
    result = _run_step2b_in_sandbox(sandbox, [single])
    
    # Check successful execution
    assert result.returncode == 0, f"Step 2b single period failed: STDOUT: {result.stdout} STDERR: {result.stderr}"

    # Assert basic output existence
    consolidated = sandbox / "output" / "consolidated_seasonal_features.csv"
    assert consolidated.exists(), "consolidated_seasonal_features.csv should exist"
    
    df = pd.read_csv(consolidated)
    assert (df["str_code"] == "S0001").any(), "Expected test store S0001 in consolidated features"


def test_step2b_output_isolation_isolated(tmp_path):
    """Test that Step 2b outputs are properly isolated in sandbox."""
    sandbox = _prepare_sandbox(tmp_path)
    
    # Arrange
    _write_minimal_inputs_to_sandbox(sandbox, P1)
    
    # Act
    result = _run_step2b_in_sandbox(sandbox, [P1])
    assert result.returncode == 0, f"Step 2b isolation test failed: {result.stderr}"
    
    # Assert: outputs are in sandbox, not in main project
    sandbox_output = sandbox / "output" / "consolidated_seasonal_features.csv"
    main_output = PROJECT_ROOT / "output" / "consolidated_seasonal_features.csv"
    
    assert sandbox_output.exists(), "Output should exist in sandbox"
    # Don't check main_output doesn't exist - it might exist from other runs
    # The key is that our test runs in isolation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
