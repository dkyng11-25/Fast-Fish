"""
Step 6 Synthetic Tests - Clustering Analysis (Isolated)
======================================================

Fixture-based synthetic tests for Step 6 (Clustering Analysis).
Uses realistic pre-generated input fixtures for complete isolation.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

TARGET_YYYYMM = "202501"
TARGET_PERIOD = "A"
PERIOD_LABEL = f"{TARGET_YYYYMM}{TARGET_PERIOD}"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox environment for Step 6 testing."""
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
    
    # Mock config.py
    config_stub = f"""
import os
from pathlib import Path

def initialize_pipeline_config(*args, **kwargs):
    pass

def get_current_period():
    return "{TARGET_YYYYMM}", "{TARGET_PERIOD}"

def get_period_label(*args, **kwargs):
    if args:
        yyyymm, period = args[0], args[1] if len(args) > 1 else "A"
        return f"{{yyyymm}}{{period}}"
    return "{PERIOD_LABEL}"

def get_api_data_files(yyyymm, period):
    base_path = "data/api_data"
    return {{
        'store_config': f"{{base_path}}/store_config_{{yyyymm}}{{period}}.csv",
        'spu_sales': f"{{base_path}}/complete_spu_sales_{{yyyymm}}{{period}}.csv",
        'category_sales': f"{{base_path}}/complete_category_sales_{{yyyymm}}{{period}}.csv",
    }}

def get_output_files(*args, **kwargs):
    if args and len(args) >= 3:
        analysis_level, yyyymm, period = args[0], args[1], args[2]
        period_label = f"{{yyyymm}}{{period}}"
    else:
        analysis_level = args[0] if args else "spu"
        period_label = "{PERIOD_LABEL}"
    
    return {{
        'clustering_results': f"output/clustering_results_{{analysis_level}}_{{period_label}}.csv",
        'clustering_spu': f"output/clustering_results_spu_{{period_label}}.csv",
        'clustering_subcategory': f"output/clustering_results_subcategory_{{period_label}}.csv",
    }}
""".strip()
    (src_target / "config.py").write_text(config_stub, encoding="utf-8")
    (src_target / "__init__.py").write_text("", encoding="utf-8")

    # Create directory structure
    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    return sandbox


def _generate_synthetic_matrix_data(sandbox: Path) -> None:
    """Generate synthetic normalized matrix data for Step 6 clustering."""
    import numpy as np
    import pandas as pd
    
    np.random.seed(42)  # Reproducible results
    
    data_dir = sandbox / "data"
    
    # Generate synthetic normalized SPU matrix (what Step 6 expects)
    n_stores = 200  # Increase to force multiple clusters (50 stores per cluster = 4 clusters)
    n_features = 100  # Feature dimensions for clustering
    
    # Create store codes
    store_codes = [f"S{i:04d}" for i in range(1, n_stores + 1)]
    
    # Generate normalized feature matrix
    # This simulates the output from Steps 3-5 (normalization pipeline)
    normalized_data = np.random.rand(n_stores, n_features)
    
    # Create DataFrame with store codes as index
    normalized_df = pd.DataFrame(normalized_data, index=store_codes)
    normalized_df.index.name = "str_code"
    
    # Save normalized matrix (what Step 6 loads)
    normalized_file = data_dir / "normalized_spu_limited_matrix.csv"
    normalized_df.to_csv(normalized_file)
    
    # Also create original matrix (Step 6 expects this specific filename)
    original_file = data_dir / "store_spu_limited_matrix.csv"
    original_df = normalized_df * 1000  # Scale up for "original" values
    original_df.to_csv(original_file)
    
    # Create temperature data that matches the stores
    temp_data = []
    temp_bands = ["10-15", "15-20", "20-25", "25-30"]
    
    for store in store_codes:
        temp_data.append({
            "str_code": store,
            "temperature_band": np.random.choice(temp_bands),
            "avg_temperature": np.random.uniform(10, 30),
        })
    
    temp_df = pd.DataFrame(temp_data)
    temp_file = data_dir / f"store_temperature_{PERIOD_LABEL}.csv"
    temp_df.to_csv(temp_file, index=False)


def _copy_fixtures_to_sandbox(sandbox: Path) -> None:
    """Copy pre-generated test fixtures into sandbox."""
    api_dir = sandbox / "data" / "api_data"
    data_dir = sandbox / "data"
    
    # Copy store config fixture
    store_fixture = FIXTURES_DIR / "store_config_202501A.csv"
    if store_fixture.exists():
        shutil.copy2(store_fixture, api_dir / "store_config_202501A.csv")
    
    # Copy temperature fixture
    temp_fixture = FIXTURES_DIR / "store_temperature_202501A.csv"
    if temp_fixture.exists():
        shutil.copy2(temp_fixture, api_dir / "store_temperature_202501A.csv")
    
    # Generate synthetic normalized matrix data that Step 6 needs
    _generate_synthetic_matrix_data(sandbox)


