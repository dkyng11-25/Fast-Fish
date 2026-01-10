#!/usr/bin/env python3
"""
Investigate Duplication Source - Check if duplicates come from API, processing, or multiple runs
"""

import pandas as pd
import os
from datetime import datetime
import hashlib

def investigate_duplication_source():
    """Investigate the source of data duplication."""
    
    print("🔍 INVESTIGATING DUPLICATION SOURCE")
    print("=" * 60)
    
    # Check API data files
    api_data_dir = 'data/api_data'
    if not os.path.exists(api_data_dir):
        print(f"❌ API data directory not found: {api_data_dir}")
        return
    
    api_files = [f for f in os.listdir(api_data_dir) if f.endswith('.csv')]
    api_files.sort()
    
    print(f"📁 FOUND {len(api_files)} API FILES:")
    print("-" * 40)
    
    file_info = []
    
    for api_file in api_files:
        file_path = os.path.join(api_data_dir, api_file)
        
        # Get file metadata
        stat = os.stat(file_path)
        file_size = stat.st_size
        created_time = datetime.fromtimestamp(stat.st_ctime)
        modified_time = datetime.fromtimestamp(stat.st_mtime)
        
        # Get file hash to detect identical files
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # Count records
        try:
            df = pd.read_csv(file_path)
            record_count = len(df)
            
            # Check for Store 51198 specifically
            store_51198_count = len(df[df['str_code'] == 51198]) if 'str_code' in df.columns else 0
            
        except Exception as e:
            record_count = f"Error: {e}"
            store_51198_count = 0
        
        file_info.append({
            'filename': api_file,
            'size': file_size,
            'created': created_time,
            'modified': modified_time,
            'hash': file_hash,
            'records': record_count,
            'store_51198_records': store_51198_count
        })
        
        print(f"📄 {api_file}")
        print(f"   Size: {file_size:,} bytes")
        print(f"   Created: {created_time}")
        print(f"   Modified: {modified_time}")
        print(f"   Records: {record_count:,}" if isinstance(record_count, int) else f"   Records: {record_count}")
        print(f"   Store 51198 records: {store_51198_count}")
        print(f"   Hash: {file_hash[:16]}...")
        print()
    
    # Check for identical files
    print("🔍 CHECKING FOR IDENTICAL FILES:")
    print("-" * 40)
    
    hash_groups = {}
    for info in file_info:
        file_hash = info['hash']
        if file_hash not in hash_groups:
            hash_groups[file_hash] = []
        hash_groups[file_hash].append(info)
    
    identical_files_found = False
    for file_hash, files in hash_groups.items():
        if len(files) > 1:
            identical_files_found = True
            print(f"🚨 IDENTICAL FILES DETECTED:")
            print(f"   Hash: {file_hash[:16]}...")
            for file_data in files:
                print(f"   - {file_data['filename']} ({file_data['size']:,} bytes)")
            print()
    
    if not identical_files_found:
        print("✅ No identical files found")
    
    # Check file naming patterns for multiple runs
    print("🔍 CHECKING FILE NAMING PATTERNS:")
    print("-" * 40)
    
    # Look for timestamp patterns that suggest multiple runs
    filename_patterns = {}
    for info in file_info:
        filename = info['filename']
        
        # Extract base name (remove timestamps)
        if '_2025' in filename:
            base_name = filename.split('_2025')[0]
        else:
            base_name = filename.split('.')[0]
        
        if base_name not in filename_patterns:
            filename_patterns[base_name] = []
        filename_patterns[base_name].append(info)
    
    multiple_versions_found = False
    for base_name, files in filename_patterns.items():
        if len(files) > 1:
            multiple_versions_found = True
            print(f"📋 MULTIPLE VERSIONS OF '{base_name}':")
            for file_data in sorted(files, key=lambda x: x['created']):
                print(f"   - {file_data['filename']}")
                print(f"     Created: {file_data['created']}")
                print(f"     Records: {file_data['records']}")
                print(f"     Store 51198: {file_data['store_51198_records']} records")
            print()
    
    if not multiple_versions_found:
        print("✅ No multiple versions detected")
    
    # Analyze content overlap
    print("🔍 ANALYZING CONTENT OVERLAP:")
    print("-" * 40)
    
    store_51198_records = []
    
    for info in file_info:
        if info['store_51198_records'] > 0:
            file_path = os.path.join(api_data_dir, info['filename'])
            try:
                df = pd.read_csv(file_path)
                store_records = df[df['str_code'] == 51198]
                
                # Create record signatures
                for _, record in store_records.iterrows():
                    # Create a signature based on key fields
                    signature_fields = []
                    for field in ['str_code', 'sub_cate_name', 'sex_name', 'display_location_name', 'spu_sales_amt', 'quantity']:
                        if field in record:
                            signature_fields.append(str(record[field]))
                    
                    signature = '|'.join(signature_fields)
                    
                    store_51198_records.append({
                        'file': info['filename'],
                        'signature': signature,
                        'record': record.to_dict()
                    })
            
            except Exception as e:
                print(f"❌ Error reading {info['filename']}: {e}")
    
    print(f"Total Store 51198 records across all files: {len(store_51198_records)}")
    
    # Check for duplicate signatures
    signatures = [r['signature'] for r in store_51198_records]
    unique_signatures = set(signatures)
    
    print(f"Unique record signatures: {len(unique_signatures)}")
    print(f"Duplicate records: {len(signatures) - len(unique_signatures)}")
    
    if len(signatures) > len(unique_signatures):
        print(f"\n🚨 DUPLICATE CONTENT DETECTED!")
        
        # Find which signatures are duplicated
        signature_counts = {}
        signature_files = {}
        
        for record in store_51198_records:
            sig = record['signature']
            file = record['file']
            
            if sig not in signature_counts:
                signature_counts[sig] = 0
                signature_files[sig] = []
            
            signature_counts[sig] += 1
            if file not in signature_files[sig]:
                signature_files[sig].append(file)
        
        print(f"\nTOP DUPLICATED RECORDS:")
        duplicated_sigs = [(sig, count) for sig, count in signature_counts.items() if count > 1]
        duplicated_sigs.sort(key=lambda x: x[1], reverse=True)
        
        for sig, count in duplicated_sigs[:5]:
            print(f"  Record appears {count} times in files: {signature_files[sig]}")
            # Show sample record
            sample_record = next(r for r in store_51198_records if r['signature'] == sig)
            if 'sub_cate_name' in sample_record['record']:
                print(f"    SPU: {sample_record['record']['sub_cate_name']}")
            if 'quantity' in sample_record['record']:
                print(f"    Quantity: {sample_record['record']['quantity']}")
            if 'spu_sales_amt' in sample_record['record']:
                print(f"    Sales: ${sample_record['record']['spu_sales_amt']}")
            print()
    
    # Check Step 1 script for accumulation issues
    print("🔍 CHECKING STEP 1 SCRIPT FOR ACCUMULATION:")
    print("-" * 40)
    
    step1_script = 'src/step1_download_api_data.py'
    if os.path.exists(step1_script):
        print(f"📄 Analyzing {step1_script}")
        
        with open(step1_script, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Check for append vs overwrite modes
        if 'mode=' in script_content:
            print("   Found file mode specifications in script")
        
        if '.append(' in script_content or 'mode="a"' in script_content or "mode='a'" in script_content:
            print("   🚨 APPEND MODE DETECTED - This could cause accumulation!")
        
        if 'to_csv' in script_content:
            print("   Found CSV writing operations")
            # Look for the specific to_csv calls
            lines = script_content.split('\n')
            for i, line in enumerate(lines):
                if 'to_csv' in line:
                    print(f"   Line {i+1}: {line.strip()}")
        
        # Check for duplicate prevention
        if 'drop_duplicates' in script_content:
            print("   ✅ Duplicate removal found in script")
        else:
            print("   ⚠️  No duplicate removal found in script")
    
    else:
        print(f"❌ Step 1 script not found: {step1_script}")
    
    # Final assessment
    print(f"\n🎯 DUPLICATION SOURCE ASSESSMENT:")
    print("-" * 50)
    
    if identical_files_found:
        print("🚨 IDENTICAL FILES: API download created identical files")
        print("   → Problem: Multiple runs or API returning same data")
        print("   → Solution: Check download logic and add file deduplication")
    
    elif multiple_versions_found:
        print("🚨 MULTIPLE VERSIONS: Multiple script runs created different files")
        print("   → Problem: Script runs accumulating instead of replacing")
        print("   → Solution: Ensure scripts overwrite instead of append")
    
    elif len(signatures) > len(unique_signatures):
        print("🚨 CONTENT DUPLICATION: Same records appear in multiple files")
        print("   → Problem: API returning overlapping data or processing issue")
        print("   → Solution: Add record-level deduplication in processing")
    
    else:
        print("✅ NO CLEAR DUPLICATION SOURCE FOUND")
        print("   → Need to investigate further or check other data sources")

if __name__ == "__main__":
    investigate_duplication_source() 