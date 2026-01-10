import pandas as pd
#!/usr/bin/env python3
"""
Step 18 Validate Results Validation Schemas

This module contains schemas for results validation from Step 18.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class ValidationResultsSchema(pa.DataFrameModel):
    """Schema for validation results from Step 18."""
    
    # Validation metadata
    validation_id: Series[str] = pa.Field()
    validation_timestamp: Series[str] = pa.Field()
    validation_type: Series[str] = pa.Field()  # "data_quality", "business_logic", "consistency"
    
    # Store and product identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999, nullable=True)
    spu_code: Series[str] = pa.Field(nullable=True)
    sub_cate_name: Series[str] = pa.Field(nullable=True)
    
    # Validation results
    validation_passed: Series[bool] = pa.Field()
    validation_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    validation_issues: Series[str] = pa.Field(nullable=True)
    
    # Data quality metrics
    completeness_score: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    accuracy_score: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    consistency_score: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Business logic validation
    business_rule_compliance: Series[bool] = pa.Field(nullable=True)
    business_rule_violations: Series[str] = pa.Field(nullable=True)
    
    # Recommendations
    recommended_action: Series[str] = pa.Field(nullable=True)
    priority_level: Series[str] = pa.Field(nullable=True)  # "critical", "high", "medium", "low"
    
    # Validation details
    validation_details: Series[str] = pa.Field(nullable=True)
    validation_notes: Series[str] = pa.Field(nullable=True)


class DataQualityReportSchema(pa.DataFrameModel):
    """Schema for data quality report from Step 18."""
    
    # Report metadata
    report_id: Series[str] = pa.Field()
    report_timestamp: Series[str] = pa.Field()
    data_source: Series[str] = pa.Field()
    
    # Quality metrics
    total_records: Series[int] = pa.Field(ge=0)
    valid_records: Series[int] = pa.Field(ge=0)
    invalid_records: Series[int] = pa.Field(ge=0)
    quality_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    
    # Issue breakdown
    missing_data_issues: Series[int] = pa.Field(ge=0)
    format_issues: Series[int] = pa.Field(ge=0)
    logic_issues: Series[int] = pa.Field(ge=0)
    consistency_issues: Series[int] = pa.Field(ge=0)
    
    # Recommendations
    improvement_recommendations: Series[str] = pa.Field()
    critical_issues: Series[str] = pa.Field(nullable=True)
    
    # Validation status
    overall_status: Series[str] = pa.Field()  # "passed", "warning", "failed"
    requires_attention: Series[bool] = pa.Field()


class BusinessLogicValidationSchema(pa.DataFrameModel):
    """Schema for business logic validation results."""
    
    # Validation context
    validation_rule: Series[str] = pa.Field()
    validation_category: Series[str] = pa.Field()  # "pricing", "inventory", "recommendations"
    
    # Store and product context
    str_code: Series[int] = pa.Field(ge=10000, le=99999, nullable=True)
    spu_code: Series[str] = pa.Field(nullable=True)
    
    # Validation results
    rule_passed: Series[bool] = pa.Field()
    rule_violation_type: Series[str] = pa.Field(nullable=True)
    rule_violation_description: Series[str] = pa.Field(nullable=True)
    
    # Business impact
    business_impact: Series[str] = pa.Field(nullable=True)  # "low", "medium", "high", "critical"
    potential_revenue_impact: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Corrective actions
    suggested_correction: Series[str] = pa.Field(nullable=True)
    correction_priority: Series[str] = pa.Field(nullable=True)
    
    # Validation metadata
    validation_timestamp: Series[str] = pa.Field()
    validator_version: Series[str] = pa.Field()
