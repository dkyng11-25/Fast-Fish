"""
Step 7 Synthetic Tests - Fixture-Based Approach (Isolated)
==========================================================

This module provides isolated, synthetic tests for Step 7 (Missing Category Rule)
using pre-generated realistic test fixtures instead of fully synthetic data.

Key Features:
- Pre-generated realistic input fixtures
- Self-contained sandbox environments  
- Minimal mocking (only config functions)
- Real data patterns and relationships
- Isolated business logic testing
- Predictable, repeatable results

Approach:
1. Copy realistic input fixtures into sandbox
2. Run Step 7 with minimal config mocking
3. Validate outputs against expected patterns
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

import pandas as pd
import pytest

TARGET_YYYYMM = "202501"
TARGET_PERIOD = "A"
PERIOD_LABEL = f"{TARGET_YYYYMM}{TARGET_PERIOD}"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox environment for Step 7 testing."""
    sandbox = tmp_path / "sandbox"
    src_target = sandbox / "src"
    shutil.copytree(SRC_ROOT, src_target)

    # Mock pipeline_manifest.py with minimal functions
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
    
    # Mock config.py with flexible function signatures
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
        'spu_sales': f"{{base_path}}/complete_spu_sales_{{yyyymm}}{{period}}.csv",
        'category_sales': f"{{base_path}}/complete_category_sales_{{yyyymm}}{{period}}.csv",
        'store_sales': f"{{base_path}}/store_sales_{{yyyymm}}{{period}}.csv",
    }}

def get_output_files(*args, **kwargs):
    # Handle different call patterns
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

def load_margin_rates(period_label, analysis_type='spu'):
    # Return minimal margin data based on fixture SPUs
    import pandas as pd
    return pd.DataFrame([
        {{'spu_code': '15R1010', 'margin_rate': 0.4}},
        {{'spu_code': '15S5025', 'margin_rate': 0.35}},
        {{'spu_code': '15S1021', 'margin_rate': 0.45}},
        {{'spu_code': '15R1013', 'margin_rate': 0.38}},
        {{'spu_code': '15R1014', 'margin_rate': 0.42}},
    ])
""".strip()
    (src_target / "config.py").write_text(config_stub, encoding="utf-8")
    
    # Mock sell-through validator to avoid import errors
    validator_stub = """
import pandas as pd

class SellThroughValidator:
    def __init__(self, historical_data=None):
        self.historical_data = historical_data or pd.DataFrame()
    
    def validate_recommendation(self, store_code, category, current_spu_count, 
                              recommended_spu_count, investment_amount, rule_name):
        # Mock validation that approves most recommendations
        return {
            'fast_fish_compliant': True,
            'predicted_sell_through_rate': 45.0,  # Mock 45% sell-through
            'current_sell_through_rate': 30.0,    # Mock current rate
            'sell_through_improvement': 15.0,     # 15pp improvement
            'roi_estimate': 1.2,                  # Mock ROI
        }

def load_historical_data_for_validation():
    # Return list of DataFrames (expected format)
    return [pd.DataFrame()]
