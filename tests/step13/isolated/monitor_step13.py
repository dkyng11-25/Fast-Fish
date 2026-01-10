"""
Monitor Step 13 execution to detect all state changes.

This script wraps Step 13 execution and records:
- Files created/modified/deleted
- Environment variables changed
- Working directory changes
- Any other state modifications
"""

import os
import sys
import subprocess
import hashlib
from pathlib import Path
import json
from datetime import datetime


def get_file_hash(filepath):
    """Get MD5 hash of a file."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None


def scan_directory(directory):
    """Scan directory and return dict of {filepath: hash}."""
    files = {}
    for path in Path(directory).rglob('*'):
        if path.is_file():
            rel_path = str(path.relative_to(directory))
            files[rel_path] = get_file_hash(path)
    return files


def compare_states(before, after, label=""):
    """Compare two directory states and report differences."""
    changes = {
        "created": [],
        "modified": [],
        "deleted": []
    }
    
    # Find created and modified files
    for filepath, hash_after in after.items():
        if filepath not in before:
            changes["created"].append(filepath)
        elif before[filepath] != hash_after:
            changes["modified"].append(filepath)
    
    # Find deleted files
    for filepath in before:
        if filepath not in after:
            changes["deleted"].append(filepath)
    
    return changes


def monitor_step13_execution(sandbox_path, target_yyyymm="202510", target_period="A"):
    """
    Monitor Step 13 execution and report all state changes.
    
    Returns:
        dict with all detected changes
    """
    sandbox = Path(sandbox_path)
    
    print(f"\n{'='*80}")
    print(f"MONITORING STEP 13 EXECUTION")
    print(f"Sandbox: {sandbox}")
    print(f"Target: {target_yyyymm}{target_period}")
    print(f"{'='*80}\n")
    
    # Capture initial state
    print("📸 Capturing BEFORE state...")
    before_env = dict(os.environ)
    before_cwd = os.getcwd()
    before_files = scan_directory(sandbox)
    
    print(f"   Files before: {len(before_files)}")
    print(f"   Env vars before: {len(before_env)}")
    print(f"   CWD before: {before_cwd}")
    
    # Run Step 13
    print("\n🚀 Running Step 13...")
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = target_yyyymm
    env["PIPELINE_TARGET_PERIOD"] = target_period
    env.setdefault("PYTHONPATH", str(sandbox))
    
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            ["python3", "src/step13_consolidate_spu_rules.py",
             "--target-yyyymm", target_yyyymm,
             "--target-period", target_period],
            cwd=sandbox,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        success = result.returncode == 0
        print(f"   Exit code: {result.returncode}")
        print(f"   Duration: {duration:.2f}s")
        
        if not success:
            print(f"\n❌ STEP 13 FAILED")
            print(f"STDERR:\n{result.stderr[:500]}")
        else:
            print(f"   ✅ Step 13 completed successfully")
            
    except subprocess.TimeoutExpired:
        print(f"   ⏱️ TIMEOUT after 30s")
        success = False
        result = None
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        success = False
        result = None
    
    # Capture final state
    print("\n📸 Capturing AFTER state...")
    after_env = dict(os.environ)
    after_cwd = os.getcwd()
    after_files = scan_directory(sandbox)
    
    print(f"   Files after: {len(after_files)}")
    print(f"   Env vars after: {len(after_env)}")
    print(f"   CWD after: {after_cwd}")
    
    # Analyze changes
    print(f"\n{'='*80}")
    print("DETECTED CHANGES:")
    print(f"{'='*80}\n")
    
    # File changes
    file_changes = compare_states(before_files, after_files)
    
    print(f"📁 FILE CHANGES:")
    print(f"   Created: {len(file_changes['created'])} files")
    if file_changes['created']:
        for f in sorted(file_changes['created'])[:10]:
            print(f"      + {f}")
        if len(file_changes['created']) > 10:
            print(f"      ... and {len(file_changes['created']) - 10} more")
    
    print(f"   Modified: {len(file_changes['modified'])} files")
    if file_changes['modified']:
        for f in sorted(file_changes['modified'])[:10]:
            print(f"      ~ {f}")
        if len(file_changes['modified']) > 10:
            print(f"      ... and {len(file_changes['modified']) - 10} more")
    
    print(f"   Deleted: {len(file_changes['deleted'])} files")
    if file_changes['deleted']:
        for f in sorted(file_changes['deleted'])[:10]:
            print(f"      - {f}")
    
    # Environment variable changes
    print(f"\n🌍 ENVIRONMENT VARIABLE CHANGES:")
    env_changes = {"added": [], "modified": [], "removed": []}
    
    for key, value in after_env.items():
        if key not in before_env:
            env_changes["added"].append(key)
        elif before_env[key] != value:
            env_changes["modified"].append((key, before_env[key], value))
    
    for key in before_env:
        if key not in after_env:
            env_changes["removed"].append(key)
    
    if env_changes["added"]:
        print(f"   Added: {env_changes['added']}")
    if env_changes["modified"]:
        print(f"   Modified:")
        for key, old, new in env_changes["modified"][:5]:
            print(f"      {key}: {old[:50]} -> {new[:50]}")
    if env_changes["removed"]:
        print(f"   Removed: {env_changes['removed']}")
    
    if not any([env_changes["added"], env_changes["modified"], env_changes["removed"]]):
        print(f"   No environment variable changes detected ✅")
    
    # Working directory changes
    print(f"\n📂 WORKING DIRECTORY:")
    if before_cwd != after_cwd:
        print(f"   Changed: {before_cwd} -> {after_cwd} ⚠️")
    else:
        print(f"   Unchanged: {before_cwd} ✅")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY:")
    print(f"{'='*80}")
    print(f"   Success: {success}")
    print(f"   Files created: {len(file_changes['created'])}")
    print(f"   Files modified: {len(file_changes['modified'])}")
    print(f"   Files deleted: {len(file_changes['deleted'])}")
    print(f"   Env vars changed: {len(env_changes['added']) + len(env_changes['modified']) + len(env_changes['removed'])}")
    print(f"   CWD changed: {before_cwd != after_cwd}")
    print(f"{'='*80}\n")
    
    return {
        "success": success,
        "file_changes": file_changes,
        "env_changes": env_changes,
        "cwd_changed": before_cwd != after_cwd,
        "result": result
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python monitor_step13.py <sandbox_path> [yyyymm] [period]")
        sys.exit(1)
    
    sandbox = sys.argv[1]
    yyyymm = sys.argv[2] if len(sys.argv) > 2 else "202510"
    period = sys.argv[3] if len(sys.argv) > 3 else "A"
    
    changes = monitor_step13_execution(sandbox, yyyymm, period)
    
    # Save report
    report_file = Path(sandbox) / "step13_execution_report.json"
    with open(report_file, 'w') as f:
        json.dump({
            "success": changes["success"],
            "file_changes": changes["file_changes"],
            "env_changes": changes["env_changes"],
            "cwd_changed": changes["cwd_changed"]
        }, f, indent=2)
    
    print(f"📄 Report saved to: {report_file}")
