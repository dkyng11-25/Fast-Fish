#!/usr/bin/env python3
"""
Step 36: Unified Delivery Builder Schemas

Validation schemas for Step 36 - Unified Delivery Builder.
This step creates unified delivery formats for all pipeline outputs.

Author: Data Pipeline
Date: 2025-09-16
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
import numpy as np


class UnifiedDeliverySchema(BaseModel):
    """Schema for unified delivery data validation"""
    str_code: str = Field(..., description="Store code")
    delivery_type: str = Field(..., description="Type of delivery")
    delivery_content: Dict[str, Any] = Field(..., description="Delivery content")
    priority: int = Field(..., ge=1, le=5, description="Delivery priority (1=highest, 5=lowest)")
    status: str = Field(..., description="Delivery status")
    created_timestamp: str = Field(..., description="Creation timestamp")
    updated_timestamp: Optional[str] = Field(None, description="Last update timestamp")
    
    @field_validator('delivery_type')
    @classmethod
    def validate_delivery_type(cls, value):
        valid_types = ['recommendation', 'alert', 'report', 'dashboard', 'data_export']
        if value not in valid_types:
            raise ValueError(f'Delivery type must be one of: {valid_types}')
        return value
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, value):
        valid_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
        if value not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return value


class DeliveryContentSchema(BaseModel):
    """Schema for delivery content validation"""
    content_id: str = Field(..., description="Content identifier")
    content_type: str = Field(..., description="Type of content")
    content_data: Dict[str, Any] = Field(..., description="Content data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Content metadata")
    validation_status: str = Field(..., description="Content validation status")
    
    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, value):
        valid_types = ['text', 'numeric', 'tabular', 'json', 'xml', 'binary']
        if value not in valid_types:
            raise ValueError(f'Content type must be one of: {valid_types}')
        return value
    
    @field_validator('validation_status')
    @classmethod
    def validate_validation_status(cls, value):
        valid_statuses = ['valid', 'invalid', 'pending', 'error']
        if value not in valid_statuses:
            raise ValueError(f'Validation status must be one of: {valid_statuses}')
        return value


class DeliveryMetadataSchema(BaseModel):
    """Schema for delivery metadata validation"""
    delivery_id: str = Field(..., description="Delivery identifier")
    source_step: int = Field(..., ge=1, le=37, description="Source pipeline step")
    target_audience: str = Field(..., description="Target audience")
    delivery_format: str = Field(..., description="Delivery format")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    checksum: Optional[str] = Field(None, description="File checksum")
    compression: Optional[str] = Field(None, description="Compression type")
    
    @field_validator('target_audience')
    @classmethod
    def validate_target_audience(cls, value):
        valid_audiences = ['store_manager', 'regional_manager', 'executive', 'analyst', 'system']
        if value not in valid_audiences:
            raise ValueError(f'Target audience must be one of: {valid_audiences}')
        return value
    
    @field_validator('delivery_format')
    @classmethod
    def validate_delivery_format(cls, value):
        valid_formats = ['csv', 'excel', 'json', 'pdf', 'html', 'xml', 'txt']
        if value not in valid_formats:
            raise ValueError(f'Delivery format must be one of: {valid_formats}')
        return value


class Step36InputSchema(BaseModel):
    """Schema for Step 36 input validation"""
    source_data: List[Dict[str, Any]] = Field(..., min_length=1, description="Source data from previous steps")
    delivery_config: Dict[str, Any] = Field(..., description="Delivery configuration")
    target_formats: List[str] = Field(..., min_length=1, description="Target delivery formats")
    output_directory: str = Field(..., description="Output directory path")
    
    @field_validator('target_formats')
    @classmethod
    def validate_target_formats(cls, value):
        valid_formats = ['csv', 'excel', 'json', 'pdf', 'html', 'xml']
        for format_type in value:
            if format_type not in valid_formats:
                raise ValueError(f'Invalid target format: {format_type}')
        return value


class Step36OutputSchema(BaseModel):
    """Schema for Step 36 output validation"""
    unified_deliveries: List[UnifiedDeliverySchema] = Field(..., min_length=1, description="Unified delivery data")
    delivery_contents: List[DeliveryContentSchema] = Field(..., min_length=1, description="Delivery content data")
    delivery_metadata: List[DeliveryMetadataSchema] = Field(..., min_length=1, description="Delivery metadata")
    delivery_summary: Dict[str, Any] = Field(..., description="Delivery summary statistics")
    
    @field_validator('unified_deliveries')
    @classmethod
    def validate_delivery_consistency(cls, value):
        if not value:
            raise ValueError('Unified deliveries cannot be empty')
        
        # Check for unique delivery IDs
        delivery_ids = [delivery.delivery_id for delivery in value if hasattr(delivery, 'delivery_id')]
        if len(delivery_ids) != len(set(delivery_ids)):
            raise ValueError('Delivery IDs must be unique')
        
        return value


class Step36ValidationSchema(BaseModel):
    """Schema for Step 36 validation results"""
    validation_passed: bool = Field(..., description="Whether validation passed")
    input_validation: Dict[str, Any] = Field(..., description="Input validation results")
    output_validation: Dict[str, Any] = Field(..., description="Output validation results")
    delivery_validation: Dict[str, Any] = Field(..., description="Delivery validation results")
    format_validation: Dict[str, Any] = Field(..., description="Format validation results")
    file_validation: Dict[str, Any] = Field(..., description="File validation results")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    statistics: Dict[str, Any] = Field(..., description="Validation statistics")


class DeliveryQualitySchema(BaseModel):
    """Schema for delivery quality validation"""
    delivery_id: str = Field(..., description="Delivery identifier")
    quality_score: float = Field(..., ge=0, le=1, description="Overall quality score")
    completeness_score: float = Field(..., ge=0, le=1, description="Completeness score")
    accuracy_score: float = Field(..., ge=0, le=1, description="Accuracy score")
    consistency_score: float = Field(..., ge=0, le=1, description="Consistency score")
    timeliness_score: float = Field(..., ge=0, le=1, description="Timeliness score")
    quality_issues: List[str] = Field(default_factory=list, description="Quality issues found")
    
    @field_validator('quality_score')
    @classmethod
    def validate_quality_score(cls, value):
        if value < 0.7:
            raise ValueError('Quality score should be at least 0.7 for reliable delivery')
        return value


# Export all schemas
__all__ = [
    'UnifiedDeliverySchema',
    'DeliveryContentSchema',
    'DeliveryMetadataSchema',
    'Step36InputSchema',
    'Step36OutputSchema',
    'Step36ValidationSchema',
    'DeliveryQualitySchema'
]