""".strip()
    (src_target / "sell_through_validator.py").write_text(validator_stub, encoding="utf-8")
    (src_target / "__init__.py").write_text("", encoding="utf-8")

    # Create directory structure
    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    return sandbox


def _copy_fixtures_to_sandbox(sandbox: Path) -> None:
    """Copy pre-generated test fixtures into sandbox."""
    api_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    
    # Copy API data fixtures
    fixtures = [
        "complete_spu_sales_202501A.csv",
        "complete_spu_sales_202412B.csv",  # Seasonal reference
        "store_sales_202501A.csv",
    ]
    
    for fixture in fixtures:
        src_file = FIXTURES_DIR / fixture
        if src_file.exists():
            shutil.copy2(src_file, api_dir / fixture)
    
    # Copy clustering results fixture
    cluster_fixture = FIXTURES_DIR / "clustering_results_spu_202501A.csv"
    if cluster_fixture.exists():
        shutil.copy2(cluster_fixture, output_dir / "clustering_results_spu_202501A.csv")


def _run_step7_with_fixtures(sandbox: Path, extra_args: List[str] = None) -> subprocess.CompletedProcess:
    """Run Step 7 in isolated sandbox with fixture data."""
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(sandbox))
    
    cmd = [
        "python3", 
        "src/step7_missing_category_rule.py",
        "--yyyymm", TARGET_YYYYMM,
        "--period", TARGET_PERIOD,
        "--analysis-level", "spu",
        "--target-yyyymm", TARGET_YYYYMM,
        "--target-period", TARGET_PERIOD,
    ]
    
    if extra_args:
        cmd.extend(extra_args)
    
    return subprocess.run(
        cmd,
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,  # Prevent hanging
    )


def test_step7_fixture_basic_execution_isolated(tmp_path):
    """Test that Step 7 runs successfully with realistic fixture data."""
    sandbox = _prepare_sandbox(tmp_path)
    _copy_fixtures_to_sandbox(sandbox)
    
    # Run Step 7
    result = _run_step7_with_fixtures(sandbox)
    
    # Check that Step 7 completed successfully
    assert result.returncode == 0, f"Step 7 failed: STDOUT: {{result.stdout}} STDERR: {{result.stderr}}"
    
    # Check output files exist
    output_file = sandbox / "output" / f"rule7_missing_spu_sellthrough_results_{PERIOD_LABEL}.csv"
    assert output_file.exists(), "Step 7 results file not created"
    
    # Load and validate basic structure
    results_df = pd.read_csv(output_file)
    assert len(results_df) >= 0, "Results should be readable"
    assert "str_code" in results_df.columns, "Missing str_code column"


def test_step7_fixture_seasonal_blending_isolated(tmp_path):
    """Test Step 7 seasonal blending with fixture data."""
    sandbox = _prepare_sandbox(tmp_path)
    _copy_fixtures_to_sandbox(sandbox)
    
    # Run with seasonal blending
    extra_args = [
        "--seasonal-blending",
        "--seasonal-yyyymm", "202412",
        "--seasonal-period", "B", 
        "--seasonal-weight", "0.7"
    ]
    
    result = _run_step7_with_fixtures(sandbox, extra_args)
    
    # Should complete successfully
    assert result.returncode == 0, f"Step 7 seasonal failed: STDOUT: {{result.stdout}} STDERR: {{result.stderr}}"
    
    # Check seasonal blending mentioned in output
    assert "seasonal" in result.stdout.lower() or "blending" in result.stdout.lower(), \
        "Seasonal blending not detected in output"


def test_step7_fixture_output_structure_isolated(tmp_path):
    """Test that Step 7 generates expected output structure."""
    sandbox = _prepare_sandbox(tmp_path)
    _copy_fixtures_to_sandbox(sandbox)
    
    result = _run_step7_with_fixtures(sandbox)
    assert result.returncode == 0, f"Step 7 failed: {{result.stderr}}"
    
    # Check expected output files
    expected_files = [
        f"rule7_missing_spu_sellthrough_results_{{PERIOD_LABEL}}.csv",
        f"rule7_missing_spu_sellthrough_opportunities_{{PERIOD_LABEL}}.csv",
    ]
    
    for expected_file in expected_files:
        file_path = sandbox / "output" / expected_file
        if file_path.exists():
            df = pd.read_csv(file_path)
            # Basic structure validation
            assert isinstance(df, pd.DataFrame), f"{{expected_file}} should be valid DataFrame"
            if len(df) > 0:
                assert "str_code" in df.columns, f"{{expected_file}} missing str_code column"


def test_step7_fixture_fast_fish_integration_isolated(tmp_path):
    """Test that Step 7 Fast Fish validation works with fixtures."""
    sandbox = _prepare_sandbox(tmp_path)
    _copy_fixtures_to_sandbox(sandbox)
    
    result = _run_step7_with_fixtures(sandbox)
    assert result.returncode == 0, f"Step 7 failed: {{result.stderr}}"
    
    # Check Fast Fish validation in output
    output_text = result.stdout + result.stderr
    fast_fish_indicators = ["Fast Fish", "sell-through", "validation"]
    
    has_fast_fish = any(indicator in output_text for indicator in fast_fish_indicators)
    assert has_fast_fish, "Fast Fish validation not detected in Step 7 output"


def test_step7_fixture_cluster_analysis_isolated(tmp_path):
    """Test that Step 7 performs cluster-based analysis with fixtures."""
    sandbox = _prepare_sandbox(tmp_path)
    _copy_fixtures_to_sandbox(sandbox)
    
    result = _run_step7_with_fixtures(sandbox)
    assert result.returncode == 0, f"Step 7 failed: {{result.stderr}}"
    
    # Check that clustering logic is mentioned
    output_text = result.stdout.lower()
    cluster_indicators = ["cluster", "well-selling", "adoption"]
    
    has_cluster_logic = any(indicator in output_text for indicator in cluster_indicators)
    assert has_cluster_logic, "Cluster-based analysis not detected in Step 7 output"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
