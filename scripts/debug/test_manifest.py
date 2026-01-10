#!/usr/bin/env python3

import os
import sys
import json

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, "src"))

print("Testing manifest file...")

try:
    # Test if we can read the manifest file
    manifest_path = os.path.join(parent_dir, "output", "pipeline_manifest.json")
    print(f"Manifest path: {manifest_path}")
    print(f"Manifest exists: {os.path.exists(manifest_path)}")
    
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            content = f.read()
            print(f"Manifest content length: {len(content)}")
            print("First 200 characters of manifest:")
            print(content[:200])
            
        # Try to parse JSON
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            print("Manifest parsed successfully")
            print(f"Manifest keys: {list(manifest.keys())}")
    else:
        print("Manifest file does not exist")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
