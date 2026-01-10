#!/usr/bin/env python3
"""
Apply trend enablement patch to pipeline.py
"""

import os
import sys

def apply_patch():
    pipeline_file = "pipeline.py"
    
    if not os.path.exists(pipeline_file):
        print(f"Error: {pipeline_file} not found")
        return False
    
    # Read the current pipeline file
    with open(pipeline_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add CLI arguments for trend enablement
    cli_args_insert_point = content.find("args = parser.parse_args()")
    if cli_args_insert_point == -1:
        print("Error: Could not find args = parser.parse_args() line")
        return False
    
    # Check if the arguments are already added
    if "--enable-trending" in content:
        print("Trend arguments already added to pipeline")
    else:
        # Insert the new CLI arguments
        new_args = '''    parser.add_argument('--enable-trending', action='store_true',
                       help='Enable trending analysis in Step 17')
    parser.add_argument('--enable-trend-utils', action='store_true',
                       help='Enable trend utilities in Step 13')
    \n'''
        content = content[:cli_args_insert_point] + new_args + content[cli_args_insert_point:]
    
    # Modify run_script function to accept extra arguments
    if "extra_args: list = None" in content:
        print("run_script function already modified")
    else:
        # Find and replace the run_script function signature and implementation
        run_script_start = content.find("def run_script(script_name: str, description: str) -> bool:")
        if run_script_start == -1:
            print("Error: Could not find run_script function")
            return False
        
        run_script_end = content.find("\n\ndef", run_script_start + 100)
        if run_script_end == -1:
            run_script_end = len(content)
        
        # Replace the run_script function
        old_run_script = content[run_script_start:run_script_end]
        new_run_script = '''def run_script(script_name: str, description: str, extra_args: list = None) -> bool:
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
        return True'''
        
        content = content[:run_script_start] + new_run_script + content[run_script_end:]
    
    # Modify run_pipeline function signature
    run_pipeline_start = content.find("def run_pipeline(")
    if run_pipeline_start == -1:
        print("Error: Could not find run_pipeline function")
        return False
    
    if "enable_trending: bool = False" in content:
        print("run_pipeline function already modified with trend arguments")
    else:
        # Find the end of the function signature
        run_pipeline_sig_end = content.find(") -> bool:", run_pipeline_start)
        if run_pipeline_sig_end == -1:
            print("Error: Could not find run_pipeline function signature end")
            return False
        
        # Insert the new parameters
        new_sig = ",\n                enable_trending: bool = False, enable_trend_utils: bool = False"
        content = content[:run_pipeline_sig_end] + new_sig + content[run_pipeline_sig_end:]
    
    # Modify the main function to pass trend flags
    main_start = content.find("def main() -> None:")
    if main_start == -1:
        print("Error: Could not find main function")
        return False
    
    # Find where run_pipeline is called
    run_pipeline_call = content.find("success = run_pipeline(")
    if run_pipeline_call == -1:
        print("Error: Could not find run_pipeline call")
        return False
    
    # Check if trend flags are already passed
    if "enable_trending=args.enable_trending" in content:
        print("Trend flags already passed to run_pipeline")
    else:
        # Find the end of the run_pipeline call
        run_pipeline_end = content.find(")", run_pipeline_call)
        if run_pipeline_end == -1:
            print("Error: Could not find end of run_pipeline call")
            return False
        
        # Insert the new arguments
        new_call_args = ",\n            enable_trending=args.enable_trending, enable_trend_utils=args.enable_trend_utils"
        content = content[:run_pipeline_end] + new_call_args + content[run_pipeline_end:]
    
    # Modify step execution to pass arguments
    step_exec_start = content.find("# Execute steps in range")
    if step_exec_start == -1:
        print("Error: Could not find step execution section")
        return False
    
    # Check if step execution is already modified
    if "extra_args = []" in content:
        print("Step execution already modified to pass arguments")
    else:
        # Find where run_script is called in the step loop
        run_script_call = content.find("success = run_script(script_name, step_name)")
        if run_script_call == -1:
            print("Error: Could not find run_script call in step loop")
            return False
        
        # Replace the run_script call with the enhanced version
        old_call = "success = run_script(script_name, step_name)"
        new_call = '''        # Build extra arguments for specific steps
        extra_args = []
        if step_num == 13 and enable_trend_utils:
            extra_args.extend(['--enable-trend-utils', '--fast-mode'])
        elif step_num == 17 and enable_trending:
            extra_args.append('--enable-trending')
        
        # Add period arguments for all steps
        current_yyyymm, current_period = get_current_period()
        if current_yyyymm and current_period:
            extra_args.extend(['--target-yyyymm', current_yyyymm, '--target-period', current_period])
        
        success = run_script(script_name, step_name, extra_args)'''
        
        content = content.replace(old_call, new_call)
    
    # Write the modified content back to the file
    with open(pipeline_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Successfully applied trend enablement patch to pipeline.py")
    return True

if __name__ == "__main__":
    apply_patch()
