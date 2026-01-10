#!/usr/bin/env python3
"""
Reorganize tests into isolated/ and integration/ subdirectories

Isolated tests: Synthetic tests that run standalone with fixtures
Integration tests: Tests that require pipeline output files
"""

import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
TESTS_DIR = PROJECT_ROOT / "tests"

# Patterns to identify isolated tests
ISOLATED_PATTERNS = [
    "synthetic",
    "isolated",
    "fixture",
]

# Patterns to identify integration tests
INTEGRATION_PATTERNS = [
    "dual_output",
    "integrity",
    "post_consolidation",
    "validation",
    "imports_and_smoke",
]

def should_be_isolated(filename: str) -> bool:
    """Check if test should be in isolated/ directory"""
    lower = filename.lower()
    return any(pattern in lower for pattern in ISOLATED_PATTERNS)

def should_be_integration(filename: str) -> bool:
    """Check if test should be in integration/ directory"""
    lower = filename.lower()
    return any(pattern in lower for pattern in INTEGRATION_PATTERNS)

def reorganize_step_tests(step_dir: Path):
    """Reorganize tests in a step directory"""
    if not step_dir.is_dir():
        return
    
    # Skip if already organized
    if (step_dir / "isolated").exists() or (step_dir / "integration").exists():
        print(f"⏭️  {step_dir.name}: Already organized")
        return
    
    # Get all test files
    test_files = list(step_dir.glob("test_*.py"))
    if not test_files:
        return
    
    isolated_files = []
    integration_files = []
    
    for test_file in test_files:
        if should_be_isolated(test_file.name):
            isolated_files.append(test_file)
        elif should_be_integration(test_file.name):
            integration_files.append(test_file)
        else:
            # Default: if it's a dual_output test, it's integration
            # Otherwise, leave it at root for manual review
            if "dual_output" in test_file.name.lower():
                integration_files.append(test_file)
    
    # Only reorganize if we have files to move
    if not isolated_files and not integration_files:
        print(f"⏭️  {step_dir.name}: No clear categorization")
        return
    
    print(f"\n📁 {step_dir.name}:")
    
    # Create subdirectories
    if isolated_files:
        isolated_dir = step_dir / "isolated"
        isolated_dir.mkdir(exist_ok=True)
        (isolated_dir / "__init__.py").touch()
        
        for test_file in isolated_files:
            dest = isolated_dir / test_file.name
            shutil.move(str(test_file), str(dest))
            print(f"  ✓ {test_file.name} → isolated/")
    
    if integration_files:
        integration_dir = step_dir / "integration"
        integration_dir.mkdir(exist_ok=True)
        (integration_dir / "__init__.py").touch()
        
        for test_file in integration_files:
            dest = integration_dir / test_file.name
            shutil.move(str(test_file), str(dest))
            print(f"  ✓ {test_file.name} → integration/")

def main():
    print("🔄 Reorganizing tests into isolated/ and integration/ subdirectories\n")
    print("=" * 70)
    
    # Get all step directories
    step_dirs = sorted([d for d in TESTS_DIR.iterdir() 
                       if d.is_dir() and d.name.startswith("step")])
    
    for step_dir in step_dirs:
        reorganize_step_tests(step_dir)
    
    print("\n" + "=" * 70)
    print("\n✅ Reorganization complete!")
    print("\nNext steps:")
    print("1. Review the reorganization")
    print("2. Run: pytest tests/ --collect-only")
    print("3. Commit changes if everything looks good")

if __name__ == "__main__":
    main()
