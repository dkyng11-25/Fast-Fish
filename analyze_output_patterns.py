#!/usr/bin/env python3
"""Analyze which dual output pattern is used by each step"""
import os
from pathlib import Path
import re

output_dir = Path("output")

# Categorize files by pattern
pattern_a_files = []  # file_YYYYMMA.ext (period, no timestamp)
pattern_b_generic = []  # file.ext (no period, no timestamp)
pattern_b_timestamped = []  # file_YYYYMMA_YYYYMMDD_HHMMSS.ext

timestamp_pattern = r'_\d{8}_\d{6}'
period_pattern = r'_\d{6}[AB]'

for file in output_dir.glob("*"):
    if file.is_file():
        name = file.name
        
        has_timestamp = bool(re.search(timestamp_pattern, name))
        has_period = bool(re.search(period_pattern, name))
        
        if has_timestamp and has_period:
            pattern_b_timestamped.append(name)
        elif has_period and not has_timestamp:
            pattern_a_files.append(name)
        elif not has_period and not has_timestamp:
            pattern_b_generic.append(name)

print("="*80)
print("OUTPUT PATTERN ANALYSIS")
print("="*80)
print()
print(f"Pattern A (period label, no timestamp): {len(pattern_a_files)} files")
print(f"Pattern B Generic (no period, no timestamp): {len(pattern_b_generic)} files")
print(f"Pattern B Timestamped (period + timestamp): {len(pattern_b_timestamped)} files")
print()
print("="*80)
print("PATTERN A FILES (period label, no timestamp):")
print("="*80)
for f in sorted(pattern_a_files)[:20]:
    print(f"  {f}")
if len(pattern_a_files) > 20:
    print(f"  ... and {len(pattern_a_files) - 20} more")
print()
print("="*80)
print("PATTERN B GENERIC FILES (no period, no timestamp):")
print("="*80)
for f in sorted(pattern_b_generic)[:20]:
    print(f"  {f}")
if len(pattern_b_generic) > 20:
    print(f"  ... and {len(pattern_b_generic) - 20} more")
print()
print("="*80)
print("PATTERN B TIMESTAMPED FILES (period + timestamp):")
print("="*80)
for f in sorted(pattern_b_timestamped)[:20]:
    print(f"  {f}")
if len(pattern_b_timestamped) > 20:
    print(f"  ... and {len(pattern_b_timestamped) - 20} more")
print()
print("="*80)
print("RECOMMENDATION:")
print("="*80)
print()
if len(pattern_a_files) > len(pattern_b_generic):
    print("✅ PATTERN A is more widely used")
    print("   Standardize to: file_YYYYMMA.ext + file.ext (copy)")
else:
    print("✅ PATTERN B is more widely used")
    print("   Standardize to: file.ext + file_YYYYMMA_YYYYMMDD_HHMMSS.ext")
print()
