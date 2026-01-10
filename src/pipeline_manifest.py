#!/usr/bin/env python3
"""
Pipeline Manifest System - Explicit File Path Tracking

This module provides a centralized system for tracking exact file paths
between pipeline steps, eliminating the need for risky glob patterns
and creation time-based file selection.

Author: Pipeline Enhancement
Date: 2025-07-24
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class PipelineManifest:
    """Manages explicit file paths between pipeline steps"""
    
    def __init__(self, manifest_path: str = "output/pipeline_manifest.json"):
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """Load existing manifest or create new one"""
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load manifest: {e}, creating new one")
        
        return {
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "steps": {},
            "current_session": datetime.now().strftime("%Y%m%d_%H%M%S")
        }
    
    def _save_manifest(self):
        """Save manifest to disk"""
        self.manifest["last_updated"] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
        
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)
        
        logger.info(f"Pipeline manifest updated: {self.manifest_path}")
    
    def register_output(self, step_name: str, output_type: str, file_path: str, metadata: Optional[Dict] = None):
        """Register an output file from a pipeline step"""
        # Global guard: forbid synthetic combined files anywhere in manifest
        forbidden_suffixes = [
            "complete_spu_sales_2025Q2_combined.csv",
            "complete_category_sales_2025Q2_combined.csv",
            "store_config_2025Q2_combined.csv",
            "_combined.csv",
        ]
        if any(str(file_path).endswith(suf) for suf in forbidden_suffixes):
            raise ValueError(f"Refusing to register forbidden combined file in manifest: {file_path}")
        if step_name not in self.manifest["steps"]:
            self.manifest["steps"][step_name] = {}
        
        if "outputs" not in self.manifest["steps"][step_name]:
            self.manifest["steps"][step_name]["outputs"] = {}
        
        self.manifest["steps"][step_name]["outputs"][output_type] = {
            "file_path": file_path,
            "created": datetime.now().isoformat(),
            "exists": os.path.exists(file_path),
            "size_mb": round(os.path.getsize(file_path) / (1024*1024), 2) if os.path.exists(file_path) else 0,
            "metadata": metadata or {}
        }
        
        self._save_manifest()
        logger.info(f"Registered {step_name} output: {output_type} -> {file_path}")
    
    def get_latest_output(self, step_name: str, key_prefix: Optional[str] = None, period_label: Optional[str] = None) -> Optional[str]:
        """Return the newest output path for a step, optionally filtered by key prefix and period.
        - key_prefix: e.g., 'enhanced_fast_fish_format' or 'enriched_store_attributes'
        - period_label: e.g., '202509A'
        """
        step = self.manifest.get("steps", {}).get(step_name, {})
        outputs: Dict = step.get("outputs", {})
        candidates = []
        for key, val in outputs.items():
            if not isinstance(val, dict):
                continue
            if key_prefix and not key.startswith(key_prefix):
                continue
            if period_label and not (key.endswith(period_label) or str(val.get("metadata", {}).get("period_label", "")).endswith(period_label)):
                continue
            created = val.get("created") or ""
            candidates.append((created, val.get("file_path")))
        candidates = [c for c in candidates if c[1]]
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        return candidates[-1][1]
    
    def get_input(self, step_name: str, input_type: str) -> Optional[str]:
        """Get the exact file path for a required input"""
        # Define input dependencies
        input_dependencies = {
            "step14": {
                "consolidated_rules": "step13:consolidated_rules"
            },
            "step15": {
                "fast_fish_format": "step14:enhanced_fast_fish_format"
            },
            "step17": {
                "fast_fish_format": "step14:enhanced_fast_fish_format"
            },
            "step18": {
                "augmented_recommendations": "step17:augmented_recommendations"
            },
            "step19": {
                "detailed_recommendations": "step13:detailed_spu_recommendations"
            },
            "step20": {
                "detailed_spu_recommendations": "step19:detailed_spu_breakdown",
                "store_level_aggregation": "step19:store_level_aggregation",
                "cluster_subcategory_aggregation": "step19:cluster_subcategory_aggregation"
            },
            "step21": {
                "spu_recommendations": "step19:detailed_spu_breakdown"
            }
        }
        
        if step_name not in input_dependencies:
            logger.warning(f"No input dependencies defined for {step_name}")
            return None
        
        if input_type not in input_dependencies[step_name]:
            logger.warning(f"No dependency defined for {step_name}:{input_type}")
            return None
        
        # Parse dependency
        source_step, source_output = input_dependencies[step_name][input_type].split(":")
        
        if source_step not in self.manifest["steps"]:
            logger.error(f"Source step {source_step} not found in manifest")
            return None
        
        if "outputs" not in self.manifest["steps"][source_step]:
            logger.error(f"No outputs found for source step {source_step}")
            return None
        
        if source_output not in self.manifest["steps"][source_step]["outputs"]:
            logger.error(f"Output {source_output} not found for step {source_step}")
            return None
        
        file_path = self.manifest["steps"][source_step]["outputs"][source_output]["file_path"]
        # Guard against combined synthetic files
        if any(str(file_path).endswith(suf) for suf in [
            "complete_spu_sales_2025Q2_combined.csv",
            "complete_category_sales_2025Q2_combined.csv",
            "store_config_2025Q2_combined.csv",
            "_combined.csv",
        ]):
            logger.error(f"Manifest refers to forbidden combined file: {file_path}")
            return None
        
        if not os.path.exists(file_path):
            logger.error(f"Required input file does not exist: {file_path}")
            return None
        
        logger.info(f"Retrieved input for {step_name}:{input_type} -> {file_path}")
        return file_path
    
    def list_available_outputs(self, step_name: str) -> List[str]:
        """List all available outputs from a step"""
        if step_name not in self.manifest["steps"]:
            return []
        
        if "outputs" not in self.manifest["steps"][step_name]:
            return []
        
        return list(self.manifest["steps"][step_name]["outputs"].keys())
    
    def get_manifest_summary(self) -> Dict:
        """Get a summary of the current manifest state"""
        summary = {
            "session": self.manifest["current_session"],
            "steps_completed": len(self.manifest["steps"]),
            "total_outputs": sum(len(step.get("outputs", {})) for step in self.manifest["steps"].values()),
            "steps": {}
        }
        
        for step_name, step_data in self.manifest["steps"].items():
            outputs = step_data.get("outputs", {})
            summary["steps"][step_name] = {
                "outputs_count": len(outputs),
                "outputs": list(outputs.keys()),
                "last_run": max((output["created"] for output in outputs.values()), default="Never")
            }
        
        return summary

# Global instance
_manifest = None

def get_manifest() -> PipelineManifest:
    """Get the global pipeline manifest instance"""
    global _manifest
    if _manifest is None:
        _manifest = PipelineManifest()
    return _manifest

def reset_manifest(delete_file: bool = True, manifest_path: Optional[str] = None) -> None:
    """Reset the pipeline manifest to a clean state.
    If delete_file is True, remove the manifest file from disk before reinitializing.
    Optionally override the manifest_path; otherwise uses the default.
    """
    global _manifest
    # Determine path to operate on
    path = manifest_path
    try:
        if path is None:
            if _manifest is not None:
                path = _manifest.manifest_path
            else:
                # Use default path from a temporary instance
                path = PipelineManifest().manifest_path
        if delete_file and path and os.path.exists(path):
            os.remove(path)
            logger.info(f"Deleted existing manifest file: {path}")
    except Exception as e:
        logger.warning(f"Failed to delete manifest file: {e}")
    # Reinitialize global instance
    _manifest = PipelineManifest(manifest_path=path if path else "output/pipeline_manifest.json")
    logger.info("Pipeline manifest has been reset")

def register_step_output(step_name: str, output_type: str, file_path: str, metadata: Optional[Dict] = None):
    """Convenience function to register step output"""
    get_manifest().register_output(step_name, output_type, file_path, metadata)

def get_step_input(step_name: str, input_type: str) -> Optional[str]:
    """Convenience function to get step input"""
    return get_manifest().get_input(step_name, input_type)

def print_manifest_summary():
    """Print a summary of the current manifest state"""
    summary = get_manifest().get_manifest_summary()
    
    print(f"\n📋 PIPELINE MANIFEST SUMMARY")
    print(f"===========================")
    print(f"Session: {summary['session']}")
    print(f"Steps completed: {summary['steps_completed']}")
    print(f"Total outputs: {summary['total_outputs']}")
    print()
    
    for step_name, step_info in summary["steps"].items():
        print(f"✅ {step_name}: {step_info['outputs_count']} outputs")
        for output in step_info["outputs"]:
            print(f"   • {output}")
    print()

if __name__ == "__main__":
    # Test the manifest system
    print_manifest_summary() 