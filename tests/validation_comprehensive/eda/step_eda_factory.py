#!/usr/bin/env python3
"""
Step EDA Factory

This module provides a factory pattern for creating step-specific EDA analyzers,
reducing complexity by centralizing analyzer creation and management.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
from typing import Dict, Any, Optional
from .base_analyzer import BaseEDAAnalyzer
from .step1_analyzer import Step1EDAAnalyzer
from .step2_analyzer import Step2EDAAnalyzer
from .step3_analyzer import Step3EDAAnalyzer
from .step4_analyzer import Step4EDAAnalyzer
from .step5_analyzer import Step5EDAAnalyzer
from .step6_analyzer import Step6EDAAnalyzer

logger = logging.getLogger(__name__)

class StepEDAFactory:
    """
    Factory for creating step-specific EDA analyzers.
    
    Centralizes analyzer creation and provides a simple interface
    for getting the appropriate analyzer for each pipeline step.
    """
    
    # Registry of available analyzers
    _analyzers = {
        'step1': Step1EDAAnalyzer,
        'step2': Step2EDAAnalyzer,
        'step3': Step3EDAAnalyzer,
        'step4': Step4EDAAnalyzer,
        'step5': Step5EDAAnalyzer,
        'step6': Step6EDAAnalyzer,
    }
    
    @classmethod
    def create_analyzer(cls, step_name: str, output_dir: str = "output/eda_reports") -> Optional[BaseEDAAnalyzer]:
        """
        Create an EDA analyzer for the specified step.
        
        Args:
            step_name: Name of the step (e.g., 'step1', 'step2')
            output_dir: Output directory for reports
            
        Returns:
            EDA analyzer instance or None if step not supported
        """
        if step_name not in cls._analyzers:
            logger.error(f"No analyzer available for step: {step_name}")
            return None
        
        try:
            analyzer_class = cls._analyzers[step_name]
            return analyzer_class(output_dir=output_dir)
        except Exception as e:
            logger.error(f"Error creating analyzer for {step_name}: {e}")
            return None
    
    @classmethod
    def get_supported_steps(cls) -> list:
        """
        Get list of supported pipeline steps.
        
        Returns:
            List of supported step names
        """
        return list(cls._analyzers.keys())
    
    @classmethod
    def analyze_step(cls, step_name: str, period: str, output_dir: str = "output/eda_reports") -> Dict[str, Any]:
        """
        Analyze a specific step for a given period.
        
        Args:
            step_name: Name of the step to analyze
            period: Time period to analyze
            output_dir: Output directory for reports
            
        Returns:
            Analysis results dictionary
        """
        analyzer = cls.create_analyzer(step_name, output_dir)
        if not analyzer:
            return {'error': f'No analyzer available for step {step_name}'}
        
        try:
            return analyzer.analyze_period(period)
        except Exception as e:
            logger.error(f"Error analyzing {step_name} for period {period}: {e}")
            return {'error': str(e)}
    
    @classmethod
    def analyze_multiple_steps(cls, steps: list, period: str, output_dir: str = "output/eda_reports") -> Dict[str, Any]:
        """
        Analyze multiple steps for a given period.
        
        Args:
            steps: List of step names to analyze
            period: Time period to analyze
            output_dir: Output directory for reports
            
        Returns:
            Dictionary mapping step names to analysis results
        """
        results = {}
        
        for step_name in steps:
            logger.info(f"Analyzing {step_name} for period {period}")
            results[step_name] = cls.analyze_step(step_name, period, output_dir)
        
        return results
    
    @classmethod
    def register_analyzer(cls, step_name: str, analyzer_class: type) -> None:
        """
        Register a new analyzer for a step.
        
        Args:
            step_name: Name of the step
            analyzer_class: Analyzer class to register
        """
        if not issubclass(analyzer_class, BaseEDAAnalyzer):
            raise ValueError(f"Analyzer class must inherit from BaseEDAAnalyzer")
        
        cls._analyzers[step_name] = analyzer_class
        logger.info(f"Registered analyzer for {step_name}")
    
    @classmethod
    def get_analyzer_info(cls, step_name: str) -> Dict[str, Any]:
        """
        Get information about an analyzer for a step.
        
        Args:
            step_name: Name of the step
            
        Returns:
            Dictionary containing analyzer information
        """
        if step_name not in cls._analyzers:
            return {'error': f'No analyzer available for step {step_name}'}
        
        analyzer_class = cls._analyzers[step_name]
        return {
            'step_name': step_name,
            'analyzer_class': analyzer_class.__name__,
            'module': analyzer_class.__module__,
            'description': analyzer_class.__doc__ or 'No description available'
        }
