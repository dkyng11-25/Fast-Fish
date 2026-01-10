#!/usr/bin/env python3

print('=== Detailed Step 30 Import Debug ===')

import sys
print(f'Python version: {sys.version}')
print(f'Python executable: {sys.executable}')

print('\nAttempting Step 30 import logic...')

# Exact replication of Step 30 import logic
try:
    print('1. Importing scipy.optimize.linprog...')
    from scipy.optimize import linprog
    print('   ✓ Success')
    
    print('2. Importing pulp.*...')
    from pulp import *
    print('   ✓ Success')
    
    OPTIMIZATION_AVAILABLE = True
    print('3. OPTIMIZATION_AVAILABLE = True')
    
except ImportError as import_error:
    OPTIMIZATION_AVAILABLE = False
    print(f'   ✗ ImportError: {import_error}')
    print('   OPTIMIZATION_AVAILABLE = False')
    
except Exception as general_error:
    OPTIMIZATION_AVAILABLE = False
    print(f'   ✗ General Exception: {general_error}')
    print('   OPTIMIZATION_AVAILABLE = False')

print(f'\nFinal result: OPTIMIZATION_AVAILABLE = {OPTIMIZATION_AVAILABLE}')

if OPTIMIZATION_AVAILABLE:
    print('\n✓ Optimization libraries are available!')
    # Test basic functionality
    try:
        prob = LpProblem("test", LpMaximize)
        x = LpVariable("x", 0, 1)
        prob += x
        print('✓ Basic PuLP functionality test passed')
    except Exception as e:
        print(f'✗ Basic PuLP functionality test failed: {e}')
else:
    print('\n✗ Optimization libraries are NOT available')

print('\n=== Debug Complete ===')
