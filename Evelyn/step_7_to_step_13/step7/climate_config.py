"""
Climate Configuration for Step 7 Time-Aware Enhancement

This module contains temperature band definitions, category mappings,
and season phase configurations used by the enhanced Step 7 module.

CONFIGURABLE SETTINGS:
- CORE_SUBCATEGORIES: Products that are always eligible (business-critical)
- CATEGORY_TEMPERATURE_MAPPING: Maps product categories to temperature bands
- TEMPERATURE_THRESHOLDS: Temperature ranges for each band

Author: Data Pipeline Team
Date: January 2026
"""

from enum import Enum
from typing import Dict, List, Set
import json
import os


class TemperatureBand(Enum):
    """Temperature bands for SPU climate suitability."""
    COLD = "Cold"           # ≤ 10°C - Winter outerwear, heavy items
    COOL = "Cool"           # 10-18°C - Light jackets, transitional
    WARM = "Warm"           # 18-26°C - Light clothing, spring/fall
    HOT = "Hot"             # > 26°C - Summer items, breathable
    ALL_SEASON = "All"      # Any temperature - basics, accessories


class SeasonPhase(Enum):
    """Season phases for time-aware logic."""
    WINTER_PEAK = "winter_peak"       # Dec, Jan, Feb
    SPRING_TRANSITION = "spring"      # Mar, Apr, May
    SUMMER_PEAK = "summer_peak"       # Jun, Jul, Aug
    FALL_TRANSITION = "fall"          # Sep, Oct, Nov


# =============================================================================
# CORE SUBCATEGORIES (CONFIGURABLE)
# =============================================================================
# These subcategories are ALWAYS eligible regardless of climate/season.
# Per client requirement E-04, W-01, I-05:
# "Core styles should receive special attention"
#
# TO MODIFY: Update this list or load from external config file
# =============================================================================

# Default core subcategories (can be overridden by config file)
DEFAULT_CORE_SUBCATEGORIES: Set[str] = {
    # Chinese names
    '直筒裤', '束脚裤', '锥形裤',
    # English names
    'Straight-Leg', 'Jogger', 'Tapered',
    # Variations
    '直筒', '束脚', '锥形',
    'straight-leg', 'jogger', 'tapered',
    'Straight Leg', 'Jogger Pants', 'Tapered Pants',
}

# Path to external config file (optional)
CORE_SUBCATEGORIES_CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), 
    'core_subcategories_config.json'
)


