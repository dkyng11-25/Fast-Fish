"""
Trendiness Data Loader
Vendored from backup trending module. Depends on BaseDataLoader.
"""

import os
import pandas as pd
import json
from typing import Dict, List, Any, Optional
from .base_data_loader import BaseDataLoader
from .trendiness_fallback_generator import generate_fallback_production_trendiness

class TrendinessDataLoader(BaseDataLoader):
    def __init__(self, output_dir: str = 'output', data_dir: str = 'data'):
        super().__init__(output_dir, data_dir)
        self.trendiness_data = {}
        self._loaded_data: Dict[str, Any] = {}
    
    def load_data(self) -> Dict[str, Any]:
        self.logger.info("Loading comprehensive trendiness data...")
        self._load_production_trendiness()
        self._load_analysis_results()
        self._calculate_cluster_trendiness()
        self._classify_store_types()
        self.logger.info(f"Trendiness data loading complete. Loaded data for {len(self.trendiness_data)} stores")
        return self.trendiness_data
    
    def _load_production_trendiness(self):
        filepath = f"{self.output_dir}/production_trendiness_analysis.json"
        data = self._load_json_safe(filepath, required=False)
        # Fallback: synthesize from diagnostics if primary JSON missing
        if not data:
            try:
                self.logger.warning(
                    "production_trendiness_analysis.json missing; generating fallback from diagnostics..."
                )
                out_path = generate_fallback_production_trendiness(
                    output_dir=self.output_dir,
                    diagnostics_dir=os.path.join(self.output_dir, 'diagnostics'),
                )
                data = self._load_json_safe(out_path, required=False)
            except Exception as exc:
                self.logger.error(f"Fallback trendiness generation failed: {exc}")
                data = {}
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
        filepath = f"{self.output_dir}/trendiness_analysis_results.json"
        data = self._load_json_safe(filepath, required=False)
        if data:
            additional_data = {}
            for store_id, store_info in data.items():
                if store_id in self.trendiness_data.get('production_analysis', {}):
                    existing = self.trendiness_data['production_analysis'][store_id]
                    for key, value in store_info.items():
                        if key not in ['store_id', 'analysis_date'] and key not in existing:
                            additional_data[key] = value
                    if additional_data:
                        existing['additional_metrics'] = additional_data
                else:
                    if 'analysis_results' not in self.trendiness_data:
                        self.trendiness_data['analysis_results'] = {}
                    self.trendiness_data['analysis_results'][store_id] = store_info
            self._loaded_data['analysis_results'] = data
            self.logger.info(f"Loaded additional analysis results")
    
    def _calculate_cluster_trendiness(self):
        if 'production_analysis' not in self.trendiness_data:
            return
        cluster_trendiness: Dict[str, Any] = {}
        self.trendiness_data['cluster_metrics'] = cluster_trendiness
        self.logger.info("Prepared cluster trendiness calculation structure")
    
    def _classify_store_types(self):
        if 'production_analysis' not in self.trendiness_data:
            return
        store_classifications: Dict[str, Any] = {}
        for store_id, data in self.trendiness_data['production_analysis'].items():
            mix = data['product_mix']
            trend = data['trend_analysis']
            fashion_ratio = mix['fashion_ratio']
            trendy_ratio = trend['trendy_ratio']
            if fashion_ratio > 0.7:
                classification = "FASHION_FORWARD" if trendy_ratio > 0.4 else "FASHION_FOCUSED"
            elif fashion_ratio < 0.3:
                classification = "BASIC_CONSERVATIVE" if trendy_ratio < 0.2 else "BASIC_TRENDY"
            else:
                classification = "BALANCED_TRENDY" if trendy_ratio > 0.3 else "BALANCED_STABLE"
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
        fashion_ratio = mix['fashion_ratio']
        trendy_ratio = trend['trendy_ratio']
        fashion_confidence = abs(fashion_ratio - 0.5) * 2
        trendy_confidence = abs(trendy_ratio - 0.3) / 0.7
        return min((fashion_confidence + trendy_confidence) / 2, 1.0)


