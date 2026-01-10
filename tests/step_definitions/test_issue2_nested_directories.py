"""
pytest-bdd tests for Issue #2: No Nested Directory Structure

This module implements the scenarios from issue-2-nested-directory-structure.feature
using pytest-bdd framework.

Author: Data Pipeline Team
Date: 2025-10-28
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from pytest_bdd import scenarios, given, when, then, parsers

from core.logger import PipelineLogger
from repositories.weather_file_repository import WeatherFileRepository

# Load all scenarios from the feature file
scenarios('../features/issue-2-nested-directory-structure.feature')


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_context():
    """Shared test context for storing state between steps."""
    return {}


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def logger():
    """Create a test logger."""
    return PipelineLogger("TestNestedDirectories")


# ============================================================================
# Scenario: Repository should not create nested weather_data directories
# ============================================================================

@given(parsers.parse('the factory passes output_dir as "{output_dir}"'))
def set_output_dir(test_context, temp_dir, output_dir):
    # Create the full path in temp directory
    full_path = Path(temp_dir) / output_dir
    test_context['output_dir'] = str(full_path)


@when('I initialize the WeatherFileRepository with this output_dir')
def initialize_repository(test_context, logger):
    output_dir = test_context['output_dir']
    repo = WeatherFileRepository(
        output_dir=output_dir,
        logger=logger
    )
    test_context['repository'] = repo


@then("the repository's weather_dir should equal the output_dir")
def verify_weather_dir_equals_output_dir(test_context):
    repo = test_context['repository']
    output_dir = Path(test_context['output_dir'])
    assert repo.weather_dir == output_dir, \
        f"weather_dir {repo.weather_dir} should equal output_dir {output_dir}"


@then('the repository should NOT create a nested "weather_data" folder')
def verify_no_nested_folder(test_context):
    repo = test_context['repository']
    output_dir = Path(test_context['output_dir'])
    nested_dir = output_dir / "weather_data"
    assert not nested_dir.exists(), \
        f"Nested directory should NOT exist: {nested_dir}"


@then(parsers.parse('the path should be "{expected_path}" not "{wrong_path}"'))
def verify_correct_path(test_context, expected_path, wrong_path):
    repo = test_context['repository']
    # Check that weather_dir ends with expected_path
    assert str(repo.weather_dir).endswith(expected_path), \
        f"Path should end with {expected_path}, got {repo.weather_dir}"
    # Check that it doesn't end with wrong_path
    assert not str(repo.weather_dir).endswith(wrong_path), \
        f"Path should NOT end with {wrong_path}"


# ============================================================================
# Scenario: Files should be saved to correct location without nesting
# ============================================================================

@given(parsers.parse('a WeatherFileRepository initialized with output_dir "{output_dir}"'))
def setup_repository(test_context, temp_dir, logger, output_dir):
    full_path = Path(temp_dir) / output_dir
    repo = WeatherFileRepository(
        output_dir=str(full_path),
        logger=logger
    )
    test_context['repository'] = repo
    test_context['output_dir'] = str(full_path)


@given(parsers.parse('I have weather data for store "{store_code}" at coordinates ({longitude:f}, {latitude:f})'))
def setup_weather_data(test_context, store_code, longitude, latitude):
    weather_df = pd.DataFrame({
        'time': ['2025-08-01 00:00:00'],
        'temperature_2m': [25.0],
        'relative_humidity_2m': [60.0],
        'wind_speed_10m': [5.0],
        'pressure_msl': [1013.0],
        'terrestrial_radiation': [100.0]
    })
    
    test_context['weather_df'] = weather_df
    test_context['store_code'] = store_code
    test_context['longitude'] = longitude
    test_context['latitude'] = latitude


@given(parsers.parse('the period label is "{period_label}"'))
def set_period_label(test_context, period_label):
    test_context['period_label'] = period_label


@when('I save the weather file')
def save_weather_file(test_context):
    repo = test_context['repository']
    repo.save_weather_file(
        weather_df=test_context['weather_df'],
        store_code=test_context['store_code'],
        latitude=test_context['latitude'],
        longitude=test_context['longitude'],
        period_label=test_context['period_label']
    )
    test_context['file_saved'] = True


@then(parsers.parse('the file should be saved to "{expected_path}"'))
def verify_file_location(test_context, expected_path):
    output_dir = Path(test_context['output_dir'])
    # Construct expected filename
    store_code = test_context['store_code']
    longitude = test_context['longitude']
    latitude = test_context['latitude']
    period_label = test_context['period_label']
    
    expected_file = output_dir / f"weather_data_{store_code}_{longitude}_{latitude}_{period_label}.csv"
    assert expected_file.exists(), \
        f"File should exist at {expected_file}"
    
    test_context['saved_file'] = expected_file


@then(parsers.parse('the file should NOT be saved to "{wrong_path}"'))
def verify_not_in_wrong_location(test_context, wrong_path):
    output_dir = Path(test_context['output_dir'])
    # Check for nested directory
    nested_dir = output_dir / "weather_data"
    if nested_dir.exists():
        files_in_nested = list(nested_dir.glob("*.csv"))
        assert len(files_in_nested) == 0, \
            f"Files should NOT be in nested location: {nested_dir}"


@then('no nested "weather_data" subdirectory should exist')
def verify_no_nested_subdirectory(test_context):
    output_dir = Path(test_context['output_dir'])
    nested_dir = output_dir / "weather_data"
    assert not nested_dir.exists(), \
        f"Nested subdirectory should NOT exist: {nested_dir}"


# ============================================================================
# Scenario: Directory structure should be flat
# ============================================================================

@when(parsers.parse('I save weather files for {count:d} different stores'))
def save_multiple_files(test_context, count):
    repo = test_context['repository']
    
    weather_df = pd.DataFrame({
        'time': ['2025-08-01 00:00:00'],
        'temperature_2m': [25.0],
        'relative_humidity_2m': [60.0],
        'wind_speed_10m': [5.0],
        'pressure_msl': [1013.0],
        'terrestrial_radiation': [100.0]
    })
    
    stores = [
        ("11014", 39.835836, 116.289163),
        ("11041", 39.698799, 115.984970),
        ("11050", 40.123456, 116.456789)
    ]
    
    for i in range(min(count, len(stores))):
        store_code, lat, lon = stores[i]
        repo.save_weather_file(
            weather_df=weather_df,
            store_code=store_code,
            latitude=lat,
            longitude=lon,
            period_label="20250801_to_20250815"
        )
    
    test_context['files_saved'] = count


@then(parsers.parse('all files should be in "{directory}" directory'))
def verify_all_files_in_directory(test_context, directory):
    output_dir = Path(test_context['output_dir'])
    files = list(output_dir.glob("weather_data_*.csv"))
    count = test_context.get('files_saved', 0)
    assert len(files) == count, \
        f"Should have {count} files in {output_dir}, found {len(files)}"


@then(parsers.parse('no subdirectories should exist in "{directory}"'))
def verify_no_subdirectories(test_context, directory):
    output_dir = Path(test_context['output_dir'])
    subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
    assert len(subdirs) == 0, \
        f"No subdirectories should exist in {output_dir}, found: {subdirs}"


@then('the directory structure should be flat')
def verify_flat_structure(test_context):
    output_dir = Path(test_context['output_dir'])
    # Check no subdirectories
    subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
    assert len(subdirs) == 0, \
        f"Directory structure should be flat, found subdirectories: {subdirs}"


# ============================================================================
# Scenario: Repository initialization should use output_dir directly
# ============================================================================

@then('the repository should use the path exactly as provided')
def verify_path_used_exactly(test_context):
    repo = test_context['repository']
    output_dir = Path(test_context['output_dir'])
    assert repo.output_dir == output_dir, \
        f"Repository should use path exactly as provided: {output_dir}"


@then('the repository should NOT modify or extend the path')
def verify_path_not_modified(test_context):
    repo = test_context['repository']
    # weather_dir should equal output_dir (not extended)
    assert repo.weather_dir == repo.output_dir, \
        "Repository should NOT modify the path"


@then('the repository should NOT add additional directory levels')
def verify_no_additional_levels(test_context):
    repo = test_context['repository']
    # Check that weather_dir doesn't have more path components than output_dir
    weather_parts = repo.weather_dir.parts
    output_parts = repo.output_dir.parts
    assert len(weather_parts) == len(output_parts), \
        f"Should not add directory levels: {weather_parts} vs {output_parts}"


# ============================================================================
# Regression Test Scenarios
# ============================================================================

@then(parsers.parse('the buggy nested directory "{nested_path}" should NOT exist'))
def verify_buggy_path_not_exists(test_context, nested_path):
    output_dir = Path(test_context['output_dir'])
    # Extract the nested part (e.g., "weather_data" from full path)
    nested_dir = output_dir / "weather_data"
    assert not nested_dir.exists(), \
        f"Buggy nested directory should NOT exist: {nested_dir}"


@then('weather_dir should equal output_dir')
def verify_dirs_equal(test_context):
    repo = test_context['repository']
    assert repo.weather_dir == repo.output_dir, \
        f"weather_dir {repo.weather_dir} should equal output_dir {repo.output_dir}"


@then(parsers.parse('the file should exist at "{expected_pattern}"'))
def verify_file_exists_at_pattern(test_context, expected_pattern):
    output_dir = Path(test_context['output_dir'])
    # Find files matching pattern
    files = list(output_dir.glob("weather_data_*.csv"))
    assert len(files) > 0, \
        f"Should find files matching pattern in {output_dir}"
    test_context['found_files'] = files


@then(parsers.parse('the file should NOT exist at "{wrong_pattern}"'))
def verify_file_not_at_wrong_pattern(test_context, wrong_pattern):
    output_dir = Path(test_context['output_dir'])
    nested_dir = output_dir / "weather_data"
    if nested_dir.exists():
        files = list(nested_dir.glob("weather_data_*.csv"))
        assert len(files) == 0, \
            f"Files should NOT exist in nested location: {nested_dir}"


@then('the buggy nested location should NOT contain any files')
def verify_no_files_in_buggy_location(test_context):
    output_dir = Path(test_context['output_dir'])
    nested_dir = output_dir / "weather_data"
    if nested_dir.exists():
        files = list(nested_dir.glob("*.csv"))
        assert len(files) == 0, \
            f"Buggy nested location should NOT contain files: {nested_dir}"
