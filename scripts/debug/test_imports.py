#!/usr/bin/env python3

print('Testing imports...')

try:
    import scipy
    print(f'scipy version: {scipy.__version__}')
except Exception as e:
    print(f'scipy import failed: {e}')

try:
    import pulp
    print(f'pulp version: {pulp.__version__}')
except Exception as e:
    print(f'pulp import failed: {e}')

try:
    from scipy.optimize import linprog
    print('scipy.optimize.linprog imported successfully')
except Exception as e:
    print(f'scipy.optimize.linprog import failed: {e}')

try:
    from pulp import *
    print('pulp.* imported successfully')
except Exception as e:
    print(f'pulp.* import failed: {e}')

print('Import test completed.')
