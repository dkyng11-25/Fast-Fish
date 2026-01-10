"""
Tests for MatrixRepository Period-Specific File Loading

Tests the new period-specific file loading functionality with fallback to generic files.

Author: Data Pipeline Team
Date: 2025-10-29
"""

import pytest
import pandas as pd
from pathlib import Path
from repositories.matrix_repository import MatrixRepository


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def synthetic_matrix_data():
    """Create synthetic matrix data for testing."""
    return pd.DataFrame({
        'spu_1': [10, 20, 30],
        'spu_2': [15, 25, 35],
        'spu_3': [12, 22, 32]
    }, index=['store_1', 'store_2', 'store_3'])


@pytest.fixture
def period_specific_matrix_files(tmp_path, synthetic_matrix_data):
    """Create period-specific matrix files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Period-specific files for subcategory
    period_normalized = data_dir / "normalized_subcategory_matrix_202506A.csv"
    synthetic_matrix_data.to_csv(period_normalized)
    
    period_original = data_dir / "store_subcategory_matrix_202506A.csv"
    synthetic_matrix_data.to_csv(period_original)
    
    # Period-specific files for SPU
    period_spu = data_dir / "normalized_spu_limited_matrix_202506A.csv"
    synthetic_matrix_data.to_csv(period_spu)
    
    return data_dir


@pytest.fixture
def generic_matrix_files(tmp_path, synthetic_matrix_data):
    """Create generic matrix files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Generic files for subcategory
    generic_normalized = data_dir / "normalized_subcategory_matrix.csv"
    synthetic_matrix_data.to_csv(generic_normalized)
    
    generic_original = data_dir / "store_subcategory_matrix.csv"
    synthetic_matrix_data.to_csv(generic_original)
    
    return data_dir


