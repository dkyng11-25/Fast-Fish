import json
import logging
import os
from typing import Any, Dict


class BaseDataLoader:
    """Minimal base class to support TrendinessDataLoader dependencies."""

    def __init__(self, output_dir: str = 'output', data_dir: str = 'data') -> None:
        self.output_dir = output_dir
        self.data_dir = data_dir
        self.logger = logging.getLogger(self.__class__.__name__)

    def _load_json_safe(self, path: str, required: bool = False) -> Dict[str, Any]:
        try:
            if not os.path.exists(path):
                if required:
                    self.logger.error(f"Required JSON not found: {path}")
                else:
                    self.logger.info(f"Optional JSON not found: {path}")
                return {}
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as exc:
            self.logger.error(f"Failed to load JSON {path}: {exc}")
            return {}


