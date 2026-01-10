from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional

from abc import ABC, abstractmethod

import pandas as pd
import os
from datetime import datetime

from src.core.logger import PipelineLogger


class Repository(ABC):
    """Base repository class with logging support."""
    def __init__(self, logger: PipelineLogger):
        self.logger = logger
        self.repo_name = self.__class__.__name__

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all data from the repository."""
        raise NotImplementedError

    @abstractmethod
    def save(self, data: pd.DataFrame) -> None:
        """Save data to the repository."""
        raise NotImplementedError


class ReadOnlyRepository(Repository):
    """Base class for read-only repositories."""
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def save(self, data: pd.DataFrame) -> None:
        """Not implemented for read-only repositories."""
        raise NotImplementedError("ReadOnlyRepository is read-only")


class WriteableRepository(Repository):
    """Base class for writeable repositories."""
    @abstractmethod
    def save(self, data: pd.DataFrame) -> None:
        raise NotImplementedError

    def get_all(self) -> List[Dict[str, Any]]:
        """Not implemented for write-only repositories."""
        raise NotImplementedError("WriteableRepository is write-only")


