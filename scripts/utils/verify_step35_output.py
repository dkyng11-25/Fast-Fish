#!/usr/bin/env python3

import os

output_dir = "/Users/frogtime/Desktop/code/boris-fix/ProducMixClustering_spu_clustering_rules_visualization-copy/output"

print("Checking Step 35 output files...")

# Check if output directory exists
if os.path.exists(output_dir):
    print(f"✓ Output directory exists: {output_dir}")
    
    # List all files in output directory
    files = os.listdir(output_dir)
    print(f"Files in output directory ({len(files)} total):")
    for file in sorted(files):
        file_path = os.path.join(output_dir, file)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            print(f"  {file} ({size} bytes)")
    
    # Check for specific Step 35 output files
    expected_files = [
        "store_level_merchandising_recommendations_202509A.csv",
        "store_level_merchandising_summary_202509A.md"
    ]
    
    print("\nChecking for Step 35 output files:")
    for expected_file in expected_files:
        file_path = os.path.join(output_dir, expected_file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {expected_file} exists ({size} bytes)")
        else:
            print(f"  ✗ {expected_file} NOT found")
            
    # Check manifest file
    manifest_path = os.path.join(output_dir, "pipeline_manifest.json")
    if os.path.exists(manifest_path):
        size = os.path.getsize(manifest_path)
        print(f"  ✓ pipeline_manifest.json exists ({size} bytes)")
    else:
        print(f"  ✗ pipeline_manifest.json NOT found")
        
else:
    print(f"✗ Output directory does not exist: {output_dir}")
