"""
Step 12 Configuration: Performance Gap Scaling Settings

CRITICAL BOUNDARY DEFINITION:
- Step 11 decides WHAT to grow (is_growth_candidate, opportunity_score)
- Step 12 decides HOW MUCH to grow (recommended_adjustment_quantity)

Step 12 MUST NOT:
- Re-decide eligibility (that's Step 11's job)
- Override Step 9 below-minimum protection
- Conflict with Step 10 overstock reduction
- Duplicate Step 11 opportunity identification

Step 12 MUST:
- Scale ONLY Step 11-approved SPUs
- Quantify performance gaps between stores within same cluster
- Recommend bounded, explainable inventory adjustments
- Provide full decision traceability

Author: Data Pipeline Team
Date: January 2026
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from pathlib import Path


class ScalingTier(Enum):
    """Scaling magnitude tiers based on performance gap severity."""
    MINIMAL = "Minimal Adjustment"      # Small gap, conservative scaling
    MODERATE = "Moderate Adjustment"    # Medium gap, standard scaling
    AGGRESSIVE = "Aggressive Adjustment" # Large gap, maximum scaling


@dataclass
class Step12Config:
    """Configuration for Step 12 Performance Gap Scaling."""
    
    # CRITICAL: Step 12 only processes Step 11 candidates
    require_step11_candidate: bool = True  # MUST be True
    
    # Performance Gap Definition (Axis A)
    gap_calculation_method: str = "cluster_percentile"  # vs cluster P75
    cluster_percentile_benchmark: int = 75  # Compare against 75th percentile
    min_cluster_size: int = 5  # Minimum stores for valid peer comparison
    
    # Controlled Scaling Logic (Axis B)
    min_gap_threshold: float = 0.10  # Minimum gap ratio to trigger scaling
    
    # Multi-factor Scaling Bounds (Axis C)
    base_scaling_factor: float = 0.5  # Base scaling (50% of gap)
    affinity_boost_max: float = 0.2   # Max boost from store affinity
    traffic_dampener_max: float = 0.3 # Max dampening from traffic mismatch
    
    # Hard Safety Caps (Axis D)
    max_increase_pct_of_current: float = 0.50  # Max 50% increase vs current
    max_increase_pct_of_cluster_median: float = 0.30  # Max 30% vs cluster median
    max_absolute_increase: float = 50.0  # Max 50 units per recommendation
    min_increase_quantity: float = 1.0   # Minimum 1 unit to recommend
    
    # Step 9/10 Conflict Prevention
    dampen_if_step9_applied: float = 0.5  # 50% dampening if Step 9 boosted
    block_if_step10_reduced: bool = True  # Block if Step 10 flagged reduction
    
    # Investment thresholds
    min_investment_threshold: float = 50.0  # Minimum ¥50 investment
    max_investment_per_store: float = 10000.0  # Max ¥10,000 per store


# Default configuration
DEFAULT_CONFIG = Step12Config()

# Paths to upstream step outputs
STEP11_OUTPUT_PATH = Path(__file__).parent.parent / "step11" / "step11_enhanced_results.csv"
STEP9_OUTPUT_PATH = Path(__file__).parent.parent / "step9" / "step9_improved_clusters_results.csv"
STEP10_OUTPUT_PATH = Path(__file__).parent.parent / "step10" / "step10_improved_clusters_results.csv"


# Boundary statements for documentation
STEP12_BOUNDARY_STATEMENTS = [
    "Step 12 scales ONLY SPUs already marked as candidates by Step 11.",
    "Step 12 does NOT decide whether to scale - only how much.",
    "Step 12 does NOT duplicate Step 11 opportunity identification.",
    "Step 12 respects Step 9 below-minimum protection (dampening applied).",
    "Step 12 respects Step 10 overstock reduction (blocked if reduced).",
    "All scaling decisions are bounded by hard safety caps.",
    "Every recommendation includes full decision traceability.",
]


def validate_step12_boundaries() -> dict:
    """Validate Step 12 configuration against boundary requirements."""
    checks = {
        'requires_step11_candidate': DEFAULT_CONFIG.require_step11_candidate,
        'has_gap_threshold': DEFAULT_CONFIG.min_gap_threshold > 0,
        'has_safety_caps': (
            DEFAULT_CONFIG.max_increase_pct_of_current > 0 and
            DEFAULT_CONFIG.max_absolute_increase > 0
        ),
        'respects_step9': DEFAULT_CONFIG.dampen_if_step9_applied > 0,
        'respects_step10': DEFAULT_CONFIG.block_if_step10_reduced,
        'no_eligibility_logic': True,  # By design - no eligibility in Step 12
    }
    return checks
