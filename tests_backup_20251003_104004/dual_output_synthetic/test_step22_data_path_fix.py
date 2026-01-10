"""
Synthetic test for Step 22 data path fix.

This test ensures that Step 22 can find store_sales files in both:
1. output/ directory (legacy location)
2. data/api_data/ directory (correct location from Step 1)

The bug was that Step 22 only looked in output/, but Step 1 creates files in data/api_data/.
"""

import pytest
import pandas as pd
import os
import tempfile
import shutil
from unittest.mock import patch


def test_step22_finds_store_sales_in_data_api_data():
    """Test that Step 22 can find store_sales files in data/api_data/ directory."""
    
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create data/api_data directory
        api_data_dir = os.path.join(tmpdir, "data", "api_data")
        os.makedirs(api_data_dir, exist_ok=True)
        
        # Create a test store_sales file in data/api_data/
        test_file = os.path.join(api_data_dir, "store_sales_202510A.csv")
        test_data = pd.DataFrame({
            'str_code': ['11014', '11017'],
            'sal_amt': [1000, 2000],
            'base_sal_amt': [500, 1000],
            'fashion_sal_amt': [500, 1000]
        })
        test_data.to_csv(test_file, index=False)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Import the function (this will use the fixed version)
            import sys
            sys.path.insert(0, original_cwd)
            from src.step22_store_attribute_enrichment import load_real_sales_data
            
            # Test that it can find the file in data/api_data/
            result = load_real_sales_data(
                target_yyyymm="202510",
                target_period="A",
                source_yyyymm="202510",
                source_period="A"
            )
            
            # Verify we got data
            assert result is not None, "Should find store_sales file in data/api_data/"
            assert len(result) > 0, "Should load data from file"
            assert 'str_code' in result.columns, "Should have str_code column"
            
        finally:
            os.chdir(original_cwd)


def test_step22_finds_store_sales_in_output_fallback():
    """Test that Step 22 can still find store_sales files in output/ directory (legacy)."""
    
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create output directory
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a test store_sales file in output/
        test_file = os.path.join(output_dir, "store_sales_202510A.csv")
        test_data = pd.DataFrame({
            'str_code': ['11014', '11017'],
            'sal_amt': [1000, 2000],
            'base_sal_amt': [500, 1000],
            'fashion_sal_amt': [500, 1000]
        })
        test_data.to_csv(test_file, index=False)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Import the function
            import sys
            sys.path.insert(0, original_cwd)
            from src.step22_store_attribute_enrichment import load_real_sales_data
            
            # Test that it can find the file in output/
            result = load_real_sales_data(
                target_yyyymm="202510",
                target_period="A",
                source_yyyymm="202510",
                source_period="A"
            )
            
            # Verify we got data
            assert result is not None, "Should find store_sales file in output/"
            assert len(result) > 0, "Should load data from file"
            
        finally:
            os.chdir(original_cwd)


def test_step22_prefers_output_over_data_api_data():
    """Test that Step 22 checks output/ first, then data/api_data/ (priority order)."""
    
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create both directories
        output_dir = os.path.join(tmpdir, "output")
        api_data_dir = os.path.join(tmpdir, "data", "api_data")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(api_data_dir, exist_ok=True)
        
        # Create different files in each location
        output_file = os.path.join(output_dir, "store_sales_202510A.csv")
        api_file = os.path.join(api_data_dir, "store_sales_202510A.csv")
        
        # Output file has 3 stores
        pd.DataFrame({
            'str_code': ['11014', '11017', '11021'],
            'sal_amt': [1000, 2000, 3000],
            'base_sal_amt': [500, 1000, 1500],
            'fashion_sal_amt': [500, 1000, 1500]
        }).to_csv(output_file, index=False)
        
        # API file has 2 stores
        pd.DataFrame({
            'str_code': ['11014', '11017'],
            'sal_amt': [1000, 2000],
            'base_sal_amt': [500, 1000],
            'fashion_sal_amt': [500, 1000]
        }).to_csv(api_file, index=False)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Import the function
            import sys
            sys.path.insert(0, original_cwd)
            from src.step22_store_attribute_enrichment import load_real_sales_data
            
            # Test that it loads from output/ (should have 3 stores)
            result = load_real_sales_data(
                target_yyyymm="202510",
                target_period="A",
                source_yyyymm="202510",
                source_period="A"
            )
            
            # Verify it loaded from output/ (3 stores, not 2)
            assert result is not None, "Should find store_sales file"
            assert len(result) == 3, "Should load from output/ first (3 stores, not 2)"
            
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    print("Running Step 22 data path fix tests...")
    pytest.main([__file__, "-v", "-s"])
