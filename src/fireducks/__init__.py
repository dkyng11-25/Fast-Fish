# Fireducks compatibility shim - uses regular pandas as fallback
# This allows code that imports fireducks.pandas to work with regular pandas

import pandas as pd
import sys

# Create a module object for fireducks.pandas
class FireducksCompat:
    """Compatibility layer that makes pandas look like fireducks.pandas"""
    def __getattr__(self, name):
        return getattr(pd, name)

# Register fireducks.pandas as a module
sys.modules['fireducks.pandas'] = FireducksCompat()
