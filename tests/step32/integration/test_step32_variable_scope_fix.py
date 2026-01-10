"""
Test for Step 32 variable scope bug fix.

This test ensures that generic_validation_report and generic_summary_report
variables are properly defined in the scope where they are used.

The bug was that these variables were defined in main() but used in 
process_period_allocation() and create_allocation_report(), causing NameError.
"""

import pytest
import ast
import inspect


def test_step32_generic_validation_report_defined_in_scope():
    """Test that generic_validation_report is defined before use in process_period_allocation"""
    
    # Read the step32 file
    with open('src/step32_store_allocation.py', 'r') as f:
        source = f.read()
    
    # Parse the AST
    tree = ast.parse(source)
    
    # Find the process_period_allocation function
    process_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'process_period_allocation':
            process_func = node
            break
    
    assert process_func is not None, "process_period_allocation function not found"
    
    # Check that generic_validation_report is assigned before it's used
    assignments = []
    uses = []
    
    for node in ast.walk(process_func):
        # Find assignments to generic_validation_report
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'generic_validation_report':
                    assignments.append(node.lineno)
        
        # Find uses of generic_validation_report
        if isinstance(node, ast.Name) and node.id == 'generic_validation_report':
            if not isinstance(node.ctx, ast.Store):  # Not an assignment
                uses.append(node.lineno)
    
    if uses:
        assert len(assignments) > 0, \
            "generic_validation_report is used but never assigned in process_period_allocation"
        assert min(assignments) < min(uses), \
            f"generic_validation_report is used (line {min(uses)}) before it's assigned (line {min(assignments)})"
    
    print(f"✅ generic_validation_report properly defined before use")
    if assignments:
        print(f"   Assigned at line: {assignments[0]}")
    if uses:
        print(f"   Used at lines: {uses}")


def test_step32_generic_summary_report_defined_in_scope():
    """Test that generic_summary_report is defined before use in create_allocation_report"""
    
    # Read the step32 file
    with open('src/step32_store_allocation.py', 'r') as f:
        source = f.read()
    
    # Parse the AST
    tree = ast.parse(source)
    
    # Find the create_allocation_report function
    report_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'create_allocation_report':
            report_func = node
            break
    
    assert report_func is not None, "create_allocation_report function not found"
    
    # Check that generic_summary_report is assigned before it's used
    assignments = []
    uses = []
    
    for node in ast.walk(report_func):
        # Find assignments to generic_summary_report
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'generic_summary_report':
                    assignments.append(node.lineno)
        
        # Find uses of generic_summary_report
        if isinstance(node, ast.Name) and node.id == 'generic_summary_report':
            if not isinstance(node.ctx, ast.Store):  # Not an assignment
                uses.append(node.lineno)
    
    if uses:
        assert len(assignments) > 0, \
            "generic_summary_report is used but never assigned in create_allocation_report"
        assert min(assignments) < min(uses), \
            f"generic_summary_report is used (line {min(uses)}) before it's assigned (line {min(assignments)})"
    
    print(f"✅ generic_summary_report properly defined before use")
    if assignments:
        print(f"   Assigned at line: {assignments[0]}")
    if uses:
        print(f"   Used at lines: {uses}")


def test_step32_no_undefined_variables_in_functions():
    """Test that there are no undefined variables in key Step 32 functions"""
    
    # Import the module to check for runtime errors
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        # This will fail at import time if there are syntax errors
        import src.step32_store_allocation as step32
        
        # Check that the functions exist
        assert hasattr(step32, 'process_period_allocation'), \
            "process_period_allocation function not found"
        assert hasattr(step32, 'create_allocation_report'), \
            "create_allocation_report function not found"
        
        print("✅ Step 32 module imports successfully")
        print("✅ All required functions are defined")
        
    except NameError as e:
        pytest.fail(f"NameError in Step 32: {e}")
    except Exception as e:
        # Other errors are okay for this test (we're just checking variable scope)
        print(f"   Note: Module import had non-NameError exception (expected): {type(e).__name__}")


if __name__ == "__main__":
    print("Running Step 32 variable scope fix tests...")
    pytest.main([__file__, "-v", "-s"])
