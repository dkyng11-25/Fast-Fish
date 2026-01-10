#!/usr/bin/env python3
"""
Validation Runners Package

This package contains specialized validation runners for different pipeline steps.
Each runner module focuses on a specific set of pipeline steps to improve maintainability.

Author: Data Pipeline
Date: 2025-01-03
"""

# Import all runner functions for backward compatibility
from .step1_runner import (
    validate_step1_period,
    validate_multiple_periods,
    run_step1_validation
)

from .step2_runner import (
    validate_step2_coordinates,
    run_step2_validation
)

from .step2b_runner import (
    validate_step2b_seasonal_data,
    run_step2b_validation
)

from .step3_runner import (
    validate_step3_matrices,
    run_step3_validation
)

from .step4_runner import (
    validate_weather_files,
    validate_store_altitudes,
    validate_weather_by_period,
    run_step4_validation
)

from .step5_runner import (
    validate_step5_feels_like_temperature,
    validate_feels_like_calculation_quality,
    run_step5_validation
)

from .step6_runner import (
    validate_step6_clustering,
    run_step6_validation
)

from .step10_runner import (
    validate_step10_comprehensive,
    validate_step10_inputs,
    run_step10_validation
)

from .step12_runner import (
    validate_step12_comprehensive,
    validate_step12_inputs_comprehensive,
    run_step12_validation
)

from .step7_runner import (
    validate_step7_missing_category_rule,
    run_step7_validation
)

from .step8_runner import (
    validate_step8_comprehensive,
    validate_step8_inputs_comprehensive,
    run_step8_validation
)

from .step9_runner import (
    validate_step9_comprehensive,
    validate_step9_inputs_comprehensive,
    run_step9_validation
)

from .step11_runner import (
    validate_step11_comprehensive,
    validate_step11_inputs_comprehensive,
    run_step11_validation
)

from .step13_runner import (
    validate_step13_comprehensive,
    run_step13_validation
)

from .step14_runner import (
    validate_step14_fast_fish_format,
    run_step14_validation
)

from .step19_runner import (
    run_step19_validation
)

from .comprehensive_test_runner import (
    ComprehensiveTestRunner
)

from .comprehensive_runner import (
    run_comprehensive_validation
)

from .steps_15_36_runner import (
    validate_step15_historical_baseline,
    validate_step16_comparison_tables,
    validate_step17_augment_recommendations,
    validate_step18_validate_results,
    validate_step19_detailed_spu_breakdown,
    validate_step20_data_validation,
    validate_steps_21_24_labeling_analysis,
    validate_steps_25_29_analysis_optimization,
    validate_steps_30_36_merchandising_delivery,
    run_steps_15_36_validation
)

__all__ = [
    # Step 1
    'validate_step1_period',
    'validate_multiple_periods', 
    'run_step1_validation',
    
    # Step 2
    'validate_step2_coordinates',
    'run_step2_validation',
    
    # Step 2B
    'validate_step2b_seasonal_data',
    'run_step2b_validation',
    
    # Step 3
    'validate_step3_matrices',
    'run_step3_validation',
    
    # Step 4
    'validate_weather_files',
    'validate_store_altitudes',
    'validate_weather_by_period',
    'run_step4_validation',
    
    # Step 5
    'validate_step5_feels_like_temperature',
    'validate_feels_like_calculation_quality',
    'run_step5_validation',
    
    # Step 6
    'validate_step6_clustering',
    'run_step6_validation',
    
    # Step 7
    'validate_step7_missing_category_rule',
    'run_step7_validation',
    
    # Step 8
    'validate_step8_comprehensive',
    'validate_step8_inputs_comprehensive',
    'run_step8_validation',
    
    # Step 9
    'validate_step9_comprehensive',
    'validate_step9_inputs_comprehensive',
    'run_step9_validation',
    
    # Step 10
    'validate_step10_comprehensive',
    'validate_step10_inputs',
    'run_step10_validation',
    
    # Step 11
    'validate_step11_comprehensive',
    'validate_step11_inputs_comprehensive',
    'run_step11_validation',
    
    # Step 12
    'validate_step12_comprehensive',
    'validate_step12_inputs_comprehensive',
    'run_step12_validation',
    
    # Step 13
    'validate_step13_comprehensive',
    'run_step13_validation',
    
    # Step 14
    'validate_step14_fast_fish_format',
    'run_step14_validation',
    
    # Step 19
    'run_step19_validation',
    
    # Comprehensive Testing
    'ComprehensiveTestRunner',
    'run_comprehensive_validation',
    
    # Advanced Steps (15-36)
    'validate_step15_historical_baseline',
    'validate_step16_comparison_tables',
    'validate_step17_augment_recommendations',
    'validate_step18_validate_results',
    'validate_step19_detailed_spu_breakdown',
    'validate_step20_data_validation',
    'validate_steps_21_24_labeling_analysis',
    'validate_steps_25_29_analysis_optimization',
    'validate_steps_30_36_merchandising_delivery',
    'run_steps_15_36_validation'
]

