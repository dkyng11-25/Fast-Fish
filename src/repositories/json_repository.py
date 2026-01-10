#!/usr/bin/env python3
"""
JSON Repository - Handles JSON file I/O operations

This repository abstracts JSON file operations for:
- Progress tracking
- Configuration storage
- Metadata persistence
"""

from typing import Dict, Any, Optional
import json
from pathlib import Path
from src.core.logger import PipelineLogger
from .base import Repository


class JsonFileError(Exception):
    """Raised when JSON file operations fail."""
    pass


class JsonFileRepository(Repository):
    """Repository for JSON file operations."""
    
    def __init__(self, file_path: str, logger: PipelineLogger):
        """
        Initialize JSON file repository.
        
        Args:
            file_path: Path to JSON file
            logger: PipelineLogger instance for logging
        """
        super().__init__(logger)
        self.file_path = Path(file_path)
    
    def load(self) -> Dict[str, Any]:
        """
        Load data from JSON file.
        
        Returns:
            Dict[str, Any]: Loaded JSON data
            
        Raises:
            JsonFileError: If file cannot be read
        """
        try:
            if not self.file_path.exists():
                self.logger.info(
                    f"JSON file does not exist: {self.file_path}, returning empty dict",
                    self.repo_name
                )
                return {}
            
            self.logger.info(f"Loading JSON from {self.file_path}", self.repo_name)
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(
                f"Successfully loaded JSON with {len(data)} keys",
                self.repo_name
            )
            
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format: {str(e)}", self.repo_name)
            raise JsonFileError(f"Invalid JSON format: {str(e)}") from e
            
        except Exception as e:
            self.logger.error(f"Error loading JSON: {str(e)}", self.repo_name)
            raise JsonFileError(f"Error loading JSON: {str(e)}") from e
    
    def save(self, data: Dict[str, Any], indent: int = 2) -> None:
        """
        Save data to JSON file.
        
        Args:
            data: Dictionary to save as JSON
            indent: Indentation level for pretty printing (default: 2)
            
        Raises:
            JsonFileError: If file cannot be written
        """
        try:
            # Create parent directory if it doesn't exist
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(
                f"Saving JSON to {self.file_path} ({len(data)} keys)",
                self.repo_name
            )
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, default=str)
            
            self.logger.info("JSON saved successfully", self.repo_name)
            
        except Exception as e:
            self.logger.error(f"Error saving JSON: {str(e)}", self.repo_name)
            raise JsonFileError(f"Error saving JSON: {str(e)}") from e
    
    def exists(self) -> bool:
        """
        Check if JSON file exists.
        
        Returns:
            bool: True if file exists
        """
        return self.file_path.exists()
    
    def delete(self) -> None:
        """
        Delete JSON file if it exists.
        
        Raises:
            JsonFileError: If file cannot be deleted
        """
        try:
            if self.file_path.exists():
                self.file_path.unlink()
                self.logger.info(f"Deleted JSON file: {self.file_path}", self.repo_name)
            else:
                self.logger.info(f"JSON file does not exist: {self.file_path}", self.repo_name)
                
        except Exception as e:
            self.logger.error(f"Error deleting JSON: {str(e)}", self.repo_name)
            raise JsonFileError(f"Error deleting JSON: {str(e)}") from e


class ProgressTrackingRepository(JsonFileRepository):
    """Specialized repository for download progress tracking."""
    
    DEFAULT_PROGRESS = {
        'completed_periods': [],
        'current_period': None,
        'completed_stores': [],
        'failed_stores': [],
        'last_update': None,
        'vpn_switches': 0
    }
    
    def load(self) -> Dict[str, Any]:
        """
        Load progress data, returning default structure if file doesn't exist.
        
        Returns:
            Dict[str, Any]: Progress data with guaranteed structure
        """
        if not self.file_path.exists():
            self.logger.info(
                "No existing progress file, returning default structure",
                self.repo_name
            )
            return self.DEFAULT_PROGRESS.copy()
        
        try:
            data = super().load()
            
            # Ensure all required keys exist
            for key, default_value in self.DEFAULT_PROGRESS.items():
                if key not in data:
                    data[key] = default_value
            
            return data
            
        except JsonFileError:
            self.logger.warning(
                "Error loading progress, returning default structure",
                self.repo_name
            )
            return self.DEFAULT_PROGRESS.copy()
    
    def update_progress(
        self,
        completed_period: Optional[str] = None,
        completed_store: Optional[str] = None,
        failed_store: Optional[str] = None,
        vpn_switch: bool = False,
        current_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update progress tracking with new information.
        
        Args:
            completed_period: Period that was completed
            completed_store: Store that was successfully processed
            failed_store: Store that failed processing
            vpn_switch: Whether a VPN switch occurred
            current_period: Current period being processed
            
        Returns:
            Dict[str, Any]: Updated progress data
        """
        from datetime import datetime
        
        progress = self.load()
        
        if completed_period and completed_period not in progress['completed_periods']:
            progress['completed_periods'].append(completed_period)
            self.logger.info(f"Marked period {completed_period} as completed", self.repo_name)
        
        if completed_store and completed_store not in progress['completed_stores']:
            progress['completed_stores'].append(completed_store)
        
        if failed_store and failed_store not in progress['failed_stores']:
            progress['failed_stores'].append(failed_store)
        
        if vpn_switch:
            progress['vpn_switches'] += 1
            self.logger.info(f"VPN switch recorded (total: {progress['vpn_switches']})", self.repo_name)
        
        if current_period:
            progress['current_period'] = current_period
        
        progress['last_update'] = datetime.now().isoformat()
        
        self.save(progress)
        return progress
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all progress data (alias for load()).
        
        Returns:
            Dict[str, Any]: Progress data
        """
        return self.load()
