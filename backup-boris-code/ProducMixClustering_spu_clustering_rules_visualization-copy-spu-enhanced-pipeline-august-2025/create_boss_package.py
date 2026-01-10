#!/usr/bin/env python3
"""
Create Boss Package - Essential Files Only
=========================================

This script creates a clean zip package containing only the essential code and documentation files,
excluding large data files, temporary files, and other unnecessary items.

Author: AI Assistant
Date: 2025-01-XX
"""

import os
import zipfile
import fnmatch
from pathlib import Path
import shutil
from datetime import datetime

def should_include_file(file_path: str) -> bool:
    """
    Determine if a file should be included in the boss package.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        bool: True if file should be included
    """
    # Convert to lowercase for case-insensitive matching
    file_lower = file_path.lower()
    
    # Include patterns - files we definitely want
    include_patterns = [
        '*.py',           # Python source code
        '*.md',           # Documentation
        '*.html',         # Executive presentation
        '*.txt',          # Text files (requirements, etc.)
        '*.sh',           # Shell scripts
        '*.json',         # Configuration files (but not large data files)
    ]
    
    # Exclude patterns - files/directories we don't want
    exclude_patterns = [
        '*.csv',          # Large data files
        '*.parquet',      # Data files
        '*.pickle',       # Data files
        '*.pkl',          # Data files
        '*backup*',       # Backup files
        '*_backup_*',     # Backup files
        '*.bak',          # Backup files
        '.DS_Store',      # macOS files
        '__pycache__/*',  # Python cache
        '*.pyc',          # Python compiled
        '.git/*',         # Git directory
        'data/api_data/*', # Large API data
        'output/backup*',  # Backup folders
        'backup/*',        # Backup directory
        'branches/*',      # Branch directories (too much duplication)
        '.specstory/*',    # Spec story files
        'src/data/*',      # Source data files
        'src/output/*',    # Source output files
        'trending_analysis/output/*',  # Trending output
    ]
    
    # Special handling for specific large files
    large_files_to_exclude = [
        'outputformat.md',  # Very large
        'response to fast fish',  # Large document
    ]
    
    # Check if file matches exclude patterns
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(file_lower, pattern.lower()):
            return False
    
    # Check for large files to exclude
    for large_file in large_files_to_exclude:
        if large_file in file_lower:
            return False
    
    # Check if file matches include patterns
    for pattern in include_patterns:
        if fnmatch.fnmatch(file_lower, pattern.lower()):
            return True
    
    return False

def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB."""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except:
        return 0

def create_boss_package():
    """Create the boss package zip file."""
    
    print("🎯 Creating Boss Package - Essential Files Only")
    print("=" * 60)
    
    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"AI_Store_Planning_Project_Package_{timestamp}.zip"
    
    # Track statistics
    total_files = 0
    included_files = 0
    total_size_mb = 0
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        
        # Walk through all files
        for root, dirs, files in os.walk('.'):
            # Filter out unwanted directories
            dirs[:] = [d for d in dirs if not any(
                fnmatch.fnmatch(d.lower(), pattern.lower().rstrip('/*')) 
                for pattern in ['.git', '__pycache__', 'backup', 'branches', '.specstory', 'data/api_data', 'output/backup*']
            )]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, '.')
                total_files += 1
                
                # Check file size (skip very large files > 10MB)
                file_size_mb = get_file_size_mb(file_path)
                if file_size_mb > 10:
                    print(f"⚠️  Skipping large file ({file_size_mb:.1f}MB): {relative_path}")
                    continue
                
                if should_include_file(relative_path):
                    try:
                        zipf.write(file_path, relative_path)
                        included_files += 1
                        total_size_mb += file_size_mb
                        print(f"✅ Included: {relative_path}")
                    except Exception as e:
                        print(f"❌ Error adding {relative_path}: {e}")
                else:
                    print(f"⏭️  Skipped: {relative_path}")
    
    print("\n" + "=" * 60)
    print(f"📦 Package created: {zip_filename}")
    print(f"📊 Statistics:")
    print(f"   • Total files scanned: {total_files:,}")
    print(f"   • Files included: {included_files:,}")
    print(f"   • Files excluded: {total_files - included_files:,}")
    print(f"   • Package size: {total_size_mb:.1f} MB")
    print(f"   • Compression ratio: {get_file_size_mb(zip_filename):.1f} MB compressed")
    
    print(f"\n🎉 Boss package ready to send: {zip_filename}")
    
    # Create a summary of what's included
    print("\n📋 Package Contents Summary:")
    print("   • Executive presentation (HTML)")
    print("   • Complete pipeline source code (Python)")
    print("   • Documentation (Markdown)")
    print("   • Configuration files")
    print("   • Requirements and setup files")
    print("   • Executive visualizations")
    print("   • Business analysis scripts")
    print("\n🚫 Excluded from package:")
    print("   • Large CSV data files")
    print("   • API data cache")
    print("   • Backup files")
    print("   • Git history")
    print("   • Temporary files")
    print("   • Python cache files")

if __name__ == "__main__":
    create_boss_package() 