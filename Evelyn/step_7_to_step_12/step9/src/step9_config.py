"""
Step 9 Configuration: Below Minimum Rule Settings

This module contains all configuration for Step 9, including:
- Core subcategory loading (configurable, not hardcoded)
- Minimum threshold settings
- 3-level fallback configuration

Per Customer Requirement:
- Core subcategories must be loaded from config file (E-04, I-05)
- Never decrease below minimum (E-06)
- No negative quantities (E-06)

Author: Data Pipeline Team
Date: January 2026
"""

import json
import os
from pathlib import Path
from typing import Set, Dict, Optional, List
from dataclasses import dataclass
from enum import Enum


class MinimumReferenceSource(Enum):
    """Source of minimum threshold value (for explainability)."""
    MANUAL_PLAN = "manual_plan"
    CLUSTER_P10 = "cluster_p10"
    GLOBAL_FALLBACK = "global_fallback"


@dataclass
class Step9Config:
    """Configuration for Step 9 Below Minimum Rule."""
    # Minimum thresholds
    global_minimum_unit_rate: float = 1.0  # Global fallback: 1 unit per 15 days
    minimum_style_threshold: float = 0.03  # For subcategory level
    min_boost_quantity: float = 0.5  # Minimum positive increase
    
    # Quantity constraints (per E-05: ±20% of manual/historical)
    max_increase_percentage: float = 0.20  # Max 20% increase
    never_decrease: bool = True  # Per E-06: Never decrease
    
    # Sell-through validation
    require_sell_through_signal: bool = True  # Per requirement
    min_sell_through_rate: float = 0.0  # Minimum sell-through to consider
    
    # Analysis settings
    min_cluster_size: int = 2  # Minimum stores in cluster for valid analysis
    min_sales_units: float = 0.1  # Minimum observed units to consider active
    
    # Period settings
    data_period_days: int = 15
    target_period_days: int = 15


# Default configuration
DEFAULT_CONFIG = Step9Config()

# Path to core subcategories config (shared with Step 7)
STEP7_CONFIG_PATH = Path(__file__).parent.parent / "step7" / "core_subcategories_config.json"
STEP9_CONFIG_PATH = Path(__file__).parent / "step9_core_subcategories_config.json"


def load_core_subcategories() -> Set[str]:
    """
    Load core subcategories from config file.
    
    Per Customer Requirement E-04, W-01, I-05:
    Core subcategories must NEVER be filtered and must always be evaluated.
    
    Priority:
    1. Step 9 specific config (if exists)
    2. Step 7 shared config (if exists)
    3. Default hardcoded list (fallback only)
    
    Returns:
        Set of core subcategory names
    """
    # Try Step 9 specific config first
    if STEP9_CONFIG_PATH.exists():
        try:
            with open(STEP9_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'core_subcategories' in config:
                    print(f"✅ Loaded core subcategories from Step 9 config: {STEP9_CONFIG_PATH}")
                    return set(config['core_subcategories'])
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading Step 9 config: {e}")
    
    # Try Step 7 shared config
    if STEP7_CONFIG_PATH.exists():
        try:
            with open(STEP7_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'core_subcategories' in config:
                    print(f"✅ Loaded core subcategories from Step 7 config: {STEP7_CONFIG_PATH}")
                    return set(config['core_subcategories'])
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading Step 7 config: {e}")
    
    # Fallback to defaults (should not happen in production)
    print("⚠️ Using default core subcategories (config file not found)")
    return {
        '直筒裤', '束脚裤', '锥形裤',
        'Straight-Leg', 'Jogger', 'Tapered',
        '直筒', '束脚', '锥形',
        'straight-leg', 'jogger', 'tapered',
        'Straight Leg', 'Jogger Pants', 'Tapered Pants',
    }


# Load core subcategories at module import
CORE_SUBCATEGORIES: Set[str] = load_core_subcategories()


def is_core_subcategory(category_name: Optional[str]) -> bool:
    """
    Check if a category is a core subcategory.
    
    Per client requirement E-04, W-01, I-05:
    Core subcategories must ALWAYS be evaluated by Step 9,
    even if climate/season logic would normally deprioritize them.
    
    Args:
        category_name: Product category name (sub_cate_name)
    
    Returns:
        True if this is a core subcategory
    """
    if category_name is None:
        return False
    
    # Check exact match
    if category_name in CORE_SUBCATEGORIES:
        return True
    
    # Check partial match
    category_lower = category_name.lower()
    for core in CORE_SUBCATEGORIES:
        if core.lower() in category_lower or category_lower in core.lower():
            return True
    
    return False


def get_minimum_reference(
    manual_plan_minimum: Optional[float],
    cluster_p10_rate: Optional[float],
    config: Step9Config = DEFAULT_CONFIG
) -> tuple:
    """
    Get minimum unit rate using 3-level fallback logic.
    
    Priority order (use first NON-NULL value):
    1. Manual Plan Minimum (customer-provided)
    2. Cluster-level P10 unit rate
    3. Global fallback minimum
    
    Args:
        manual_plan_minimum: Customer-provided minimum (if any)
        cluster_p10_rate: 10th percentile of cluster unit rates
        config: Step 9 configuration
    
    Returns:
        Tuple of (minimum_value, MinimumReferenceSource)
    """
    if manual_plan_minimum is not None and manual_plan_minimum > 0:
        return (manual_plan_minimum, MinimumReferenceSource.MANUAL_PLAN)
    
    if cluster_p10_rate is not None and cluster_p10_rate > 0:
        return (cluster_p10_rate, MinimumReferenceSource.CLUSTER_P10)
    
    return (config.global_minimum_unit_rate, MinimumReferenceSource.GLOBAL_FALLBACK)


def validate_config_against_requirements() -> Dict[str, bool]:
    """
    Validate current configuration against customer requirements.
    
    Returns:
        Dictionary of requirement checks
    """
    checks = {
        'E-04_core_subcategories_loaded': len(CORE_SUBCATEGORIES) > 0,
        'E-06_never_decrease': DEFAULT_CONFIG.never_decrease,
        'E-05_max_increase_capped': DEFAULT_CONFIG.max_increase_percentage <= 0.20,
        'I-05_core_subcategories_configurable': (
            STEP9_CONFIG_PATH.exists() or STEP7_CONFIG_PATH.exists()
        ),
    }
    return checks
