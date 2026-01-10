"""
Matrix validation utilities for Step 3 testing.

This module provides validation functions for matrix preparation outputs.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os

class MatrixValidator:
    """Validator for matrix preparation outputs."""
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_matrix_dimensions(self, matrix_file: str) -> Tuple[bool, str]:
        """
        Validate that matrix has reasonable dimensions.
        
        Args:
            matrix_file: Path to matrix file
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            df = pd.read_csv(matrix_file, index_col=0)
            
            rows, cols = df.shape
            
            # Check for reasonable dimensions
            if rows < 5:
                return False, f"Matrix has too few rows ({rows}), minimum 5 required"
            
            if cols < 3:
                return False, f"Matrix has too few columns ({cols}), minimum 3 required"
            
            if rows > 1000:
                self.validation_warnings.append(f"Matrix has many rows ({rows}), may cause performance issues")
            
            if cols > 2000:
                return False, f"Matrix has too many columns ({cols}), maximum 2000 allowed"
            
            return True, f"Matrix dimensions OK: {rows} rows × {cols} columns"
            
        except Exception as e:
            return False, f"Error reading matrix file: {str(e)}"
    
    def validate_matrix_normalization(self, matrix_file: str) -> Tuple[bool, str]:
        """
        Validate that matrix is properly normalized (rows sum to 1).
        
        Args:
            matrix_file: Path to normalized matrix file
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            df = pd.read_csv(matrix_file, index_col=0)
            
            # Check that rows sum to approximately 1
            row_sums = df.sum(axis=1)
            max_deviation = max(abs(sum_val - 1.0) for sum_val in row_sums)
            
            if max_deviation > 1e-10:
                return False, f"Matrix not properly normalized, max deviation: {max_deviation}"
            
            # Check for any negative values (shouldn't happen after normalization)
            if (df < 0).any().any():
                return False, "Matrix contains negative values after normalization"
            
            return True, f"Matrix properly normalized, max deviation: {max_deviation:.2e}"
            
        except Exception as e:
            return False, f"Error validating normalization: {str(e)}"
    
    def validate_matrix_sparsity(self, matrix_file: str) -> Tuple[bool, str]:
        """
        Validate matrix sparsity levels.
        
        Args:
            matrix_file: Path to matrix file
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            df = pd.read_csv(matrix_file, index_col=0)
            
            total_elements = df.size
            zero_elements = (df == 0).sum().sum()
            sparsity = zero_elements / total_elements
            
            # Check sparsity levels
            if sparsity > 0.95:
                self.validation_warnings.append(f"Matrix is very sparse ({sparsity:.1%} zeros)")
            
            if sparsity < 0.1:
                return False, f"Matrix is too dense ({sparsity:.1%} zeros), may indicate data issues"
            
            return True, f"Matrix sparsity OK: {sparsity:.1%} zeros"
            
        except Exception as e:
            return False, f"Error validating sparsity: {str(e)}"
    
    def validate_file_completeness(self, expected_files: List[str]) -> Tuple[bool, str]:
        """
        Validate that all expected output files exist and have content.
        
        Args:
            expected_files: List of expected file paths
            
        Returns:
            Tuple of (is_valid, message)
        """
        missing_files = []
        empty_files = []
        
        for file_path in expected_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
            else:
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    empty_files.append(file_path)
        
        if missing_files:
            return False, f"Missing files: {missing_files}"
        
        if empty_files:
            return False, f"Empty files: {empty_files}"
        
        return True, f"All {len(expected_files)} files exist and have content"
    
    def validate_matrix_consistency(self, original_file: str, normalized_file: str) -> Tuple[bool, str]:
        """
        Validate that normalized matrix is derived correctly from original.
        
        Args:
            original_file: Path to original matrix
            normalized_file: Path to normalized matrix
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            original_df = pd.read_csv(original_file, index_col=0)
            normalized_df = pd.read_csv(normalized_file, index_col=0)
            
            # Check dimensions match
            if original_df.shape != normalized_df.shape:
                return False, f"Matrix dimensions don't match: {original_df.shape} vs {normalized_df.shape}"
            
            # Check that normalized values are between 0 and 1
            if normalized_df.min().min() < 0 or normalized_df.max().max() > 1:
                return False, "Normalized matrix contains values outside [0,1] range"
            
            # Check that zero rows in original correspond to zero rows in normalized
            original_zeros = original_df.sum(axis=1) == 0
            normalized_zeros = normalized_df.sum(axis=1) == 0
            
            if not original_zeros.equals(normalized_zeros):
                return False, "Zero rows don't match between original and normalized matrices"
            
            return True, "Matrix consistency validated"
            
        except Exception as e:
            return False, f"Error validating matrix consistency: {str(e)}"
    
    def run_comprehensive_validation(self) -> Dict[str, any]:
        """
        Run comprehensive validation of all matrix outputs.
        
        Returns:
            Dictionary with validation results
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        results = {}
        
        # Define expected files
        expected_files = [
            'data/store_subcategory_matrix.csv',
            'data/normalized_subcategory_matrix.csv',
            'data/store_spu_limited_matrix.csv',
            'data/normalized_spu_limited_matrix.csv',
            'data/store_category_agg_matrix.csv',
            'data/normalized_category_agg_matrix.csv'
        ]
        
        # Validate file completeness
        file_valid, file_msg = self.validate_file_completeness(expected_files)
        results['file_completeness'] = {'valid': file_valid, 'message': file_msg}
        
        if not file_valid:
            self.validation_errors.append(file_msg)
            return results
        
        # Validate each matrix type
        matrix_types = [
            ('subcategory', 'data/store_subcategory_matrix.csv', 'data/normalized_subcategory_matrix.csv'),
            ('spu_limited', 'data/store_spu_limited_matrix.csv', 'data/normalized_spu_limited_matrix.csv'),
            ('category_agg', 'data/store_category_agg_matrix.csv', 'data/normalized_category_agg_matrix.csv')
        ]
        
        for matrix_type, original_file, normalized_file in matrix_types:
            # Validate dimensions
            dim_valid, dim_msg = self.validate_matrix_dimensions(original_file)
            results[f'{matrix_type}_dimensions'] = {'valid': dim_valid, 'message': dim_msg}
            
            if not dim_valid:
                self.validation_errors.append(f"{matrix_type} dimensions: {dim_msg}")
            
            # Validate normalization
            norm_valid, norm_msg = self.validate_matrix_normalization(normalized_file)
            results[f'{matrix_type}_normalization'] = {'valid': norm_valid, 'message': norm_msg}
            
            if not norm_valid:
                self.validation_errors.append(f"{matrix_type} normalization: {norm_msg}")
            
            # Validate consistency between original and normalized
            const_valid, const_msg = self.validate_matrix_consistency(original_file, normalized_file)
            results[f'{matrix_type}_consistency'] = {'valid': const_valid, 'message': const_msg}
            
            if not const_valid:
                self.validation_errors.append(f"{matrix_type} consistency: {const_msg}")
        
        # Overall validation result
        overall_valid = len(self.validation_errors) == 0
        results['overall'] = {
            'valid': overall_valid,
            'errors': len(self.validation_errors),
            'warnings': len(self.validation_warnings)
        }
        
        return results

def validate_matrix_preparation_output() -> Dict[str, any]:
    """
    Convenience function to validate matrix preparation outputs.
    
    Returns:
        Validation results dictionary
    """
    validator = MatrixValidator()
    return validator.run_comprehensive_validation()

if __name__ == "__main__":
    results = validate_matrix_preparation_output()
    
    print("Matrix Preparation Validation Results:")
    print(f"Overall: {'✅ PASS' if results['overall']['valid'] else '❌ FAIL'}")
    print(f"Errors: {results['overall']['errors']}")
    print(f"Warnings: {results['overall']['warnings']}")
    
    for key, result in results.items():
        if key != 'overall':
            status = '✅' if result['valid'] else '❌'
            print(f"  {status} {key}: {result['message']}")
