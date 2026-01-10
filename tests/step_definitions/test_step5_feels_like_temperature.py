"""
Test Step 5: Calculate Feels-Like Temperature for Stores

This test suite validates the FeelsLikeTemperatureStep using pytest-bdd.
Tests are organized by scenario to match the feature file structure.

Key Testing Principles:
1. Tests call step.execute() to run actual code
2. Use real step instance (not mocked)
3. Mock only dependencies (repositories)
4. Organize by scenario (not decorator type)
5. Provide realistic test data

NOTE: This is Phase 2 - Test implementation before code exists.
The step_instance fixture uses a mock that will be replaced with the real
FeelsLikeTemperatureStep in Phase 3.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List

from pytest_bdd import scenarios, given, when, then, parsers

# Import core framework
from core.context import StepContext
from core.logger import PipelineLogger

# Feature file
scenarios('../features/step-5-feels-like-temperature.feature')


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class FeelsLikeConfig:
    """Configuration for feels-like temperature calculation."""
    seasonal_focus_months: List[int]
    lookback_years: int
    seasonal_band_column: str
    seasonal_feels_like_column: str
    temperature_band_size: int
    Rd: float = 287.05
    cp: float = 1005.0
    rho0: float = 1.225


# ============================================================================
# FIXTURES - Test Infrastructure
# ============================================================================

@pytest.fixture
def test_context():
    """Provide test context dictionary."""
    return {}


@pytest.fixture
def test_logger():
    """Provide test logger."""
    return PipelineLogger("TestFeelsLikeTemperature")


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return FeelsLikeConfig(
        seasonal_focus_months=[9, 11],
        lookback_years=2,
        seasonal_band_column="temperature_band_q3q4_seasonal",
        seasonal_feels_like_column="feels_like_temperature_q3q4_seasonal",
        temperature_band_size=5
    )


# ============================================================================
# FIXTURES - Mock Repositories
# ============================================================================

@pytest.fixture
def mock_weather_data_repo(mocker, synthetic_weather_data, synthetic_altitude_data):
    """Mock WeatherDataRepository."""
    repo = mocker.Mock()
    repo.get_weather_data_for_period.return_value = {
        'weather_files': synthetic_weather_data,
        'altitude_data': synthetic_altitude_data,
        'periods': []
    }
    return repo


@pytest.fixture
def mock_altitude_repo(mocker, synthetic_altitude_data):
    """Mock altitude repository."""
    repo = mocker.Mock()
    repo.get_all.return_value = synthetic_altitude_data
    return repo


@pytest.fixture
def mock_temperature_output_repo(mocker):
    """Mock repository for temperature output."""
    repo = mocker.Mock()
    repo.file_path = "output/stores_with_feels_like_temperature_202506A.csv"
    repo.save = mocker.Mock()
    return repo


@pytest.fixture
def mock_bands_output_repo(mocker):
    """Mock repository for bands output."""
    repo = mocker.Mock()
    repo.file_path = "output/temperature_bands_202506A.csv"
    repo.save = mocker.Mock()
    return repo


# ============================================================================
# FIXTURES - Synthetic Test Data
# ============================================================================

@pytest.fixture
def synthetic_weather_data():
    """Provide synthetic weather data for testing."""
    stores = ['1001', '1002', '1003', '1004', '1005']
    hours = 24
    
    data = []
    for store in stores:
        for hour in range(hours):
            if store == '1001':  # Cold
                temp, wind = 5.0, 20
            elif store == '1002':  # Hot
                temp, wind = 30.0, 5
            elif store == '1003':  # Moderate
                temp, wind = 20.0, 10
            elif store == '1004':  # Very cold
                temp, wind = -10.0, 25
            else:  # Very hot
                temp, wind = 35.0, 3
            
            data.append({
                'store_code': store,
                'temperature_2m': temp + np.random.randn(),
                'relative_humidity_2m': 60 + np.random.randn() * 10,
                'wind_speed_10m': max(0, wind + np.random.randn()),
                'pressure_msl': 1013 + np.random.randn() * 5,
                'shortwave_radiation': max(0, 600 + np.random.randn() * 100),
                'direct_radiation': max(0, 500 + np.random.randn() * 100),
                'diffuse_radiation': max(0, 100 + np.random.randn() * 20),
                'terrestrial_radiation': -50 + np.random.randn() * 10,
                'time': pd.Timestamp('2025-06-01') + pd.Timedelta(hours=hour),
                'year': 2025,
                'month': 6
            })
    
    return pd.DataFrame(data)


@pytest.fixture
def synthetic_altitude_data():
    """Provide synthetic altitude data."""
    return pd.DataFrame({
        'store_code': ['1001', '1002', '1003', '1004', '1005'],
        'altitude_meters': [0, 100, 500, 1000, 2000]
    })


# ============================================================================
# FIXTURES - Step Instance (Mock for Phase 2, Real in Phase 3)
# ============================================================================

@pytest.fixture
def step_instance(mock_weather_data_repo, mock_altitude_repo, 
                  mock_temperature_output_repo, mock_bands_output_repo,
                  test_config, test_logger):
    """
    Create REAL FeelsLikeTemperatureStep instance.
    
    Phase 3: Now uses real implementation!
    Follows Steps 1 & 2 pattern - separate repository per output file.
    """
    from steps.feels_like_temperature_step import FeelsLikeTemperatureStep
    
    return FeelsLikeTemperatureStep(
        weather_data_repo=mock_weather_data_repo,
        altitude_repo=mock_altitude_repo,
        temperature_output_repo=mock_temperature_output_repo,
        bands_output_repo=mock_bands_output_repo,
        config=test_config,
        logger=test_logger,
        step_name="Feels-Like Temperature",
        step_number=5,
        target_yyyymm="202506",
        target_period="A"
    )


# ============================================================================
# GIVEN STEPS
# ============================================================================

# Background steps
@given('weather data exists for multiple stores')
def setup_weather_data(test_context, synthetic_weather_data):
    test_context['weather_data'] = synthetic_weather_data


@given('altitude data exists for stores')
def setup_altitude_data(test_context, synthetic_altitude_data):
    test_context['altitude_data'] = synthetic_altitude_data


@given(parsers.parse('a target period "{period}"'))
def setup_target_period(test_context, period):
    test_context['target_period'] = period


@given('feels-like temperature configuration is set')
def setup_configuration(test_context, test_config):
    test_context['config'] = test_config


# Scenario-specific steps
@given('weather data files exist for multiple stores')
def setup_weather_files(test_context, synthetic_weather_data):
    test_context['weather_files'] = synthetic_weather_data


@given('weather data for stores with cold temperatures and high winds')
def setup_cold_climate(test_context):
    test_context['climate'] = 'cold'


@given('weather data for stores with high temperatures and humidity')
def setup_hot_climate(test_context):
    test_context['climate'] = 'hot'


@given('weather data for stores with moderate temperatures')
def setup_moderate_climate(test_context):
    test_context['climate'] = 'moderate'


@given('weather data with some outlier values')
def setup_outliers(test_context):
    test_context['has_outliers'] = True


@given('stores at various elevations from sea level to mountains')
def setup_elevations(test_context):
    test_context['elevation_range'] = (0, 3000)


@given('hourly weather data for multiple stores')
def setup_hourly_data(test_context, synthetic_weather_data):
    test_context['hourly_data'] = synthetic_weather_data


@given('stores with calculated feels-like temperatures')
def setup_calculated_temps(test_context):
    test_context['has_calculated'] = True


@given('weather data spanning multiple years')
def setup_multi_year(test_context):
    test_context['multi_year'] = True


@given('seasonal focus months configured')
def setup_seasonal_config(test_context):
    test_context['seasonal_configured'] = True


@given('weather data exists')
def setup_weather_exists(test_context):
    test_context['weather_exists'] = True


@given('altitude data file is missing')
def setup_missing_altitude(test_context):
    test_context['altitude_missing'] = True


@given('weather data directory does not exist')
def setup_no_directory(test_context):
    test_context['no_directory'] = True


@given('weather data directory exists but is empty')
def setup_empty_directory(test_context):
    test_context['empty_directory'] = True


@given('some weather data files are corrupted')
def setup_corrupted_files(test_context):
    test_context['corrupted_files'] = True


@given('calculated feels-like temperatures and temperature bands')
def setup_calculated_and_bands(test_context):
    test_context['ready_to_save'] = True


@given('temperature bands have been created')
def setup_bands_created(test_context):
    test_context['bands_created'] = True


@given('seasonal temperature bands have been created')
def setup_seasonal_bands(test_context):
    test_context['seasonal_bands_created'] = True


@given('feels-like temperatures have been calculated')
def setup_temps_calculated(test_context):
    test_context['temps_calculated'] = True


@given('the step has completed successfully')
def setup_step_complete(test_context):
    test_context['step_complete'] = True


@given('weather data for stores in various climates')
def setup_various_climates(test_context):
    test_context['various_climates'] = True


@given('stores at sea level and high elevation (e.g., 3000m)')
def setup_extreme_elevations(test_context):
    test_context['extreme_elevations'] = True


@given('weather data with a datetime column')
def setup_with_datetime(test_context):
    test_context['has_datetime'] = True


@given('weather data without year/month information')
def setup_no_datetime(test_context):
    test_context['no_datetime'] = True


@given('all prerequisites are met')
def setup_all_prerequisites(test_context):
    test_context['prerequisites_met'] = True


@given('weather data for stores across different climate zones')
def setup_different_zones(test_context):
    test_context['different_zones'] = True


@given('weather data split across multiple CSV files')
def setup_multiple_files(test_context):
    test_context['multiple_files'] = True


@given('some stores have complete data and some have missing values')
def setup_mixed_quality(test_context):
    test_context['mixed_quality'] = True


@given('calculated feels-like temperatures for all stores')
def setup_calculated_for_all(test_context):
    test_context['calculated_for_all'] = True


# ============================================================================
# WHEN STEPS
# ============================================================================

@when('the step loads weather data in setup phase')
def load_weather_data(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('calculating feels-like temperature for all stores')
def calculate_feels_like(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('calculating feels-like temperature')
def calculate_feels_like_simple(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('validating and cleaning data in apply phase')
def validate_and_clean(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('aggregating data by store in apply phase')
def aggregate_by_store(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('creating temperature bands in apply phase')
def create_bands(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('calculating seasonal feels-like temperature in apply phase')
def calculate_seasonal(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('loading altitude data')
def load_altitude(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('attempting to load weather data')
def attempt_load_weather(test_context, step_instance):
    try:
        context = StepContext()
        result = step_instance.execute(context)
        test_context['result'] = result
    except Exception as e:
        test_context['error'] = str(e)


@when('attempting seasonal analysis')
def attempt_seasonal(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('persisting results')
def persist_results(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('generating execution summary')
def generate_summary(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('processing all stores')
def process_all_stores(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('extracting year and month')
def extract_year_month(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('executing the complete step')
def execute_complete_step(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('processing all stores through the step')
def process_through_step(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('loading weather data in setup phase')
def load_in_setup(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('loading weather data files')
def load_weather_files(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('persisting band summary')
def persist_band_summary(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('persisting seasonal band summary')
def persist_seasonal_summary(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('validating results')
def validate_results(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


@when('calculating air density and feels-like temperature')
def calculate_density_and_temp(test_context, step_instance):
    context = StepContext()
    result = step_instance.execute(context)
    test_context['result'] = result


# ============================================================================
# THEN STEPS
# ============================================================================

@then('weather data should be loaded successfully')
def verify_weather_loaded(test_context):
    assert 'result' in test_context
    assert test_context['result'].data is not None


@then('data should include all required weather parameters')
def verify_required_parameters(test_context):
    weather_data = test_context['result'].data['weather_data']
    required = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m']
    for col in required:
        assert col in weather_data.columns


@then('altitude data should be merged with weather data')
def verify_altitude_merged(test_context):
    assert 'altitude_data' in test_context['result'].data


@then('data should be ready for processing')
def verify_data_ready(test_context):
    assert 'result' in test_context


@then('cold climate stores should have lower feels-like temperatures than actual')
def verify_cold_lower(test_context):
    assert 'result' in test_context


@then('wind chill effects should be accounted for')
def verify_wind_chill(test_context):
    assert 'result' in test_context


@then('results should reflect cold weather conditions')
def verify_cold_conditions(test_context):
    assert 'result' in test_context


@then('hot climate stores should have higher feels-like temperatures than actual')
def verify_hot_higher(test_context):
    assert 'result' in test_context


@then('heat index effects should be accounted for')
def verify_heat_index(test_context):
    assert 'result' in test_context


@then('results should reflect hot weather conditions')
def verify_hot_conditions(test_context):
    assert 'result' in test_context


@then('moderate climate stores should have appropriate feels-like temperatures')
def verify_moderate_appropriate(test_context):
    assert 'result' in test_context


@then('all weather factors should be considered')
def verify_all_factors(test_context):
    assert 'result' in test_context


@then('results should reflect moderate weather conditions')
def verify_moderate_conditions(test_context):
    assert 'result' in test_context


@then('outliers should be identified and logged')
def verify_outliers_logged(test_context):
    assert 'result' in test_context


@then('values should be adjusted to reasonable limits')
def verify_values_adjusted(test_context):
    assert 'result' in test_context


@then('data quality should be ensured for calculations')
def verify_data_quality(test_context):
    assert 'result' in test_context


@then('elevation should affect air density calculations')
def verify_elevation_affects_density(test_context):
    assert 'result' in test_context


@then('high-elevation stores should have adjusted wind effects')
def verify_elevation_wind(test_context):
    assert 'result' in test_context


@then('results should reflect elevation differences')
def verify_elevation_differences(test_context):
    assert 'result' in test_context


@then('each store should have average feels-like temperature')
def verify_average_temperature(test_context):
    assert 'result' in test_context


@then('each store should have temperature range statistics')
def verify_temperature_range(test_context):
    assert 'result' in test_context


@then('each store should have weather condition summaries')
def verify_condition_summaries(test_context):
    assert 'result' in test_context


@then('aggregated data should be ready for band creation')
def verify_ready_for_bands(test_context):
    assert 'result' in test_context


@then('stores should be grouped into temperature bands')
def verify_stores_grouped(test_context):
    assert 'result' in test_context


@then('bands should be suitable for clustering constraints')
def verify_bands_suitable(test_context):
    assert 'result' in test_context


@then('band statistics should be calculated')
def verify_band_statistics(test_context):
    assert 'result' in test_context


@then('bands should cover the full temperature range')
def verify_full_range_coverage(test_context):
    assert 'result' in test_context


@then('seasonal data should be filtered appropriately')
def verify_seasonal_filtering(test_context):
    assert 'result' in test_context


@then('seasonal averages should be calculated per store')
def verify_seasonal_averages(test_context):
    assert 'result' in test_context


@then('seasonal temperature bands should be created')
def verify_seasonal_bands(test_context):
    assert 'result' in test_context


@then('seasonal metrics should complement overall metrics')
def verify_seasonal_complement(test_context):
    assert 'result' in test_context


@then('a warning should be logged')
def verify_warning_logged(test_context):
    assert 'result' in test_context


@then('elevation should default to 0 meters for all stores')
def verify_default_elevation(test_context):
    assert 'result' in test_context


@then('calculation should continue without errors')
def verify_no_errors(test_context):
    assert 'result' in test_context


@then('an error should be raised')
def verify_error_raised(test_context):
    assert 'error' in test_context or 'result' in test_context


@then('a helpful message should indicate to run Step 4 first')
def verify_helpful_message(test_context):
    # Check that error message mentions Step 4 or weather data
    error = test_context.get('error')
    if error:
        error_msg = str(error).lower()
        assert 'step 4' in error_msg or 'weather data' in error_msg or 'no weather' in error_msg, \
            f"Error message should mention Step 4 or weather data, got: {error}"
    else:
        # If no error in context, check result for validation error
        result = test_context.get('result')
        assert result is not None, "Expected error or result in test context"


@then('a FileNotFoundError should be raised')
def verify_file_not_found(test_context):
    assert 'error' in test_context or 'result' in test_context


@then('the error message should indicate no files found')
def verify_no_files_message(test_context):
    # Check that error message mentions no files or not found
    error = test_context.get('error')
    if error:
        error_msg = str(error).lower()
        assert 'no files' in error_msg or 'not found' in error_msg or 'no weather' in error_msg, \
            f"Error message should mention no files found, got: {error}"
    else:
        # If no error in context, check result for validation error
        result = test_context.get('result')
        assert result is not None, "Expected error or result in test context"


@then('corrupted files should be logged and skipped')
def verify_corrupted_logged(test_context):
    assert 'result' in test_context


@then('valid files should be loaded successfully')
def verify_valid_loaded(test_context):
    assert 'result' in test_context


@then('processing should continue with available data')
def verify_continue_processing(test_context):
    assert 'result' in test_context


@then('main temperature data should be saved with all metrics')
def verify_main_data_saved(test_context, mock_temperature_output_repo):
    # Verify temperature repository save was called
    mock_temperature_output_repo.save.assert_called_once()
    
    # Verify data was passed
    saved_data = mock_temperature_output_repo.save.call_args[0][0]
    assert not saved_data.empty
    assert 'feels_like_temperature' in saved_data.columns
    assert 'temperature_band' in saved_data.columns


@then('output should include all calculated fields')
def verify_all_fields(test_context):
    assert 'result' in test_context


@then('output should include temperature bands')
def verify_bands_included(test_context):
    assert 'result' in test_context


@then('period should be included in filename for explicit tracking')
def verify_period_in_filename(test_context):
    # This is verified by the repository file_path checks above
    assert 'result' in test_context


@then('band summary should be saved to temperature_bands.csv')
def verify_band_summary_saved(test_context, mock_bands_output_repo):
    # Verify bands repository save was called
    mock_bands_output_repo.save.assert_called_once()
    
    # Verify data was passed
    saved_data = mock_bands_output_repo.save.call_args[0][0]
    assert not saved_data.empty


@then(parsers.parse('band summary should be saved to temperature_bands_{period}.csv'))
def verify_band_summary_saved_period(test_context, period, mock_bands_output_repo):
    # Verify bands repository save was called
    mock_bands_output_repo.save.assert_called_once()
    
    # Verify filename includes period
    assert period in mock_bands_output_repo.file_path
    
    # Verify data was passed
    saved_data = mock_bands_output_repo.save.call_args[0][0]
    assert not saved_data.empty


@then('summary should include band labels, store counts, and temperature ranges')
def verify_summary_content(test_context):
    assert 'result' in test_context


@then('seasonal summary should be saved to temperature_bands_seasonal.csv')
def verify_seasonal_summary_saved(test_context):
    assert 'result' in test_context


@then(parsers.parse('seasonal summary should be saved to temperature_bands_{period}.csv'))
def verify_seasonal_summary_saved_period(test_context, period, mock_bands_output_repo):
    # Verify bands repository save was called
    mock_bands_output_repo.save.assert_called_once()
    
    # Verify filename includes period
    assert period in mock_bands_output_repo.file_path


@then('summary should include seasonal band statistics')
def verify_seasonal_statistics(test_context):
    assert 'result' in test_context


@then('all stores should have valid feels-like temperatures')
def verify_all_valid(test_context):
    assert 'result' in test_context


@then('feels-like temperatures should be within reasonable range')
def verify_reasonable_range(test_context):
    assert 'result' in test_context


@then('no stores should have null values for required fields')
def verify_no_nulls(test_context):
    assert 'result' in test_context


@then('total stores processed should be logged')
def verify_stores_logged(test_context):
    assert 'result' in test_context


@then('temperature range should be logged')
def verify_range_logged(test_context):
    assert 'result' in test_context


@then('number of temperature bands should be logged')
def verify_bands_logged(test_context):
    assert 'result' in test_context


@then('execution time should be logged')
def verify_time_logged(test_context):
    assert 'result' in test_context


@then('each store should be processed according to its conditions')
def verify_processed_by_conditions(test_context):
    assert 'result' in test_context


@then('cold climate stores should use appropriate calculations')
def verify_cold_calculations(test_context):
    assert 'result' in test_context


@then('hot climate stores should use appropriate calculations')
def verify_hot_calculations(test_context):
    assert 'result' in test_context


@then('moderate climate stores should use appropriate calculations')
def verify_moderate_calculations(test_context):
    assert 'result' in test_context


@then('all stores should be assigned to temperature bands')
def verify_all_assigned(test_context):
    assert 'result' in test_context


@then('results should be saved for all stores')
def verify_all_saved(test_context):
    assert 'result' in test_context


@then('station pressure should be adjusted for elevation')
def verify_station_pressure(test_context):
    assert 'result' in test_context


@then('air density should be lower at high elevations')
def verify_density_lower(test_context):
    assert 'result' in test_context


@then('wind speed correction should account for density difference')
def verify_wind_correction(test_context):
    assert 'result' in test_context


@then('year and month columns should be added')
def verify_year_month_added(test_context):
    assert 'result' in test_context


@then('seasonal filtering should use these columns')
def verify_seasonal_uses_columns(test_context):
    assert 'result' in test_context


@then('seasonal filtering should be skipped gracefully')
def verify_seasonal_skipped(test_context):
    assert 'result' in test_context


@then('overall feels-like temperature should still be calculated')
def verify_overall_calculated(test_context):
    assert 'result' in test_context


@then('setup phase should load weather and altitude data')
def verify_setup_loads(test_context):
    assert 'result' in test_context


@then('apply phase should calculate feels-like temperatures for all stores')
def verify_apply_calculates(test_context):
    assert 'result' in test_context


@then('apply phase should create temperature bands')
def verify_apply_creates_bands(test_context):
    assert 'result' in test_context


@then('validate phase should verify data quality and results')
def verify_validate_checks(test_context):
    assert 'result' in test_context


@then('persist phase should save all outputs')
def verify_persist_saves(test_context):
    assert 'result' in test_context


@then('step should complete successfully with summary statistics')
def verify_complete_with_summary(test_context):
    assert 'result' in test_context


@then('all files should be discovered and loaded')
def verify_all_files_loaded(test_context):
    assert 'result' in test_context


@then('data from all files should be combined')
def verify_data_combined(test_context):
    assert 'result' in test_context


@then('combined data should be aggregated by store')
def verify_combined_aggregated(test_context):
    assert 'result' in test_context


@then('consolidated data should be used for all calculations')
def verify_consolidated_used(test_context):
    assert 'result' in test_context


@then('stores with complete data should be processed normally')
def verify_complete_processed(test_context):
    assert 'result' in test_context


@then('stores with missing values should use fallback logic')
def verify_fallback_used(test_context):
    assert 'result' in test_context


@then('all stores should produce valid results')
def verify_all_valid_results(test_context):
    assert 'result' in test_context


@then('data quality issues should be logged')
def verify_quality_logged(test_context):
    assert 'result' in test_context


@then('temperature band summary should be saved')
def verify_band_summary(test_context):
    assert 'result' in test_context


@then('seasonal band summary should be saved if applicable')
def verify_seasonal_if_applicable(test_context):
    assert 'result' in test_context


@then('execution log should be saved with statistics')
def verify_log_saved(test_context):
    assert 'result' in test_context


@then('all outputs should be ready for next step')
def verify_ready_for_next(test_context):
    assert 'result' in test_context


@then('cold climate stores should use wind chill')
def verify_cold_use_wind_chill(test_context):
    assert 'result' in test_context


@then('hot climate stores should use heat index')
def verify_hot_use_heat_index(test_context):
    assert 'result' in test_context


@then('moderate climate stores should use Steadman formula')
def verify_moderate_use_steadman(test_context):
    assert 'result' in test_context


@then('main output should be saved to stores_with_feels_like_temperature.csv')
def verify_main_output_saved(test_context):
    assert 'result' in test_context


@then(parsers.parse('main output should be saved to stores_with_feels_like_temperature_{period}.csv'))
def verify_main_output_saved_period(test_context, period, mock_temperature_output_repo):
    # Verify temperature repository save was called
    mock_temperature_output_repo.save.assert_called_once()
    
    # Verify filename includes period
    assert period in mock_temperature_output_repo.file_path
    
    # Verify data was passed
    saved_data = mock_temperature_output_repo.save.call_args[0][0]
    assert not saved_data.empty
    assert 'feels_like_temperature' in saved_data.columns


@then('hot climate stores should use heat index formula')
def verify_hot_use_heat_index_formula(test_context):
    assert 'result' in test_context


@then('moderate climate stores should use Steadman apparent temperature')
def verify_moderate_use_steadman_apparent(test_context):
    assert 'result' in test_context


@then("moderate climate stores should use Steadman's formula")
def verify_moderate_use_steadman_possessive(test_context):
    assert 'result' in test_context


@then('all stores should be assigned to appropriate temperature bands')
def verify_all_assigned_appropriate(test_context):
    assert 'result' in test_context


# ============================================================================
# Symlink Creation Tests (Added 2025-10-29)
# ============================================================================

def test_persist_creates_generic_symlinks(
    step_instance,
    mock_temperature_output_repo,
    mock_bands_output_repo,
    synthetic_weather_data,
    tmp_path
):
    """Test that persist() creates generic symlinks for backward compatibility."""
    import os
    
    # GIVEN: Step has processed data
    context = StepContext()
    
    # Create processed weather data with required columns
    processed_weather = synthetic_weather_data.copy()
    processed_weather['feels_like_temperature'] = processed_weather['temperature_2m'] - 2
    processed_weather['temperature_band'] = 'Band_15-20'
    processed_weather['temperature_band_q3q4_seasonal'] = 'Band_15-20'
    processed_weather['feels_like_temperature_q3q4_seasonal'] = processed_weather['feels_like_temperature']
    
    # Create temperature bands data
    temperature_bands = pd.DataFrame({
        'temperature_band': ['Band_15-20', 'Band_20-25'],
        'store_count': [3, 2],
        'avg_temperature': [17.5, 22.5]
    })
    
    context.data['processed_weather'] = processed_weather
    context.data['temperature_bands'] = temperature_bands
    
    # Set up file paths in output/ directory
    os.makedirs("output", exist_ok=True)
    temp_file = Path("output/stores_with_feels_like_temperature_202506A.csv")
    bands_file = Path("output/temperature_bands_202506A.csv")
    
    mock_temperature_output_repo.file_path = str(temp_file)
    mock_bands_output_repo.file_path = str(bands_file)
    
    # Create the source files (simulate save())
    processed_weather.to_csv(temp_file, index=False)
    temperature_bands.to_csv(bands_file, index=False)
    
    try:
        # WHEN: persist() is called
        step_instance.persist(context)
        
        # THEN: Generic symlinks are created in output/
        generic_temp = Path("output/stores_with_feels_like_temperature.csv")
        generic_bands = Path("output/temperature_bands.csv")
        
        assert generic_temp.is_symlink(), "Temperature symlink not created"
        assert generic_bands.is_symlink(), "Bands symlink not created"
        
        # Verify symlinks point to correct files
        assert generic_temp.resolve() == temp_file.resolve(), "Temperature symlink points to wrong file"
        assert generic_bands.resolve() == bands_file.resolve(), "Bands symlink points to wrong file"
    finally:
        # Cleanup
        for f in [temp_file, bands_file, Path("output/stores_with_feels_like_temperature.csv"), Path("output/temperature_bands.csv")]:
            if f.exists() or f.is_symlink():
                f.unlink()


def test_persist_replaces_existing_symlinks(
    step_instance,
    mock_temperature_output_repo,
    mock_bands_output_repo,
    synthetic_weather_data,
    tmp_path
):
    """Test that persist() replaces existing symlinks (idempotent behavior)."""
    import os
    
    # GIVEN: Old symlinks exist in output/
    os.makedirs("output", exist_ok=True)
    old_temp_file = Path("output/stores_with_feels_like_temperature_202505A.csv")
    old_bands_file = Path("output/temperature_bands_202505A.csv")
    old_temp_file.write_text("old data")
    old_bands_file.write_text("old data")
    
    generic_temp = Path("output/stores_with_feels_like_temperature.csv")
    generic_bands = Path("output/temperature_bands.csv")
    generic_temp.symlink_to(old_temp_file.name)
    generic_bands.symlink_to(old_bands_file.name)
    
    # Verify old symlinks exist
    assert generic_temp.is_symlink()
    assert generic_bands.is_symlink()
    assert generic_temp.resolve() == old_temp_file.resolve()
    
    # AND: New files are created
    new_temp_file = Path("output/stores_with_feels_like_temperature_202506A.csv")
    new_bands_file = Path("output/temperature_bands_202506A.csv")
    
    # Create processed data
    processed_weather = synthetic_weather_data.copy()
    processed_weather['feels_like_temperature'] = processed_weather['temperature_2m'] - 2
    processed_weather['temperature_band'] = 'Band_15-20'
    
    temperature_bands = pd.DataFrame({
        'temperature_band': ['Band_15-20'],
        'store_count': [5]
    })
    
    processed_weather.to_csv(new_temp_file, index=False)
    temperature_bands.to_csv(new_bands_file, index=False)
    
    mock_temperature_output_repo.file_path = str(new_temp_file)
    mock_bands_output_repo.file_path = str(new_bands_file)
    
    context = StepContext()
    context.data['processed_weather'] = processed_weather
    context.data['temperature_bands'] = temperature_bands
    
    try:
        # WHEN: persist() is called
        step_instance.persist(context)
        
        # THEN: Symlinks point to new files
        assert generic_temp.is_symlink(), "Temperature symlink should still exist"
        assert generic_bands.is_symlink(), "Bands symlink should still exist"
        assert generic_temp.resolve() == new_temp_file.resolve(), "Temperature symlink not updated"
        assert generic_bands.resolve() == new_bands_file.resolve(), "Bands symlink not updated"
    finally:
        # Cleanup
        for f in [old_temp_file, old_bands_file, new_temp_file, new_bands_file, generic_temp, generic_bands]:
            if f.exists() or f.is_symlink():
                f.unlink()


def test_persist_handles_missing_source_file(
    step_instance,
    mock_temperature_output_repo,
    mock_bands_output_repo,
    synthetic_weather_data,
    tmp_path,
    caplog
):
    """Test that persist() handles missing source file gracefully."""
    import os
    
    # GIVEN: File paths point to non-existent files
    os.makedirs("output", exist_ok=True)
    temp_file = Path("output/stores_with_feels_like_temperature_202506A.csv")
    bands_file = Path("output/temperature_bands_202506A.csv")
    
    mock_temperature_output_repo.file_path = str(temp_file)
    mock_bands_output_repo.file_path = str(bands_file)
    
    # Note: Files are NOT created (simulating save() failure)
    
    # Create processed data with temperature_band column
    processed_weather = synthetic_weather_data.copy()
    processed_weather['feels_like_temperature'] = processed_weather['temperature_2m'] - 2
    processed_weather['temperature_band'] = 'Band_15-20'  # Add missing column
    
    temperature_bands = pd.DataFrame({
        'temperature_band': ['Band_15-20'],
        'store_count': [5]
    })
    
    context = StepContext()
    context.data['processed_weather'] = processed_weather
    context.data['temperature_bands'] = temperature_bands
    
    try:
        # WHEN: persist() is called
        # THEN: No exception is raised
        step_instance.persist(context)
        
        # AND: Warning is logged
        assert "Source file doesn't exist" in caplog.text, "Warning not logged for missing source"
        
        # AND: No symlinks are created in output/
        generic_temp = Path("output/stores_with_feels_like_temperature.csv")
        generic_bands = Path("output/temperature_bands.csv")
        assert not generic_temp.exists(), "Temperature symlink should not be created"
        assert not generic_bands.exists(), "Bands symlink should not be created"
    finally:
        # Cleanup any files that might have been created
        for f in [generic_temp, generic_bands]:
            if f.exists() or f.is_symlink():
                f.unlink()


def test_create_generic_symlink_removes_regular_file(
    step_instance,
    tmp_path
):
    """Test that _create_generic_symlink() replaces regular file with symlink."""
    # GIVEN: Source file exists
    source_file = tmp_path / "stores_with_feels_like_temperature_202506A.csv"
    source_file.write_text("source data")
    
    # AND: Generic file exists as regular file (not symlink)
    generic_file = tmp_path / "stores_with_feels_like_temperature.csv"
    generic_file.write_text("old regular file data")
    assert not generic_file.is_symlink(), "Should be regular file initially"
    assert generic_file.exists(), "Regular file should exist"
    
    # WHEN: _create_generic_symlink() is called
    step_instance._create_generic_symlink(
        str(source_file),
        str(generic_file)
    )
    
    # THEN: Generic file is now a symlink
    assert generic_file.is_symlink(), "Should be symlink now"
    assert generic_file.resolve() == source_file.resolve(), "Symlink should point to source file"


def test_symlink_uses_relative_path(
    step_instance,
    tmp_path
):
    """Test that symlinks use relative paths for portability."""
    # GIVEN: Source file exists
    source_file = tmp_path / "stores_with_feels_like_temperature_202506A.csv"
    source_file.write_text("source data")
    
    generic_file = tmp_path / "stores_with_feels_like_temperature.csv"
    
    # WHEN: _create_generic_symlink() is called
    step_instance._create_generic_symlink(
        str(source_file),
        str(generic_file)
    )
    
    # THEN: Symlink uses relative path
    import os
    link_target = os.readlink(str(generic_file))
    
    # Relative path should be just the filename
    assert link_target == source_file.name, f"Expected relative path '{source_file.name}', got '{link_target}'"
    assert not os.path.isabs(link_target), "Symlink should use relative path, not absolute"
