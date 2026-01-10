#!/usr/bin/env python3
"""
Test script for refactored step3 (matrix preparation)
"""
import os
import sys

# Set environment variables
os.environ['PIPELINE_TARGET_YYYYMM'] = '202509'
os.environ['PIPELINE_TARGET_PERIOD'] = 'A'

# Add src to path
sys.path.append('.')

try:
    from steps.matrix_preparation_step import MatrixPreparationStep
    from core.context import StepContext
    from core.logger import PipelineLogger
    
    print("🚀 Testing refactored step3 (matrix preparation)...")
    
    # Initialize components using convenience factory
    from config_new.output_config import create_step3_for_comparison

    step3 = create_step3_for_comparison("temp_refactored")
    context = StepContext()
    
    # Setup phase
    print("Setting up refactored step3...")
    context = step3.setup(context)
    print(f"Setup completed. Context has data: {context.get_data() is not None}")
    
    # Apply phase
    print("Applying refactored step3...")
    result = step3.apply(context)
    print("Refactored step3 completed successfully")
    
    # Validation
    print("Validating results...")
    is_valid = step3.validate(result)
    print(f"Validation passed: {is_valid}")
    
    # Check outputs using configuration system
    print("\n📊 REFACTORED STEP 3 OUTPUTS:")
    from config_new.output_config import (
        get_step3_subcategory_matrix_file,
        get_step3_normalized_subcategory_matrix_file,
        get_step3_spu_matrix_file,
        get_step3_normalized_spu_matrix_file,
        get_step3_category_matrix_file,
        get_step3_normalized_category_matrix_file,
        get_step3_store_list_file,
        get_step3_subcategory_list_file
    )

    output_files = [
        get_step3_subcategory_matrix_file(),
        get_step3_normalized_subcategory_matrix_file(),
        get_step3_subcategory_list_file(),
        get_step3_store_list_file(),
        get_step3_spu_matrix_file(),
        get_step3_normalized_spu_matrix_file(),
        get_step3_category_matrix_file(),
        get_step3_normalized_category_matrix_file()
    ]
    
    for file_path in output_files:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"✅ {file_path} ({size_mb:.1f} MB)")
        else:
            print(f"❌ {file_path} (not found)")

except Exception as e:
    print(f"❌ Error running refactored step3: {e}")
    import traceback
    traceback.print_exc()
