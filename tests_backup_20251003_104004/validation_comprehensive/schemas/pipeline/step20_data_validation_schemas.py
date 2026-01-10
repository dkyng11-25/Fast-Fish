import pandas as pd
#!/usr/bin/env python3
"""
Step 20 Data Validation Validation Schemas

This module contains schemas for data validation from Step 20.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class DataValidationReportSchema(pa.DataFrameModel):
    """Schema for data validation report from Step 20."""
    
    # Validation metadata
    validation_id: Series[str] = pa.Field()
    validation_timestamp: Series[str] = pa.Field()
    data_source: Series[str] = pa.Field()
    validation_type: Series[str] = pa.Field()  # "completeness", "accuracy", "consistency", "integrity"
    
    # Data scope
    total_records: Series[int] = pa.Field(ge=0)
    validated_records: Series[int] = pa.Field(ge=0)
    failed_records: Series[int] = pa.Field(ge=0)
    
    # Quality scores
    overall_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    completeness_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    accuracy_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    consistency_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    integrity_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Issue summary
    critical_issues: Series[int] = pa.Field(ge=0)
    major_issues: Series[int] = pa.Field(ge=0)
    minor_issues: Series[int] = pa.Field(ge=0)
    warnings: Series[int] = pa.Field(ge=0)
    
    # Validation status
    validation_passed: Series[bool] = pa.Field()
    requires_manual_review: Series[bool] = pa.Field()
    data_ready_for_production: Series[bool] = pa.Field()
    
    # Recommendations
    improvement_recommendations: Series[str] = pa.Field(nullable=True)
    next_validation_date: Series[str] = pa.Field(nullable=True)


class DataQualityIssueSchema(pa.DataFrameModel):
    """Schema for individual data quality issues."""
    
    # Issue identification
    issue_id: Series[str] = pa.Field()
    issue_type: Series[str] = pa.Field()  # "missing_data", "invalid_format", "out_of_range", "duplicate"
    issue_severity: Series[str] = pa.Field()  # "critical", "major", "minor", "warning"
    
    # Data context
    table_name: Series[str] = pa.Field()
    column_name: Series[str] = pa.Field()
    record_id: Series[str] = pa.Field(nullable=True)
    
    # Issue details
    issue_description: Series[str] = pa.Field()
    expected_value: Series[str] = pa.Field(nullable=True)
    actual_value: Series[str] = pa.Field(nullable=True)
    
    # Impact assessment
    business_impact: Series[str] = pa.Field(nullable=True)  # "high", "medium", "low"
    affected_records: Series[int] = pa.Field(ge=0)
    potential_data_loss: Series[bool] = pa.Field()
    
    # Resolution
    auto_fixable: Series[bool] = pa.Field()
    suggested_fix: Series[str] = pa.Field(nullable=True)
    resolution_priority: Series[str] = pa.Field()  # "immediate", "high", "medium", "low"
    
    # Validation metadata
    detected_by: Series[str] = pa.Field()
    detection_timestamp: Series[str] = pa.Field()
    status: Series[str] = pa.Field()  # "open", "in_progress", "resolved", "ignored"


class ValidationRuleSchema(pa.DataFrameModel):
    """Schema for validation rules applied."""
    
    # Rule identification
    rule_id: Series[str] = pa.Field()
    rule_name: Series[str] = pa.Field()
    rule_category: Series[str] = pa.Field()  # "data_type", "range", "format", "business_logic"
    
    # Rule definition
    rule_description: Series[str] = pa.Field()
    rule_expression: Series[str] = pa.Field(nullable=True)
    rule_parameters: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Application scope
    table_name: Series[str] = pa.Field()
    column_name: Series[str] = pa.Field(nullable=True)
    applies_to_all_records: Series[bool] = pa.Field()
    
    # Rule performance
    records_checked: Series[int] = pa.Field(ge=0)
    violations_found: Series[int] = pa.Field(ge=0)
    rule_execution_time: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Rule status
    rule_enabled: Series[bool] = pa.Field()
    rule_priority: Series[int] = pa.Field(ge=1, le=10)
    last_updated: Series[str] = pa.Field()
