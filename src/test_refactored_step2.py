#!/usr/bin/env python3
"""
Test script for over-engineered modular step2 (NOT RECOMMENDED)

⚠️ WARNING: This tests an overly complex modular implementation that is not recommended for use.
Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production instead.

This script is provided for reference only and demonstrates testing of the modular architecture,
but the modular approach is unnecessarily complex for this use case.
"""
import os
import sys

# Set environment variables
os.environ['PIPELINE_TARGET_YYYYMM'] = '202509'
os.environ['PIPELINE_TARGET_PERIOD'] = 'A'

# Add src to path
sys.path.append('.')

try:
    from steps.extract_coordinates_step import create_extract_coordinates_step
    from core.context import StepContext
    from core.logger import PipelineLogger

    print("🚀 Testing over-engineered modular step2 (coordinate extraction)...")
    print("⚠️ WARNING: This is testing an overly complex implementation not recommended for use.")

    # Initialize components using convenience factory for over-engineered modular step
    from config_new.output_config import create_step2_for_comparison

    step2 = create_step2_for_comparison("temp_refactored")
    context = StepContext()

    # Setup phase
    print("Setting up over-engineered modular step2...")
    context = step2.setup(context)
    print(f"Setup completed. Context has data: {context.get_data() is not None}")

    # Apply phase
    print("Applying over-engineered modular step2...")
    result = step2.apply(context)
    print("Over-engineered modular step2 completed successfully")

    # Persist phase
    print("Persisting over-engineered modular step2 results...")
    final_context = step2.persist(result)
    print("Over-engineered modular step2 persistence completed")

    # Check outputs using configuration system
    print("\n📊 OVER-ENGINEERED MODULAR STEP 2 OUTPUTS:")
    print("⚠️ NOTE: These outputs are from an overly complex implementation not recommended for production.")
    from config_new.output_config import (
        get_step2_coordinate_file,
        get_step2_spu_mapping_file,
        get_step2_spu_metadata_file
    )

    output_files = [
        get_step2_coordinate_file(),
        get_step2_spu_mapping_file(),
        get_step2_spu_metadata_file()
    ]

    for file_path in output_files:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"✅ {file_path} ({size_mb:.1f} MB)")
        else:
            print(f"❌ {file_path} (not found)")

except Exception as e:
    print(f"❌ Error running refactored step2: {e}")
    import traceback
    traceback.print_exc()
