from __future__ import annotations

from typing import List, Optional

from .context import StepContext
from .logger import PipelineLogger
from .step import Step


class Pipeline:
    """The master orchestrator for a sequence of steps."""

    def __init__(self, steps: List[Step], logger: PipelineLogger):
        self.steps = steps
        self.logger = logger

    def run(self, initial_context: Optional[StepContext] = None) -> StepContext:
        self.logger.info("Starting pipeline execution.", "Pipeline")
        context = initial_context or StepContext()
        for step in self.steps:
            context = step.execute(context)
        self.logger.info("Pipeline execution completed successfully.", "Pipeline")
        return context