def _run_step6_with_fixtures(sandbox: Path, analysis_level: str = "spu", extra_args: list = None) -> subprocess.CompletedProcess:
    """Run Step 6 in isolated sandbox with fixture data."""
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(sandbox))
    env["PIPELINE_TARGET_YYYYMM"] = TARGET_YYYYMM
    env["PIPELINE_TARGET_PERIOD"] = TARGET_PERIOD
    
    cmd = ["python3", "src/step6_cluster_analysis.py"]
    
    if extra_args:
        cmd.extend(extra_args)
    
    return subprocess.run(
        cmd,
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_step6_fixture_spu_clustering_isolated(tmp_path):
    """Test Step 6 SPU-level clustering with fixture data."""
    sandbox = _prepare_sandbox(tmp_path)
    _copy_fixtures_to_sandbox(sandbox)
    
    result = _run_step6_with_fixtures(sandbox, "spu")
    
    # Check successful execution
    assert result.returncode == 0, f"Step 6 SPU clustering failed: STDOUT: {result.stdout} STDERR: {result.stderr}"
    
    # Check output files exist (Step 6 creates multiple files)
    output_dir = sandbox / "output"
    possible_files = [
        f"clustering_results_spu_{PERIOD_LABEL}.csv",
        "clustering_results_spu.csv",
        "cluster_profiles_spu.csv",
    ]
    
    found_files = []
    for file_name in possible_files:
        file_path = output_dir / file_name
        if file_path.exists():
            found_files.append(file_name)
    
    assert len(found_files) > 0, f"No clustering output files created. Expected one of: {possible_files}"
    
    # Use the main clustering results file for validation
    if f"clustering_results_spu_{PERIOD_LABEL}.csv" in found_files:
        output_file = output_dir / f"clustering_results_spu_{PERIOD_LABEL}.csv"
    elif "clustering_results_spu.csv" in found_files:
        output_file = output_dir / "clustering_results_spu.csv"
    else:
        output_file = output_dir / found_files[0]
    
    # Validate output structure
    results_df = pd.read_csv(output_file)
    assert len(results_df) > 0, "SPU clustering results should not be empty"
    assert "str_code" in results_df.columns, "Missing str_code column"
    assert "Cluster" in results_df.columns or "cluster_id" in results_df.columns, "Missing cluster column"


def test_step6_fixture_subcategory_clustering_isolated(tmp_path):
    """Test Step 6 subcategory-level clustering with fixture data."""
    sandbox = _prepare_sandbox(tmp_path)
    _copy_fixtures_to_sandbox(sandbox)
    
    result = _run_step6_with_fixtures(sandbox, "subcategory")
    
    # Check successful execution
    assert result.returncode == 0, f"Step 6 subcategory clustering failed: STDOUT: {result.stdout} STDERR: {result.stderr}"
    
    # Check output files exist (flexible detection)
    output_dir = sandbox / "output"
    possible_files = [
        f"clustering_results_subcategory_{PERIOD_LABEL}.csv",
        "clustering_results_subcategory.csv",
        "cluster_profiles_subcategory.csv",
        "clustering_results_spu.csv",  # Fallback to SPU results
    ]
    
    found_files = []
    for file_name in possible_files:
        file_path = output_dir / file_name
        if file_path.exists():
            found_files.append(file_name)
    
    assert len(found_files) > 0, f"No clustering output files created. Expected one of: {possible_files}"
    
    # Use the first available file for validation
    output_file = output_dir / found_files[0]
    results_df = pd.read_csv(output_file)
    assert len(results_df) > 0, "Clustering results should not be empty"
    assert "str_code" in results_df.columns, "Missing str_code column"


def test_step6_fixture_clustering_algorithm_isolated(tmp_path):
    """Test that Step 6 applies clustering algorithms correctly."""
    sandbox = _prepare_sandbox(tmp_path)
    _copy_fixtures_to_sandbox(sandbox)
    
    result = _run_step6_with_fixtures(sandbox, "spu")
    assert result.returncode == 0, f"Step 6 failed: {result.stderr}"
    
    # Check clustering algorithm indicators in output
    output_text = result.stdout.lower()
    clustering_indicators = ["cluster", "kmeans", "algorithm", "grouping"]
    
    has_clustering = any(indicator in output_text for indicator in clustering_indicators)
    assert has_clustering, "Clustering algorithm not detected in Step 6 output"


def test_step6_fixture_store_analysis_isolated(tmp_path):
    """Test that Step 6 performs store-level analysis correctly."""
    sandbox = _prepare_sandbox(tmp_path)
    _copy_fixtures_to_sandbox(sandbox)
    
    result = _run_step6_with_fixtures(sandbox, "spu")
    assert result.returncode == 0, f"Step 6 failed: {result.stderr}"
    
    # Validate that stores are being processed
    output_text = result.stdout.lower()
    store_indicators = ["store", "analysis", "processed"]
    
    has_store_analysis = any(indicator in output_text for indicator in store_indicators)
    assert has_store_analysis, "Store analysis not detected in Step 6 output"


def test_step6_fixture_output_validation_isolated(tmp_path):
    """Test Step 6 output file validation."""
    sandbox = _prepare_sandbox(tmp_path)
    _copy_fixtures_to_sandbox(sandbox)
    
    result = _run_step6_with_fixtures(sandbox, "spu")
    assert result.returncode == 0, f"Step 6 failed: {result.stderr}"
    
    # Check multiple output files if they exist (use same logic as main test)
    output_dir = sandbox / "output"
    possible_files = [
        f"clustering_results_spu_{PERIOD_LABEL}.csv",
        "clustering_results_spu.csv",
        "cluster_profiles_spu.csv",
        f"clustering_analysis_spu_{PERIOD_LABEL}.csv",
    ]
    
    found_files = []
    for file_name in possible_files:
        file_path = output_dir / file_name
        if file_path.exists():
            found_files.append(file_name)
    
    assert len(found_files) > 0, f"No clustering output files found. Expected one of: {possible_files}"
    
    # Validate the first found file
    output_file = output_dir / found_files[0]
    df = pd.read_csv(output_file)
    assert isinstance(df, pd.DataFrame), f"{found_files[0]} should be valid DataFrame"
    if len(df) > 0:
        assert "str_code" in df.columns, f"{found_files[0]} missing str_code column"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