@pytest.fixture
def both_matrix_files(tmp_path, synthetic_matrix_data):
    """Create both period-specific and generic matrix files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Period-specific files
    period_normalized = data_dir / "normalized_subcategory_matrix_202506A.csv"
    period_data = synthetic_matrix_data.copy()
    period_data['period_marker'] = 'period_specific'  # Marker to distinguish
    period_data.to_csv(period_normalized)
    
    # Generic files
    generic_normalized = data_dir / "normalized_subcategory_matrix.csv"
    generic_data = synthetic_matrix_data.copy()
    generic_data['period_marker'] = 'generic'  # Marker to distinguish
    generic_data.to_csv(generic_normalized)
    
    return data_dir


# ============================================================================
# Category 1: Period-Specific File Loading
# ============================================================================

class TestPeriodSpecificFileLoading:
    """Tests for period-specific file loading."""
    
    def test_load_period_specific_normalized_matrix(self, period_specific_matrix_files, synthetic_matrix_data):
        """Test 1.1: Load period-specific normalized matrix."""
        # GIVEN: MatrixRepository with period_label
        repo = MatrixRepository(
            base_path=str(period_specific_matrix_files.parent),
            period_label="202506A"
        )
        
        # WHEN: Get normalized matrix
        result = repo.get_normalized_matrix("subcategory")
        
        # THEN: Returns DataFrame from period-specific file
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.shape == synthetic_matrix_data.shape
        assert list(result.columns) == list(synthetic_matrix_data.columns)
    
    def test_load_period_specific_original_matrix(self, period_specific_matrix_files, synthetic_matrix_data):
        """Test 1.2: Load period-specific original matrix."""
        # GIVEN: MatrixRepository with period_label
        repo = MatrixRepository(
            base_path=str(period_specific_matrix_files.parent),
            period_label="202506A"
        )
        
        # WHEN: Get original matrix
        result = repo.get_original_matrix("subcategory")
        
        # THEN: Returns DataFrame from period-specific file
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.shape == synthetic_matrix_data.shape
    
    def test_load_period_specific_spu_matrix(self, period_specific_matrix_files, synthetic_matrix_data):
        """Test 1.3: Load period-specific SPU matrix."""
        # GIVEN: MatrixRepository with period_label
        repo = MatrixRepository(
            base_path=str(period_specific_matrix_files.parent),
            period_label="202506A"
        )
        
        # WHEN: Get SPU normalized matrix
        result = repo.get_normalized_matrix("spu")
        
        # THEN: Returns DataFrame from period-specific file
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.shape == synthetic_matrix_data.shape


# ============================================================================
# Category 2: Fallback Logic
# ============================================================================

class TestFallbackLogic:
    """Tests for fallback to generic files."""
    
    def test_fallback_to_generic_when_period_missing(self, generic_matrix_files, synthetic_matrix_data):
        """Test 2.1: Fallback to generic when period file missing."""
        # GIVEN: MatrixRepository with period_label but only generic files exist
        repo = MatrixRepository(
            base_path=str(generic_matrix_files.parent),
            period_label="202506A"
        )
        
        # WHEN: Get normalized matrix
        result = repo.get_normalized_matrix("subcategory")
        
        # THEN: Returns DataFrame from generic file (fallback)
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.shape == synthetic_matrix_data.shape
    
    def test_error_when_both_files_missing(self, tmp_path):
        """Test 2.2: Error when both files missing."""
        # GIVEN: MatrixRepository with period_label but no files exist
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        repo = MatrixRepository(
            base_path=str(tmp_path),
            period_label="202506A"
        )
        
        # WHEN/THEN: Get normalized matrix raises FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            repo.get_normalized_matrix("subcategory")
        
        # Verify error message is helpful
        assert "subcategory" in str(exc_info.value).lower()
    
    def test_fallback_for_original_matrix(self, generic_matrix_files, synthetic_matrix_data):
        """Test 2.3: Fallback for original matrix."""
        # GIVEN: MatrixRepository with period_label but only generic files exist
        repo = MatrixRepository(
            base_path=str(generic_matrix_files.parent),
            period_label="202506A"
        )
        
        # WHEN: Get original matrix
        result = repo.get_original_matrix("subcategory")
        
        # THEN: Returns DataFrame from generic file (fallback)
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.shape == synthetic_matrix_data.shape
    
    def test_period_specific_preferred_over_generic(self, both_matrix_files):
        """Test 2.4: Period-specific file preferred when both exist."""
        # GIVEN: Both period-specific and generic files exist
        repo = MatrixRepository(
            base_path=str(both_matrix_files.parent),
            period_label="202506A"
        )
        
        # WHEN: Get normalized matrix
        result = repo.get_normalized_matrix("subcategory")
        
        # THEN: Returns period-specific file (has 'period_specific' marker)
        assert result is not None
        assert 'period_marker' in result.columns
        assert result['period_marker'].iloc[0] == 'period_specific'


# ============================================================================
# Category 3: Backward Compatibility
# ============================================================================

class TestBackwardCompatibility:
    """Tests for backward compatibility without period_label."""
    
    def test_generic_file_loading_without_period(self, generic_matrix_files, synthetic_matrix_data):
        """Test 3.1: Generic file loading without period."""
        # GIVEN: MatrixRepository without period_label
        repo = MatrixRepository(
            base_path=str(generic_matrix_files.parent),
            period_label=None
        )
        
        # WHEN: Get normalized matrix
        result = repo.get_normalized_matrix("subcategory")
        
        # THEN: Returns DataFrame from generic file
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert result.shape == synthetic_matrix_data.shape
    
    def test_default_initialization(self, generic_matrix_files, synthetic_matrix_data):
        """Test 3.2: Default initialization."""
        # GIVEN: MatrixRepository with default parameters
        repo = MatrixRepository(base_path=str(generic_matrix_files.parent))
        
        # WHEN: Get normalized matrix
        result = repo.get_normalized_matrix("subcategory")
        
        # THEN: Returns DataFrame from generic file
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        # Verify period_label defaults to None
        assert repo.period_label is None


# ============================================================================
# Category 4: Path Construction
# ============================================================================

class TestPathConstruction:
    """Tests for path construction logic."""
    
    def test_period_specific_path_construction(self):
        """Test 4.1: Period-specific path construction."""
        # GIVEN: MatrixRepository with period_label
        repo = MatrixRepository(base_path=".", period_label="202506A")
        
        # WHEN: Get period-specific path
        path = repo._get_period_specific_path("subcategory", "normalized")
        
        # THEN: Path is correct
        expected = Path("data/normalized_subcategory_matrix_202506A.csv")
        assert path == expected
    
    def test_generic_path_construction(self):
        """Test 4.2: Generic path construction."""
        # GIVEN: MatrixRepository
        repo = MatrixRepository(base_path=".")
        
        # WHEN: Get generic path
        path = repo._get_generic_path("subcategory", "normalized")
        
        # THEN: Path is correct
        expected = Path("data/normalized_subcategory_matrix.csv")
        assert path == expected
    
    def test_path_construction_for_all_matrix_types(self):
        """Test 4.3: Path construction for all matrix types."""
        # GIVEN: MatrixRepository with period_label
        repo = MatrixRepository(base_path=".", period_label="202506A")
        
        # WHEN/THEN: Verify paths for all matrix types
        subcategory_path = repo._get_period_specific_path("subcategory", "normalized")
        assert "normalized_subcategory_matrix_202506A.csv" in str(subcategory_path)
        
        spu_path = repo._get_period_specific_path("spu", "normalized")
        assert "normalized_spu_limited_matrix_202506A.csv" in str(spu_path)
        
        category_agg_path = repo._get_period_specific_path("category_agg", "normalized")
        assert "normalized_category_agg_matrix_202506A.csv" in str(category_agg_path)


# ============================================================================
# Category 5: Error Handling
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_matrix_type(self):
        """Test 5.1: Invalid matrix type."""
        # GIVEN: MatrixRepository
        repo = MatrixRepository(base_path=".")
        
        # WHEN/THEN: Get matrix with invalid type raises ValueError
        with pytest.raises(ValueError) as exc_info:
            repo.get_normalized_matrix("invalid_type")
        
        # Verify error message lists valid types
        error_msg = str(exc_info.value).lower()
        assert "invalid" in error_msg or "must be" in error_msg
    
    def test_invalid_period_label_format(self, generic_matrix_files, synthetic_matrix_data):
        """Test 5.2: Invalid period label format."""
        # GIVEN: MatrixRepository with invalid period_label format
        repo = MatrixRepository(
            base_path=str(generic_matrix_files.parent),
            period_label="invalid"
        )
        
        # WHEN: Get normalized matrix
        result = repo.get_normalized_matrix("subcategory")
        
        # THEN: Falls back to generic file (graceful handling)
        assert result is not None
        assert isinstance(result, pd.DataFrame)
    
    def test_corrupted_file_handling(self, tmp_path):
        """Test 5.3: Corrupted file handling."""
        # GIVEN: Corrupted period-specific file
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        corrupted_file = data_dir / "normalized_subcategory_matrix_202506A.csv"
        corrupted_file.write_text("corrupted,data\nthis,is,not,valid,csv")
        
        repo = MatrixRepository(
            base_path=str(tmp_path),
            period_label="202506A"
        )
        
        # WHEN/THEN: Get matrix raises pandas error (not silently falling back)
        with pytest.raises(Exception):  # pandas will raise various exceptions
            repo.get_normalized_matrix("subcategory")


# ============================================================================
# Category 6: Integration Tests
# ============================================================================

class TestMatrixRepositoryIntegration:
    """Integration tests with Step 6."""
    
    def test_step6_with_period_specific_matrices(self, period_specific_matrix_files, synthetic_matrix_data, tmp_path):
        """Test 6.1: Step 6 with period-specific matrices."""
        # GIVEN: Period-specific matrix files exist
        # AND: MatrixRepository configured with period
        repo = MatrixRepository(
            base_path=str(period_specific_matrix_files.parent),
            period_label="202506A"
        )
        
        # WHEN: Load both normalized and original matrices
        normalized = repo.get_normalized_matrix("subcategory")
        original = repo.get_original_matrix("subcategory")
        
        # THEN: Both matrices loaded successfully
        assert normalized is not None
        assert original is not None
        assert normalized.shape == original.shape
        
        # AND: Data is correct
        assert normalized.shape == synthetic_matrix_data.shape
    
    def test_step6_with_generic_matrices_fallback(self, generic_matrix_files, synthetic_matrix_data):
        """Test 6.2: Step 6 with generic matrices (fallback)."""
        # GIVEN: Only generic matrix files exist
        # AND: MatrixRepository configured with period (but files don't exist)
        repo = MatrixRepository(
            base_path=str(generic_matrix_files.parent),
            period_label="202506A"
        )
        
        # WHEN: Load matrices (should fall back to generic)
        normalized = repo.get_normalized_matrix("subcategory")
        original = repo.get_original_matrix("subcategory")
        
        # THEN: Both matrices loaded successfully from generic files
        assert normalized is not None
        assert original is not None
        assert normalized.shape == synthetic_matrix_data.shape
    
    def test_step6_backward_compatible_no_period(self, generic_matrix_files, synthetic_matrix_data):
        """Test 6.3: Step 6 backward compatible (no period)."""
        # GIVEN: Generic matrix files exist
        # AND: MatrixRepository without period (backward compatible mode)
        repo = MatrixRepository(
            base_path=str(generic_matrix_files.parent)
        )
        
        # WHEN: Load matrices
        normalized = repo.get_normalized_matrix("subcategory")
        original = repo.get_original_matrix("subcategory")
        
        # THEN: Both matrices loaded successfully
        assert normalized is not None
        assert original is not None
        assert normalized.shape == synthetic_matrix_data.shape
        
        # AND: Backward compatible behavior (no period_label)
        assert repo.period_label is None
