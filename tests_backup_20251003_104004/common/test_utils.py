"""
Test utilities and helpers.

This module provides common test utilities and helper functions that can be used
across different test modules.
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import pytest

from . import data_validators

class TestDataManager:
    """Helper class for managing test data files."""
    
    def __init__(self, test_data_dir: Union[str, Path]):
        """Initialize with the test data directory."""
        self.test_data_dir = Path(test_data_dir)
        self.temp_dir = None
        
    def __enter__(self):
        """Create a temporary directory for test data."""
        self.temp_dir = tempfile.mkdtemp(prefix='test_data_')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def get_test_data(self, filename: str) -> Path:
        """Get the path to a test data file.
        
        Args:
            filename: Name of the test data file
            
        Returns:
            Path to the test data file
            
        Raises:
            FileNotFoundError: If the test data file doesn't exist
        """
        path = self.test_data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Test data file not found: {path}")
        return path
    
    def create_temp_copy(self, source_filename: str, dest_filename: Optional[str] = None) -> Path:
        """Create a temporary copy of a test data file.
        
        Args:
            source_filename: Name of the source test data file
            dest_filename: Optional destination filename (defaults to source filename)
            
        Returns:
            Path to the temporary copy
        """
        if not self.temp_dir:
            raise RuntimeError("TestDataManager must be used as a context manager")
            
        source_path = self.get_test_data(source_filename)
        dest_path = Path(self.temp_dir) / (dest_filename or source_filename)
        
        # Create parent directories if they don't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source_path, dest_path)
        return dest_path


def assert_dataframe_equals(actual: pd.DataFrame, expected: pd.DataFrame, **kwargs) -> None:
    """Assert that two DataFrames are equal, with helpful error messages.
    
    Args:
        actual: The actual DataFrame
        expected: The expected DataFrame
        **kwargs: Additional arguments to pass to pandas.testing.assert_frame_equal
    """
    pd.testing.assert_frame_equal(
        actual.reset_index(drop=True).sort_index(axis=1),
        expected.reset_index(drop=True).sort_index(axis=1),
        check_dtype=False,
        **kwargs
    )


def validate_test_data(data: pd.DataFrame, schema: Dict[str, Dict[str, Any]]) -> None:
    """Validate test data against a schema.
    
    Args:
        data: The test data to validate
        schema: Schema definition (see data_validators.validate_dataframe_against_schema)
        
    Raises:
        AssertionError: If validation fails
    """
    errors = data_validators.validate_dataframe_against_schema(data, schema)
    if errors:
        error_msg = "\n".join(["Test data validation failed:"] + [f"- {error}" for error in errors])
        raise AssertionError(error_msg)


# Common pytest fixtures
@pytest.fixture
def test_data_manager():
    """Fixture that provides a TestDataManager instance."""
    # This will be overridden by conftest.py in each test directory
    return TestDataManager(Path(__file__).parent / 'test_data')


@pytest.fixture
def temp_dir():
    """Fixture that provides a temporary directory that's cleaned up after the test."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
