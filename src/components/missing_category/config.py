"""Configuration for Missing Category/SPU Rule step."""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class MissingCategoryConfig:
    """
    Configuration for Missing Category/SPU Rule analysis.
    
    Attributes:
        analysis_level: 'subcategory' or 'spu' - determines analysis granularity
        period_label: Period identifier (e.g., '202510A')
        min_cluster_adoption: Minimum % of stores in cluster selling feature
        min_cluster_sales: Minimum total sales threshold for feature
        min_opportunity_value: Minimum value for opportunity to be considered
        use_blended_seasonal: Enable seasonal data blending
        seasonal_weight: Weight for seasonal data (0.0-1.0)
        recent_weight: Weight for recent data (0.0-1.0)
        seasonal_years_back: Number of years to look back for seasonal data
        min_stores_selling: Minimum stores selling for sell-through validation
        min_adoption: Minimum adoption rate for validation
        min_predicted_st: Minimum predicted sell-through rate
        use_roi: Enable ROI calculation and filtering
        roi_min_threshold: Minimum ROI threshold
        min_margin_uplift: Minimum margin uplift threshold
        min_comparables: Minimum number of comparable stores
        data_period_days: Days in data period
        target_period_days: Days in target period
    """
    
    # Analysis settings
    analysis_level: str = 'subcategory'
    period_label: str = '202510A'
    
    # Thresholds (vary by analysis level)
    # NOTE: Legacy output shows min adoption of 80%, not 70%
    # This is the CRITICAL threshold that determines how many well-selling features are identified
    min_cluster_stores_selling: float = 0.80  # 80% adoption threshold (matches legacy)
    min_cluster_sales_threshold: float = 100.0
    min_opportunity_value: float = 50.0
    
    # Seasonal blending
    use_blended_seasonal: bool = False
    seasonal_weight: float = 0.6
    recent_weight: float = 0.4
    seasonal_years_back: int = 1
    
    # Sell-through validation
    min_stores_selling: int = 5
    min_adoption: float = 0.25
    min_predicted_st: float = 0.30
    
    # ROI settings (LEGACY DEFAULT: True)
    use_roi: bool = True
    roi_min_threshold: float = 0.30
    min_margin_uplift: float = 100.0
    min_comparables: int = 10
    
    # Scaling
    data_period_days: int = 15
    target_period_days: int = 15
    
    def __post_init__(self):
        """Adjust thresholds based on analysis level."""
        if self.analysis_level == 'spu':
            # SPU analysis requires higher thresholds
            self.min_cluster_stores_selling = 0.80
            self.min_cluster_sales_threshold = 1500.0
        
        # Validate weights sum to 1.0
        if self.use_blended_seasonal:
            total_weight = self.seasonal_weight + self.recent_weight
            if abs(total_weight - 1.0) > 0.01:
                raise ValueError(
                    f"Seasonal and recent weights must sum to 1.0, got {total_weight}"
                )
    
    @classmethod
    def from_env_and_args(cls, **kwargs):
        """
        Create config from environment variables and arguments.
        
        Environment variables override defaults, kwargs override environment.
        
        Args:
            **kwargs: Configuration overrides
            
        Returns:
            MissingCategoryConfig instance
        """
        config_dict = {}
        
        # Load from environment
        env_mappings = {
            'ANALYSIS_LEVEL': 'analysis_level',
            'PERIOD_LABEL': 'period_label',
            'USE_BLENDED_SEASONAL': 'use_blended_seasonal',
            'SEASONAL_WEIGHT': 'seasonal_weight',
            'USE_ROI': 'use_roi',
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion
                if config_key in ['use_blended_seasonal', 'use_roi']:
                    config_dict[config_key] = value.lower() in ('true', '1', 'yes')
                elif config_key in ['seasonal_weight']:
                    config_dict[config_key] = float(value)
                else:
                    config_dict[config_key] = value
        
        # Override with kwargs
        config_dict.update(kwargs)
        
        return cls(**config_dict)
    
    @property
    def feature_column(self) -> str:
        """Get the feature column name based on analysis level."""
        return 'spu_code' if self.analysis_level == 'spu' else 'sub_cate_name'
    
    @property
    def scaling_factor(self) -> float:
        """Get the scaling factor for quantity calculations."""
        return self.target_period_days / self.data_period_days
