"""
Shared test fixtures and configuration for the test suite.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch
import os # Added for mock_filesystem fixture
import logging

# Add src to path to allow importing the module being tested
import sys
import importlib

# Fireducks fallback for testing - use regular pandas if fireducks not available
try:
    import fireducks.pandas
except ImportError:
    # Create a mock fireducks module that uses regular pandas
    import pandas
    sys.modules['fireducks'] = type(sys)('fireducks')
    sys.modules['fireducks'].pandas = pandas
    sys.modules['fireducks.pandas'] = pandas

# Add src to path to allow importing the module being tested
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# Import period detection utilities
from tests.utils.periods import detect_available_period, split_period_label
from tests.data_generators.period_data_manager import PeriodDataManager

def pytest_addoption(parser):
    parser.addoption(
        "--period-label", action="store", default="202508A", help="Period label for data (e.g., 202508A)"
    )

@pytest.fixture(scope="session")
def period_label(request):
    label = request.config.getoption("--period-label")
    return label

@pytest.fixture(scope="session")
def period_data_manager():
    """Period data manager for test data setup."""
    return PeriodDataManager(Path(__file__).parent.parent)

@pytest.fixture(scope="session")
def detected_period(period_data_manager):
    """Detect the best available period for testing."""
    return period_data_manager.get_best_available_period()

@pytest.fixture(scope="session")
def period_parts(detected_period):
    """Split detected period into parts."""
    if detected_period:
        return split_period_label(detected_period)
    return None

@pytest.fixture(scope="session")
def test_data_setup(period_data_manager, detected_period):
    """Ensure test data is set up for the detected period."""
    if detected_period:
        success = period_data_manager.setup_test_data_for_period(detected_period)
        if not success:
            pytest.skip(f"Could not set up test data for period {detected_period}")
    return detected_period

@pytest.fixture(autouse=True)
def mock_src_config(period_label):
    """Mock src.config functions globally for all tests that import src.config."""
    mock_config_module = MagicMock()
    
    # Set up essential config values that modules import directly
    mock_config_module.OUTPUT_DIR = "output"  # Real string, not mock
    mock_config_module.DATA_DIR = "data"
    mock_config_module.API_DATA_DIR = "data/api_data"
    
    mock_config_module.get_current_period.return_value = (period_label[:6], period_label)
    mock_config_module.get_period_label.return_value = period_label
    mock_config_module.get_api_data_files.return_value = {
        'store_config': f'data/api_data/store_config_{period_label}.csv',
        'store_sales': f'data/api_data/store_sales_{period_label}.csv',
        'category_sales': f'data/api_data/complete_category_sales_{period_label}.csv',
        'spu_sales': f'data/api_data/complete_spu_sales_{period_label}.csv',
        'processed_stores': f'data/api_data/processed_stores_{period_label}.txt',
    }
    mock_config_module.get_output_files.return_value = {
        'clustering_results': f'output/clustering_results_spu_{period_label}.csv',
        'cluster_analysis_report': f'output/cluster_analysis_report_{period_label}.md',
        'rule7_opportunities': f'output/rule7_missing_category_opportunities_{period_label}.csv',
        'rule8_opportunities': f'output/rule8_imbalanced_spu_opportunities_{period_label}.csv',
        'rule9_results': f'output/rule9_below_minimum_spu_sellthrough_results_{period_label}.csv',
        'rule10_optimization': f'output/rule10_spu_assortment_optimization_results_{period_label}.csv',
        'rule11_opportunities': f'output/rule11_missed_sales_opportunity_opportunities_{period_label}.csv',
        'rule12_results': f'output/rule12_sales_performance_rule_results_{period_label}.csv',
    }

    with patch.dict('sys.modules', {'src.config': mock_config_module}):
        # The src modules need to be reloaded after patching sys.modules to pick up the mock.
        # This is a common pattern when mocking modules that are imported early.
        # We'll reload the specific modules we care about.
        for module_name in [
            'src.step6_cluster_analysis',
            'src.step7_missing_category_rule',
            'src.step8_imbalanced_rule',
            'src.step9_below_minimum_rule',
            'src.step10_spu_assortment_optimization',
            'src.step11_missed_sales_opportunity',
            'src.step12_sales_performance_rule',
            # Add other src.stepX_... modules that import from src.config
        ]:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                # If not already imported, import it so it uses the mocked config.
                # This might not be strictly necessary if pytest-bdd imports them, but good for completeness.
                importlib.import_module(module_name)
        yield

@pytest.fixture
def mock_filesystem():
    """Mocks file system operations to control file existence and content."""
    _data = {}
    _file_contents = {}

    # Initializing mock objects without side_effect to start. Side effects will be set by patches.
    mock_exists = MagicMock()
    mock_read_csv = MagicMock(side_effect=lambda path, **kwargs: _data.get(path))
    # For DataFrame.to_csv, we need to patch the method on the class, not create a standalone mock
    mock_to_csv = MagicMock()

    def mock_open_side_effect(*args, **kwargs):
        print(f"DEBUG: mock_open_side_effect called with args={args}, kwargs={kwargs}")
        file_path = args[0] if args else kwargs.get('file')
        mode = args[1] if len(args) > 1 else kwargs.get('mode', 'r')
        encoding = kwargs.get('encoding')

        if file_path is None:
            raise ValueError("Mocked open received no file_path argument.")

        file_path = str(file_path) # Ensure path is always a string

        if 'w' in mode or 'a' in mode:
            # For write modes, capture content into _file_contents
            mock_file = MagicMock()
            def write_side_effect(content):
                _file_contents[file_path] = content
            mock_file.write.side_effect = write_side_effect
            return mock_file
        elif 'r' in mode:
            # For read modes, return content from _file_contents if available
            if file_path in _file_contents:
                mock_file = MagicMock()
                mock_file.read.return_value = _file_contents[file_path]
                return mock_file
            else:
                # Fallback to original open if not mocked
                raise FileNotFoundError(f"Mock file not found: {file_path}") # Fail fast if not mocked
        return MagicMock() # Default for other modes
    mock_open_builtin = MagicMock(side_effect=mock_open_side_effect)

    with patch('os.path.exists', mock_exists) as patched_exists, \
         patch('pandas.read_csv', mock_read_csv) as patched_read_csv, \
         patch('pandas.DataFrame.to_csv', side_effect=lambda self, *args, **kwargs: print(f"DEBUG: to_csv called with args={args}, kwargs={kwargs}") or _data.__setitem__(args[0], self.copy()) if args else None) as patched_to_csv, \
         patch('builtins.open', mock_open_builtin) as patched_open_builtin, \
         patch('os.path.isfile', side_effect=lambda path: path in _data or path in _file_contents) as patched_isfile, \
         patch('src.config.register_step_output') as mock_register_step_output: # Patch for manifest registration
        
        # Initial side effects for exists and read_csv will be set up dynamically by 'Given' steps.
        # We store the *original* functions to allow selective un-mocking or fallback if needed.
        original_exists = os.path.exists
        original_read_csv = pd.read_csv
        original_open = open

        # Set side effect for os.path.exists to check both _data (for dataframes) and _file_contents (for text files)
        patched_exists.side_effect = lambda path: (
            path in _data or path in _file_contents
        )
        
        # Mock os.path.isfile to behave similarly

        # Expose objects to allow tests to manipulate the mock state
        mock_objects = {
            "exists": patched_exists,
            "read_csv": patched_read_csv,
            "to_csv": patched_to_csv,
            "open": patched_open_builtin,
            "isfile": patched_isfile, # Expose new mock
            "_data": _data, # For dataframes
            "_file_contents": _file_contents, # For text content (e.g., markdown)
            "original_exists": original_exists,
            "original_read_csv": original_read_csv,
            "original_open": original_open,
            "register_step_output": mock_register_step_output, # Expose register_step_output mock
        }
        yield mock_objects

@pytest.fixture
def get_dataframe_from_mocked_to_csv():
    def _get_dataframe_from_mocked_to_csv(mock_filesystem, filename_substring):
        for filepath, df in mock_filesystem["_data"].items():
            if filename_substring in filepath:
                return df
        return None
    return _get_dataframe_from_mocked_to_csv

@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / 'test_data'

@pytest.fixture
def sample_cluster_data():
    """Create sample cluster data for testing."""
    return pd.DataFrame({
        'str_code': [f'store_{i:03d}' for i in range(1, 11)],
        'cluster_id': [1, 1, 1, 1, 2, 2, 2, 3, 3, 3],
        'store_name': [f'Store {i}' for i in range(1, 11)],
        'region': ['North'] * 5 + ['South'] * 5,
        'store_type': ['A', 'A', 'B', 'B', 'A', 'B', 'B', 'A', 'A', 'B']
    })

@pytest.fixture
def sample_sales_data():
    """Create sample sales data for testing."""
    # Create base sales data for 10 stores, 3 clusters, 5 categories
    stores = [f'store_{i:03d}' for i in range(1, 11)]
    categories = [f'category_{i:02d}' for i in range(1, 6)]
    
    # Generate sales data
    data = []
    for store in stores:
        for category in categories:
            # Create some missing categories for testing
            if (store == 'store_001' and category == 'category_01') or \
               (store == 'store_005' and category == 'category_03'):
                continue
                
            # Add sales data
            cluster_id = int(store.split('_')[1]) % 3 + 1
            sales = np.random.uniform(100, 1000)
            data.append({
                'str_code': store,
                'sub_cate_name': category,
                'sal_amt': sales,
                'sal_qty': int(sales / np.random.uniform(20, 100))
            })
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_quantity_data():
    """Create sample quantity data for testing."""
    return pd.DataFrame({
        'str_code': [f'store_{i:03d}' for i in range(1, 11)],
        'base_sal_qty': [100, 150, 200, 120, 180, 90, 210, 130, 170, 190],
        'fashion_sal_qty': [50, 70, 60, 80, 90, 40, 100, 60, 70, 80],
        'base_sal_amt': [1000, 1500, 2000, 1200, 1800, 900, 2100, 1300, 1700, 1900],
        'fashion_sal_amt': [500, 700, 600, 800, 900, 400, 1000, 600, 700, 800]
    })

@pytest.fixture
def sample_well_selling_features(sample_sales_data, sample_cluster_data):
    """Create sample well-selling features for testing."""
    from step7_missing_category_rule import identify_well_selling_features
    return identify_well_selling_features(
        sales_df=sample_sales_data,
        cluster_df=sample_cluster_data
    )

# Dynamic period detection fixtures
@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def detected_period(project_root):
    """Detect the best available period for testing."""
    period = detect_available_period(project_root)
    if period is None:
        pytest.skip("No valid data period found (need store_config and spu_sales files)")
    return period

@pytest.fixture(scope="session")
def period_parts(detected_period):
    """Split detected period into yyyymm and period parts."""
    return split_period_label(detected_period)

@pytest.fixture(scope="session")
def test_logger(project_root):
    """Create a logger for test output."""
    # Ensure test logs directory exists
    log_dir = project_root / "tests" / "test_logs"
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger("test_runner")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    handler = logging.FileHandler(log_dir / "test_session.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
