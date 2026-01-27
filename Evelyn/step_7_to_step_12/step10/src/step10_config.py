"""
Step 10 Configuration: Overcapacity Reduction Settings

This module contains all configuration for Step 10, including:
- Reduction eligibility gate (CRITICAL: respect Step 7-9 increases)
- Core subcategory protection
- Overcapacity thresholds

Per Customer Requirement:
- Any SPU increased in Step 7, 8, or 9 MUST NOT be reduced in Step 10
- Core subcategories must be protected from aggressive reduction
- Step 10 is a cleanup layer, NOT an optimizer

Author: Data Pipeline Team
Date: January 2026
"""

import json
from pathlib import Path
from typing import Set, Dict, Optional
from dataclasses import dataclass


@dataclass
class Step10Config:
    """Configuration for Step 10 Overcapacity Reduction."""
    # Reduction thresholds
    min_reduction_quantity: float = 1.0  # Minimum units to recommend reduction
    max_reduction_percentage: float = 0.40  # Max 40% reduction per SPU
    min_sales_volume: float = 20.0  # Minimum sales to consider
    
    # Cluster settings
    min_cluster_size: int = 3  # Minimum stores in cluster
    
    # Core subcategory protection
    protect_core_subcategories: bool = True  # Reduce less aggressively
    core_subcategory_max_reduction: float = 0.20  # Max 20% for core
    
    # Step 7-9 integration (CRITICAL)
    respect_prior_increases: bool = True  # MUST be True per requirement
    
    # Period settings
    data_period_days: int = 15
    target_period_days: int = 15


# Default configuration
DEFAULT_CONFIG = Step10Config()

# Path to core subcategories config (shared with Step 7/9)
STEP7_CONFIG_PATH = Path(__file__).parent.parent / "step7" / "core_subcategories_config.json"
STEP9_CONFIG_PATH = Path(__file__).parent.parent / "step9" / "step9_core_subcategories_config.json"


def load_core_subcategories() -> Set[str]:
    """
    Load core subcategories from config file.
    
    Per Customer Requirement E-04, W-01, I-05:
    Core subcategories must be protected from aggressive reduction.
    
    Returns:
        Set of core subcategory names
    """
    # Try Step 7 shared config first (canonical source)
    if STEP7_CONFIG_PATH.exists():
        try:
            with open(STEP7_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'core_subcategories' in config:
                    print(f"✅ Loaded core subcategories from Step 7 config")
                    return set(config['core_subcategories'])
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading Step 7 config: {e}")
    
    # Fallback to defaults
    print("⚠️ Using default core subcategories (config file not found)")
    return {
        '直筒裤', '束脚裤', '锥形裤',
        'Straight-Leg', 'Jogger', 'Tapered',
    }


# Load core subcategories at module import
CORE_SUBCATEGORIES: Set[str] = load_core_subcategories()


def is_core_subcategory(category_name: Optional[str]) -> bool:
    """
    Check if a category is a core subcategory.
    
    Core subcategories receive protection from aggressive reduction.
    
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


def validate_config_against_requirements() -> Dict[str, bool]:
    """
    Validate current configuration against customer requirements.
    
    Returns:
        Dictionary of requirement checks
    """
    checks = {
        'CRITICAL_respect_prior_increases': DEFAULT_CONFIG.respect_prior_increases,
        'E-04_core_subcategories_loaded': len(CORE_SUBCATEGORIES) > 0,
        'E-05_max_reduction_capped': DEFAULT_CONFIG.max_reduction_percentage <= 0.40,
        'core_subcategory_protection': DEFAULT_CONFIG.protect_core_subcategories,
    }
    return checks
