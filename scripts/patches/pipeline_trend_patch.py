# Pipeline Trend Enablement Patch
# This file contains the necessary changes to enable trend analysis in the pipeline

# 1. Add these CLI arguments to the argument parser (around line 1324 in pipeline.py):
"""
parser.add_argument('--enable-trending', action='store_true',
                   help='Enable trending analysis in Step 17')
parser.add_argument('--enable-trend-utils', action='store_true',
                   help='Enable trend utilities in Step 13')
"""

# 2. Modify the run_script function to accept additional arguments:
"""
def run_script(script_name: str, description: str, extra_args: list = None) -> bool:
    """
    Run a Python script and return success status.
    
    Args:
        script_name: Name of the script file in src/ directory
        description: Human-readable description for logging
        extra_args: List of additional arguments to pass to the script
        
    Returns:
        True if script succeeded, False otherwise
    """
    log_message(f"Starting {description}...")
    script_path = os.path.join("src", script_name)
    
    if not os.path.exists(script_path):
        log_error(f"Script {script_path} not found!")
        return False
    
    # Build command with extra arguments if provided
    cmd = [sys.executable, script_path]
    if extra_args:
        cmd.extend(extra_args)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        log_error(f"{description} failed!")
        print(result.stdout)
        print(result.stderr)
        return False
    else:
        print(result.stdout)
        log_success(f"{description} completed successfully")
        return True
"""

# 3. Modify the pipeline execution logic to pass trend flags to specific steps:
"""
# In the step execution loop (around line 1150), replace:
# success = run_script(script_name, step_name)
# 
# With:
extra_args = []
if step_num == 13 and enable_trend_utils:
    extra_args.extend(['--enable-trend-utils', '--fast-mode'])
elif step_num == 17 and enable_trending:
    extra_args.append('--enable-trending')

# Add period arguments for all steps
yyyymm, period = get_current_period()
if yyyymm and period:
    extra_args.extend(['--target-yyyymm', yyyymm, '--target-period', period])

success = run_script(script_name, step_name, extra_args)
"""

# 4. Make sure to pass the enable flags to the run_pipeline function call
"""
def run_pipeline(skip_api: bool = False, skip_weather: bool = False,
                start_step: int = None, end_step: int = None,
                strict_mode: bool = False, validate_data: bool = False,
                allow_sample_data: bool = False,
                enable_trending: bool = False, enable_trend_utils: bool = False) -> bool:
"""
