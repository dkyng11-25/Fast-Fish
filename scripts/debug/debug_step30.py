import os
import sys
sys.path.append('src')

# Check if the enhanced fast fish file exists
file_path = 'output/enhanced_fast_fish_format_202509A.csv'
print(f'Checking if file exists: {file_path}')
print(f'File exists: {os.path.exists(file_path)}')

if os.path.exists(file_path):
    print('File size:', os.path.getsize(file_path))
    
# Check manifest
from pipeline_manifest import get_manifest
manifest = get_manifest()
step14_outputs = manifest.manifest.get('steps', {}).get('step14', {}).get('outputs', {})
print('Step 14 output keys:')
for key in step14_outputs.keys():
    if 'enhanced_fast_fish_format' in key:
        print(f'  {key}')

period_label = '202509A'
specific_key = f'enhanced_fast_fish_format_{period_label}'
print(f'\nLooking for key: {specific_key}')
print(f'Key exists: {specific_key in step14_outputs}')

if specific_key in step14_outputs:
    manifest_file_path = step14_outputs[specific_key]['file_path']
    print(f'Manifest file path: {manifest_file_path}')
    print(f'Manifest file exists: {os.path.exists(manifest_file_path)}')
