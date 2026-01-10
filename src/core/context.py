from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd


class StepContext:
    """Stateful object that carries data and metadata through the pipeline."""

    def __init__(self, data: Optional[pd.DataFrame] = None):
        self._data: Optional[pd.DataFrame] = data
        self._state: Dict[str, Any] = {}
        self.data: Dict[str, Any] = {}  # For step-specific data storage

    def get_data(self) -> pd.DataFrame:
        if self._data is None:
            raise ValueError("Primary data has not been set in the context.")
        return self._data

    def set_data(self, data: pd.DataFrame) -> None:
        self._data = data

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        state_keys = list(self._state.keys())
        data_shape = self._data.shape if self._data is not None else "No data"
        return f"StepContext(data_shape={data_shape}, state_keys={state_keys})"


