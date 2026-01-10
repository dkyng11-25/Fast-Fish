import logging
from typing import Optional


class PipelineLogger:
    """Centralized logging for the entire pipeline.

    Provides a thin wrapper around Python's standard logging with
    optional context tagging.
    """

    def __init__(self, name: str = "Pipeline", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, message: str, context: Optional[str] = None) -> None:
        if context:
            self.logger.info(f"[{context}] {message}")
        else:
            self.logger.info(message)

    def warning(self, message: str, context: Optional[str] = None) -> None:
        if context:
            self.logger.warning(f"[{context}] {message}")
        else:
            self.logger.warning(message)

    def error(self, message: str, context: Optional[str] = None) -> None:
        if context:
            self.logger.error(f"[{context}] {message}")
        else:
            self.logger.error(message)

    def debug(self, message: str, context: Optional[str] = None) -> None:
        if context:
            self.logger.debug(f"[{context}] {message}")
        else:
            self.logger.debug(message)