def load_core_subcategories() -> Set[str]:
    """
    Load core subcategories from config file if available, else use defaults.
    
    This allows the business team to modify core subcategories without
    changing code. Simply update core_subcategories_config.json.
    
    Returns:
        Set of core subcategory names
    """
    if os.path.exists(CORE_SUBCATEGORIES_CONFIG_FILE):
        try:
            with open(CORE_SUBCATEGORIES_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'core_subcategories' in config:
                    return set(config['core_subcategories'])
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading core subcategories config: {e}")
            print("   Falling back to default core subcategories")
    
    return DEFAULT_CORE_SUBCATEGORIES


# Load core subcategories at module import
CORE_SUBCATEGORIES: Set[str] = load_core_subcategories()


def is_core_subcategory(category_name: str) -> bool:
    """
    Check if a category is a core subcategory that must always be eligible.
    
    Per client requirement E-04, W-01, I-05:
    Core subcategories must NEVER be filtered by climate/season eligibility logic.
    
    Args:
        category_name: Product category name (sub_cate_name)
    
    Returns:
        True if this is a core subcategory that should always be ELIGIBLE
    """
    if category_name is None:
        return False
    
    # Check exact match
    if category_name in CORE_SUBCATEGORIES:
        return True
    
    # Check partial match (category contains core keyword)
    category_lower = category_name.lower()
    for core in CORE_SUBCATEGORIES:
        if core.lower() in category_lower or category_lower in core.lower():
            return True
    
    return False


def update_core_subcategories(new_subcategories: List[str], save_to_file: bool = True) -> None:
    """
    Update the core subcategories list.
    
    This function allows programmatic updates to core subcategories.
    Changes can optionally be persisted to the config file.
    
    Args:
        new_subcategories: List of new core subcategory names to add
        save_to_file: If True, save changes to config file
    """
    global CORE_SUBCATEGORIES
    CORE_SUBCATEGORIES = CORE_SUBCATEGORIES.union(set(new_subcategories))
    
    if save_to_file:
        config = {'core_subcategories': list(CORE_SUBCATEGORIES)}
        with open(CORE_SUBCATEGORIES_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ Core subcategories saved to {CORE_SUBCATEGORIES_CONFIG_FILE}")


# =============================================================================
# CATEGORY TO TEMPERATURE BAND MAPPING
# =============================================================================

# Category to temperature band mapping (business rule)
# This maps Fast Fish product categories to their appropriate temperature bands
CATEGORY_TEMPERATURE_MAPPING: Dict[str, TemperatureBand] = {
    # Winter items (Cold: ≤10°C)
    "羽绒服": TemperatureBand.COLD,      # Down jackets
    "棉服": TemperatureBand.COLD,        # Padded jackets
    "毛呢大衣": TemperatureBand.COLD,    # Wool coats
    "皮草": TemperatureBand.COLD,        # Fur coats
    "厚外套": TemperatureBand.COLD,      # Heavy outerwear
    
    # Transitional items (Cool: 10-18°C)
    "风衣": TemperatureBand.COOL,        # Trench coats
    "夹克": TemperatureBand.COOL,        # Jackets
    "针织衫": TemperatureBand.COOL,      # Knitwear
    "卫衣": TemperatureBand.COOL,        # Hoodies
    "薄外套": TemperatureBand.COOL,      # Light outerwear
    
    # Spring/Fall items (Warm: 18-26°C)
    "衬衫": TemperatureBand.WARM,        # Shirts
    "长裤": TemperatureBand.WARM,        # Long pants
    "连衣裙": TemperatureBand.WARM,      # Dresses (general)
    "半身裙": TemperatureBand.WARM,      # Skirts
    
    # Summer items (Hot: >26°C)
    "T恤": TemperatureBand.HOT,          # T-shirts
    "短裤": TemperatureBand.HOT,         # Shorts
    "吊带": TemperatureBand.HOT,         # Tank tops
    "凉鞋": TemperatureBand.HOT,         # Sandals
    "短袖": TemperatureBand.HOT,         # Short sleeves
    
    # All-season items
    "内衣": TemperatureBand.ALL_SEASON,  # Underwear
    "配饰": TemperatureBand.ALL_SEASON,  # Accessories
    "包包": TemperatureBand.ALL_SEASON,  # Bags
    "鞋类": TemperatureBand.ALL_SEASON,  # General footwear
}

# Temperature thresholds for band matching
TEMPERATURE_THRESHOLDS: Dict[TemperatureBand, tuple] = {
    TemperatureBand.COLD: (-float('inf'), 10),
    TemperatureBand.COOL: (10, 18),
    TemperatureBand.WARM: (18, 26),
    TemperatureBand.HOT: (26, float('inf')),
    TemperatureBand.ALL_SEASON: (-float('inf'), float('inf')),
}

# Month to season phase mapping
MONTH_TO_SEASON: Dict[int, SeasonPhase] = {
    12: SeasonPhase.WINTER_PEAK, 1: SeasonPhase.WINTER_PEAK, 2: SeasonPhase.WINTER_PEAK,
    3: SeasonPhase.SPRING_TRANSITION, 4: SeasonPhase.SPRING_TRANSITION, 5: SeasonPhase.SPRING_TRANSITION,
    6: SeasonPhase.SUMMER_PEAK, 7: SeasonPhase.SUMMER_PEAK, 8: SeasonPhase.SUMMER_PEAK,
    9: SeasonPhase.FALL_TRANSITION, 10: SeasonPhase.FALL_TRANSITION, 11: SeasonPhase.FALL_TRANSITION,
}

# Which temperature bands are appropriate for each season
SEASON_APPROPRIATE_BANDS: Dict[SeasonPhase, List[TemperatureBand]] = {
    SeasonPhase.WINTER_PEAK: [TemperatureBand.COLD, TemperatureBand.COOL, TemperatureBand.ALL_SEASON],
    SeasonPhase.SPRING_TRANSITION: [TemperatureBand.COOL, TemperatureBand.WARM, TemperatureBand.ALL_SEASON],
    SeasonPhase.SUMMER_PEAK: [TemperatureBand.WARM, TemperatureBand.HOT, TemperatureBand.ALL_SEASON],
    SeasonPhase.FALL_TRANSITION: [TemperatureBand.COOL, TemperatureBand.WARM, TemperatureBand.ALL_SEASON],
}
