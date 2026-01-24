"""
Climate Configuration for Step 7 Time-Aware Enhancement

This module contains temperature band definitions, category mappings,
and season phase configurations used by the enhanced Step 7 module.

Author: Data Pipeline Team
Date: January 2026
"""

from enum import Enum
from typing import Dict, List


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
