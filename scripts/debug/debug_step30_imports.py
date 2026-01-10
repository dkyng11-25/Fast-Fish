#!/usr/bin/env python3

print('Debugging Step 30 optimization library imports...')

# Replicate the exact import logic from step30_sellthrough_optimization_engine.py
try:
    print('Attempting to import scipy.optimize.linprog...')
    from scipy.optimize import linprog
    print('✓ scipy.optimize.linprog imported successfully')
    
    print('Attempting to import pulp.*...')
    from pulp import *
    print('✓ pulp.* imported successfully')
    
    OPTIMIZATION_AVAILABLE = True
    print('✓ OPTIMIZATION_AVAILABLE = True')
    
except ImportError as e:
    OPTIMIZATION_AVAILABLE = False
    print(f'✗ ImportError occurred: {e}')
    print('OPTIMIZATION_AVAILABLE = False')

except Exception as e:
    OPTIMIZATION_AVAILABLE = False
    print(f'✗ Unexpected error occurred: {e}')
    print('OPTIMIZATION_AVAILABLE = False')

print(f'Final result: OPTIMIZATION_AVAILABLE = {OPTIMIZATION_AVAILABLE}')
