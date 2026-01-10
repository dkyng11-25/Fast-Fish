"""
Trendiness Data Loader
=====================

Loads and processes trendiness analysis data:
- Fashion vs Basic product ratios
- Trendy vs Core item analysis
- Store product mix classifications
- Seasonal and trend patterns
"""

import pandas as pd
import json
from typing import Dict, List, Any, Optional
from .base_data_loader import BaseDataLoader

class TrendinessDataLoader(BaseDataLoader):
    """Loads comprehensive trendiness and product mix data."""
    
    def __init__(self, output_dir: str = 'output', data_dir: str = 'data'):
        super().__init__(output_dir, data_dir)
        self.trendiness_data = {}
        
    def load_data(self) -> Dict[str, Any]:
        """Load all trendiness-related data sources."""
        self.logger.info("Loading comprehensive trendiness data...")
        
        # Load different trendiness data sources
        self._load_production_trendiness()
        self._load_analysis_results()
        
        # Process and enhance data
        self._calculate_cluster_trendiness()
        self._classify_store_types()
        
        self.logger.info(f"Trendiness data loading complete. Loaded data for {len(self.trendiness_data)} stores")
        return self.trendiness_data
    
    def _load_production_trendiness(self):
        """Load production trendiness analysis data."""
        filepath = f"{self.output_dir}/production_trendiness_analysis.json"
        data = self._load_json_safe(filepath, required=False)
        
        if data:
            store_data = {}
            for store_id, store_info in data.items():
                processed_data = {
                    'store_id': str(store_id),
                    'analysis_date': store_info.get('analysis_date'),
                    'product_mix': {
                        'basic_count': store_info.get('basic_items_count', 0),
                        'fashion_count': store_info.get('fashion_items_count', 0),
                        'basic_ratio': store_info.get('basic_ratio', 0),
                        'fashion_ratio': store_info.get('fashion_ratio', 0),
                        'basic_sales_ratio': store_info.get('basic_sales_ratio', 0),
                        'fashion_sales_ratio': store_info.get('fashion_sales_ratio', 0)
                    },
                    'trend_analysis': {
                        'trendy_count': store_info.get('trendy_items_count', 0),
                        'core_count': store_info.get('core_items_count', 0),
                        'trendy_ratio': store_info.get('trendy_ratio', 0),
                        'core_ratio': store_info.get('core_ratio', 0)
                    },
                    'mix_status': store_info.get('mix_balance_status', 'UNKNOWN'),
                    'recommendations': store_info.get('recommendations', [])
                }
                store_data[str(store_id)] = processed_data
            
            self.trendiness_data['production_analysis'] = store_data
            self._loaded_data['production_trendiness'] = data
            self.logger.info(f"Loaded production trendiness data for {len(store_data)} stores")
    
    def _load_analysis_results(self):
        """Load additional trendiness analysis results."""
        filepath = f"{self.output_dir}/trendiness_analysis_results.json"
        data = self._load_json_safe(filepath, required=False)
        
        if data:
            # Process additional analysis data
            additional_data = {}
            for store_id, store_info in data.items():
                if store_id in self.trendiness_data.get('production_analysis', {}):
                    # Merge with existing data
                    existing = self.trendiness_data['production_analysis'][store_id]
                    
                    # Add any additional fields not in production data
                    for key, value in store_info.items():
                        if key not in ['store_id', 'analysis_date'] and key not in existing:
                            additional_data[key] = value
                    
                    if additional_data:
                        existing['additional_metrics'] = additional_data
                else:
                    # Store as separate entry if not in production data
                    if 'analysis_results' not in self.trendiness_data:
                        self.trendiness_data['analysis_results'] = {}
                    self.trendiness_data['analysis_results'][store_id] = store_info
            
            self._loaded_data['analysis_results'] = data
            self.logger.info(f"Loaded additional analysis results")
    
    def _calculate_cluster_trendiness(self):
        """Calculate cluster-level trendiness metrics."""
        if 'production_analysis' not in self.trendiness_data:
            return
            
        # Need cluster mapping - will be provided by main dashboard
        # For now, create placeholder structure
        cluster_trendiness = {}
        
        # This will be enhanced when cluster mapping is available
        self.trendiness_data['cluster_metrics'] = cluster_trendiness
        self.logger.info("Prepared cluster trendiness calculation structure")
    
    def _classify_store_types(self):
        """Classify stores based on their product mix patterns."""
        if 'production_analysis' not in self.trendiness_data:
            return
            
        store_classifications = {}
        
        for store_id, data in self.trendiness_data['production_analysis'].items():
            mix = data['product_mix']
            trend = data['trend_analysis']
            
            # Classify based on fashion/basic ratio
            fashion_ratio = mix['fashion_ratio']
            trendy_ratio = trend['trendy_ratio']
            
            if fashion_ratio > 0.7:
                if trendy_ratio > 0.4:
                    classification = "FASHION_FORWARD"
                else:
                    classification = "FASHION_FOCUSED"
            elif fashion_ratio < 0.3:
                if trendy_ratio < 0.2:
                    classification = "BASIC_CONSERVATIVE"
                else:
                    classification = "BASIC_TRENDY"
            else:
                if trendy_ratio > 0.3:
                    classification = "BALANCED_TRENDY"
                else:
                    classification = "BALANCED_STABLE"
            
            store_classifications[store_id] = {
                'classification': classification,
                'fashion_ratio': fashion_ratio,
                'trendy_ratio': trendy_ratio,
                'mix_balance': data['mix_status'],
                'confidence_score': self._calculate_classification_confidence(mix, trend)
            }
        
        self.trendiness_data['store_classifications'] = store_classifications
        self.logger.info(f"Classified {len(store_classifications)} stores by product mix type")
    
    def _calculate_classification_confidence(self, mix: Dict, trend: Dict) -> float:
        """Calculate confidence score for store classification."""
        # Based on how definitive the ratios are
        fashion_ratio = mix['fashion_ratio']
        trendy_ratio = trend['trendy_ratio']
        
        # Higher confidence for more extreme ratios
        fashion_confidence = abs(fashion_ratio - 0.5) * 2  # 0 to 1
        trendy_confidence = abs(trendy_ratio - 0.3) / 0.7  # Assuming 0.3 is neutral
        
        # Average the confidences
        return min((fashion_confidence + trendy_confidence) / 2, 1.0)
    
    def get_store_trendiness(self, store_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive trendiness data for a specific store."""
        store_data = {}
        
        # Get production analysis data
        if 'production_analysis' in self.trendiness_data:
            prod_data = self.trendiness_data['production_analysis'].get(store_id)
            if prod_data:
                store_data.update(prod_data)
        
        # Get classification data
        if 'store_classifications' in self.trendiness_data:
            class_data = self.trendiness_data['store_classifications'].get(store_id)
            if class_data:
                store_data['classification'] = class_data
        
        return store_data if store_data else None
    
    def get_cluster_trendiness_summary(self, cluster_stores: List[str]) -> Dict[str, Any]:
        """Calculate trendiness summary for a cluster of stores."""
        if 'production_analysis' not in self.trendiness_data:
            return {}
            
        cluster_data = []
        for store_id in cluster_stores:
            store_data = self.trendiness_data['production_analysis'].get(store_id)
            if store_data:
                cluster_data.append(store_data)
        
        if not cluster_data:
            return {}
        
        # Calculate cluster averages
        total_stores = len(cluster_data)
        
        avg_fashion_ratio = sum(s['product_mix']['fashion_ratio'] for s in cluster_data) / total_stores
        avg_basic_ratio = sum(s['product_mix']['basic_ratio'] for s in cluster_data) / total_stores
        avg_trendy_ratio = sum(s['trend_analysis']['trendy_ratio'] for s in cluster_data) / total_stores
        
        # Determine dominant cluster type
        if avg_fashion_ratio > 0.6:
            cluster_type = "FASHION_DOMINANT"
        elif avg_basic_ratio > 0.6:
            cluster_type = "BASIC_DOMINANT"
        else:
            cluster_type = "MIXED_BALANCED"
        
        # Calculate consistency (how similar stores are within cluster)
        fashion_std = (sum((s['product_mix']['fashion_ratio'] - avg_fashion_ratio) ** 2 for s in cluster_data) / total_stores) ** 0.5
        consistency_score = max(0, 1 - fashion_std)  # Lower std = higher consistency
        
        return {
            'cluster_type': cluster_type,
            'average_ratios': {
                'fashion': round(avg_fashion_ratio, 3),
                'basic': round(avg_basic_ratio, 3),
                'trendy': round(avg_trendy_ratio, 3)
            },
            'consistency_score': round(consistency_score, 3),
            'total_stores_analyzed': total_stores,
            'store_classifications': [
                self.trendiness_data.get('store_classifications', {}).get(store_id, {}).get('classification', 'UNKNOWN')
                for store_id in cluster_stores 
                if store_id in self.trendiness_data.get('production_analysis', {})
            ]
        } 