"""ROI calculator component for financial analysis."""

import numpy as np
import fireducks.pandas as pd
from typing import Optional, Tuple
from .config import MissingCategoryConfig


class ROICalculator:
    """
    Calculates ROI metrics and filters opportunities by financial criteria.
    
    Calculates:
    - Unit cost (from price and margin)
    - Margin per unit
    - Total margin uplift
    - Investment required
    - ROI (return on investment)
    """
    
    def __init__(self, config: MissingCategoryConfig, logger):
        """
        Initialize ROI calculator.
        
        Args:
            config: Configuration for the analysis
            logger: Pipeline logger instance
        """
        self.config = config
        self.logger = logger
    
    def calculate_and_filter(
        self,
        opportunities_df: pd.DataFrame,
        margin_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate ROI metrics and filter by thresholds.
        
        Args:
            opportunities_df: DataFrame with opportunities
            margin_df: DataFrame with margin rates
            
        Returns:
            DataFrame with ROI metrics added and filtered
        """
        if not self.config.use_roi:
            self.logger.info("ROI calculation disabled, skipping")
            return opportunities_df
        
        if len(opportunities_df) == 0:
            self.logger.warning("No opportunities to calculate ROI for")
            return opportunities_df
        
        self.logger.info(f"Calculating ROI for {len(opportunities_df)} opportunities...")
        
        # Build margin lookup
        margin_lookup = self._build_margin_lookup(margin_df)
        
        # Calculate ROI metrics
        enriched = opportunities_df.copy()
        
        enriched[['margin_rate', 'margin_source']] = enriched.apply(
            lambda row: pd.Series(self._resolve_margin_rate(row, margin_lookup)),
            axis=1
        )
        
        # Calculate financial metrics
        enriched['unit_cost'] = enriched.apply(
            lambda row: row['unit_price'] * (1 - row['margin_rate']),
            axis=1
        )
        
        enriched['margin_per_unit'] = enriched.apply(
            lambda row: row['unit_price'] - row['unit_cost'],
            axis=1
        )
        
        # LEGACY QUIRK: Calculate expected_units from median_sales (line 1005)
        # This is DIFFERENT from recommended_quantity!
        # Legacy uses median_sales for ROI, but robust median for recommendation
        enriched['expected_units'] = enriched.apply(
            lambda row: int(max(1.0, np.ceil(row['median_sales'] / max(1e-6, row['unit_price'])))),
            axis=1
        )
        
        # Use expected_units for ROI calculation (NOT recommended_quantity!)
        enriched['margin_uplift'] = enriched.apply(
            lambda row: row['margin_per_unit'] * row['expected_units'],
            axis=1
        )
        
        enriched['investment_required'] = enriched.apply(
            lambda row: row['unit_cost'] * row['expected_units'],
            axis=1
        )
        
        enriched['roi'] = enriched.apply(
            lambda row: row['margin_uplift'] / row['investment_required']
            if row['investment_required'] > 0 else 0.0,
            axis=1
        )
        
        # Apply filters
        filtered = self._apply_roi_filter(enriched)
        
        return filtered
    
    def _build_margin_lookup(self, margin_df: pd.DataFrame) -> dict:
        """
        Build margin rate lookup dictionary.
        
        Args:
            margin_df: DataFrame with margin rates
            
        Returns:
            Dictionary with margin lookups
        """
        if len(margin_df) == 0:
            return {'store_feature': {}, 'store_avg': {}}
        
        feature_col = self.config.feature_column
        
        # Store-feature level lookup
        store_feature_lookup = {}
        for _, row in margin_df.iterrows():
            if feature_col in row and pd.notna(row[feature_col]):
                key = (row['str_code'], row[feature_col])
                store_feature_lookup[key] = row['margin_rate']
        
        # Store average lookup
        store_avg = margin_df.groupby('str_code')['margin_rate'].mean().to_dict()
        
        return {
            'store_feature': store_feature_lookup,
            'store_avg': store_avg
        }
    
    def _resolve_margin_rate(
        self,
        opportunity: pd.Series,
        margin_lookup: dict
    ) -> Tuple[float, str]:
        """
        Resolve margin rate with 2-level fallback.
        
        Priority:
        1. Store + feature specific margin
        2. Store average margin
        3. Default margin (30%)
        
        Args:
            opportunity: Opportunity data
            margin_lookup: Margin lookup dictionary
            
        Returns:
            Tuple of (margin_rate, source)
        """
        store_code = opportunity['str_code']
        feature = opportunity[self.config.feature_column]
        
        # Level 1: Store + feature specific
        key = (store_code, feature)
        if key in margin_lookup['store_feature']:
            return margin_lookup['store_feature'][key], 'store_feature'
        
        # Level 2: Store average
        if store_code in margin_lookup['store_avg']:
            return margin_lookup['store_avg'][store_code], 'store_avg'
        
        # Level 3: Default (LEGACY: 45%)
        default_margin = 0.45  # 45% default margin (matching legacy)
        return default_margin, 'default'
    
    def _apply_roi_filter(self, opportunities_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter opportunities by ROI criteria (LEGACY LOGIC).
        
        Criteria (line 1010 of legacy):
        1. ROI >= roi_min_threshold (30%)
        2. Margin uplift >= min_margin_uplift ($100)
        3. n_comparables >= min_comparables (10 stores)
        
        Args:
            opportunities_df: DataFrame with ROI metrics
            
        Returns:
            Filtered DataFrame
        """
        initial_count = len(opportunities_df)
        
        # Filter by ROI threshold
        filtered = opportunities_df[
            opportunities_df['roi'] >= self.config.roi_min_threshold
        ].copy()
        
        roi_filtered = initial_count - len(filtered)
        
        # Filter by margin uplift
        filtered = filtered[
            filtered['margin_uplift'] >= self.config.min_margin_uplift
        ].copy()
        
        margin_filtered = (initial_count - roi_filtered) - len(filtered)
        
        # Filter by n_comparables (LEGACY: line 1010)
        filtered = filtered[
            filtered['n_comparables'] >= self.config.min_comparables
        ].copy()
        
        comparables_filtered = (initial_count - roi_filtered - margin_filtered) - len(filtered)
        
        self.logger.info(
            f"ROI filtering: {initial_count} → {len(filtered)} opportunities. "
            f"Filtered: {roi_filtered} by ROI "
            f"(>={self.config.roi_min_threshold:.0%}), "
            f"{margin_filtered} by margin uplift "
            f"(>=${self.config.min_margin_uplift:,.0f}), "
            f"{comparables_filtered} by comparables "
            f"(>={self.config.min_comparables})"
        )
        
        # Log statistics for remaining opportunities
        if len(filtered) > 0:
            avg_roi = filtered['roi'].mean()
            avg_margin = filtered['margin_uplift'].mean()
            total_investment = filtered['investment_required'].sum()
            total_margin = filtered['margin_uplift'].sum()
            
            self.logger.info(
                f"ROI metrics (filtered): "
                f"Avg ROI={avg_roi:.1%}, "
                f"Avg margin=${avg_margin:,.0f}, "
                f"Total investment=${total_investment:,.0f}, "
                f"Total margin=${total_margin:,.0f}"
            )
        
        return filtered
    
    def get_roi_summary(self, opportunities_df: pd.DataFrame) -> dict:
        """
        Generate ROI summary statistics.
        
        Args:
            opportunities_df: DataFrame with ROI metrics
            
        Returns:
            Dictionary with summary statistics
        """
        if len(opportunities_df) == 0 or 'roi' not in opportunities_df.columns:
            return {
                'total_opportunities': 0,
                'total_investment': 0.0,
                'total_margin_uplift': 0.0,
                'total_roi': 0.0,
                'avg_roi': 0.0
            }
        
        return {
            'total_opportunities': len(opportunities_df),
            'total_investment': opportunities_df['investment_required'].sum(),
            'total_margin_uplift': opportunities_df['margin_uplift'].sum(),
            'total_roi': (
                opportunities_df['margin_uplift'].sum() /
                opportunities_df['investment_required'].sum()
                if opportunities_df['investment_required'].sum() > 0 else 0.0
            ),
            'avg_roi': opportunities_df['roi'].mean()
        }
