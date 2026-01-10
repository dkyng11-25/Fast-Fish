"""
Pytest configuration and shared fixtures for Step 13 isolated tests.

This module provides shared fixtures that create complete synthetic test environments
for Step 13 testing. All isolated tests should use these fixtures to ensure consistency.
"""

import os
import sys
import shutil
from pathlib import Path
import pytest

# Add the isolated test directory to path so we can import fixtures
_test_dir = Path(__file__).parent
if str(_test_dir) not in sys.path:
    sys.path.insert(0, str(_test_dir))

from fixtures import create_complete_step13_fixtures


@pytest.fixture
def step13_sandbox(tmp_path):
    """
    Create a complete isolated sandbox for Step 13 testing.
    
    This fixture:
    1. Copies the src/ directory to a temporary location
    2. Creates stub pipeline_manifest.py to avoid dependencies
    3. Creates complete synthetic fixtures (clustering, sales, rules)
    4. Returns the sandbox path
    
    The sandbox is automatically cleaned up after the test.
    
    Usage:
        def test_something(step13_sandbox):
            # step13_sandbox is a Path to the sandbox directory
            # All fixtures are already created
            # Run Step 13 or load outputs
            pass
    """
    # Get project root
    project_root = Path(__file__).resolve().parents[3]
    src_root = project_root / "src"
    
    # Create sandbox
    sandbox = tmp_path / "sandbox"
    src_target = sandbox / "src"
    shutil.copytree(src_root, src_target)
    
    # Create stub pipeline_manifest.py to avoid dependencies
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
    
    # Create output and data directories
    (sandbox / "output").mkdir(parents=True)
    (sandbox / "data" / "api_data").mkdir(parents=True)
    
    # Create complete synthetic fixtures
    create_complete_step13_fixtures(sandbox, "202510A")
    
    return sandbox


@pytest.fixture(scope="session")
def step13_real_outputs():
    """
    Provide paths to real Step 13 outputs for integration tests.
    
    This fixture does NOT run Step 13 - it assumes Step 13 has already been run
    and just provides the paths to the output files.
    
    Returns:
        dict: Paths to output files
    """
    project_root = Path(__file__).resolve().parents[3]
    
    return {
        "detailed": project_root / "output" / "consolidated_spu_rule_results_detailed_202510A.csv",
        "store": project_root / "output" / "consolidated_spu_rule_results.csv",
        "cluster": project_root / "output" / "consolidated_cluster_subcategory_results.csv",
    }


def pytest_configure(config):
    """
    Pytest hook to configure test environment.
    
    This sets environment variables before any tests run to ensure
    consistent period configuration across all tests.
    """
    # Set default test period if not already set
    if "PIPELINE_TARGET_YYYYMM" not in os.environ:
        os.environ["PIPELINE_TARGET_YYYYMM"] = "202510"
    if "PIPELINE_TARGET_PERIOD" not in os.environ:
        os.environ["PIPELINE_TARGET_PERIOD"] = "A"
