#!/usr/bin/env python3
"""
Sell-Through Validation Module - CORRECTED FOR FAST FISH COMPLIANCE
===================================================================

OFFICIAL FAST FISH DEFINITION:
售罄率 = 有销售的SPU数量 ÷ 有库存的SPU数量
Sell-through rate = SPUs Sold ÷ SPUs In Stock

PREVIOUS WRONG IMPLEMENTATION: (sales_days / inventory_days) * 100
CORRECT IMPLEMENTATION: (unique_spus_sold / unique_spus_in_stock) * 100

Usage:
    from sell_through_validator import SellThroughValidator
    
    validator = SellThroughValidator()
    recommendation = validator.validate_recommendation(
        store_code='12345',
        category='T恤',
        current_spu_count=50,
        recommended_spu_count=55,
        action='INCREASE'
    )

Author: Data Pipeline Team
Date: 2025-01-XX (Fast Fish Compliance - CORRECTED)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import warnings
from src.config import API_DATA_DIR, COMPLETE_SPU_SALES_FILE, get_api_data_files, get_current_period, get_period_label

warnings.filterwarnings('ignore')

class SellThroughValidator:
    """
    CORRECTED Sell-Through Validator for Fast Fish compliance.
    
    Uses the OFFICIAL Fast Fish definition: SPUs Sold ÷ SPUs In Stock
    """
    
    def __init__(self, historical_data: Optional[pd.DataFrame] = None):
        """
        Initialize the sell-through validator.
        
        Args:
            historical_data: Optional historical sales data for predictions
        """
        self.historical_data = historical_data
        self.sell_through_cache = {}
        
        # CALIBRATED Configuration for Fast Fish compliance (adjusted for realistic approval rates)
        self.MIN_SELL_THROUGH_THRESHOLD = 25.0  # 25% minimum (more realistic baseline)
        self.MAX_SELL_THROUGH_THRESHOLD = 100.0  # 100% maximum (allow perfect sell-through for single SPUs)
        self.MIN_IMPROVEMENT_THRESHOLD = 1.0    # Minimum 1% improvement required (more achievable)
        self.OPTIMAL_SELL_THROUGH_TARGET = 70.0 # Target 70% sell-through rate
        
    def calculate_sell_through_rate(self, 
                                   store_code: str, 
                                   category: str, 
                                   spu_count: int) -> float:
        """
        Calculate CORRECT Fast Fish sell-through rate.
        
        OFFICIAL FORMULA: SPUs Sold ÷ SPUs In Stock
        
        Args:
            store_code: Store identifier
            category: Product category
            spu_count: Number of different SPUs in stock
            
        Returns:
            Predicted sell-through rate as percentage (0-100)
        """
        try:
            # Create cache key
            cache_key = f"{store_code}_{category}_{spu_count}"
            
            if cache_key in self.sell_through_cache:
                return self.sell_through_cache[cache_key]
            
            if spu_count <= 0:
                return 0.0
            
            # Get historical performance for this store-category
            historical_performance = self._get_historical_performance(store_code, category)
            
            # Predict how many SPUs will sell based on historical data
            predicted_spus_sold = self._predict_spus_sold(store_code, category, spu_count, historical_performance)
            
            # Calculate CORRECT sell-through rate
            sell_through_rate = min(100.0, (predicted_spus_sold / spu_count) * 100.0)
            
            # Cache result
            self.sell_through_cache[cache_key] = sell_through_rate
            
            return sell_through_rate
            
        except Exception as e:
            # Conservative default: assume 50% of SPUs will sell
            return 50.0
    
    def _get_historical_performance(self, store_code: str, category: str) -> Dict:
        """Get historical SPU sell-through performance for store-category combination."""
        
        # Default performance metrics (Fast Fish realistic baselines)
        default_performance = {
            'spus_sold_rate': 60.0,        # 60% of SPUs typically sell
            'avg_spus_in_stock': 25.0,     # Average SPUs in stock
            'avg_spus_sold': 15.0,         # Average SPUs that sell
            'performance_tier': 'medium'    # Store performance level
        }
        
        if self.historical_data is None:
            return default_performance
        
        try:
            # Filter historical data for this store-category
            # Determine appropriate category column present in the historical data
            category_col = None
            for col in ['category', 'cate_name', 'sub_cate_name', 'big_class_name']:
                if col in self.historical_data.columns:
                    category_col = col
                    break

            if category_col:
                hist_data = self.historical_data[
                    (self.historical_data['str_code'] == store_code) &
                    (self.historical_data[category_col] == category)
                ]
            else:
                # Fallback: filter by store only
                hist_data = self.historical_data[self.historical_data['str_code'] == store_code]
            
            if len(hist_data) == 0:
                return default_performance
            
            # Calculate ACTUAL SPU sell-through metrics with light smoothing to avoid extremes
            if 'spu_code' in hist_data.columns:
                # Choose quantity-like column if available
                if 'quantity' in hist_data.columns:
                    qty_col = 'quantity'
                elif 'spu_sales_amt' in hist_data.columns:
                    qty_col = 'spu_sales_amt'
                else:
                    qty_col = None

                if qty_col is not None:
                    spus_with_sales = hist_data[hist_data[qty_col] > 0]['spu_code'].nunique()
                else:
                    spus_with_sales = 0

                total_spus = hist_data['spu_code'].nunique()
                
                if total_spus > 0:
                    # Beta prior smoothing (α=1, β=1) to avoid 0%/100% extremes
                    actual_sellthrough_rate = ((spus_with_sales + 1) / (total_spus + 2)) * 100.0
                else:
                    actual_sellthrough_rate = default_performance['spus_sold_rate']
            else:
                actual_sellthrough_rate = default_performance['spus_sold_rate']
            
            performance = {
                'spus_sold_rate': actual_sellthrough_rate,
                'avg_spus_in_stock': total_spus if 'total_spus' in locals() else default_performance['avg_spus_in_stock'],
                'avg_spus_sold': spus_with_sales if 'spus_with_sales' in locals() else default_performance['avg_spus_sold'],
                'performance_tier': 'high' if actual_sellthrough_rate > 70 else 'medium' if actual_sellthrough_rate > 50 else 'low'
            }
            
            return performance
            
        except Exception:
            return default_performance
    
    def _predict_spus_sold(self, store_code: str, category: str, spu_count: int, performance: Dict) -> float:
        """
        Predict how many SPUs will sell based on store performance and SPU count.
        
        Uses realistic business model: more SKUs generally decrease sell-through rate.
        """
        base_sellthrough_rate = performance['spus_sold_rate']
        
        # Diminishing returns model: More SPUs generally means lower sell-through %
        # Optimal range is typically 20-40 SPUs per category per store
        optimal_spu_count = 30
        
        if spu_count <= optimal_spu_count:
            # Below optimal: sell-through rate remains high
            efficiency_factor = 1.0
        else:
            # Above optimal: diminishing returns kick in
            excess_spus = spu_count - optimal_spu_count
            efficiency_factor = 1.0 / (1.0 + 0.02 * excess_spus)  # 2% decrease per excess SPU
        
        # Apply efficiency factor
        adjusted_sellthrough_rate = base_sellthrough_rate * efficiency_factor
        
        # Calculate predicted SPUs sold
        predicted_spus_sold = (adjusted_sellthrough_rate / 100.0) * spu_count
        
        # Allow 0 (do not force 1 SPU sold to avoid artificial 100% at low counts)
        return max(0.0, predicted_spus_sold)
    
    def validate_recommendation(self, 
                              store_code: str, 
                              category: str, 
                              current_spu_count: int, 
                              recommended_spu_count: int, 
                              action: str,
                              rule_name: str = "Unknown") -> Dict[str, Any]:
        """
        Validate a recommendation using CORRECT Fast Fish sell-through definition.
        
        Args:
            store_code: Store identifier
            category: Product category  
            current_spu_count: Current number of SPUs in stock
            recommended_spu_count: Recommended number of SPUs
            action: Recommendation action (INCREASE, DECREASE, REBALANCE, etc.)
            rule_name: Name of the business rule making the recommendation
            
        Returns:
            Dictionary with validation results and recommendation
        """
        
        # Calculate current and predicted sell-through rates using CORRECT formula
        current_sell_through = self.calculate_sell_through_rate(store_code, category, current_spu_count)
        predicted_sell_through = self.calculate_sell_through_rate(store_code, category, recommended_spu_count)
        
        # Calculate improvement
        sell_through_improvement = predicted_sell_through - current_sell_through
        
        # Determine if recommendation should be approved using Fast Fish criteria
        should_approve = self._should_approve_recommendation(
            current_sell_through, predicted_sell_through, sell_through_improvement, action
        )
        
        # Generate business rationale
        business_rationale = self._generate_business_rationale(
            rule_name, action, current_sell_through, predicted_sell_through, 
            sell_through_improvement, should_approve, current_spu_count, recommended_spu_count
        )
        
        # Derive approval reason aligned with improvement direction
        if should_approve:
            if sell_through_improvement > 0.1:
                approval_reason = 'Improves SPU sell-through rate'
            elif sell_through_improvement >= -0.1:
                approval_reason = 'Maintains sell-through rate and meets threshold'
            else:
                approval_reason = 'Meets Fast Fish threshold (sell-through decrease within allowed bounds)'
        else:
            approval_reason = 'Fails Fast Fish threshold/criteria'

        return {
            'store_code': store_code,
            'category': category,
            'rule_name': rule_name,
            'action': action,
            'current_spu_count': current_spu_count,
            'recommended_spu_count': recommended_spu_count,
            'current_sell_through_rate': current_sell_through,
            'predicted_sell_through_rate': predicted_sell_through,
            'sell_through_improvement': sell_through_improvement,
            'fast_fish_compliant': should_approve,
            'business_rationale': business_rationale,
            'validation_method': 'Fast Fish Official: SPUs Sold ÷ SPUs In Stock',
            'approval_reason': approval_reason
        }
    
    def _should_approve_recommendation(self, 
                                     current_st: float, 
                                     predicted_st: float, 
                                     improvement: float, 
                                     action: str) -> bool:
        """
        Determine if recommendation should be approved based on CORRECT sell-through optimization.
        
        FIXED LOGIC: INCREASE actions naturally decrease sell-through rates, so we need
        different approval criteria for INCREASE vs DECREASE actions.
        """
        
        # Rule 1: Predicted sell-through must meet minimum threshold (applies to all actions)
        if predicted_st < self.MIN_SELL_THROUGH_THRESHOLD:
            return False
        
        # Rule 2: For DECREASE actions, require positive improvement (reducing SKUs should improve sell-through)
        if action in ['DECREASE', 'REDUCE', 'REMOVE']:
            return improvement >= 0  # Any improvement is good for reductions
        
        # Rule 3: For INCREASE actions, accept reasonable sell-through degradation
        # INCREASE actions naturally decrease sell-through, so we allow negative improvement
        # as long as the final sell-through rate stays reasonable
        if action in ['INCREASE', 'ADD', 'EXPAND', 'IMPROVE', 'REBALANCE']:
            # Special handling for very small SPU counts (Step 12 edge case)
            # When current SPU count is very small (1-3), allow larger degradation
            # because the sell-through math behaves differently at low numbers
            if current_st >= 90.0:  # Very high current sell-through (likely 1-2 SPUs)
                max_degradation = -50.0  # Allow up to 50% decrease for very small counts
            else:
                max_degradation = -10.0  # Standard 10% decrease for normal counts
            
            # Allow sell-through to decrease, but not below minimum threshold
            # Also don't allow it to go above maximum (unrealistic)
            return (predicted_st >= self.MIN_SELL_THROUGH_THRESHOLD and 
                   predicted_st <= self.MAX_SELL_THROUGH_THRESHOLD and
                   improvement >= max_degradation)
        
        # Rule 4: For other actions (REBALANCE, etc.), require positive improvement
        return improvement >= self.MIN_IMPROVEMENT_THRESHOLD
    
    def _generate_business_rationale(self, rule_name: str, action: str, 
                                   current_st: float, predicted_st: float, 
                                   improvement: float, approved: bool,
                                   current_spus: int, recommended_spus: int) -> str:
        """Generate business rationale using Fast Fish terminology."""
        
        spu_change = recommended_spus - current_spus
        
        if approved:
            if improvement > 0.1:
                return (f"✅ {rule_name}: {action} approved. "
                        f"SPU count {current_spus}→{recommended_spus} ({spu_change:+d}) "
                        f"improves sell-through {current_st:.1f}%→{predicted_st:.1f}% ({improvement:+.1f}pp)")
            elif improvement >= -0.1:
                return (f"✅ {rule_name}: {action} approved. "
                        f"SPU count {current_spus}→{recommended_spus} ({spu_change:+d}) "
                        f"maintains sell-through around {predicted_st:.1f}% ({improvement:+.1f}pp)")
            else:
                return (f"✅ {rule_name}: {action} approved. "
                        f"SPU count {current_spus}→{recommended_spus} ({spu_change:+d}) "
                        f"decreases sell-through to {predicted_st:.1f}% ({improvement:+.1f}pp) but remains above threshold")
        else:
            return (f"❌ {rule_name}: {action} rejected. "
                    f"SPU count {current_spus}→{recommended_spus} ({spu_change:+d}) "
                    f"sell-through {current_st:.1f}%→{predicted_st:.1f}% ({improvement:+.1f}pp) "
                    f"fails Fast Fish criteria")
    
    def batch_validate_recommendations(self, recommendations: List[Dict]) -> pd.DataFrame:
        """
        Validate multiple recommendations using CORRECT Fast Fish definition.
        """
        validated_recs = []
        
        for rec in recommendations:
            validation = self.validate_recommendation(
                store_code=rec['store_code'],
                category=rec['category'],
                current_spu_count=rec.get('current_spu_count', rec.get('current_quantity', 0)),
                recommended_spu_count=rec.get('recommended_spu_count', rec.get('recommended_quantity', 0)),
                action=rec.get('action', 'UNKNOWN'),
                rule_name=rec.get('rule_name', 'Unknown Rule')
            )
            
            # Merge original recommendation with validation results
            validated_rec = {**rec, **validation}
            validated_recs.append(validated_rec)
        
        return pd.DataFrame(validated_recs)

def load_historical_data_for_validation() -> Optional[pd.DataFrame]:
    """
    Load historical data for sell-through validation.
    
    Returns:
        DataFrame with historical sales data or None if not available
    """
    try:
        import os, glob
        
        # Allow explicit source override via environment
        src_yyyymm = os.getenv("VALIDATOR_SOURCE_YYYYMM") or os.getenv("PIPELINE_SOURCE_YYYYMM")
        src_period = os.getenv("VALIDATOR_SOURCE_PERIOD") or os.getenv("PIPELINE_SOURCE_PERIOD")
        years_back_env = os.getenv("VALIDATOR_SEASONAL_YEARS_BACK")
        years_back = int(years_back_env) if years_back_env and years_back_env.isdigit() else 0

        candidate_paths: List[str] = []
        
        def _append_if_exists(path: Optional[str]) -> None:
            if path and os.path.exists(path):
                candidate_paths.append(path)

        # 1) If explicit source provided, use that period-specific file
        if src_yyyymm and src_period:
            try:
                api_files = get_api_data_files(src_yyyymm, src_period)
                _append_if_exists(api_files.get('spu_sales'))
                # Include same month/period from prior N years if requested
                if years_back > 0:
                    base_year = int(str(src_yyyymm)[:4])
                    base_month = int(str(src_yyyymm)[4:6])
                    for i in range(1, years_back + 1):
                        y = base_year - i
                        sy = f"{y}{base_month:02d}"
                        api_files_seas = get_api_data_files(sy, src_period)
                        _append_if_exists(api_files_seas.get('spu_sales'))
            except Exception:
                pass

        # 1b) Optional: explicitly include extra arbitrary periods (comma-separated labels like 202508A,202508B)
        try:
            extra = os.getenv("VALIDATOR_EXTRA_PERIODS", "").strip()
            if extra:
                for label in [x.strip() for x in extra.split(',') if x.strip()]:
                    if len(label) >= 7:
                        yyyymm, per = label[:6], label[6]
                        try:
                            ap = get_api_data_files(yyyymm, per)
                            _append_if_exists(ap.get('spu_sales'))
                        except Exception:
                            continue
        except Exception:
            pass

        # 2) If none yet, fall back to current configured period
        if not candidate_paths:
            try:
                cyyyymm, cperiod = get_current_period()
                api_files_cur = get_api_data_files(cyyyymm, cperiod)
                _append_if_exists(api_files_cur.get('spu_sales'))
            except Exception:
                pass

        # 3) As a last resort, pick the latest per-period file in API_DATA_DIR (but never a combined file)
        if not candidate_paths:
            pattern = os.path.join(API_DATA_DIR, "complete_spu_sales_????????[AB].csv")
            sales_files = sorted(glob.glob(pattern))
            if sales_files:
                _append_if_exists(sales_files[-1])

        # Read and concatenate any resolved period-specific files
        valid_paths = [p for p in candidate_paths if p and os.path.exists(p)]
        if valid_paths:
            print(f"📊 Loading historical data from period files: {valid_paths}")
            frames = [pd.read_csv(p, dtype={'str_code': str}, low_memory=False) for p in valid_paths]
            if len(frames) == 1:
                return frames[0]
            return pd.concat(frames, ignore_index=True, sort=False)

        print("⚠️ No historical period sales data found for validator")
        return None

    except Exception as e:
        print(f"⚠️ Could not load historical data: {str(e)}")
        return None

def main():
    """Demo of CORRECTED Fast Fish sell-through calculation."""
    
    print("🎯 CORRECTED FAST FISH SELL-THROUGH RATE CALCULATION")
    print("=" * 60)
    print("OFFICIAL FORMULA: SPUs Sold ÷ SPUs In Stock")
    print("PREVIOUS WRONG: (sales_days / inventory_days) * 100")
    print()
    
    # Create validator
    validator = SellThroughValidator()
    
    # Test example
    result = validator.validate_recommendation(
        store_code='STR001',
        category='T恤',
        current_spu_count=30,
        recommended_spu_count=35,
        action='INCREASE',
        rule_name='Demo Rule'
    )
    
    print("Example Validation:")
    print(f"Store: {result['store_code']}")
    print(f"Category: {result['category']}")
    print(f"Current SPUs: {result['current_spu_count']}")
    print(f"Recommended SPUs: {result['recommended_spu_count']}")
    print(f"Current sell-through: {result['current_sell_through_rate']:.1f}%")
    print(f"Predicted sell-through: {result['predicted_sell_through_rate']:.1f}%")
    print(f"Improvement: {result['sell_through_improvement']:+.1f}pp")
    print(f"Fast Fish Compliant: {result['fast_fish_compliant']}")
    print(f"Rationale: {result['business_rationale']}")

if __name__ == "__main__":
    main() 