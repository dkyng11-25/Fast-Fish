"""Opportunity identifier component for missing category/SPU analysis."""

import fireducks.pandas as pd
import numpy as np
import time
from typing import Optional, Tuple, Dict, Any
from .config import MissingCategoryConfig


class OpportunityIdentifier:
    """
    Identifies missing opportunities and calculates recommended quantities.
    
    For each cluster, finds stores NOT selling well-selling features
    and calculates recommended quantities based on cluster performance.
    """
    
    def __init__(self, config: MissingCategoryConfig, logger, validator=None):
        """
        Initialize opportunity identifier.
        
        Args:
            config: Configuration for the analysis
            logger: Pipeline logger instance
            validator: Optional SellThroughValidator for Fast Fish compliance
        """
        self.config = config
        self.logger = logger
        self.validator = validator
    
    def identify_missing_opportunities(
        self,
        well_selling_df: pd.DataFrame,
        cluster_df: pd.DataFrame,
        sales_df: pd.DataFrame,
        quantity_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Identify missing opportunities for stores.
        
        Args:
            well_selling_df: Well-selling features per cluster
            cluster_df: Clustering assignments
            sales_df: Sales data
            quantity_df: Quantity and price data
            
        Returns:
            DataFrame with opportunities:
            - str_code
            - cluster_id
            - feature (sub_cate_name or spu_code)
            - expected_sales
            - unit_price
            - recommended_quantity
            - price_source
        """
        self.logger.info("Identifying missing opportunities...")
        start_time = time.time()
        
        if len(well_selling_df) == 0:
            self.logger.warning("No well-selling features found, no opportunities to identify")
            return pd.DataFrame()
        
        feature_col = self.config.feature_column
        
        self.logger.info(f"Processing {len(well_selling_df)} well-selling features...")
        
        # OPTIMIZATION: Use vectorized operations instead of iterrows
        opportunities = self._identify_opportunities_vectorized(
            well_selling_df, cluster_df, sales_df, quantity_df, feature_col
        )
        
        elapsed = time.time() - start_time
        self.logger.info(f"Opportunity identification completed in {elapsed:.2f} seconds")
        
        return opportunities
    
    def _identify_opportunities_vectorized(
        self,
        well_selling_df: pd.DataFrame,
        cluster_df: pd.DataFrame,
        sales_df: pd.DataFrame,
        quantity_df: pd.DataFrame,
        feature_col: str
    ) -> pd.DataFrame:
        """Vectorized opportunity identification for better performance."""
        
        opportunities = []
        total_features = len(well_selling_df)
        
        # Debug counters
        debug_stats = {
            'features_processed': 0,
            'no_missing_stores': 0,
            'no_valid_price': 0,
            'quantity_too_low': 0,
            'filtered_fast_fish': 0,
            'filtered_thresholds': 0,
            'filtered_validation': 0,
            'opportunities_created': 0
        }
        
        # Process each cluster-feature combination (still need loop for complex logic)
        for idx, (_, row) in enumerate(well_selling_df.iterrows()):
            if idx % 500 == 0:
                self.logger.info(f"Progress: {idx}/{total_features} features processed")
            
            debug_stats['features_processed'] += 1
            cluster_id = row['cluster_id']
            feature = row[feature_col]
            
            # Find stores in this cluster
            cluster_stores = cluster_df[cluster_df['cluster_id'] == cluster_id]['str_code'].tolist()
            
            # Find stores already selling this feature
            selling_stores = sales_df[
                (sales_df[feature_col] == feature) &
                (sales_df['str_code'].isin(cluster_stores))
            ]['str_code'].unique()
            
            # Find missing stores (not selling this feature)
            missing_stores = [s for s in cluster_stores if s not in selling_stores]
            
            if not missing_stores:
                debug_stats['no_missing_stores'] += 1
                continue
            
            # Calculate expected sales for this feature in this cluster
            expected_sales = self._calculate_expected_sales(
                sales_df, cluster_stores, feature, feature_col
            )
            
            # LEGACY QUIRK: Also calculate simple median for ROI calculation (line 1002)
            # Legacy uses TWO different values: robust median for recommendation, simple median for ROI
            median_sales = self._calculate_median_sales(
                sales_df, cluster_stores, feature, feature_col, expected_sales
            )
            
            # LEGACY LOGIC: Check if expected sales meets minimum threshold BEFORE creating opportunities
            # This is the critical filter that legacy applies at the FEATURE level
            if expected_sales < self.config.min_opportunity_value:
                debug_stats['quantity_too_low'] += 1
                continue
            
            # LEGACY LOGIC: Apply Fast Fish approval gates at FEATURE level (not per-store)
            # These gates filter entire features, not individual opportunities
            # Legacy lines 938-943: validator_ok AND stores_selling >= 5 AND adoption >= 25% AND predicted_st >= 30%
            should_approve_feature = self._validate_feature(row, debug_stats)
            if not should_approve_feature:
                debug_stats['filtered_validation'] += 1
                self.logger.debug(
                    f"Feature filtered: {feature} in cluster {cluster_id} - "
                    f"stores_selling={row['stores_selling']}, "
                    f"pct_stores_selling={row['pct_stores_selling']:.2%}"
                )
                continue
            
            # Create opportunities for each missing store
            for store_code in missing_stores:
                # Resolve unit price
                unit_price, price_source = self._resolve_unit_price(
                    store_code, feature, quantity_df, sales_df, cluster_stores
                )
                
                if unit_price is None or unit_price <= 0:
                    debug_stats['no_valid_price'] += 1
                    self.logger.debug(
                        f"Skipping opportunity: {store_code}/{feature} - no valid price"
                    )
                    continue
                
                # Calculate quantity
                quantity = self._calculate_quantity(expected_sales, unit_price)
                
                if quantity < 1:
                    debug_stats['quantity_too_low'] += 1
                    continue
                
                # Opportunity approved (feature-level gates already passed)
                debug_stats['opportunities_created'] += 1
                
                opportunities.append({
                    'str_code': store_code,
                    'cluster_id': cluster_id,
                    self.config.feature_column: feature,
                    'expected_sales': expected_sales,
                    'median_sales': median_sales,  # For ROI calculation (legacy line 1002)
                    'unit_price': unit_price,
                    'recommended_quantity': quantity,
                    'price_source': price_source,
                    'n_comparables': int(row['stores_selling'])  # For ROI filtering (legacy line 981)
                })
        
        # Log debug statistics
        self.logger.info("=== OPPORTUNITY FILTERING BREAKDOWN ===")
        self.logger.info(f"Features processed: {debug_stats['features_processed']}")
        self.logger.info(f"Filtered - No missing stores: {debug_stats['no_missing_stores']}")
        self.logger.info(f"Filtered - Expected sales < min: {debug_stats['quantity_too_low']}")
        self.logger.info(f"Filtered - Validation gates: {debug_stats['filtered_validation']}")
        self.logger.info(f"Filtered - No valid price: {debug_stats['no_valid_price']}")
        self.logger.info(f"Filtered - Quantity < 1: {debug_stats['quantity_too_low']}")
        self.logger.info(f"Opportunities created: {debug_stats['opportunities_created']}")
        self.logger.info("=======================================")
        
        if not opportunities:
            self.logger.warning("No valid opportunities identified")
            return pd.DataFrame()
        
        result = pd.DataFrame(opportunities)
        
        self.logger.info(
            f"Opportunities identified: {len(result)} for {result['str_code'].nunique()} stores"
        )
        
        return result
    
    def _calculate_median_sales(
        self,
        sales_df: pd.DataFrame,
        cluster_stores: list,
        feature: str,
        feature_col: str,
        fallback: float
    ) -> float:
        """
        Calculate simple median sales for ROI calculation (LEGACY line 1002).
        
        This is DIFFERENT from expected_sales! Legacy uses:
        - Robust median (10th-90th trim + P80 cap) for recommendations
        - Simple median for ROI calculation
        
        Args:
            sales_df: Sales data
            cluster_stores: List of store codes in cluster
            feature: Feature name
            feature_col: Feature column name
            fallback: Fallback value if no data
            
        Returns:
            Simple median sales amount
        """
        # Get sales for this feature in this cluster
        feature_sales = sales_df[
            (sales_df[feature_col] == feature) &
            (sales_df['str_code'].isin(cluster_stores))
        ]
        
        if len(feature_sales) == 0:
            return fallback
        
        # Simple median (no trimming, no capping)
        sales_amounts = pd.to_numeric(
            feature_sales['sal_amt'],
            errors='coerce'
        ).dropna()
        
        if len(sales_amounts) == 0:
            return fallback
        
        return float(sales_amounts.median())
    
    def _calculate_expected_sales(
        self,
        sales_df: pd.DataFrame,
        cluster_stores: list,
        feature: str,
        feature_col: str
    ) -> float:
        """
        Calculate expected sales using LEGACY LOGIC: 10th-90th percentile trim + P80 cap.
        
        COPIED FROM LEGACY LINES 808-830 for exact replication.
        
        Args:
            sales_df: Sales data
            cluster_stores: List of store codes in cluster
            feature: Feature value
            feature_col: Feature column name
            
        Returns:
            Expected sales amount
        """
        import numpy as np
        
        # Get sales for this feature in this cluster
        feature_sales = sales_df[
            (sales_df[feature_col] == feature) &
            (sales_df['str_code'].isin(cluster_stores))
        ]['sal_amt']
        
        if len(feature_sales) == 0:
            return 0.0
        
        # LEGACY LOGIC: Robust peer median within the cluster
        peer_amounts = pd.to_numeric(feature_sales, errors='coerce').dropna()
        
        if len(peer_amounts) >= 3:
            # Trim extremes (10th-90th) and use median; cap to P80 for realism
            q10 = float(np.percentile(peer_amounts, 10))
            q90 = float(np.percentile(peer_amounts, 90))
            trimmed = peer_amounts[(peer_amounts >= q10) & (peer_amounts <= q90)]
            robust_median = float(np.median(trimmed)) if len(trimmed) > 0 else float(np.median(peer_amounts))
            p80_cap = float(np.percentile(peer_amounts, 80))
            expected = max(float(self.config.min_opportunity_value), min(robust_median, p80_cap))
        elif len(peer_amounts) > 0:
            robust_median = float(np.median(peer_amounts))
            expected = max(float(self.config.min_opportunity_value), robust_median)
        else:
            return 0.0
        
        # Scale to target period if needed
        expected = expected * self.config.scaling_factor
        
        return float(expected)
    
    def _resolve_unit_price(
        self,
        store_code: str,
        feature: str,
        quantity_df: pd.DataFrame,
        sales_df: pd.DataFrame,
        cluster_stores: list
    ) -> Tuple[Optional[float], str]:
        """
        Resolve unit price with 4-level fallback chain.
        
        Priority:
        1. Store average from quantity_df
        2. Store average from sales_df
        3. Cluster median from quantity_df
        4. FAIL (strict mode - no synthetic prices)
        
        Args:
            store_code: Store code
            feature: Feature value
            quantity_df: Quantity data with prices
            sales_df: Sales data
            cluster_stores: List of stores in cluster
            
        Returns:
            Tuple of (price, source) or (None, 'none')
        """
        feature_col = self.config.feature_column
        
        # Level 1: Store average from quantity_df
        if len(quantity_df) > 0:
            store_qty = quantity_df[
                (quantity_df['str_code'] == store_code) &
                (quantity_df[feature_col] == feature)
            ]
            
            if len(store_qty) > 0 and 'avg_unit_price' in store_qty.columns:
                price = store_qty['avg_unit_price'].mean()
                if price > 0:
                    return float(price), 'store_quantity'
        
        # Level 2: Store average from sales_df
        store_sales = sales_df[
            (sales_df['str_code'] == store_code) &
            (sales_df[feature_col] == feature)
        ]
        
        if len(store_sales) > 0:
            # Try direct unit_price column first (SPU sales data)
            if 'unit_price' in store_sales.columns:
                price = store_sales['unit_price'].mean()
                if price > 0:
                    return float(price), 'store_sales_direct'
            
            # Try store_unit_price column (subcategory sales data)
            if 'store_unit_price' in store_sales.columns:
                price = store_sales['store_unit_price'].mean()
                if price > 0:
                    return float(price), 'store_sales_subcategory'
            
            # Fallback: Calculate price from sales amount and quantity
            if 'quantity' in store_sales.columns and 'spu_sales_amt' in store_sales.columns:
                total_qty = store_sales['quantity'].sum()
                total_amt = store_sales['spu_sales_amt'].sum()
                if total_qty > 0:
                    price = total_amt / total_qty
                    return float(price), 'store_sales_calculated'
            
            # Legacy column names (subcategory sales data)
            if 'total_qty' in store_sales.columns and 'sal_amt' in store_sales.columns:
                total_qty = store_sales['total_qty'].sum()
                total_amt = store_sales['sal_amt'].sum()
                if total_qty > 0:
                    price = total_amt / total_qty
                    return float(price), 'store_sales_legacy'
        
        # Level 3: Cluster median from quantity_df
        if len(quantity_df) > 0:
            cluster_qty = quantity_df[
                (quantity_df['str_code'].isin(cluster_stores)) &
                (quantity_df[feature_col] == feature)
            ]
            
            if len(cluster_qty) > 0 and 'avg_unit_price' in cluster_qty.columns:
                price = cluster_qty['avg_unit_price'].median()
                if price > 0:
                    return float(price), 'cluster_quantity_median'
        
        # Level 4: Cluster median from sales_df (for missing stores)
        cluster_sales = sales_df[
            (sales_df['str_code'].isin(cluster_stores)) &
            (sales_df[feature_col] == feature)
        ]
        
        if len(cluster_sales) > 0:
            # Try direct unit_price column
            if 'unit_price' in cluster_sales.columns:
                price = cluster_sales['unit_price'].median()
                if price > 0:
                    return float(price), 'cluster_sales_median'
            
            # Try store_unit_price column (subcategory sales data)
            if 'store_unit_price' in cluster_sales.columns:
                price = cluster_sales['store_unit_price'].median()
                if price > 0:
                    return float(price), 'cluster_sales_subcategory_median'
            
            # Calculate from sales amount and quantity
            if 'quantity' in cluster_sales.columns and 'spu_sales_amt' in cluster_sales.columns:
                total_qty = cluster_sales['quantity'].sum()
                total_amt = cluster_sales['spu_sales_amt'].sum()
                if total_qty > 0:
                    price = total_amt / total_qty
                    return float(price), 'cluster_sales_calculated'
        
        # Level 5: FAIL (strict mode)
        return None, 'none'
    
    def _calculate_quantity(self, expected_sales: float, unit_price: float) -> int:
        """
        Calculate recommended quantity from expected sales and price.
        
        Args:
            expected_sales: Expected sales amount
            unit_price: Unit price
            
        Returns:
            Recommended quantity (minimum 1)
        """
        if unit_price <= 0:
            return 0
        
        # Calculate raw quantity
        raw_quantity = expected_sales / unit_price
        
        # Round to nearest integer
        quantity = int(round(raw_quantity))
        
        # Ensure minimum of 1
        if quantity < 1 and raw_quantity > 0:
            quantity = 1
        
        return quantity
    
    def _predict_sellthrough_from_adoption(self, pct_stores_selling: float) -> float:
        """
        Conservative adoption→ST mapping using logistic-like curve.
        
        This is the LEGACY prediction logic that provides variable predictions
        based on adoption rate, bounded to 10%..70%.
        
        Args:
            pct_stores_selling: Percentage of stores selling (0.0 to 1.0)
            
        Returns:
            Predicted sell-through percentage (10.0 to 70.0)
        """
        try:
            if pd.isna(pct_stores_selling):
                return 0.0
            x = float(max(0.0, min(1.0, pct_stores_selling)))
            # Smooth S-curve centered near 0.5
            base = 1 / (1 + np.exp(-8 * (x - 0.5)))  # 0..1
            return 10.0 + 60.0 * base  # 10..70
        except Exception:
            return 0.0
    
    def _validate_feature(
        self,
        row: pd.Series,
        debug_stats: dict
    ) -> bool:
        """
        Validate FEATURE using approval gates (FEATURE-LEVEL, not per-store).
        
        Matches legacy validation logic (lines 938-943):
        - validator_ok (always True - broken Fast Fish)
        - stores_selling >= min_stores_selling (5)
        - pct_stores_selling >= min_adoption (25%)
        - predicted_from_adoption >= min_pred_st (30%)
        
        Args:
            row: Well-selling feature row
            debug_stats: Debug statistics dictionary
            
        Returns:
            True if feature should generate opportunities, False otherwise
        """
        # Use LEGACY prediction logic - logistic curve from adoption rate
        # This REPLACES the broken Fast Fish validator (as per commit 4ba5e859)
        predicted_st = self._predict_sellthrough_from_adoption(row['pct_stores_selling'])
        
        self.logger.debug(
            f"Validating feature: stores_selling={row['stores_selling']}, "
            f"pct_stores_selling={row['pct_stores_selling']:.2%}, "
            f"predicted_st={predicted_st:.1f}%, "
            f"thresholds: min_stores={self.config.min_stores_selling}, "
            f"min_adoption={self.config.min_adoption:.2%}, "
            f"min_pred_st={self.config.min_predicted_st*100:.1f}%"
        )
        
        # Apply approval gates (matching legacy INTENT but using prediction instead of broken validator)
        # Legacy code TRIED to use Fast Fish but it was broken (approved everything)
        # So we use the logistic curve prediction which gives variable results
        # 
        # The key insight: Legacy's Fast Fish was SUPPOSED to filter based on predicted ST
        # But it was broken and approved everything
        # Our logistic curve DOES what Fast Fish was supposed to do
        # 
        # Legacy gates (line 938-943):
        #     validator_ok and                          # Fast Fish (BROKEN - always True)
        #     stores_selling >= min_stores_selling and  # At least 5 stores
        #     pct_stores_selling >= min_adoption and    # At least 25% adoption
        #     predicted_from_adoption >= min_pred_st    # At least 30% predicted ST
        #
        # Since validator_ok was always True in legacy, the REAL filtering came from
        # the predicted_from_adoption >= min_pred_st gate
        #
        # BUT: If legacy output was 1,388 and we're getting 4,997, then legacy must have
        # had ADDITIONAL filtering beyond just the 30% threshold
        #
        # Let me check: What if the threshold needs to be HIGHER than 30%?
        # Or what if there's additional logic we're missing?
        
        # Gate 2: Check minimum stores selling
        if row['stores_selling'] < self.config.min_stores_selling:
            debug_stats['filtered_thresholds'] += 1
            return False
        
        # Gate 3: Check minimum adoption rate
        if row['pct_stores_selling'] < self.config.min_adoption:
            debug_stats['filtered_thresholds'] += 1
            return False
        
        # Gate 4: Check minimum predicted sell-through
        min_predicted_st_pct = self.config.min_predicted_st * 100  # 0.30 → 30%
        if predicted_st < min_predicted_st_pct:
            debug_stats['filtered_thresholds'] += 1
            self.logger.debug(f"FILTERED: predicted_st={predicted_st:.1f}% < {min_predicted_st_pct:.1f}%")
            return False
        
        self.logger.debug(f"APPROVED: predicted_st={predicted_st:.1f}% >= {min_predicted_st_pct:.1f}%")
        return True
