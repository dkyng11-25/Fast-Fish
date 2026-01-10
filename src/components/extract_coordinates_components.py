#!/usr/bin/env python3

"""
Extract Coordinates Components (Modular Components for Step 2)

This module contains the modular components for coordinate extraction and SPU processing.
Separated from the main step implementation for better maintainability and testability.

✅ MODULAR: Clean separation of concerns
✅ TESTABLE: Easy to mock and test individually
✅ REUSABLE: Components can be used in different contexts
✅ MAINTAINABLE: Clear responsibilities for each component

Author: Data Pipeline
Date: 2025-01-27
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import pandas as pd
import os

from src.core.logger import PipelineLogger
from src.repositories.base import Repository
from dataclasses import dataclass


@dataclass
class PeriodData:
    """Data structure for a specific period (matches test expectations)."""
    yyyymm: str
    half: str
    store_data: Optional[pd.DataFrame] = None
    category_data: Optional[pd.DataFrame] = None
    spu_data: Optional[pd.DataFrame] = None
    coordinate_count: int = 0


class CoordinateWriterRepository(Repository):
    """Repository for writing coordinate data."""

    def __init__(self, output_path: str, logger: PipelineLogger):
        super().__init__(logger)
        self.output_path = output_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Not used for writing repository."""
        raise NotImplementedError("CoordinateWriterRepository is write-only")

    def save(self, data: pd.DataFrame) -> None:
        """Save coordinate data to file."""
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        data.to_csv(self.output_path, index=False)
        self.logger.info(f"Saved {len(data)} coordinate records to {self.output_path}", self.repo_name)


class SpuMappingWriterRepository(Repository):
    """Repository for writing SPU mapping data."""

    def __init__(self, output_path: str, logger: PipelineLogger):
        super().__init__(logger)
        self.output_path = output_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Not used for writing repository."""
        raise NotImplementedError("SpuMappingWriterRepository is write-only")

    def save(self, data: pd.DataFrame) -> None:
        """Save SPU mapping data to file."""
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        data.to_csv(self.output_path, index=False)
        self.logger.info(f"Saved {len(data)} SPU mapping records to {self.output_path}", self.repo_name)


class SpuMetadataWriterRepository(Repository):
    """Repository for writing SPU metadata."""

    def __init__(self, output_path: str, logger: PipelineLogger):
        super().__init__(logger)
        self.output_path = output_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Not used for writing repository."""
        raise NotImplementedError("SpuMetadataWriterRepository is write-only")

    def save(self, data: pd.DataFrame) -> None:
        """Save SPU metadata to file."""
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        data.to_csv(self.output_path, index=False)
        self.logger.info(f"Saved {len(data)} SPU metadata records to {self.output_path}", self.repo_name)


class MultiPeriodDataRepository(Repository):
    """Repository for loading multi-period data with structured period objects."""

    def __init__(self, data_path: str, logger: PipelineLogger):
        super().__init__(logger)
        self.data_path = data_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all period data objects."""
        # This is a mock interface for testing - actual implementation would
        # scan directories and return structured period data
        return []

    def save(self, data: pd.DataFrame) -> None:
        """Not implemented for data repository."""
        raise NotImplementedError("MultiPeriodDataRepository does not support save operation")
