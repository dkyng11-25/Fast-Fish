import pandas as pd
#!/usr/bin/env python3
"""
Comprehensive Weather Validation Schemas

This module contains comprehensive validation schemas for weather data,
including temperature, precipitation, wind, humidity, pressure, and radiation.
Based on research of 2024-2025 weather patterns and extremes.

NOTE: This file has been refactored into modular schemas. The schemas are now imported
from the weather package for backward compatibility.

Author: Data Pipeline
Date: 2025-01-03
"""

# Import all weather schemas from the modular structure
from .weather import *
from .geographic import *
from .seasonal import *
from .matrix import *
from .clustering import *